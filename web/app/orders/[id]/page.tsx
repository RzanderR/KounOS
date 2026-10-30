import OrderDetailView from "./detail-view";

// Prerendered per order id; data still loads from the API in the browser.
export function generateStaticParams() {
  return [
    { id: "ORD-001" },
    { id: "ORD-002" },
    { id: "ORD-003" },
    { id: "ORD-004" },
    { id: "ORD-005" },
  ];
}

export default async function OrderPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <OrderDetailView orderId={id} />;
}
