import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { DiagramResult, GeneratedPaperResponse } from "@/lib/types";

interface ResultsSummaryProps {
  paper: GeneratedPaperResponse;
  onGenerateDiagrams?: () => void;
  generatingDiagrams?: boolean;
  diagramResults?: DiagramResult[] | null;
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border p-3">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-lg font-semibold">{value}</span>
    </div>
  );
}

export function ResultsSummary({
  paper,
  onGenerateDiagrams,
  generatingDiagrams,
  diagramResults,
}: ResultsSummaryProps) {
  const paperTypeLabel =
    paper.paper_type === "UNIT_TEST_20" ? "Unit Test" : "CBSE Board";

  const hasDiagrams = paper.summary.diagram_questions > 0;
  const diagramsGenerated = diagramResults != null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Paper Summary</CardTitle>
        <CardDescription>Paper {paper.paper_id}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Paper Type" value={paperTypeLabel} />
          <Stat label="Total Questions" value={paper.summary.total_questions} />
          <Stat label="Total Marks" value={paper.total_marks} />
          <Stat
            label="Configured Split"
            value={`${Math.round(paper.summary.configured_pyq_ratio * 100)}% / ${Math.round(paper.summary.configured_ai_ratio * 100)}%`}
          />
          <Stat
            label="Actual Split"
            value={`${(paper.summary.actual_pyq_ratio * 100).toFixed(1)}% / ${(paper.summary.actual_ai_ratio * 100).toFixed(1)}%`}
          />
          <Stat label="PYQ Questions" value={paper.summary.pyq_questions} />
          <Stat label="AI Questions" value={paper.summary.ai_questions} />
          <Stat
            label="Diagram Questions"
            value={paper.summary.diagram_questions}
          />
        </div>
        {hasDiagrams && onGenerateDiagrams && (
          <div className="mt-3">
            {diagramsGenerated ? (
              <p className="text-xs text-muted-foreground">
                Generated:{" "}
                {diagramResults!.filter((r) => r.status === "SUCCESS").length} |{" "}
                Failed:{" "}
                {diagramResults!.filter((r) => r.status === "FAILED").length}
              </p>
            ) : (
              <Button
                onClick={onGenerateDiagrams}
                disabled={generatingDiagrams}
              >
                {generatingDiagrams
                  ? "Generating..."
                  : `Generate ${paper.summary.diagram_questions} Diagram${paper.summary.diagram_questions !== 1 ? "s" : ""}`}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
