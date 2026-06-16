"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, analyzeDiagram } from "@/lib/api";
import type {
  AnalyzeDiagramResponse,
  GeneratorSelection,
  NcertContext,
  UnderstandingLayer,
  ValidationReport,
} from "@/lib/types";

const EXAMPLE_QUESTION =
  "Sketch the magnetic field lines due to a current-carrying circular loop, viewed along its axis.";

function JsonPanel({ title, data }: { title: string; data: unknown }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <pre className="max-h-96 overflow-auto rounded-lg border border-border bg-muted/30 p-3 text-xs whitespace-pre-wrap break-words">
          {JSON.stringify(data, null, 2)}
        </pre>
      </CardContent>
    </Card>
  );
}

function ListField({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="font-medium text-foreground">{label}</p>
      {items.length > 0 ? (
        <ul className="list-disc space-y-0.5 pl-5 text-muted-foreground">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground">—</p>
      )}
    </div>
  );
}

function UnderstandingPanel({
  understanding,
}: {
  understanding: UnderstandingLayer;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Understanding Layer</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4 text-sm">
        <div>
          <p className="font-medium text-foreground">
            What is the question asking?
          </p>
          <p className="text-muted-foreground">
            {understanding.what_is_the_question_asking || "—"}
          </p>
        </div>
        <div>
          <p className="font-medium text-foreground">
            What physics concept is involved?
          </p>
          <p className="text-muted-foreground">
            {understanding.what_physics_concept_is_involved || "—"}
          </p>
        </div>
        <div>
          <p className="font-medium text-foreground">
            Why is a diagram required?
          </p>
          <p className="text-muted-foreground">
            {understanding.why_is_a_diagram_required || "—"}
          </p>
        </div>
        <ListField
          label="What must be visible"
          items={understanding.what_must_be_visible}
        />
        <ListField
          label="What labels must be present"
          items={understanding.what_labels_must_be_present}
        />
        <div>
          <p className="font-medium text-foreground">
            What does the examiner expect to see?
          </p>
          <p className="text-muted-foreground">
            {understanding.what_examiner_expects_to_see || "—"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function NcertContextPanel({ context }: { context: NcertContext }) {
  const hasContext = context.description.trim().length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">NCERT Context</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4 text-sm">
        {hasContext ? (
          <>
            <div>
              <p className="font-medium text-foreground">Chapter / Topic</p>
              <p className="text-muted-foreground">
                {context.chapter || "—"}
                {context.topic ? ` — ${context.topic}` : ""}
              </p>
            </div>
            <div>
              <p className="font-medium text-foreground">Description</p>
              <p className="whitespace-pre-wrap text-muted-foreground">
                {context.description}
              </p>
            </div>
            {context.diagram_explanation &&
              context.diagram_explanation !== context.description && (
                <div>
                  <p className="font-medium text-foreground">
                    Diagram Explanation
                  </p>
                  <p className="whitespace-pre-wrap text-muted-foreground">
                    {context.diagram_explanation}
                  </p>
                </div>
              )}
            <ListField
              label="Expected Labels"
              items={context.expected_labels}
            />
            <ListField
              label="Important Points"
              items={context.important_points}
            />
          </>
        ) : (
          <p className="text-muted-foreground">
            No NCERT context available for this chapter yet.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function GeneratorSelectionPanel({
  selection,
}: {
  selection: GeneratorSelection;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Generator Selected</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="font-medium text-foreground">Engine</p>
          <p className="text-muted-foreground">{selection.engine}</p>
        </div>
        <div>
          <p className="font-medium text-foreground">Diagram Type</p>
          <p className="text-muted-foreground">{selection.diagram_type}</p>
        </div>
        <div>
          <p className="font-medium text-foreground">Concept</p>
          <p className="text-muted-foreground">{selection.concept || "—"}</p>
        </div>
        <div>
          <p className="font-medium text-foreground">Scenario</p>
          <p className="text-muted-foreground">{selection.scenario || "—"}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function ValidationReportPanel({ report }: { report: ValidationReport }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Validation Report</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4 text-sm">
        <div>
          <p className="font-medium text-foreground">Diagram Score</p>
          <p className="text-muted-foreground">
            {report.diagram_score.toFixed(1)} / 100
          </p>
        </div>
        <ListField
          label="Missing Entities"
          items={report.missing_entities}
        />
        <ListField label="Missing Labels" items={report.missing_labels} />
        <ListField label="Warnings" items={report.warnings} />
      </CardContent>
    </Card>
  );
}

export default function TestPlaygroundPage() {
  const [question, setQuestion] = useState(EXAMPLE_QUESTION);
  const [result, setResult] = useState<AnalyzeDiagramResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAnalyze() {
    setLoading(true);
    try {
      const response = await analyzeDiagram({ question });
      setResult(response);
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Something went wrong while analyzing the diagram.";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-1 px-4 py-6">
          <h1 className="text-2xl font-semibold tracking-tight">
            Diagram Intelligence Playground
          </h1>
          <p className="text-sm text-muted-foreground">
            Inspect every stage of the Question → Understanding Layer → NCERT
            Context → Semantic Schema → Selected Template → Generator
            Selected → Generator Input → Render Schema → Validation Report →
            Final Diagram pipeline.
          </p>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Question</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={EXAMPLE_QUESTION}
              rows={3}
            />
            <Button
              onClick={handleAnalyze}
              disabled={loading || question.trim().length < 3}
              className="self-start"
            >
              {loading ? "Analyzing..." : "Generate Diagram Analysis"}
            </Button>
          </CardContent>
        </Card>

        {result && (
          <>
            <UnderstandingPanel understanding={result.understanding} />
            <NcertContextPanel context={result.ncert_context} />
            <JsonPanel title="Semantic Schema" data={result.semantic_schema} />
            <JsonPanel title="Selected Template" data={result.selected_template} />
            <GeneratorSelectionPanel selection={result.generator_selection} />
            <JsonPanel title="Generator Input" data={result.generator_input} />
            <JsonPanel title="Render Schema" data={result.render_schema} />
            <ValidationReportPanel report={result.validation_report} />

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Final Diagram</CardTitle>
              </CardHeader>
              <CardContent>
                {result.svg ? (
                  <div
                    className="overflow-x-auto rounded-lg border border-border bg-white p-2 [&_svg]:mx-auto [&_svg]:h-auto [&_svg]:max-w-full"
                    dangerouslySetInnerHTML={{ __html: result.svg }}
                  />
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No diagram was generated for this question.
                  </p>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </main>
    </div>
  );
}
