"use client";

import { useEffect, useMemo, useState } from "react";

import { errorMessage, fetchAward, fetchComparison, fetchDecision } from "@/lib/api";
import type {
  AwardRecord,
  QuoteComparison,
  SourcingDecision,
} from "@/lib/kounos-types";

function VerdictBadge({ verdict }: { verdict: "pass" | "fail" | "needs_confirmation" }) {
  const label =
    verdict === "pass" ? "pass" : verdict === "fail" ? "fail" : "needs confirmation";
  const tone =
    verdict === "pass"
      ? "border-emerald-700 text-emerald-700"
      : verdict === "fail"
        ? "border-red-700 text-red-700"
        : "border-amber-700 text-amber-700";
  return (
    <span
      className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${tone}`}
    >
      {label}
    </span>
  );
}

function money(value: string): string {
  const [dollars, cents] = value.split(".");
  return `$${Number(dollars).toLocaleString("en-US")}.${(cents ?? "00").padEnd(2, "0")}`;
}

/** Live margin preview at a bid price from the served landed cost. No model call. */
function marginAtBid(bid: number, landed: number): string {
  if (!(bid > 0)) return "—";
  return `${(((bid - landed) / bid) * 100).toFixed(2)}%`;
}

export default function QuotesPage() {
  const [rows, setRows] = useState<QuoteComparison[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [bidInput, setBidInput] = useState("91880.12");
  const [selected, setSelected] = useState<string | null>(null);
  const [decision, setDecision] = useState<SourcingDecision | null>(null);
  const [awardRecord, setAwardRecord] = useState<AwardRecord | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [data, decisions, awardData] = await Promise.all([
          fetchComparison(),
          fetchDecision(),
          fetchAward(),
        ]);
        if (cancelled) return;
        setRows(data);
        setDecision(decisions[0] ?? null);
        setAwardRecord(awardData);
        const firstPassing = data.find((row) => row.verdict.overall !== "fail");
        const firstId: unknown = firstPassing?.quote.quote_id ?? data[0]?.quote.quote_id;
        setSelected(typeof firstId === "string" ? firstId : null);
      } catch (err) {
        if (!cancelled) setError(errorMessage(err));
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const bid = useMemo(() => Number(bidInput), [bidInput]);
  const chosen = rows?.find((row) => row.quote.quote_id === selected) ?? null;

  if (error !== null) {
    return (
      <main className="mx-auto w-full max-w-6xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Quotes</h1>
        <p role="alert" className="mt-4 text-sm">
          {error}
        </p>
      </main>
    );
  }
  if (rows === null) {
    return (
      <main className="mx-auto w-full max-w-6xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Quotes</h1>
        <p className="mt-4 text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  const award = rows[0];
  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-10">
      <h1 className="text-2xl font-semibold">Quote comparison</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Solicitation 1232SA26Q0557 · award {money(award.award_total)} · fictional quotes
        for the demo
      </p>

      <section aria-label="Bid price" className="mt-6">
        <label htmlFor="bid-price" className="text-sm font-medium">
          Bid price ($)
        </label>
        <input
          id="bid-price"
          type="number"
          min="0"
          step="0.01"
          value={bidInput}
          onChange={(event) => setBidInput(event.target.value)}
          className="ml-3 w-40 rounded border px-2 py-1 text-sm"
        />
        <span className="ml-3 text-sm text-muted-foreground">
          Margins below recompute instantly, no model call.
        </span>
      </section>

      <section aria-label="Comparison" className="mt-6 overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2 pr-4">Supplier</th>
              <th className="py-2 pr-4">Quote</th>
              <th className="py-2 pr-4">Landed</th>
              <th className="py-2 pr-4">Margin at bid</th>
              <th className="py-2 pr-4">Safe bid (10%)</th>
              <th className="py-2 pr-4">Checks</th>
              <th className="py-2">Select</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.quote.quote_id} className="border-b align-top">
                <td className="py-2 pr-4 font-medium">{row.quote.supplier}</td>
                <td className="py-2 pr-4">{money(row.quote.total)}</td>
                <td className="py-2 pr-4">{money(row.landed_cost)}</td>
                <td className="py-2 pr-4">{marginAtBid(bid, Number(row.landed_cost))}</td>
                <td className="py-2 pr-4">{money(row.safe_bid_total)}</td>
                <td className="py-2 pr-4">
                  <ul className="space-y-1">
                    {(row.verdict.checks ?? []).map((check) => (
                      <li key={check.check} className="flex items-center gap-2">
                        <VerdictBadge verdict={check.verdict} />
                        <span className="text-xs text-muted-foreground">
                          {check.check}: {check.reason}
                        </span>
                      </li>
                    ))}
                  </ul>
                </td>
                <td className="py-2">
                  <input
                    type="radio"
                    name="supplier"
                    aria-label={`Select ${row.quote.supplier}`}
                    checked={selected === row.quote.quote_id}
                    onChange={() => setSelected(row.quote.quote_id ?? null)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {decision === null || awardRecord === null ? null : (
        <section aria-label="Recommendation" className="mt-10">
          <h2 className="text-lg font-medium">Recommendation</h2>
          <div className="mt-2 rounded border p-4 text-sm">
            {decision.decision === "pursue" ? (
              <p>
                <strong>
                  Pursue at {decision.bid_price === null || decision.bid_price === undefined ? "—" : money(decision.bid_price)}
                </strong>{" "}
                with {decision.supplier ?? "the selected supplier"}.
              </p>
            ) : (
              <p>
                <strong>Pass</strong>, because no quote is compliant.
              </p>
            )}
            <ul className="mt-2 list-disc pl-5">
              {(decision.reasons ?? []).map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
            <p className="mt-3">
              Actual award {awardRecord.award_id}: {money(awardRecord.total)} · signed{" "}
              {awardRecord.date_signed} · {awardRecord.number_of_offers} offers received ·{" "}
              {awardRecord.awardee}.
            </p>
            <ul className="mt-2 list-disc pl-5 text-muted-foreground">
              <li>Only award totals are public.</li>
              <li>Today&apos;s quotes reflect today&apos;s prices.</li>
              <li>One award is one data point.</li>
            </ul>
          </div>
        </section>
      )}

      {chosen === null ? null : (
        <section aria-label="Sourcing package" className="mt-10">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-medium">Sourcing package</h2>
            <button
              type="button"
              onClick={() => window.print()}
              className="rounded border px-3 py-1 text-sm"
            >
              Print
            </button>
          </div>
          <div className="mt-2 rounded border p-4 text-sm">
            <p>
              <strong>{chosen.quote.supplier}</strong> · quote {money(chosen.quote.total)} ·
              landed {money(chosen.landed_cost)} · deposit {money(chosen.deposit_due)}
            </p>
            <ul className="mt-2 list-disc pl-5">
              {(chosen.verdict.checks ?? []).map((check) => (
                <li key={check.check}>
                  {check.check}: {check.verdict} — {check.reason}
                </li>
              ))}
            </ul>
            <p className="mt-2">
              Sourcing clause FAR 52.225-3: country of origin{" "}
              {chosen.quote.country_of_origin ?? "not stated"} — confirm with the
              supplier before award.
            </p>
            <p className="mt-2 text-muted-foreground">
              Measured against award 1232SA26P0357 ({money(chosen.award_total)}).
              Fictional quotes for the demo; only award totals are public.
            </p>
          </div>
        </section>
      )}
    </main>
  );
}
