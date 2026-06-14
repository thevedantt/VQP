"use client";

import { useState } from "react";
import { Loader2Icon, SparklesIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import type { DifficultyLevel, GeneratePaperRequest } from "@/lib/types";

const MIN_QUESTIONS = 4;
const MAX_QUESTIONS = 50;

const DIFFICULTY_OPTIONS: { value: DifficultyLevel; label: string }[] = [
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" },
];

interface PaperFormProps {
  loading: boolean;
  onSubmit: (request: GeneratePaperRequest) => void;
}

export function PaperForm({ loading, onSubmit }: PaperFormProps) {
  const [difficulty, setDifficulty] = useState<DifficultyLevel>("medium");
  const [pyqPercentage, setPyqPercentage] = useState(60);
  const [includeDiagrams, setIncludeDiagrams] = useState(true);
  const [totalQuestions, setTotalQuestions] = useState(16);

  const aiPercentage = 100 - pyqPercentage;

  function handleTotalQuestionsChange(rawValue: string) {
    if (rawValue === "") {
      setTotalQuestions(MIN_QUESTIONS);
      return;
    }
    const parsed = Number(rawValue);
    if (Number.isNaN(parsed)) return;
    setTotalQuestions(parsed);
  }

  function handleTotalQuestionsBlur() {
    const clamped = Math.min(
      MAX_QUESTIONS,
      Math.max(MIN_QUESTIONS, Math.round(totalQuestions) || MIN_QUESTIONS)
    );
    setTotalQuestions(clamped);
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const clampedTotal = Math.min(
      MAX_QUESTIONS,
      Math.max(MIN_QUESTIONS, Math.round(totalQuestions) || MIN_QUESTIONS)
    );

    onSubmit({
      difficulty,
      pyq_percentage: pyqPercentage,
      ai_percentage: aiPercentage,
      include_diagrams: includeDiagrams,
      total_questions: clampedTotal,
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generate Paper</CardTitle>
        <CardDescription>
          Configure the paper and call the orchestrator to assemble a CBSE
          Physics test.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="grid gap-6 sm:grid-cols-2">
          <div className="flex flex-col gap-2">
            <Label htmlFor="difficulty">Difficulty</Label>
            <Select
              value={difficulty}
              onValueChange={(value) => setDifficulty(value as DifficultyLevel)}
            >
              <SelectTrigger id="difficulty" className="w-full">
                <SelectValue placeholder="Select difficulty" />
              </SelectTrigger>
              <SelectContent>
                {DIFFICULTY_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="total-questions">Number of Questions</Label>
            <Input
              id="total-questions"
              type="number"
              inputMode="numeric"
              min={MIN_QUESTIONS}
              max={MAX_QUESTIONS}
              value={totalQuestions}
              onChange={(event) => handleTotalQuestionsChange(event.target.value)}
              onBlur={handleTotalQuestionsBlur}
            />
            <p className="text-xs text-muted-foreground">
              Between {MIN_QUESTIONS} and {MAX_QUESTIONS} questions.
            </p>
          </div>

          <div className="flex flex-col gap-2 sm:col-span-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="pyq-percentage">PYQ / AI Split</Label>
              <span className="text-sm text-muted-foreground">
                PYQ {pyqPercentage}% · AI {aiPercentage}%
              </span>
            </div>
            <Slider
              id="pyq-percentage"
              value={[pyqPercentage]}
              min={0}
              max={100}
              step={5}
              onValueChange={([value]) => setPyqPercentage(value)}
            />
          </div>

          <div className="flex items-center justify-between gap-2 rounded-lg border border-border p-3 sm:col-span-2">
            <div className="flex flex-col gap-0.5">
              <Label htmlFor="include-diagrams">Include Diagrams</Label>
              <span className="text-xs text-muted-foreground">
                Run diagram detection and generate diagram specifications.
              </span>
            </div>
            <Switch
              id="include-diagrams"
              checked={includeDiagrams}
              onCheckedChange={setIncludeDiagrams}
            />
          </div>
        </CardContent>
        <CardFooter className="justify-end gap-2">
          <Button type="submit" disabled={loading}>
            {loading ? (
              <Loader2Icon className="animate-spin" />
            ) : (
              <SparklesIcon />
            )}
            {loading ? "Generating..." : "Generate Paper"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
