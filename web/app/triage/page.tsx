"use client";

import { useEffect, useState } from "react";

import { fetchFit, fetchNotices } from "@/lib/api";
import type { FitAssessment, Notice } from "@/lib/kounos-types";

const DEMO_NOTICE_ID = "1232SA26Q0557";

type RankedNotice = {
  notice: Notice;
  fit: FitAssessment | null;
};

function VerdictBadge({ verdict }: { verdict: string }) {
  const pursue = verdict === "pursue";
  return (
    <span
      className={
        pursue
          ? "inline-block rounded border border-emerald-700 px-2 py-0.5 text-xs font-medium text-emerald-700"
          : "inline-block rounded border border-amber-700 px-2 py-0.5 text-xs font-medium text-amber-700"
      }
    >
      {pursue ? "pursue" : "pass"}
    </span>
  );
}

export default function TriagePage() {
  const [rows, setRows] = useState<RankedNotice[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const notices = await fetchNotices();
      if (cancelled) return;
      if (notices === null) {
        setFailed(true);
        return;
      }
      const ranked = await Promise.all(
        notices.map(async (notice) => ({
          notice,
          fit: await fetchFit(notice.notice_id),
        })),
      );
      if (!cancelled) {
        ranked.sort((a, b) =>
          a.fit?.verdict === b.fit?.verdict
            ? 0
            : a.fit?.verdict === "pursue"
              ? -1
              : 1,
        );
        setRows(ranked);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (failed) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Triage</h1>
        <p role="alert" className="mt-4 text-sm">
          The API is unreachable. Start it with{" "}
          <code>uvicorn app.main:app --reload</code> from api/ and reload.
        </p>
      </main>
    );
  }
  if (rows === null) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Triage</h1>
        <p className="mt-4 text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }
  if (rows.length === 0) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Triage</h1>
        <p className="mt-4 text-sm text-muted-foreground">
          No notices yet — the triage batch lands with H16.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold">Triage</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {rows.length} notices ranked by fit — pursue or pass, with a reason per factor
      </p>

      <table className="mt-6 w-full border-collapse text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="py-2 pr-4">Notice</th>
            <th className="py-2 pr-4">Agency</th>
            <th className="py-2 pr-4">Fit</th>
            <th className="py-2">Reasons</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ notice, fit }) => (
            <tr key={notice.notice_id} className="border-b align-top">
              <td className="py-2 pr-4">
                {notice.notice_id === DEMO_NOTICE_ID ? (
                  <a className="underline" href="/solicitation">
                    {notice.title}
                  </a>
                ) : (
                  notice.title
                )}
                <span className="block text-xs text-muted-foreground">
                  {notice.notice_id}
                </span>
              </td>
              <td className="py-2 pr-4">{notice.agency}</td>
              <td className="py-2 pr-4">
                {fit === null ? (
                  <span className="text-xs text-muted-foreground">
                    scoring unavailable (H15 profile pending)
                  </span>
                ) : (
                  <VerdictBadge verdict={fit.verdict} />
                )}
              </td>
              <td className="py-2">
                {fit === null ? (
                  <span className="text-muted-foreground">—</span>
                ) : (
                  <ul className="list-disc pl-4">
                    {(fit.reasons ?? []).map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
