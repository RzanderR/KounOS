"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchOrders } from "@/lib/api";
import type { Order } from "@/lib/kounos-types";
import { SimulatedAwardBanner } from "./banner";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const data = await fetchOrders();
      if (!cancelled) {
        if (data === null) setFailed(true);
        else setOrders(data);
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
        <h1 className="text-2xl font-semibold">Orders</h1>
        <p role="alert" className="mt-4 text-sm">
          The API is unreachable. Start it with <code>uvicorn app.main:app --reload</code> from
          api/ and reload.
        </p>
      </main>
    );
  }
  if (orders === null) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Orders</h1>
        <p className="mt-4 text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold">Orders</h1>
      <SimulatedAwardBanner />
      <table className="mt-6 w-full border-collapse text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="py-2 pr-4">Order</th>
            <th className="py-2 pr-4">Supplier</th>
            <th className="py-2 pr-4">Due</th>
            <th className="py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.order_id} className="border-b align-top">
              <td className="py-2 pr-4">
                <Link
                  href={`/orders/${encodeURIComponent(order.order_id)}`}
                  className="underline"
                >
                  {order.order_id}
                </Link>
              </td>
              <td className="py-2 pr-4">{order.supplier}</td>
              <td className="py-2 pr-4">{order.customer_due_date ?? "—"}</td>
              <td className="py-2">{order.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
