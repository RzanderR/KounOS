import type {
  AwardRecord,
  ContractFile,
  ImpactAnalysis,
  Ripple,
  FitAssessment,
  Flag,
  HealthStatus,
  Notice,
  Order,

  OrderDetail,
  PassageBytes,

  Quote,
  QuoteComparison,
  Solicitation,
  SourcingDecision,
} from "./kounos-types";




const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** A failed API call, carrying a reason a person can act on. */
export class ApiError extends Error {}

/** The message to show for anything a fetcher threw. */
export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/** One API call; throws ApiError with the API's own reason on failure. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError(
      `Cannot reach the API at ${API_URL}. Start it with uvicorn app.main:app --reload from api/ and reload.`,
    );
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Not JSON: keep the status text.
    }
    throw new ApiError(`The API answered ${res.status} for ${path}: ${detail}`);
  }
  return (await res.json()) as T;
}

function getJson<T>(path: string): Promise<T> {
  return request<T>(path);
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

/** Typed GET /health. Throws when the API is unreachable or unhealthy. */
export async function fetchHealth(): Promise<HealthStatus> {
  const data = await getJson<HealthStatus>("/health");
  if (data.status !== "ok") throw new ApiError("The API reports it is unhealthy.");
  return data;
}

/** Typed GET /solicitations. Empty until extraction lands (A05). */
export function fetchSolicitations(): Promise<Solicitation[]> {
  return getJson<Solicitation[]>("/solicitations");
}

/** Typed GET /solicitations/{id}. */
export function fetchSolicitation(solicitationId: string): Promise<Solicitation> {
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
export function fetchQuotes(): Promise<Quote[]> {
  return getJson<Quote[]>("/quotes");
}

export type { AwardRecord, QuoteComparison, SourcingDecision };

/** Typed GET /quotes/comparison. */
export function fetchComparison(): Promise<QuoteComparison[]> {
  return getJson<QuoteComparison[]>("/quotes/comparison");
}

/** Typed GET /sourcing-decisions. */
export function fetchDecision(): Promise<SourcingDecision[]> {
  return getJson<SourcingDecision[]>("/sourcing-decisions");
}

/** Typed GET /sourcing-decisions/award. */
export function fetchAward(): Promise<AwardRecord> {
  return getJson<AwardRecord>("/sourcing-decisions/award");
}

/** Typed GET /orders. Empty until seeding lands (A16). */
export function fetchOrders(): Promise<Order[]> {
  return getJson<Order[]>("/orders");
}

export type { Flag, OrderDetail };

/** Typed GET /orders/{id}. */
export function fetchOrderDetail(orderId: string): Promise<OrderDetail> {
  return getJson<OrderDetail>(`/orders/${encodeURIComponent(orderId)}`);
}

/** Typed GET /orders/{id}/contract-file. */
export function fetchContractFile(orderId: string): Promise<ContractFile> {
  return getJson<ContractFile>(`/orders/${encodeURIComponent(orderId)}/contract-file`);
}

/** Typed GET /orders/{id}/ripple. Null when the order is on track. */
export function fetchRipple(orderId: string): Promise<Ripple | null> {
  return getJson<Ripple | null>(`/orders/${encodeURIComponent(orderId)}/ripple`);
}

/** Typed POST /impact/analyze. The API answers 409 for an on-time order. */
export function fetchImpactAnalysis(orderId: string): Promise<ImpactAnalysis> {
  return postJson<ImpactAnalysis>("/impact/analyze", { order_id: orderId });
}

/** Typed GET /notices. Empty until the H16 batch lands. */
export function fetchNotices(): Promise<Notice[]> {
  return getJson<Notice[]>("/notices");
}

/** Typed GET /notices/{id}/fit. The API answers 503 until the H15 profile lands. */
export function fetchFit(noticeId: string): Promise<FitAssessment> {
  return getJson<FitAssessment>(`/notices/${encodeURIComponent(noticeId)}/fit`);
}

/** Typed GET /events/flags. */
export function fetchFlags(): Promise<Flag[]> {
  return getJson<Flag[]>("/events/flags");
}
