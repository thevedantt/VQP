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
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import type { DifficultyLevel, GeneratePaperRequest, PaperType } from "@/lib/types";

const PAPER_TYPE_OPTIONS: { value: PaperType; label: string }[] = [
  { value: "UNIT_TEST_20", label: "Unit Test (20 Marks)" },
  { value: "CBSE_70", label: "CBSE Board (70 Marks)" },
];

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
  const [paperType, setPaperType] = useState<PaperType>("UNIT_TEST_20");
  const [pyqRatio, setPyqRatio] = useState(60);
  const [difficulty, setDifficulty] = useState<DifficultyLevel>("medium");

  const aiRatio = 100 - pyqRatio;

  function handlePyqChange([value]: number[]) {
    setPyqRatio(value);
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit({
      paper_type: paperType,
      pyq_ratio: pyqRatio,
      ai_ratio: aiRatio,
      difficulty,
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generate Paper</CardTitle>
        <CardDescription>
          Configure paper type, source ratio, and difficulty to generate a
          Physics question paper.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <Label htmlFor="paper-type">Paper Type</Label>
            <Select
              value={paperType}
              onValueChange={(value) => setPaperType(value as PaperType)}
            >
              <SelectTrigger id="paper-type" className="w-full">
                <SelectValue placeholder="Select paper type" />
              </SelectTrigger>
              <SelectContent>
                {PAPER_TYPE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="pyq-ratio">PYQ Ratio</Label>
              <span className="text-sm text-muted-foreground">
                {pyqRatio}%
              </span>
            </div>
            <Slider
              id="pyq-ratio"
              value={[pyqRatio]}
              min={0}
              max={100}
              step={5}
              onValueChange={handlePyqChange}
            />
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="ai-ratio">AI Ratio</Label>
              <span className="text-sm text-muted-foreground">
                {aiRatio}%
              </span>
            </div>
            <Slider
              id="ai-ratio"
              value={[aiRatio]}
              min={0}
              max={100}
              step={5}
              onValueChange={([value]) => setPyqRatio(100 - value)}
            />
            <p className="text-xs text-muted-foreground">
              PYQ + AI = {pyqRatio + aiRatio}%
            </p>
          </div>

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
