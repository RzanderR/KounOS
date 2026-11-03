"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { errorMessage, fetchOrders } from "@/lib/api";
import type { Order } from "@/lib/kounos-types";
import { PageError, PageLoading } from "@/components/page-state";
import { SimulatedAwardBanner } from "./banner";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchOrders();
        if (!cancelled) setOrders(data);
      } catch (err) {
        if (!cancelled) setError(errorMessage(err));
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [reload]);

  function handleRetry() {
    setError(null);
    setOrders(null);
    setReload((value) => value + 1);
  }

  if (error !== null) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Orders</h1>
        <PageError message={error} onRetry={handleRetry} />
      </main>
    );
  }
  if (orders === null) {
    return (
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Orders</h1>
        <PageLoading label="Loading orders…" />
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold">Orders</h1>
      <SimulatedAwardBanner />
      <div className="overflow-x-auto">
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
      </div>
    </main>
  );
}
