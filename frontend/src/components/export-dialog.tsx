"use client";

import { useCallback, useEffect, useState } from "react";
import { DownloadIcon, FileTextIcon, RefreshCwIcon } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { listPapers } from "@/lib/api";
import type { PaperListItem } from "@/lib/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

interface ExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ExportDialog({ open, onOpenChange }: ExportDialogProps) {
  const [papers, setPapers] = useState<PaperListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPaper, setSelectedPaper] = useState<string | null>(null);

  const fetchPapers = useCallback(async () => {
    setLoading(true);
    try {
      const result = await listPapers();
      setPapers(result);
    } catch (e) {
      toast.error("Failed to load papers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      fetchPapers();
    }
  }, [open, fetchPapers]);

  function handleExport() {
    if (!selectedPaper) return;
    const paperUrl = `${API_BASE_URL}/api/papers/${encodeURIComponent(selectedPaper)}/export`;
    window.open(paperUrl, "_blank");
    toast.success(`Exporting ${selectedPaper}...`);
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/10 backdrop-blur-xs"
      onClick={() => onOpenChange(false)}
    >
      <Card
        className="w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <CardHeader>
          <CardTitle>Export Paper</CardTitle>
          <CardDescription>
            Select a generated paper to export.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {loading ? (
            <div className="flex items-center justify-center py-4">
              <RefreshCwIcon className="size-5 animate-spin text-muted-foreground" />
            </div>
          ) : papers.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              No papers found. Generate a paper first.
            </p>
          ) : (
            papers.map((paper) => (
              <button
                key={paper.id}
                className={`flex items-center gap-3 rounded-lg border p-3 text-left text-sm transition-colors hover:bg-muted ${
                  selectedPaper === paper.id
                    ? "border-primary bg-primary/5"
                    : "border-border"
                }`}
                onClick={() => setSelectedPaper(paper.id)}
              >
                <FileTextIcon className="size-5 shrink-0 text-muted-foreground" />
                <div className="flex flex-col">
                  <span className="font-medium">{paper.id}</span>
                  <span className="text-xs text-muted-foreground truncate">
                    {paper.path}
                  </span>
                </div>
              </button>
            ))
          )}
        </CardContent>
        <CardFooter className="justify-between gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button
            onClick={handleExport}
            disabled={!selectedPaper}
          >
            <DownloadIcon />
            Export
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
