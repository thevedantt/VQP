import type {
  ApiErrorBody,
  GenerateAllDiagramsResponse,
  GeneratePaperRequest,
  GeneratedPaperResponse,
  OutputsResponse,
  ReviseDiagramResponse,
  SuggestionsResponse,
  VersionsResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

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

async function getJson<TResponse>(path: string): Promise<TResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
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

export interface PaperListItem {
  id: string;
  path: string;
}

export function generatePaper(
  request: GeneratePaperRequest
): Promise<GeneratedPaperResponse> {
  return postJson<GeneratedPaperResponse>("/api/generate-paper", request);
}

export function listPapers(): Promise<PaperListItem[]> {
  return getJson<PaperListItem[]>("/api/papers");
}

export function getPaperFileNames(): Promise<string[]> {
  return getJson<string[]>("/api/papers/list");
}

export function generateAllDiagrams(
  paper_id: string
): Promise<GenerateAllDiagramsResponse> {
  return postJson<GenerateAllDiagramsResponse>("/api/generate-all-diagrams", {
    paper_id,
  });
}

export function reviseDiagram(
  paper_id: string,
  question_id: string,
  feedback: string,
  selectedSuggestions: string[] = []
): Promise<ReviseDiagramResponse> {
  return postJson<ReviseDiagramResponse>(
    `/api/diagrams/${paper_id}/${question_id}/revise`,
    { feedback, selected_suggestions: selectedSuggestions }
  );
}

export function getDiagramSuggestions(
  paper_id: string,
  question_id: string
): Promise<SuggestionsResponse> {
  return getJson<SuggestionsResponse>(
    `/api/diagrams/${paper_id}/${question_id}/suggestions`
  );
}

export function getDiagramVersions(
  paper_id: string,
  question_id: string
): Promise<VersionsResponse> {
  return getJson<VersionsResponse>(
    `/api/diagrams/${paper_id}/${question_id}/versions`
  );
}

export function analyzeDiagram(body: {
  question: string;
}): Promise<import("./types").AnalyzeDiagramResponse> {
  return postJson<import("./types").AnalyzeDiagramResponse>(
    "/api/analyze-diagram",
    body
  );
}

export function listOutputs(refresh = false): Promise<OutputsResponse> {
  return getJson<OutputsResponse>(`/api/outputs?refresh=${refresh}`);
}

export function getDiagramSvgUrl(
  paper_id: string,
  question_id: string,
  revision?: number
): string {
  const base = `${API_BASE_URL}/api/papers/${paper_id}/diagrams/${question_id}`;
  if (revision && revision > 0) {
    return `${base}?v=${revision}`;
  }
  return base;
}
