/** Thin API service layer for the VisualQ Pilot FastAPI backend. */

import type {
  ApiErrorBody,
  GeneratePaperRequest,
  GeneratedPaperResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

/** Error thrown for both network failures and backend error responses. */
export class ApiError extends Error {
  readonly status: number;
  readonly detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function postJson<TResponse>(
  path: string,
  body: unknown
): Promise<TResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      `Unable to reach the backend at ${API_BASE_URL}. Make sure the API server is running.`,
      0
    );
  }

  if (!response.ok) {
    let payload: Partial<ApiErrorBody> = {};
    try {
      payload = (await response.json()) as ApiErrorBody;
    } catch {
      // Response body wasn't JSON - fall back to the status text below.
    }
    throw new ApiError(
      payload.message ?? `Request failed with status ${response.status}.`,
      response.status,
      payload.detail
    );
  }

  return (await response.json()) as TResponse;
}

/** POST /api/generate-paper */
export function generatePaper(
  request: GeneratePaperRequest
): Promise<GeneratedPaperResponse> {
  return postJson<GeneratedPaperResponse>("/api/generate-paper", request);
}
