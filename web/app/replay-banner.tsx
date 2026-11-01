"use client";

import { useEffect, useState } from "react";

import { fetchHealth } from "@/lib/api";

/** Shown on every screen while the API serves stored model responses (A27). */
export function ReplayBanner() {
  const [replay, setReplay] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function check() {
      try {
        const health = await fetchHealth();
        if (!cancelled) setReplay(health.demo_mode === "replay");
      } catch {
        // Each page reports an unreachable API itself; the banner only
        // answers "is replay on?".
      }
    }
    void check();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!replay) return null;
  return (
    <p
      role="status"
      className="border-b border-amber-700 bg-amber-50 px-6 py-2 text-center text-sm text-amber-900"
    >
      Replay mode: AI steps show stored responses from earlier live model runs. Every
      figure is still computed by code.
    </p>
  );
}
