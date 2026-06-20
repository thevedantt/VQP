"use client";

import { useState } from "react";
import { DownloadIcon, SettingsIcon } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ExportDialog } from "@/components/export-dialog";
import { PaperForm } from "@/components/paper-form";
import { QuestionList } from "@/components/question-list";
import { ResultsSummary } from "@/components/results-summary";
import { SettingsPanel } from "@/components/settings-panel";
import { ThemeToggle } from "@/components/theme-toggle";
import {
  ApiError,
  generatePaper,
  generateAllDiagrams,
} from "@/lib/api";
import type {
  GeneratedPaperResponse,
  GeneratePaperRequest,
  DiagramResult,
} from "@/lib/types";

export default function PaperGenerationPage() {
  const [paper, setPaper] = useState<GeneratedPaperResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [diagramResults, setDiagramResults] = useState<DiagramResult[] | null>(
    null
  );
  const [generatingDiagrams, setGeneratingDiagrams] = useState(false);

  async function handleGenerate(request: GeneratePaperRequest) {
    setLoading(true);
    setPaper(null);
    setDiagramResults(null);
    try {
      const result = await generatePaper(request);
      setPaper(result);
      toast.success(
        `Generated ${result.summary.total_questions} questions (${result.total_marks} marks).`
      );
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Something went wrong while generating the paper.";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateDiagrams() {
    if (!paper) return;
    setGeneratingDiagrams(true);
    setDiagramResults(null);
    try {
      const result = await generateAllDiagrams(paper.paper_id);
      setDiagramResults(result.results);
      toast.success(
        `Generated ${result.generated} diagram${result.generated !== 1 ? "s" : ""}${result.failed > 0 ? ` (${result.failed} failed).` : "."}`
      );
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Something went wrong while generating diagrams.";
      toast.error(message);
    } finally {
      setGeneratingDiagrams(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-1 px-4 py-6">
          <div className="flex items-center justify-between gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">
              VisualQ
            </h1>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <Button variant="outline" onClick={() => setSettingsOpen(true)}>
                <SettingsIcon />
                Settings
              </Button>
              <Button variant="outline" onClick={() => setExportOpen(true)}>
                <DownloadIcon />
                Export
              </Button>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            AI-powered Physics question paper generation.
          </p>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-6">
        <PaperForm loading={loading} onSubmit={handleGenerate} />

        {paper && (
          <>
            <ResultsSummary
              paper={paper}
              onGenerateDiagrams={handleGenerateDiagrams}
              generatingDiagrams={generatingDiagrams}
              diagramResults={diagramResults}
            />
            <QuestionList paper={paper} diagramResults={diagramResults} />
          </>
        )}
      </main>

      <ExportDialog open={exportOpen} onOpenChange={setExportOpen} />
      <SettingsPanel open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  );
}
