#!/usr/bin/env python3
"""Deploy an app to Railway via GitHub repo + Railway GraphQL API."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx


RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
RAILWAY_API = "https://backboard.railway.app/graphql/v2"
GITHUB_ORG = "menonpg"


def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def railway_gql(query: str, variables: dict | None = None) -> dict:
    resp = httpx.post(
        RAILWAY_API,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {RAILWAY_TOKEN}", "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        print(f"Railway API error: {data['errors']}", file=sys.stderr)
        sys.exit(1)
    return data["data"]


def github_api(method: str, path: str, payload: dict | None = None) -> dict:
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com{path}"
    resp = httpx.request(method, url, json=payload, headers=headers, timeout=20)
    if resp.status_code not in (200, 201, 204):
        print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json() if resp.content else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--description", default="Deployed by ThinkCreate.AI")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"ERROR: source dir not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    if not (source_dir / "Dockerfile").exists():
        print("ERROR: no Dockerfile found. Write a Dockerfile first.", file=sys.stderr)
        sys.exit(1)

    if not RAILWAY_TOKEN:
        print("ERROR: RAILWAY_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    repo_name = args.project_name
    github_repo = f"{GITHUB_ORG}/{repo_name}"

    # ── Step 1: Create GitHub repo ──────────────────────────────────────────
    print(f"Creating GitHub repo: {github_repo}...")
    try:
        github_api("POST", "/user/repos", {
            "name": repo_name,
            "description": args.description,
            "private": False,
            "auto_init": False,
        })
        print(f"  Created: https://github.com/{github_repo}")
    except SystemExit:
        # Might already exist
        print(f"  Repo may already exist, continuing...")

    # ── Step 2: Push code to GitHub ─────────────────────────────────────────
    print("Pushing code to GitHub...")
    with tempfile.TemporaryDirectory() as tmpdir:
        import shutil
        app_dir = os.path.join(tmpdir, "app")
        shutil.copytree(str(source_dir), app_dir)

        run(["git", "init", "-b", "main"], cwd=app_dir)
        run(["git", "config", "user.email", "monica@themenonlab.com"], cwd=app_dir)
        run(["git", "config", "user.name", "Monica (ThinkCreate.AI)"], cwd=app_dir)
        run(["git", "add", "-A"], cwd=app_dir)
        run(["git", "commit", "-m", f"init: {args.description}"], cwd=app_dir)
        run([
            "git", "remote", "add", "origin",
            f"https://x-access-token:{GITHUB_TOKEN}@github.com/{github_repo}.git"
        ], cwd=app_dir)
        run(["git", "push", "-u", "origin", "main", "--force"], cwd=app_dir)
        print(f"  Pushed to: https://github.com/{github_repo}")

    # ── Step 3: Create Railway project ──────────────────────────────────────
    print("Creating Railway project...")
    proj_data = railway_gql("""
        mutation CreateProject($name: String!, $description: String) {
            projectCreate(input: { name: $name, description: $description }) {
                id
                name
                defaultEnvironment { id }
            }
        }
    """, {"name": repo_name, "description": args.description})

    project_id = proj_data["projectCreate"]["id"]
    env_id = proj_data["projectCreate"]["defaultEnvironment"]["id"]
    print(f"  Project ID: {project_id}")

    # ── Step 4: Create service linked to GitHub repo ─────────────────────────
    print("Creating Railway service...")
    svc_data = railway_gql("""
        mutation CreateService($projectId: String!, $name: String!) {
            serviceCreate(input: { projectId: $projectId, name: $name }) {
                id
                name
            }
        }
    """, {"projectId": project_id, "name": repo_name})

    service_id = svc_data["serviceCreate"]["id"]

    # Connect to GitHub repo
    railway_gql("""
        mutation ConnectRepo($id: String!, $repo: String!) {
            serviceConnect(id: $id, input: { repo: $repo, branch: "main" }) { id }
        }
    """, {"id": service_id, "repo": github_repo})
    print(f"  Service connected to {github_repo}")

    # ── Step 5: Generate public domain ──────────────────────────────────────
    print("Generating public domain...")
    domain_data = railway_gql("""
        mutation GenDomain($serviceId: String!, $envId: String!) {
            serviceDomainCreate(input: { serviceId: $serviceId, environmentId: $envId }) {
                domain
            }
        }
    """, {"serviceId": service_id, "envId": env_id})

    domain = domain_data["serviceDomainCreate"]["domain"]
    public_url = f"https://{domain}"

    # ── Step 6: Trigger deploy ───────────────────────────────────────────────
    print("Triggering deployment...")
    railway_gql("""
        mutation Redeploy($serviceId: String!, $envId: String!) {
            serviceInstanceRedeploy(serviceId: $serviceId, environmentId: $envId)
        }
    """, {"serviceId": service_id, "envId": env_id})

    print(f"\n✅ Deployed to Railway!")
    print(f"🌐 Public URL: {public_url}")
    print(f"📦 GitHub repo: https://github.com/{github_repo}")
    print(f"🚂 Railway project: https://railway.app/project/{project_id}")
    print(f"⏱  First build takes 2–3 minutes. Check Railway dashboard for logs.")
    print(f"\nℹ  To add environment variables:")
    print(f"   Railway dashboard → project '{repo_name}' → Variables")


if __name__ == "__main__":
    main()
