"use client";

import { useEffect, useState } from "react";

import { fetchFlags, fetchOrderDetail } from "@/lib/api";
import type { Flag, OrderDetail } from "@/lib/kounos-types";
import { SimulatedAwardBanner } from "../banner";

function TimelineRow({ label, value }: { label: string; value: string }) {
  return (
    <li className="flex gap-4 border-b py-2">
      <span className="w-40 shrink-0 font-medium">{label}</span>
      <span>{value}</span>
    </li>
  );
}

export default function OrderDetailView({ orderId }: { orderId: string }) {
  const [detail, setDetail] = useState<OrderDetail | null>(null);
  const [flags, setFlags] = useState<Flag[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const [orderData, flagData] = await Promise.all([
        fetchOrderDetail(orderId),
        fetchFlags(),
      ]);
      if (!cancelled) {
        if (orderData === null || flagData === null) setFailed(true);
        else {
          setDetail(orderData);
          setFlags(flagData.filter((flag) => flag.order_id === orderData.order.order_id));
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [orderId]);

  if (failed) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Order</h1>
        <p role="alert" className="mt-4 text-sm">
          The API is unreachable or the order is unknown. Start it with{" "}
          <code>uvicorn app.main:app --reload</code> from api/ and reload.
        </p>
      </main>
    );
  }
  if (detail === null || flags === null) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Order</h1>
        <p className="mt-4 text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  const { order, po } = detail;
  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold">
        {order.order_id} · {order.supplier}
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">Status: {order.status}</p>
      <SimulatedAwardBanner />

      {flags.length === 0 ? null : (
        <section aria-label="Flags" className="mt-6">
          <h2 className="text-lg font-medium">Needs attention</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {flags.map((flag) => (
              <li key={flag.flag_id} role="alert">
                <strong>{flag.severity}:</strong> {flag.message}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section aria-label="Timeline" className="mt-6">
        <h2 className="text-lg font-medium">Timeline</h2>
        <ul className="mt-2 text-sm">
          <TimelineRow
            label="Customer commitment"
            value={`Due ${order.customer_due_date ?? "—"}${
              order.bid_price === null || order.bid_price === undefined
                ? ""
                : ` · bid $${order.bid_price}`
            }`}
          />
          <TimelineRow
            label="Supplier PO"
            value={
              po === null || po === undefined
                ? "—"
                : `${po.po_id} · $${po.amount} · ${po.status}`
            }
          />
          {(detail.shipments ?? []).map((shipment) => (
            <TimelineRow
              key={shipment.shipment_id}
              label="Shipment"
              value={`${shipment.shipment_id} · shipped ${shipment.ship_date ?? "—"} · arrived ${
                shipment.arrival_date ?? "in transit"
              }${shipment.carrier === null || shipment.carrier === undefined ? "" : ` · ${shipment.carrier}`}`}
            />
          ))}
          {(detail.invoices ?? []).map((invoice) => (
            <TimelineRow
              key={invoice.invoice_id}
              label={invoice.paid ? "Payment" : "Invoice"}
              value={`${invoice.invoice_id} · $${invoice.amount} · due ${invoice.due_date ?? "—"}${
                invoice.paid ? " · paid" : ""
              }`}
            />
          ))}
          {(detail.events ?? []).map((event) => (
            <TimelineRow
              key={event.event_id}
              label={`Event (${event.source})`}
              value={event.summary}
            />
          ))}
        </ul>
        {(order.notes ?? []).length === 0 ? null : (
          <ul className="mt-4 space-y-1 text-sm text-muted-foreground">
            {(order.notes ?? []).map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
