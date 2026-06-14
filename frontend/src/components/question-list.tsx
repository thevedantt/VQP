import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type {
  DiagramSpec,
  DiagramType,
  GeneratedPaperResponse,
  QuestionItem,
} from "@/lib/types";

const DIAGRAM_TYPE_LABELS: Record<DiagramType, string> = {
  free_body: "Free Body",
  circuit: "Circuit",
  graph: "Graph",
  ray_diagram: "Ray Diagram",
  magnetic_field: "Magnetic Field",
  none: "None",
};

interface QuestionListProps {
  paper: GeneratedPaperResponse;
}

function QuestionCard({
  question,
  index,
  diagram,
}: {
  question: QuestionItem;
  index: number;
  diagram?: DiagramSpec;
}) {
  const options = Object.entries(question.options);

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-sm text-muted-foreground">
            Q{index}
          </CardTitle>
          <Badge variant={question.source === "pyq" ? "secondary" : "default"}>
            {question.source === "pyq" ? "PYQ" : "AI"}
          </Badge>
          <Badge variant="outline">{question.type}</Badge>
          <Badge variant="outline">{question.chapter}</Badge>
          <Badge variant="outline">
            {question.marks} {question.marks === 1 ? "mark" : "marks"}
          </Badge>
          {question.requires_diagram && (
            <Badge variant="secondary">
              Diagram: {DIAGRAM_TYPE_LABELS[question.diagram_type]}
            </Badge>
          )}
        </div>
        <CardDescription className="pt-1 text-base whitespace-pre-wrap text-foreground">
          {question.question}
        </CardDescription>
      </CardHeader>
      {(options.length > 0 || diagram) && (
        <CardContent className="flex flex-col gap-3">
          {options.length > 0 && (
            <ul className="flex flex-col gap-1 text-sm">
              {options.map(([key, value]) => (
                <li key={key}>
                  <span className="font-medium">{key}.</span> {value}
                </li>
              ))}
            </ul>
          )}
          {diagram && (
            <details className="rounded-lg border border-border p-2 text-xs">
              <summary className="cursor-pointer font-medium text-muted-foreground">
                Diagram specification ({DIAGRAM_TYPE_LABELS[diagram.diagram_type]})
              </summary>
              <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words">
                {JSON.stringify(diagram.specification, null, 2)}
              </pre>
            </details>
          )}
        </CardContent>
      )}
    </Card>
  );
}

export function QuestionList({ paper }: QuestionListProps) {
  const diagramsByQuestionId = new Map(
    paper.diagrams.map((diagram) => [diagram.question_id, diagram])
  );

  const allQuestions = [...paper.questions, ...paper.generated_questions];

  if (allQuestions.length === 0) {
    return (
      <Card>
        <CardContent className="py-6 text-center text-sm text-muted-foreground">
          No questions were generated for this configuration.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {allQuestions.map((question, index) => (
        <QuestionCard
          key={question.question_id}
          question={question}
          index={index + 1}
          diagram={diagramsByQuestionId.get(question.question_id)}
        />
      ))}
    </div>
  );
}
