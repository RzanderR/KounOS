"use client";

import { useEffect, useState } from "react";

import { fetchContractFile, fetchImpactAnalysis, fetchRipple } from "@/lib/api";
import type { ContractFile, ImpactAnalysis, LinkedFigure, Ripple } from "@/lib/kounos-types";
import { SimulatedAwardBanner } from "../../orders/banner";

const SECTION_TITLES: Record<string, string> = {
  requirements: "Requirements",
  quotes: "Quotes and checks",
  cost_bid: "Cost and bid",
  award: "Award",
  order: "Order",
  events: "Events",
  cash: "Cash",
};

function LineagePanel({ figure }: { figure: LinkedFigure }) {
  const lineage = figure.lineage;
  return (
    <div className="mt-2 rounded border p-3 text-sm">
      <p className="font-medium">
        {figure.label}: {figure.value}
      </p>
      {lineage.kind === "doc" ? (
        <>
          <p className="mt-2 text-muted-foreground">
            Source: {lineage.file ?? "unknown file"}
            {lineage.page === null || lineage.page === undefined
              ? ""
              : `, page ${lineage.page}`}
          </p>
          {lineage.snippet === null || lineage.snippet === undefined ? null : (
            <blockquote className="mt-2 border-l-2 pl-3">
              “{lineage.snippet}”
            </blockquote>
          )}
          {lineage.file !== null &&
          lineage.file !== undefined &&
          lineage.file.startsWith("data/solicitations/") ? (
            <p className="mt-2">
              <a className="underline" href="/solicitation">
                Open in the solicitation reader
              </a>
            </p>
          ) : null}
        </>
      ) : (
        <>
          <p className="mt-2 text-muted-foreground">
            Calculated by <code>{lineage.calculation ?? "code"}</code>
          </p>
          <table className="mt-2 w-full border-collapse">
            <tbody>
              {Object.entries(lineage.inputs ?? {}).map(([name, input]) => (
                <tr key={name} className="border-b align-top">
                  <td className="py-1 pr-4 font-medium">{name}</td>
                  <td className="py-1">{input}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

export default function ContractView({ orderId }: { orderId: string }) {
  const [file, setFile] = useState<ContractFile | null>(null);
  const [failed, setFailed] = useState(false);
  const [selection, setSelection] = useState<LinkedFigure | null>(null);
  const [ripple, setRipple] = useState<Ripple | null>(null);
  const [impact, setImpact] = useState<ImpactAnalysis | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const [data, rippleData] = await Promise.all([
        fetchContractFile(orderId),
        fetchRipple(orderId),
      ]);
      if (cancelled) return;
      if (data === null) setFailed(true);
      else setFile(data);
      setRipple(rippleData);
      // Recovery options only exist for a late order, and the model call is
      // slow, so it loads after the rest of the page is on screen.
      if (rippleData === null || rippleData.days_late <= 0) return;
      const impactData = await fetchImpactAnalysis(orderId);
      if (!cancelled) setImpact(impactData);
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [orderId]);

  if (failed) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Contract file</h1>
        <p role="alert" className="mt-4 text-sm">
          The API is unreachable or the order is unknown. Start it with{" "}
          <code>uvicorn app.main:app --reload</code> from api/ and reload.
        </p>
      </main>
    );
  }
  if (file === null) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Contract file</h1>
        <p className="mt-4 text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold">Contract file</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {file.order_id} · {file.solicitation_id} · every number links to its source
      </p>
      <SimulatedAwardBanner />

      {(file.sections ?? []).map((section) => (
        <section
          key={section.name}
          aria-label={SECTION_TITLES[section.name] ?? section.name}
          className="mt-8"
        >
          <h2 className="text-lg font-medium">
            {SECTION_TITLES[section.name] ?? section.name}
          </h2>
          <ul className="mt-2">
            {(section.figures ?? []).map((figure) => (
              <li key={figure.label} className="border-b py-2">
                <button
                  type="button"
                  className="flex w-full cursor-pointer gap-4 text-left text-sm"
                  onClick={() => setSelection(figure)}
                  aria-label={`Show lineage for ${figure.label}`}
                >
                  <span className="w-56 shrink-0 font-medium">{figure.label}</span>
                  <span className="underline decoration-dotted">{figure.value}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}

      {ripple === null ? null : (
        <section aria-label="Delay ripple" className="mt-8">
          <h2 className="text-lg font-medium">Delay ripple</h2>
          <p className="mt-2 text-sm">
            Arrival {ripple.arrival_date ?? "unknown"} is {ripple.days_late}{" "}
            {ripple.days_late === 1 ? "day" : "days"} late (due{" "}
            {ripple.customer_due_date ?? "unknown"}).
          </p>
          <table className="mt-2 w-full border-collapse text-sm">
            <tbody>
              <tr className="border-b align-top">
                <td className="py-2 pr-4 font-medium">Margin now</td>
                <td className="py-2">{ripple.margin_now}%</td>
              </tr>
              <tr className="border-b align-top">
                <td className="py-2 pr-4 font-medium">Margin if expedited</td>
                <td className="py-2">
                  {ripple.margin_expedited}% (overnight {ripple.expedite_cost})
                </td>
              </tr>
              <tr className="border-b align-top">
                <td className="py-2 pr-4 font-medium">Deposit due</td>
                <td className="py-2">{ripple.deposit_due}</td>
              </tr>
              <tr className="border-b align-top">
                <td className="py-2 pr-4 font-medium">Invoice balance</td>
                <td className="py-2">{ripple.invoice_balance}</td>
              </tr>
              {(ripple.risks ?? []).map((risk) => (
                <tr key={risk} className="border-b align-top">
                  <td className="py-2 pr-4 font-medium">Risk</td>
                  <td className="py-2">{risk}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {impact === null ? null : (
        <section aria-label="Recovery options" className="mt-8">
          <h2 className="text-lg font-medium">Recovery options</h2>
          {impact.grounded === false ? (
            <p role="alert" className="mt-1 text-sm text-amber-700">
              Explanation from {impact.generated_by} withheld: it cited figures no tool returned (
              {(impact.ungrounded_figures ?? []).join(", ")}). Showing code-computed options and
              rule-based flags instead.
            </p>
          ) : (
            <p className="mt-1 text-sm text-muted-foreground">
              Analysis by {impact.generated_by}
            </p>
          )}
          <ul className="mt-2">
            {(impact.options ?? []).map((option) => (
              <li key={option.name} className="border-b py-2 text-sm">
                <p className="font-medium">{option.name}</p>
                <p className="mt-1">{option.summary}</p>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-sm">{impact.note}</p>
        </section>
      )}

      <section aria-label="Lineage" className="mt-8">
        <h2 className="text-lg font-medium">Lineage</h2>
        {selection === null ? (
          <p className="mt-2 text-sm text-muted-foreground">
            Select any number to see where it came from.
          </p>
        ) : (
          <LineagePanel figure={selection} />
        )}
      </section>
    </main>
  );
}
