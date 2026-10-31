"use client";

import { useEffect, useState } from "react";

import { fetchHealth } from "@/lib/api";

type ApiStatus = "checking" | "ok" | "unreachable";

const NAV_LINKS = [
  { label: "Triage", href: "#" },
  { label: "Solicitation", href: "/solicitation" },
  { label: "Quotes", href: "#" },
  { label: "Orders", href: "#" },
];

export default function Home() {
  const [status, setStatus] = useState<ApiStatus>("checking");

  useEffect(() => {
    let cancelled = false;
    async function checkApi() {
      let next: ApiStatus = "ok";
      try {
        await fetchHealth();
      } catch {
        next = "unreachable";
      }
      if (!cancelled) setStatus(next);
    }
    void checkApi();
    return () => {
      cancelled = true;
    };
  }, []);

  const statusText =
    status === "checking"
      ? "API: checking…"
      : status === "ok"
        ? "API: ok"
        : "API: unreachable";

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-3xl flex-col gap-8 px-6 py-10">
      <header className="flex items-baseline justify-between border-b pb-4">
        <h1 className="text-2xl font-semibold">KounOS</h1>
        <p role="status" aria-live="polite" className="text-sm text-muted-foreground">
          {statusText}
        </p>
      </header>

      <nav aria-label="Placeholder">
        <ul className="flex gap-6">
          {NAV_LINKS.map((link) => (
            <li key={link.label}>
              <a href={link.href} className="text-sm font-medium underline underline-offset-4">
                {link.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      <section aria-label="Ask KounOS" className="rounded-lg border p-4">
        <h2 className="text-lg font-medium">Ask KounOS</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          The assistant panel arrives in a later task.
        </p>
      </section>
    </div>
  );
}
