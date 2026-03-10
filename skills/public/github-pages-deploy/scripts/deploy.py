#!/usr/bin/env python3
"""Deploy a static site to menonpg/thinkcreateai-sites (GitHub Pages)."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SITES_REPO = "menonpg/thinkcreateai-sites"
PAGES_BASE = "https://sites.thinkcreateai.com"


def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"ERROR running {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Deploy static site to GitHub Pages")
    parser.add_argument("--source-dir", required=True, help="Directory containing site files")
    parser.add_argument("--slug", required=True, help="URL slug (e.g. my-site-20260310)")
    parser.add_argument("--title", default="", help="Human-readable site title")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"ERROR: source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    if not (source_dir / "index.html").exists():
        print(f"ERROR: no index.html found in {source_dir}", file=sys.stderr)
        sys.exit(1)

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("ERROR: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = os.path.join(tmpdir, "sites-repo")

        print(f"Cloning {SITES_REPO}...")
        run([
            "git", "clone", "--depth=1",
            f"https://x-access-token:{github_token}@github.com/{SITES_REPO}.git",
            repo_dir,
        ])

        # Configure git identity
        run(["git", "config", "user.email", "monica@themenonlab.com"], cwd=repo_dir)
        run(["git", "config", "user.name", "Monica (ThinkCreate.AI)"], cwd=repo_dir)

        # Copy site files into sites/{slug}/
        site_target = os.path.join(repo_dir, "sites", args.slug)
        if os.path.exists(site_target):
            shutil.rmtree(site_target)
        shutil.copytree(str(source_dir), site_target)

        # Stage and commit
        run(["git", "add", "-A"], cwd=repo_dir)

        title = args.title or args.slug
        commit_msg = f"deploy: {title} → sites/{args.slug}"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=repo_dir, capture_output=True, text=True
        )
        if result.returncode != 0 and "nothing to commit" in result.stdout + result.stderr:
            print("No changes to deploy (site already up to date)")
        else:
            print(f"Pushing to GitHub...")
            run(["git", "push", "origin", "main"], cwd=repo_dir)

    live_url = f"{PAGES_BASE}/sites/{args.slug}/"
    print(f"\n✅ Deployed successfully!")
    print(f"🌐 Live URL: {live_url}")
    print(f"⏱  GitHub Pages may take 1–2 minutes to update on first deploy.")
    return live_url


if __name__ == "__main__":
    main()
