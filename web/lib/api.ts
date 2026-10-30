import type { HealthStatus, Order, PassageBytes, Quote, Solicitation } from "./kounos-types";

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

/** Viewer bytes endpoint: same PDF wrapped in JSON, no .pdf path. */
export function passageBytesUrl(solicitationId: string, filename: string): string {
  const id = encodeURIComponent(solicitationId);
  const file = encodeURIComponent(filename);
  return `${API_URL}/solicitations/${id}/passage-bytes?file=${file}`;
}

export type { PassageBytes };

/** Fetch viewer bytes and decode the base64 payload. */
export async function fetchPassageBytes(url: string): Promise<Uint8Array> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Passage bytes fetch failed: ${res.status}`);
  const body = (await res.json()) as { data?: unknown };
  if (typeof body.data !== "string") throw new Error("Passage bytes missing data");
  const binary = atob(body.data);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

/** Typed GET /quotes. Empty until intake lands (A10). */
export function fetchQuotes(): Promise<Quote[] | null> {
  return getJson<Quote[]>("/quotes");
}

/** Typed GET /orders. Empty until seeding lands (A16). */
export function fetchOrders(): Promise<Order[] | null> {
  return getJson<Order[]>("/orders");
}
