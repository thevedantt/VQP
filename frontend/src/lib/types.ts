/** Shared types mirroring the VisualQ Pilot backend Pydantic models. */

export type DifficultyLevel = "easy" | "medium" | "hard";

export type QuestionType =
  | "MCQ"
  | "VSA"
  | "SA"
  | "LA"
  | "Case Study"
  | "Assertion Reason";

export type DiagramType =
  | "free_body"
  | "circuit"
  | "graph"
  | "ray_diagram"
  | "magnetic_field"
  | "none";

export type QuestionSource = "pyq" | "ai";

export interface GeneratePaperRequest {
  difficulty: DifficultyLevel;
  pyq_percentage: number;
  ai_percentage: number;
  include_diagrams: boolean;
  total_questions: number;
  chapters?: string[] | null;
}

export interface QuestionItem {
  question_id: string;
  source: QuestionSource;
  type: QuestionType;
  marks: number;
  chapter: string;
  difficulty: DifficultyLevel;
  question: string;
  options: Record<string, string>;
  concept: string | null;
  requires_diagram: boolean;
  diagram_type: DiagramType;
  diagram_id: string | null;
}

export interface DiagramSpec {
  diagram_id: string;
  question_id: string;
  diagram_type: DiagramType;
  specification: Record<string, unknown>;
}

export interface GeneratedPaperResponse {
  paper_id: string;
  generated_at: string;
  difficulty: DifficultyLevel;
  total_questions: number;
  total_marks: number;
  pyq_percentage: number;
  ai_percentage: number;
  chapter_weightage: Record<string, number>;
  chapter_distribution: Record<string, number>;
  type_distribution: Record<string, number>;
  questions: QuestionItem[];
  generated_questions: QuestionItem[];
  diagrams: DiagramSpec[];
}

/** Error envelope returned by the backend's global exception handlers. */
export interface ApiErrorBody {
  error: string;
  message: string;
  detail?: string;
}
