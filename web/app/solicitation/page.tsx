"use client";

import { useEffect, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import { attachmentUrl, fetchSolicitation } from "@/lib/api";
import type {
  KeyClause,
  Requirement,
  Solicitation,
  WordBox,
} from "@/lib/kounos-types";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

const DEMO_ID = "1232SA26Q0557";
const PAGE_WIDTH = 640;

type PdfPage = {
  getViewport: (options: { scale: number }) => { width: number; height: number };
};
type PdfDoc = { getPage: (pageNumber: number) => Promise<PdfPage> };

type Selection = {
  kind: string;
  label: string;
  file: string;
  page: number;
  snippet: string;
  boxes: WordBox[];
};

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
  const [failed, setFailed] = useState(false);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [pdf, setPdf] = useState<PdfDoc | null>(null);
  const [dims, setDims] = useState<{ w: number; h: number } | null>(null);
  const [viewerError, setViewerError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const data = await fetchSolicitation(DEMO_ID);
      if (!cancelled) {
        if (data === null) setFailed(true);
        else setSolicitation(data);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    setPdf(null);
    setDims(null);
    setViewerError(false);
  }, [selection?.file]);

  useEffect(() => {
    let cancelled = false;
    async function measure() {
      if (pdf === null || selection === null) return;
      try {
        const page = await pdf.getPage(selection.page);
        const viewport = page.getViewport({ scale: 1 });
        if (!cancelled) setDims({ w: viewport.width, h: viewport.height });
      } catch {
        if (!cancelled) setViewerError(true);
      }
    }
    void measure();
    return () => {
      cancelled = true;
    };
  }, [pdf, selection]);

  if (failed) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Solicitation</h1>
        <p role="alert" className="mt-4 text-sm">
          The API is unreachable. Start it with <code>uvicorn app.main:app --reload</code> from
          api/ and reload.
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

  const viewerUrl = selection === null ? "" : attachmentUrl(DEMO_ID, selection.file);

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
          <div className="mt-2">
            <p className="text-sm">
              {selection.kind} <strong>{selection.label}</strong> · {selection.file}, page{" "}
              {selection.page} · citations checked in code
            </p>
            <blockquote className="mt-2 rounded border p-3 text-sm">“{selection.snippet}”</blockquote>
            {viewerError ? (
              <p role="alert" className="mt-2 text-sm">
                The PDF failed to render. The API serves it at {viewerUrl}.
              </p>
            ) : (
              <div className="relative mt-2 max-w-full overflow-auto border" style={{ maxWidth: PAGE_WIDTH + 2 }}>
                <Document
                  file={viewerUrl}
                  onLoadSuccess={setPdf}
                  onLoadError={() => setViewerError(true)}
                  loading={<p className="p-4 text-sm text-muted-foreground">Loading PDF…</p>}
                >
                  <Page pageNumber={selection.page} width={PAGE_WIDTH} />
                </Document>
                {dims === null
                  ? null
                  : selection.boxes.map((box, index) => (
                      <div
                        key={index}
                        aria-hidden="true"
                        className="pointer-events-none absolute border-2 border-yellow-500 bg-yellow-300/30"
                        style={{
                          left: `${(box.x0 / dims.w) * 100}%`,
                          top: `${(box.top / dims.h) * 100}%`,
                          width: `${((box.x1 - box.x0) / dims.w) * 100}%`,
                          height: `${((box.bottom - box.top) / dims.h) * 100}%`,
                        }}
                      />
                    ))}
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
