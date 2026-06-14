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

export function ResultsSummary({ paper }: ResultsSummaryProps) {
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
      </CardContent>
    </Card>
  );
}
