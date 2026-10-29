"use client";

import { useEffect, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import type { WordBox } from "@/lib/kounos-types";

// Client-only: this module is loaded with next/dynamic { ssr: false }, so
// pdf.js never evaluates during prerender (its Node entry needs
// Promise.withResolvers, absent on Node 20).
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

const PAGE_WIDTH = 640;

type PdfPage = {
  getViewport: (options: { scale: number }) => { width: number; height: number };
};
type PdfDoc = { getPage: (pageNumber: number) => Promise<PdfPage> };

export type Selection = {
  kind: string;
  label: string;
  file: string;
  page: number;
  snippet: string;
  boxes: WordBox[];
};

export default function PassageViewer({
  fileUrl,
  selection,
}: {
  fileUrl: string;
  selection: Selection;
}) {
  const [pdf, setPdf] = useState<PdfDoc | null>(null);
  const [dims, setDims] = useState<{ w: number; h: number } | null>(null);
  const [viewerError, setViewerError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function measure() {
      if (pdf === null) return;
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
  }, [pdf, selection.page]);

  return (
    <div className="mt-2">
      <p className="text-sm">
        {selection.kind} <strong>{selection.label}</strong> · {selection.file}, page{" "}
        {selection.page} · citations checked in code
      </p>
      <blockquote className="mt-2 rounded border p-3 text-sm">“{selection.snippet}”</blockquote>
      {viewerError ? (
        <p role="alert" className="mt-2 text-sm">
          The PDF failed to render. The API serves it at {fileUrl}.
        </p>
      ) : (
        <div className="relative mt-2 max-w-full overflow-auto border" style={{ maxWidth: PAGE_WIDTH + 2 }}>
          <Document
            file={fileUrl}
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
  );
}
