import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { GeneratedPaperResponse } from "@/lib/types";

interface ResultsSummaryProps {
  paper: GeneratedPaperResponse;
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border p-3">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-lg font-semibold">{value}</span>
    </div>
  );
}

function DistributionList({
  title,
  data,
  suffix = "",
}: {
  title: string;
  data: Record<string, number>;
  suffix?: string;
}) {
  const entries = Object.entries(data);
  if (entries.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-medium">{title}</h3>
      <div className="flex flex-wrap gap-2">
        {entries.map(([key, value]) => (
          <Badge key={key} variant="outline">
            {key}: {value}
            {suffix}
          </Badge>
        ))}
      </div>
    </div>
  );
}

const DIAGRAM_TYPE_LABELS: Record<string, string> = {
  free_body: "Free Body",
  circuit: "Circuit",
  ray_diagram: "Ray Diagram",
  graph: "Graph",
  magnetic_field: "Magnetic Field",
};

export function ResultsSummary({ paper }: ResultsSummaryProps) {
  const coverage = paper.diagram_coverage;
  const evaluation = paper.quality_evaluation;
  const diagramTypeCounts = coverage
    ? Object.fromEntries(
        Object.entries(DIAGRAM_TYPE_LABELS)
          .map(([key, label]) => [label, coverage[key as keyof typeof coverage] as number])
          .filter(([, value]) => (value as number) > 0)
      )
    : {};

  return (
    <Card>
      <CardHeader>
        <CardTitle>Paper Summary</CardTitle>
        <CardDescription>
          Paper {paper.paper_id} · generated{" "}
          {new Date(paper.generated_at).toLocaleString()}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Difficulty" value={paper.difficulty} />
          <Stat label="Total Questions" value={paper.total_questions} />
          <Stat label="Total Marks" value={paper.total_marks} />
          <Stat
            label="PYQ / AI Split"
            value={`${paper.pyq_percentage}% / ${paper.ai_percentage}%`}
          />
        </div>

        <Separator />

        <DistributionList
          title="Chapter Weightage"
          data={paper.chapter_weightage}
          suffix="%"
        />
        <DistributionList
          title="Chapter Distribution"
          data={paper.chapter_distribution}
        />
        <DistributionList
          title="Question Type Distribution"
          data={paper.type_distribution}
        />

        {coverage && (
          <>
            <Separator />
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium">Diagram Coverage</h3>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Stat label="Diagram Questions" value={coverage.diagram_questions} />
                <Stat
                  label="Diagram %"
                  value={`${coverage.diagram_percentage}%`}
                />
              </div>
              <DistributionList title="By Diagram Type" data={diagramTypeCounts} />
            </div>
          </>
        )}

        {paper.sections.length > 0 && (
          <>
            <Separator />
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium">CBSE Section Structure</h3>
              <div className="flex flex-wrap gap-2">
                {paper.sections.map((section) => (
                  <Badge key={section.name} variant="outline">
                    Section {section.name} ({section.title}): {section.question_count}{" "}
                    {section.question_count === 1 ? "question" : "questions"},{" "}
                    {section.total_marks} marks
                  </Badge>
                ))}
              </div>
            </div>
          </>
        )}

        {evaluation && (
          <>
            <Separator />
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium">Quality Evaluation</h3>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                <Stat label="Overall Score" value={`${evaluation.overall_score}%`} />
                <Stat label="CBSE Compliance" value={`${evaluation.cbse_compliance}%`} />
                <Stat label="Diagram Coverage" value={`${evaluation.diagram_coverage}%`} />
                <Stat label="Chapter Coverage" value={`${evaluation.chapter_coverage}%`} />
                <Stat label="Difficulty Balance" value={`${evaluation.difficulty_balance}%`} />
                <Stat label="Question Diversity" value={`${evaluation.question_diversity}%`} />
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
