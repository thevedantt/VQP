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
  diagram_percentage: number;
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
  question_number: number;
}

export interface PaperSection {
  name: string;
  title: string;
  instructions: string;
  marks_per_question: number;
  question_count: number;
  total_marks: number;
  questions: QuestionItem[];
}

export interface QualityEvaluation {
  overall_score: number;
  cbse_compliance: number;
  diagram_coverage: number;
  chapter_coverage: number;
  difficulty_balance: number;
  question_diversity: number;
}

export interface DiagramSpec {
  diagram_id: string;
  question_id: string;
  diagram_type: DiagramType;
  specification: Record<string, unknown>;
  svg: string;
}

export interface DiagramCoverage {
  diagram_questions: number;
  diagram_percentage: number;
  free_body: number;
  circuit: number;
  ray_diagram: number;
  graph: number;
  magnetic_field: number;
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
  diagram_coverage: DiagramCoverage;
  sections: PaperSection[];
  quality_evaluation: QualityEvaluation;
}

/** Error envelope returned by the backend's global exception handlers. */
export interface ApiErrorBody {
  error: string;
  message: string;
  detail?: string;
}

export interface AnalyzeDiagramRequest {
  question: string;
}

/** The ONLY information the LLM layer is allowed to produce - no coordinates/geometry. */
export interface PhysicsAnalysis {
  diagram_required: boolean;
  diagram_type: DiagramType;
  chapter: string | null;
  concept: string | null;
  scenario: string | null;
  entities: string[];
  confidence: number;
}

export interface AnalyzeDiagramResponse {
  question: string;
  physics_analysis: PhysicsAnalysis;
  selected_template: Record<string, unknown>;
  semantic_schema: Record<string, unknown>;
  render_schema: Record<string, unknown>;
  svg: string;
}
