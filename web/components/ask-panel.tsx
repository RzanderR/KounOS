"use client";

import Link from "next/link";
import { type FormEvent, type ReactNode, useState } from "react";

import { Button } from "@/components/ui/button";
import { askKounOS, errorMessage } from "@/lib/api";
import type { AskAnswer, AskRecord } from "@/lib/kounos-types";

const DEFAULT_QUESTION = "Which orders need attention today?";

const KIND_LABEL: Record<AskRecord["kind"], string> = {
  order: "Order",
  po: "Supplier PO",
  invoice: "Invoice",
  shipment: "Shipment",
  event: "Event",
};

function recordHref(record: AskRecord): string {
  return `/orders/${encodeURIComponent(record.order_id)}`;
}

/** The answer text with every cited record ID turned into a link. */
function linkedAnswer(text: string, records: AskRecord[]): ReactNode[] {
  const byId = new Map(records.map((record) => [record.record_id, record]));
  if (byId.size === 0) return [text];
  const ids = [...byId.keys()].sort((a, b) => b.length - a.length);
  const pattern = new RegExp(`\\b(${ids.map((id) => id.replace(/[-]/g, "\\-")).join("|")})\\b`);
  return text.split(pattern).map((part, index) => {
    const record = byId.get(part);
    if (!record) return part;
    return (
      <Link key={`${part}-${index}`} href={recordHref(record)} className="font-medium underline">
        {part}
      </Link>
    );
  });
}

/** Ask KounOS (A24): a question answered from read-only tool calls. */
export function AskPanel() {
  const [question, setQuestion] = useState(DEFAULT_QUESTION);
  const [answer, setAnswer] = useState<AskAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = question.trim();
    if (!text || asking) return;
    setAsking(true);
    setError(null);
    try {
      setAnswer(await askKounOS(text));
    } catch (err) {
      setAnswer(null);
      setError(errorMessage(err));
    } finally {
      setAsking(false);
    }
  }

  const records = answer?.records ?? [];
  const calls = answer?.tool_calls ?? [];

  return (
    <section aria-label="Ask KounOS" className="rounded-lg border p-4">
      <h2 className="text-lg font-medium">Ask KounOS</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Answers come from read-only tool calls over the five orders. Every figure and record ID is
        checked against the tool results.
      </p>
      <form onSubmit={submit} className="mt-3 flex flex-col gap-2 sm:flex-row">
        <label htmlFor="ask-question" className="sr-only">
          Question
        </label>
        <input
          id="ask-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          maxLength={500}
          className="min-w-0 flex-1 rounded-md border px-3 py-2 text-sm"
        />
        <Button type="submit" disabled={asking || !question.trim()}>
          {asking ? "Asking…" : "Ask"}
        </Button>
      </form>

      {error !== null && (
        <p role="alert" className="mt-3 text-sm">
          {error}
        </p>
      )}

      {answer !== null && (
        <div className="mt-4 flex flex-col gap-3" aria-live="polite">
          {answer.grounded === false ? (
            <p role="alert" className="text-sm text-amber-700">
              Answer from {answer.generated_by} withheld: it cited{" "}
              {[...(answer.ungrounded_figures ?? []), ...(answer.unknown_records ?? [])].join(", ")}
              , which no tool returned. Showing the rule-based answer instead.
            </p>
          ) : (
            <p className="text-xs text-muted-foreground">
              Answer by {answer.generated_by} · as of {answer.as_of}
            </p>
          )}
          <p className="text-sm leading-6">{linkedAnswer(answer.answer, records)}</p>
          {records.length > 0 && (
            <div>
              <h3 className="text-sm font-medium">Records used</h3>
              <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                {records.map((record) => (
                  <li key={record.record_id}>
                    <Link href={recordHref(record)} className="underline">
                      {KIND_LABEL[record.kind]} {record.record_id}
                    </Link>
                    {record.kind !== "order" && (
                      <span className="text-muted-foreground"> ({record.order_id})</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {calls.length > 0 && (
            <p className="text-xs text-muted-foreground">
              Tool calls:{" "}
              {calls
                .map((call) => {
                  const args = Object.values(call.arguments ?? {}).join(", ");
                  return `${call.name}(${args})`;
                })
                .join(" → ")}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
