import { useMemo } from "react";

export function Footer() {
  const year = useMemo(() => new Date().getFullYear(), []);
  return (
    <footer className="container-md mx-auto mt-32 flex flex-col items-center justify-center">
      <hr className="from-border/0 to-border/0 m-0 h-px w-full border-none bg-linear-to-r via-white/20" />
      <div className="text-muted-foreground container mb-8 mt-8 flex flex-col items-center justify-center text-xs gap-1">
        <p>
          <a href="https://thinkcreateai.com" className="hover:text-white transition-colors">
            ThinkCreate.AI
          </a>
          {" · "}
          <a href="mailto:hello@thinkcreateai.com" className="hover:text-white transition-colors">
            Contact
          </a>
        </p>
        <p>&copy; {year} ThinkCreate.AI. All rights reserved.</p>
      </div>
    </footer>
  );
}
