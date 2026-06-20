import { useEffect, useState } from "react";
import { CheckIcon, DownloadIcon, RefreshCwIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import type { GeneratedPaperResponse, QuestionItem, DiagramResult } from "@/lib/types";
import {
  getDiagramSuggestions,
  getDiagramSvgUrl,
  getDiagramVersions,
  reviseDiagram,
} from "@/lib/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

interface QuestionListProps {
  paper: GeneratedPaperResponse;
  diagramResults?: DiagramResult[] | null;
}

function QuestionCard({
  question,
  diagramResults,
  paperId,
}: {
  question: QuestionItem;
  diagramResults?: DiagramResult[] | null;
  paperId: string;
}) {
  const options = question.options
    ? Object.entries(question.options)
    : [];

  const [dialogOpen, setDialogOpen] = useState(false);
  const [manualInstructions, setManualInstructions] = useState("");
  const [revising, setRevising] = useState(false);
  const [revisionNumber, setRevisionNumber] = useState(0);
  const [reviseError, setReviseError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState<string | null>(null);
  const [suggestionsFetched, setSuggestionsFetched] = useState(false);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<string>>(
    new Set()
  );

  const diagramResult = diagramResults?.find(
    (r) => r.question_id === question.question_id
  );

  // Pick up any pre-existing revision history (e.g. after a page reload)
  // so the "Revision: vN" badge and SVG stay accurate without manual refresh.
  useEffect(() => {
    if (diagramResult?.status !== "SUCCESS") return;
    let cancelled = false;
    getDiagramVersions(paperId, question.question_id)
      .then((res) => {
        if (cancelled || res.versions.length === 0) return;
        const latest = Math.max(...res.versions.map((v) => v.revision));
        setRevisionNumber(latest);
      })
      .catch(() => {
        // No history yet - fine, stay at v0 (initial generation).
      });
    return () => {
      cancelled = true;
    };
  }, [diagramResult?.status, paperId, question.question_id]);

  const handleDialogOpenChange = (open: boolean) => {
    setDialogOpen(open);
    if (open && !suggestionsFetched) {
      setSuggestionsLoading(true);
      setSuggestionsError(null);
      getDiagramSuggestions(paperId, question.question_id)
        .then((res) => {
          setSuggestions(res.suggestions);
          setSuggestionsFetched(true);
        })
        .catch((err: unknown) => {
          setSuggestionsError(
            err instanceof Error ? err.message : "Could not load suggestions"
          );
        })
        .finally(() => setSuggestionsLoading(false));
    }
  };

  const toggleSuggestion = (suggestion: string) => {
    setSelectedSuggestions((prev) => {
      const next = new Set(prev);
      if (next.has(suggestion)) {
        next.delete(suggestion);
      } else {
        next.add(suggestion);
      }
      return next;
    });
  };

  const allSelected =
    suggestions.length > 0 && selectedSuggestions.size === suggestions.length;

  const toggleSelectAll = () => {
    setSelectedSuggestions(allSelected ? new Set() : new Set(suggestions));
  };

  const canSubmit =
    selectedSuggestions.size > 0 || manualInstructions.trim().length > 0;

  const handleRevise = async () => {
    if (!canSubmit) return;
    setRevising(true);
    setReviseError(null);
    try {
      const res = await reviseDiagram(
        paperId,
        question.question_id,
        manualInstructions,
        Array.from(selectedSuggestions)
      );
      if (res.success) {
        setRevisionNumber(res.revision_number);
        setDialogOpen(false);
        setManualInstructions("");
        setSelectedSuggestions(new Set());
        // Blueprint changed - next time the modal opens, fetch fresh suggestions.
        setSuggestions([]);
        setSuggestionsFetched(false);
      } else {
        setReviseError(res.error ?? "Revision failed");
      }
    } catch (err: unknown) {
      setReviseError(err instanceof Error ? err.message : "Revision request failed");
    } finally {
      setRevising(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-sm text-muted-foreground">
            Q{question.question_id}
          </CardTitle>
          <Badge
            variant={question.source === "PYQ" ? "secondary" : "default"}
          >
            {question.source}
          </Badge>
          <Badge variant="outline">{question.type}</Badge>
          <Badge variant="outline">
            {question.marks} {question.marks === 1 ? "mark" : "marks"}
          </Badge>
          {question.diagram_required ? (
            <Badge variant="destructive">Diagram Required: YES</Badge>
          ) : (
            <Badge variant="ghost">Diagram Required: NO</Badge>
          )}
        </div>
        <CardDescription className="pt-1 text-base whitespace-pre-wrap text-foreground">
          {question.question}
        </CardDescription>
      </CardHeader>
      {options.length > 0 && (
        <CardContent>
          <ul className="flex flex-col gap-1 text-sm">
            {options.map(([key, value]) => (
              <li key={key}>
                <span className="font-medium">{key}.</span> {value}
              </li>
            ))}
          </ul>
        </CardContent>
      )}
      {question.diagram_required && diagramResult?.status === "SUCCESS" && (
        <CardFooter className="flex-col items-start gap-3">
          <p className="text-xs text-muted-foreground">
            <span className="font-medium">Reason:</span> {diagramResult.reason}
          </p>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
            <span>Mode: {diagramResult.generation_mode ?? "—"}</span>
            <span>Similarity: {diagramResult.similarity_score ?? "—"}</span>
            <span>Confidence: {diagramResult.confidence ?? "—"}</span>
            {revisionNumber > 0 && <span>Revision: v{revisionNumber}</span>}
          </div>
          <div className="flex w-full items-center justify-center p-6 rounded-xl min-h-[500px]" style={{ backgroundColor: "var(--diagram-surface)" }}>
            <img
              src={getDiagramSvgUrl(paperId, question.question_id, revisionNumber)}
              alt={`Diagram for Q${question.question_id}`}
              className="max-w-[90%] w-auto h-auto object-contain"
              style={{ maxHeight: "70vh" }}
            />
          </div>

          <Dialog open={dialogOpen} onOpenChange={handleDialogOpenChange}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <RefreshCwIcon />
                Revise Diagram
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Improve Diagram</DialogTitle>
                <DialogDescription>
                  Q{question.question_id} — tick the suggestions you want
                  applied, and/or write your own instructions below.
                </DialogDescription>
              </DialogHeader>

              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium text-muted-foreground">
                    Suggestions
                  </p>
                  {suggestions.length > 0 && (
                    <button
                      type="button"
                      onClick={toggleSelectAll}
                      className="text-xs font-medium text-primary hover:underline"
                    >
                      {allSelected ? "Deselect all" : "Select all"}
                    </button>
                  )}
                </div>
                {suggestionsLoading && (
                  <p className="text-xs text-muted-foreground">Loading suggestions…</p>
                )}
                {suggestionsError && (
                  <p className="text-xs text-destructive">{suggestionsError}</p>
                )}
                {!suggestionsLoading && suggestions.length > 0 && (
                  <div className="flex flex-col gap-1">
                    {suggestions.map((s) => {
                      const checked = selectedSuggestions.has(s);
                      return (
                        <button
                          key={s}
                          type="button"
                          aria-pressed={checked}
                          onClick={() => toggleSuggestion(s)}
                          className={`flex items-center gap-2 rounded-md border px-3 py-2 text-left text-xs transition-colors ${
                            checked
                              ? "border-primary bg-primary/10"
                              : "border-border bg-muted hover:bg-accent"
                          }`}
                        >
                          <span
                            className={`flex size-4 shrink-0 items-center justify-center rounded-sm border ${
                              checked
                                ? "border-primary bg-primary text-primary-foreground"
                                : "border-muted-foreground"
                            }`}
                          >
                            {checked && <CheckIcon className="size-3" />}
                          </span>
                          {s}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              <Textarea
                placeholder="Describe changes you want."
                value={manualInstructions}
                onChange={(e) => setManualInstructions(e.target.value)}
                rows={4}
              />
              {reviseError && (
                <p className="text-xs text-destructive">{reviseError}</p>
              )}
              <DialogFooter>
                <Button
                  variant="default"
                  onClick={handleRevise}
                  disabled={revising || !canSubmit}
                >
                  {revising ? "Revising…" : "Submit Revision"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardFooter>
      )}
      {question.diagram_required && diagramResult?.status === "FAILED" && (
        <CardFooter>
          <p className="text-xs text-destructive">{diagramResult.error}</p>
        </CardFooter>
      )}
    </Card>
  );
}

export function QuestionList({ paper, diagramResults }: QuestionListProps) {
  if (paper.questions.length === 0) {
    return (
      <Card>
        <CardContent className="py-6 text-center text-sm text-muted-foreground">
          No questions were generated.
        </CardContent>
      </Card>
    );
  }

  const exportUrl = `${API_BASE_URL}/api/papers/${encodeURIComponent(paper.paper_id)}/export`;

  return (
    <div className="flex flex-col gap-3">
      {paper.questions.map((question) => (
        <QuestionCard
          key={question.question_id}
          question={question}
          diagramResults={diagramResults}
          paperId={paper.paper_id}
        />
      ))}
      <Button
        variant="default"
        className="w-full"
        onClick={() => window.open(exportUrl, "_blank")}
      >
        <DownloadIcon />
        Export as PDF
      </Button>
    </div>
  );
}
