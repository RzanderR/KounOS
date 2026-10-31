"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { errorMessage, fetchSolicitation, passageBytesUrl } from "@/lib/api";
import type {
  KeyClause,
  Requirement,
  Solicitation,
  WordBox,
} from "@/lib/kounos-types";
import type { Selection } from "./passage-viewer";

// Client-only: react-pdf's pdf.js entry needs Promise.withResolvers (absent
// on Node 20), so the viewer never renders during prerender.
const PassageViewer = dynamic(() => import("./passage-viewer"), {
  ssr: false,
  loading: () => <p className="mt-2 text-sm text-muted-foreground">Loading viewer…</p>,
});

const DEMO_ID = "1232SA26Q0557";

function toSelection(
  kind: string,
  label: string,
  row: Requirement | KeyClause,
  source: { file: string; page: number; snippet: string },
  boxes: WordBox[],
): Selection {
  return { kind, label, file: source.file, page: source.page, snippet: source.snippet, boxes };
}

function Badge({ status }: { status: "verified" | "needs_review" | null | undefined }) {
  const verified = status === "verified";
  return (
    <span
      className={
        verified
          ? "inline-block rounded border border-emerald-700 px-2 py-0.5 text-xs font-medium text-emerald-700"
          : "inline-block rounded border border-amber-700 px-2 py-0.5 text-xs font-medium text-amber-700"
      }
    >
      {verified ? "verified" : "needs review"}
    </span>
  );
}

export default function SolicitationPage() {
  const [solicitation, setSolicitation] = useState<Solicitation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchSolicitation(DEMO_ID);
        if (!cancelled) setSolicitation(data);
      } catch (err) {
        if (!cancelled) setError(errorMessage(err));
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error !== null) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Solicitation</h1>
        <p role="alert" className="mt-4 text-sm">
          {error}
        </p>
      </main>
    );
  }
  if (solicitation === null) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Solicitation</h1>
        <p className="mt-4 text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  const viewerUrl = selection === null ? "" : passageBytesUrl(DEMO_ID, selection.file);

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold">{solicitation.title}</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {solicitation.solicitation_id} · {solicitation.agency}
      </p>
      {solicitation.provenance_note === null ||
      solicitation.provenance_note === undefined ? null : (
        <p role="note" className="mt-3 rounded border p-3 text-sm">
          {solicitation.provenance_note}
        </p>
      )}

      <section aria-label="Requirements" className="mt-8">
        <h2 className="text-lg font-medium">Requirements</h2>
        <table className="mt-2 w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2 pr-4">Line</th>
              <th className="py-2 pr-4">Description</th>
              <th className="py-2 pr-4">Qty</th>
              <th className="py-2 pr-4">Part</th>
              <th className="py-2">Citation</th>
            </tr>
          </thead>
          <tbody>
            {(solicitation.requirements ?? []).map((req) => (
              <tr key={req.line} className="border-b align-top">
                <td className="py-2 pr-4">{req.line}</td>
                <td className="py-2 pr-4">{req.description}</td>
                <td className="py-2 pr-4">
                  {req.quantity} {req.unit}
                </td>
                <td className="py-2 pr-4">{req.part_or_nsn ?? "—"}</td>
                <td className="py-2">
                  <button
                    type="button"
                    className="cursor-pointer"
                    onClick={() =>
                      req.source === null || req.source === undefined
                        ? undefined
                        : setSelection(toSelection("requirement", req.line, req, req.source, req.boxes ?? []))
                    }
                    aria-label={`Show citation for line ${req.line}`}
                  >
                    <Badge status={req.citation_status} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section aria-label="Key clauses" className="mt-8">
        <h2 className="text-lg font-medium">Key clauses</h2>
        <table className="mt-2 w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2 pr-4">Clause</th>
              <th className="py-2 pr-4">Summary</th>
              <th className="py-2">Citation</th>
            </tr>
          </thead>
          <tbody>
            {(solicitation.key_clauses ?? []).map((clause) => (
              <tr key={clause.name} className="border-b align-top">
                <td className="py-2 pr-4">{clause.name}</td>
                <td className="py-2 pr-4">{clause.summary}</td>
                <td className="py-2">
                  <button
                    type="button"
                    className="cursor-pointer"
                    onClick={() => setSelection(toSelection("clause", clause.name, clause, clause.source, clause.boxes ?? []))}
                    aria-label={`Show citation for clause ${clause.name}`}
                  >
                    <Badge status={clause.citation_status} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section aria-label="Passage viewer" className="mt-8">
        <h2 className="text-lg font-medium">Passage</h2>
        {selection === null ? (
          <p className="mt-2 text-sm text-muted-foreground">
            Select a citation badge to jump to the passage in the PDF.
          </p>
        ) : (
          <PassageViewer
            key={`${selection.file}:${selection.page}`}
            fileUrl={viewerUrl}
            selection={selection}
          />
        )}
      </section>
    </main>
  );
}
