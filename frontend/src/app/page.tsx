"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { PaperForm } from "@/components/paper-form";
import { QuestionList } from "@/components/question-list";
import { ResultsSummary } from "@/components/results-summary";
import { ApiError, generatePaper } from "@/lib/api";
import type { GeneratedPaperResponse, GeneratePaperRequest } from "@/lib/types";

export default function Home() {
  const [paper, setPaper] = useState<GeneratedPaperResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleGenerate(request: GeneratePaperRequest) {
    setLoading(true);
    try {
      const result = await generatePaper(request);
      setPaper(result);
      toast.success(
        `Generated ${result.total_questions} questions (${result.total_marks} marks).`
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

  return (
    <div className="flex flex-1 flex-col bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-1 px-4 py-6">
          <div className="flex items-center justify-between gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">
              VisualQ Pilot
            </h1>
            <Link
              href="/test"
              className="text-sm font-medium text-primary underline-offset-4 hover:underline"
            >
              Diagram Playground
            </Link>
          </div>
          <p className="text-sm text-muted-foreground">
            AI-powered CBSE Class 12 Physics paper generator - backend test
            console.
          </p>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-6">
        <PaperForm loading={loading} onSubmit={handleGenerate} />

        {paper && (
          <>
            <ResultsSummary paper={paper} />
            <QuestionList paper={paper} />
          </>
        )}
      </main>
    </div>
  );
}
