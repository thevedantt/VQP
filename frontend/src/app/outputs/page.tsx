"use client";

import { useEffect, useState } from "react";
import { ArrowRightIcon, ChevronLeftIcon, FileIcon, RefreshCwIcon, SearchIcon, XIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ThemeToggle } from "@/components/theme-toggle";
import { listOutputs } from "@/lib/api";
import type { OutputCategory, OutputFile, OutputsResponse } from "@/lib/types";

const CATEGORY_TABS = [
  "All",
  "Question Papers",
  "Ray Diagrams",
  "Circuit Diagrams",
  "FBD Diagrams",
  "Magnetic Diagrams",
  "Semiconductor Diagrams",
  "Graph Diagrams",
  "PDF Exports",
  "Validation Reports",
  "Test Outputs",
  "Other Assets",
];

const SOURCE_FILTERS = ["all", "backend_v2", "approch2"];

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function getFileIcon(type: string) {
  switch (type) {
    case "svg":
      return "▲";
    case "pdf":
      return "▢";
    case "json":
      return "{ }";
    default:
      return "●";
  }
}

export default function OutputsPage() {
  const [data, setData] = useState<OutputsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("All");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [preview, setPreview] = useState<OutputFile | null>(null);

  async function fetchOutputs(refresh = false) {
    setLoading(true);
    try {
      const result = await listOutputs(refresh);
      setData(result);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchOutputs();
  }, []);

  const allFiles =
    data?.categories.flatMap((c) => c.files) ?? [];

  let filtered = allFiles;

  if (activeTab !== "All") {
    const cat = data?.categories.find((c) => c.name === activeTab);
    filtered = cat?.files ?? [];
  }

  if (sourceFilter !== "all") {
    filtered = filtered.filter((f) => f.source === sourceFilter);
  }

  if (search.trim()) {
    const q = search.toLowerCase();
    filtered = filtered.filter(
      (f) =>
        f.name.toLowerCase().includes(q) ||
        f.path.toLowerCase().includes(q) ||
        f.source.toLowerCase().includes(q)
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* Navbar */}
      <header className="border-b border-border">
        <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" asChild>
              <a href="/">
                <ChevronLeftIcon className="size-3.5" />
                Back
              </a>
            </Button>
            <span className="text-sm font-semibold">Outputs Explorer</span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchOutputs(true)}
              disabled={loading}
            >
              <RefreshCwIcon className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <ThemeToggle />
          </div>
        </nav>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Outputs Explorer</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Browse all generated VisualQ artifacts.
            {data && <span className="ml-1">({data.total_files} files)</span>}
          </p>
        </div>

        {/* Search + Source filter */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="Search by filename, paper ID, diagram family..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="flex gap-1.5">
            {SOURCE_FILTERS.map((s) => (
              <Button
                key={s}
                variant={sourceFilter === s ? "default" : "outline"}
                size="sm"
                onClick={() => setSourceFilter(s)}
                className="capitalize"
              >
                {s === "all" ? "All Sources" : s}
              </Button>
            ))}
          </div>
        </div>

        {/* Category tabs */}
        <div className="flex gap-2 overflow-x-auto pb-1">
          {CATEGORY_TABS.map((tab) => {
            const count =
              tab === "All"
                ? allFiles.length
                : data?.categories.find((c) => c.name === tab)?.count ?? 0;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                  activeTab === tab
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                {tab}
                {count > 0 && (
                  <span className="ml-1.5 opacity-70">{count}</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Gallery */}
        {loading && !data ? (
          <div className="flex items-center justify-center py-20 text-sm text-muted-foreground">
            Scanning outputs...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex items-center justify-center py-20 text-sm text-muted-foreground">
            No files found.
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {filtered.map((file) => (
              <button
                key={file.path}
                onClick={() => setPreview(file)}
                className="group relative flex flex-col rounded-xl border border-border bg-card overflow-hidden text-left transition-all hover:shadow-md hover:border-primary/30"
              >
                {/* Preview */}
                <div className="aspect-[4/3] bg-muted/30 flex items-center justify-center overflow-hidden">
                  {file.type === "svg" ? (
                    <object
                      data={`http://127.0.0.1:8000/api/outputs/file?path=${encodeURIComponent(file.path)}`}
                      type="image/svg+xml"
                      className="w-full h-full object-contain p-2"
                    >
                      <div className="text-2xl text-muted-foreground">
                        {getFileIcon(file.type)}
                      </div>
                    </object>
                  ) : file.type === "pdf" ? (
                    <div className="text-4xl text-destructive/70 font-bold">PDF</div>
                  ) : file.type === "json" ? (
                    <div className="text-2xl text-muted-foreground font-mono">
                      {getFileIcon(file.type)}
                    </div>
                  ) : (
                    <div className="text-2xl text-muted-foreground">
                      {getFileIcon(file.type)}
                    </div>
                  )}
                </div>
                {/* Info */}
                <div className="flex flex-col gap-1 p-3">
                  <p className="text-xs font-medium truncate">{file.name}</p>
                  <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                    <Badge variant="outline" className="text-[9px] px-1 py-0 h-auto">
                      {file.type}
                    </Badge>
                    <span>{file.size}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </main>

      {/* Preview Modal */}
      {preview && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={() => setPreview(null)}
        >
          <div
            className="bg-background border border-border rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div className="flex flex-col gap-0.5">
                <p className="text-sm font-semibold">{preview.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatDate(preview.created_at)} — {preview.source}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {preview.type === "svg" && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      window.open(
                        `http://127.0.0.1:8000/api/outputs/file?path=${encodeURIComponent(preview.path)}`,
                        "_blank"
                      );
                    }}
                  >
                    Open SVG
                  </Button>
                )}
                <Button variant="ghost" size="icon" onClick={() => setPreview(null)}>
                  <XIcon className="size-4" />
                </Button>
              </div>
            </div>
            {/* Modal content */}
            <div className="flex-1 overflow-auto p-6 flex items-center justify-center bg-muted/20">
              {preview.type === "svg" ? (
                <object
                  data={`http://127.0.0.1:8000/api/outputs/file?path=${encodeURIComponent(preview.path)}`}
                  type="image/svg+xml"
                  className="max-w-full max-h-[70vh]"
                >
                  <img
                    src={`http://127.0.0.1:8000/api/outputs/file?path=${encodeURIComponent(preview.path)}`}
                    alt={preview.name}
                    className="max-w-full max-h-[70vh] object-contain"
                  />
                </object>
              ) : preview.type === "pdf" ? (
                <div className="text-center">
                  <div className="text-6xl text-destructive/60 font-bold mb-4">PDF</div>
                  <p className="text-sm text-muted-foreground">{preview.name}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-4"
                    onClick={() => {
                      window.open(
                        `http://127.0.0.1:8000/api/outputs/file?path=${encodeURIComponent(preview.path)}`,
                        "_blank"
                      );
                    }}
                  >
                    Open PDF
                  </Button>
                </div>
              ) : (
                <div className="text-center">
                  <div className="text-4xl text-muted-foreground font-mono mb-4">
                    {getFileIcon(preview.type)}
                  </div>
                  <p className="text-sm text-muted-foreground">{preview.name}</p>
                  <p className="text-xs text-muted-foreground/60 mt-1">{preview.path}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-4"
                    onClick={() => {
                      window.open(
                        `http://127.0.0.1:8000/api/outputs/file?path=${encodeURIComponent(preview.path)}`,
                        "_blank"
                      );
                    }}
                  >
                    Open File
                  </Button>
                </div>
              )}
            </div>
            {/* Modal footer: file info */}
            <div className="border-t border-border px-5 py-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
              <span>Path: {preview.path}</span>
              <span>Size: {preview.size}</span>
              <span>Source: {preview.source}</span>
              <span>Type: {preview.type}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
