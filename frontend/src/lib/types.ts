export type DifficultyLevel = "easy" | "medium" | "hard";

export type PaperType = "UNIT_TEST_20" | "CBSE_70";

export type QuestionSource = "PYQ" | "AI";

export interface GeneratePaperRequest {
  paper_type: PaperType;
  pyq_ratio: number;
  ai_ratio: number;
  difficulty: DifficultyLevel;
}

export interface QuestionItem {
  question_id: string;
  question: string;
  source: QuestionSource;
  type: string;
  section_id: string;
  marks: number;
  options: Record<string, string> | null;
  diagram_required: boolean;
  diagram_family: string | null;
  chapter: string | null;
  concept: string | null;
}

export interface PaperSummary {
  total_questions: number;
  pyq_questions: number;
  ai_questions: number;
  diagram_questions: number;
  diagram_family_counts?: Record<string, number>;
  configured_pyq_ratio: number;
  configured_ai_ratio: number;
  actual_pyq_ratio: number;
  actual_ai_ratio: number;
}

export interface GeneratedPaperResponse {
  paper_id: string;
  paper_type: string;
  total_marks: number;
  pyq_ratio: number;
  ai_ratio: number;
  questions: QuestionItem[];
  summary: PaperSummary;
}

export interface DiagramResult {
  question_id: string;
  family: string | null;
  reason: string | null;
  similarity_score: number | null;
  generation_mode: "EXAMPLE_BASED" | "SCHEMA_BASED" | null;
  confidence: number | null;
  status: "SUCCESS" | "SKIPPED" | "FAILED";
  svg_path: string | null;
  error: string | null;
}

export interface GenerateAllDiagramsResponse {
  paper_id: string;
  generated: number;
  failed: number;
  svg_files: string[];
  results: DiagramResult[];
}

export interface ReviseDiagramResponse {
  success: boolean;
  revision_number: number;
  svg_path: string | null;
  changes: string[];
  error: string | null;
}

export interface SuggestionsResponse {
  success: boolean;
  suggestions: string[];
  error: string | null;
}

export interface VersionInfo {
  revision: number;
  blueprint: string | null;
  svg: string | null;
  feedback?: string;
}

export interface VersionsResponse {
  versions: VersionInfo[];
}

export interface ApiErrorBody {
  error: string;
  message: string;
  detail?: string;
}

export interface UnderstandingLayer {
  what_is_the_question_asking: string;
  what_physics_concept_is_involved: string;
  why_is_a_diagram_required: string;
  what_must_be_visible: string[];
  what_labels_must_be_present: string[];
  what_examiner_expects_to_see: string;
}

export interface NcertContext {
  chapter: string;
  topic: string;
  description: string;
  diagram_explanation: string;
  expected_labels: string[];
  important_points: string[];
}

export interface GeneratorSelection {
  engine: string;
  diagram_type: string;
  concept: string;
  scenario: string;
}

export interface ValidationReport {
  diagram_score: number;
  missing_entities: string[];
  missing_labels: string[];
  warnings: string[];
}

export interface AnalyzeDiagramResponse {
  svg: string;
  understanding: UnderstandingLayer;
  ncert_context: NcertContext;
  semantic_schema: Record<string, unknown>;
  selected_template: Record<string, unknown>;
  generator_selection: GeneratorSelection;
  generator_input: Record<string, unknown>;
  render_schema: Record<string, unknown>;
  validation_report: ValidationReport;
}
