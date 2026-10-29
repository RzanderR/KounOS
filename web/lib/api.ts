import type { HealthStatus, Order, Quote, Solicitation } from "./kounos-types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/** Typed GET /health. Null when the API is unreachable or unhealthy. */
export async function fetchHealth(): Promise<HealthStatus | null> {
  const data = await getJson<HealthStatus>("/health");
  if (data === null || data.status !== "ok") return null;
  return data;
}

/** Typed GET /solicitations. Empty until extraction lands (A05). */
export function fetchSolicitations(): Promise<Solicitation[] | null> {
  return getJson<Solicitation[]>("/solicitations");
}

/** Typed GET /solicitations/{id}. Null when unreachable or unknown. */
export function fetchSolicitation(solicitationId: string): Promise<Solicitation | null> {
  return getJson<Solicitation>(`/solicitations/${encodeURIComponent(solicitationId)}`);
}

/** URL of a solicitation PDF served by the API for the viewer. */
export function attachmentUrl(solicitationId: string, filename: string): string {
  const id = encodeURIComponent(solicitationId);
  const file = encodeURIComponent(filename);
  return `${API_URL}/solicitations/${id}/attachments/${file}`;
}

/** Typed GET /quotes. Empty until intake lands (A10). */
export function fetchQuotes(): Promise<Quote[] | null> {
  return getJson<Quote[]>("/quotes");
}

/** Typed GET /orders. Empty until seeding lands (A16). */
export function fetchOrders(): Promise<Order[] | null> {
  return getJson<Order[]>("/orders");
}
