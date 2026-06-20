"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRightIcon, SparklesIcon, XIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ThemeToggle } from "@/components/theme-toggle";

interface ApproachData {
  id: string;
  number: string;
  title: string;
  status: string;
  statusVariant: "default" | "secondary" | "destructive" | "outline" | "ghost";
  keyIdea: string;
  result: string;
  overview: string;
  flow: { label: string; description: string }[];
  advantages: string[];
  problems: string[];
  lessons: string[];
  outcome: string;
}

/* ── APPROACHES DATA (UNCHANGED) ── */
const APPROACHES: ApproachData[] = [
  {
    id: "1",
    number: "1",
    title: "Direct AI Image Generation",
    status: "Rejected",
    statusVariant: "destructive",
    keyIdea: "Generate diagrams directly using AI image models.",
    result: "Physics inconsistencies and non-deterministic outputs.",
    overview:
      "Attempted to generate Physics diagrams directly using image generation models such as ChatGPT Image Generation, Flux, Flux Schnell, and Stable Diffusion.",
    flow: [
      { label: "Question", description: "Physics question input" },
      { label: "Prompt", description: "AI image prompt generated" },
      { label: "Image Model", description: "Flux, SD, ChatGPT" },
      { label: "PNG", description: "Generated raster image" },
    ],
    advantages: ["Fast generation", "No domain logic required"],
    problems: [
      "Inconsistent outputs",
      "Wrong labels on diagrams",
      "Missing rays and vectors",
      "Physics inaccuracies",
      "No validation mechanism",
      "Non-deterministic results",
    ],
    lessons: [
      "AI images are not deterministic enough for educational diagrams",
      "Raster format cannot be reliably validated",
      "Domain-specific structure is essential",
    ],
    outcome:
      "Rejected. AI-generated images were not deterministic enough for educational diagrams.",
  },
  {
    id: "1.5",
    number: "1.5",
    title: "Diagram Knowledge Base",
    status: "Completed",
    statusVariant: "secondary",
    keyIdea:
      "Understand what information is required to recreate Physics diagrams.",
    result: "Foundation for schemas and blueprints.",
    overview:
      "Created the first Diagram Knowledge Base by collecting CBSE diagrams, generating prompts, reverse engineering diagram structure, and extracting structural information.",
    flow: [
      { label: "CBSE Diagrams", description: "Collected existing diagrams" },
      { label: "Analysis", description: "Reverse engineer structure" },
      { label: "Knowledge Base", description: "Extracted structured data" },
    ],
    advantages: [
      "Established that images contain structured information",
      "Provided foundation for later approaches",
    ],
    problems: ["Manual effort required", "Limited coverage"],
    lessons: [
      "Structure is more important than visual appearance",
      "Diagrams can be represented as structured blueprints",
    ],
    outcome: "Foundation for schemas and blueprints established.",
  },
  {
    id: "2",
    number: "2",
    title: "Schema-Based Representation",
    status: "Completed",
    statusVariant: "secondary",
    keyIdea: "Represent diagrams as structured JSON.",
    result: "Better than image generation but still unstable.",
    overview:
      "Introduced schema-based representation where diagrams are represented as structured JSON, then rendered to SVG through a dedicated renderer.",
    flow: [
      { label: "Question", description: "Physics question input" },
      { label: "LLM", description: "Generates structured schema" },
      { label: "Schema", description: "JSON diagram representation" },
      { label: "Renderer", description: "Converts schema to SVG" },
      { label: "SVG", description: "Final vector diagram" },
    ],
    advantages: ["Deterministic rendering", "Validatable output"],
    problems: [
      "Missing fields in generated schemas",
      "Hallucinated values by LLMs",
      "Weak consistency across runs",
    ],
    lessons: [
      "Schemas need strict validation",
      "LLMs alone cannot guarantee correct diagram structure",
    ],
    outcome:
      "Better than image generation but still unstable for production use.",
  },
  {
    id: "3",
    number: "3",
    title: "APPROCH2 Compiler System",
    status: "Completed",
    statusVariant: "secondary",
    keyIdea: "Create dedicated Physics rendering engines.",
    result: "Reliable SVG generation for 6 diagram families.",
    overview:
      "Built dedicated Physics rendering engines for six diagram families: Ray optics, Circuits, Free Body Diagrams, Magnetic fields, Semiconductors, and Graphs.",
    flow: [
      { label: "Validator", description: "Validates input parameters" },
      { label: "Layout Engine", description: "Computes positions" },
      { label: "Compiler", description: "Generates SVG instructions" },
      { label: "Renderer", description: "Produces final SVG" },
    ],
    advantages: [
      "Reliable SVG generation",
      "Physics-correct by construction",
      "Deterministic output",
    ],
    problems: [
      "Limited to predefined families",
      "Cannot handle unseen diagram types",
    ],
    lessons: [
      "Domain-specific compilers produce the most reliable results",
      "Layout engines must encode Physics rules explicitly",
    ],
    outcome: "Reliable SVG generation across 6 Physics diagram families.",
  },
  {
    id: "3.1",
    number: "3.1",
    title: "Example-Based Generation",
    status: "Completed",
    statusVariant: "secondary",
    keyIdea: "Reuse existing validated diagrams for similar questions.",
    result: "Higher accuracy, but fails for unseen questions.",
    overview:
      "Developed example-based generation that retrieves similar diagrams and modifies their blueprints to match the target question.",
    flow: [
      { label: "Retrieve", description: "Find similar diagram" },
      { label: "Modify", description: "Adapt blueprint" },
      { label: "Compile", description: "Generate SVG" },
    ],
    advantages: [
      "Higher accuracy on known patterns",
      "Physics consistency maintained",
      "Reuses validated knowledge",
    ],
    problems: ["Fails for completely unseen questions", "Limited by library size"],
    lessons: [
      "Example-based approaches need large, diverse libraries",
      "Similarity threshold tuning is critical",
    ],
    outcome: "Higher accuracy on known patterns, but fails for unseen questions.",
  },
  {
    id: "3.2",
    number: "3.2",
    title: "Hybrid Generation",
    status: "Current Production",
    statusVariant: "default",
    keyIdea: "Combine example retrieval with schema generation.",
    result: "Highest success rate achieved.",
    overview:
      "Implemented a hybrid approach: if similarity to an existing diagram ≥ 0.85, use example-based generation; otherwise fall back to schema-based generation.",
    flow: [
      { label: "Question", description: "Physics question" },
      { label: "Classifier", description: "Check similarity ≥ 0.85" },
      { label: "Example Path", description: "Retrieve and modify" },
      { label: "Schema Path", description: "Generate from schema" },
      { label: "SVG", description: "Final diagram output" },
    ],
    advantages: [
      "Handles both known and unseen questions",
      "Highest success rate across all approaches",
      "Graceful degradation",
    ],
    problems: [
      "Complexity of maintaining two systems",
      "Edge cases at similarity boundary",
    ],
    lessons: [
      "Hybrid systems provide the best balance of accuracy and coverage",
      "The 0.85 threshold was empirically determined",
    ],
    outcome: "Current production architecture with highest success rate.",
  },
  {
    id: "4",
    number: "4",
    title: "Diagram Engine V2",
    status: "Completed",
    statusVariant: "secondary",
    keyIdea: "Hide diagram complexity behind a single unified API.",
    result: "Reusable diagram service.",
    overview:
      "Encapsulated all diagram generation complexity behind a single DiagramEngine.generate_diagram() API, handling classification, retrieval, evaluation, and compilation internally.",
    flow: [
      { label: "Request", description: "generate_diagram() call" },
      { label: "Classifier", description: "Determine diagram family" },
      { label: "Retrieval", description: "Find existing matches" },
      { label: "Evaluator", description: "Check quality" },
      { label: "Compiler", description: "Produce SVG" },
    ],
    advantages: [
      "Clean API surface",
      "Separation of concerns",
      "Reusable across the application",
    ],
    problems: ["Tight coupling between stages"],
    lessons: [
      "Unified APIs simplify integration with question paper pipeline",
      "Internal modularity is still important",
    ],
    outcome: "Reusable diagram service integrated into the paper pipeline.",
  },
  {
    id: "5",
    number: "5",
    title: "Diagram Revision Engine",
    status: "Under Development",
    statusVariant: "outline",
    keyIdea: "Improve generated diagrams using natural language feedback.",
    result: "Improved SVG versions through iterative feedback.",
    overview:
      "Building a revision engine that accepts teacher feedback via natural language and regenerates diagram SVGs with changes applied, with full versioning support.",
    flow: [
      { label: "Diagram", description: "Generated SVG" },
      { label: "Feedback", description: "Teacher revision request" },
      { label: "Revision Engine", description: "Processes changes" },
      { label: "Regeneration", description: "Updated SVG" },
      { label: "Versioning", description: "Track revisions" },
    ],
    advantages: [
      "Iterative improvement",
      "Teacher-in-the-loop",
      "Full version history",
    ],
    problems: [
      "Revision quality depends on feedback clarity",
      "Under active development",
    ],
    lessons: ["Human feedback loops significantly improve output quality"],
    outcome: "Under Development — enabling iterative diagram refinement.",
  },
];

/* ── APPROACHES HELPERS (UNCHANGED) ── */
function FlowBlock({
  label,
  description,
  isLast,
}: {
  label: string;
  description: string;
  isLast: boolean;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex flex-col items-center">
        <div className="size-3 rounded-full bg-primary shrink-0 mt-1.5" />
        {!isLast && <div className="w-0.5 grow bg-border my-1" />}
      </div>
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

function ApproachTimelineCard({
  approach,
  isSelected,
  onClick,
}: {
  approach: ApproachData;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col gap-2 rounded-xl border p-4 text-left transition-all hover:shadow-md ${
        isSelected
          ? "border-primary bg-primary/5 ring-1 ring-primary"
          : "border-border bg-card hover:border-primary/50"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <Badge variant="outline" className="shrink-0 font-mono text-xs">
          v{approach.number}
        </Badge>
        <Badge variant={approach.statusVariant} className="shrink-0 text-[10px]">
          {approach.status}
        </Badge>
      </div>
      <h3 className="text-sm font-semibold leading-tight">{approach.title}</h3>
      <p className="text-xs text-muted-foreground line-clamp-2">
        {approach.keyIdea}
      </p>
      <p className="text-xs text-muted-foreground/70 line-clamp-1 italic">
        {approach.result}
      </p>
    </button>
  );
}

/* ── DIAGRAM FAMILIES DATA ── */
const DIAGRAM_FAMILIES = [
  { name: "Ray Optics", desc: "Light, mirrors, lenses" },
  { name: "Circuit", desc: "Resistors, batteries, switches" },
  { name: "FBD", desc: "Force vectors, equilibrium" },
  { name: "Magnetic", desc: "Fields, coils, electromagnets" },
  { name: "Semiconductor", desc: "Diodes, transistors, logic" },
  { name: "Graph", desc: "Motion, energy, wave plots" },
];

export default function Home() {
  const [selectedApproach, setSelectedApproach] = useState<ApproachData | null>(
    null
  );

  return (
    <div className="flex flex-col bg-background">
      {/* ══════════════════════════════════════ */}
      {/* 1. HERO                               */}
      {/* ══════════════════════════════════════ */}
      <section className="relative border-b border-border">
        {/* Navbar */}
        <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-5">
          <span className="text-lg font-bold tracking-tight text-foreground">
            VisualQ
          </span>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Button size="sm" asChild>
              <Link href="/paper_generation">
                <SparklesIcon className="size-3.5" />
                Generate Paper
              </Link>
            </Button>
          </div>
        </nav>

        {/* Hero content */}
        <div className="mx-auto flex w-full max-w-6xl flex-col lg:flex-row items-center gap-16 px-4 py-16 lg:py-24">
          {/* Left */}
          <div className="flex-1 flex flex-col gap-8 text-center lg:text-left">
            <div className="flex flex-col gap-4">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-foreground leading-[1.1]">
                VisualQ
              </h1>
              <p className="max-w-xl text-lg text-muted-foreground/90 leading-relaxed">
                AI Powered Physics Question Paper &amp; Diagram Intelligence
                Engine
              </p>
              <p className="max-w-xl text-sm text-muted-foreground/70 leading-relaxed">
                Generate CBSE Physics papers, detect diagram questions, create
                accurate SVG diagrams, and export ready-to-use assessments.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <Button size="lg" className="px-8 h-11 text-base" asChild>
                <Link href="/paper_generation">
                  <SparklesIcon className="size-4" />
                  Generate Paper
                </Link>
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="px-8 h-11 text-base"
                onClick={() =>
                  document
                    .getElementById("current-architecture")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
              >
                Explore Architecture
                <ArrowRightIcon className="size-4" />
              </Button>
            </div>
          </div>

          {/* Right: Pipeline visual */}
          <div className="hidden lg:flex flex-col items-center">
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <p className="text-xs font-medium text-muted-foreground text-center mb-5 uppercase tracking-widest">
                Pipeline
              </p>
              {[
                "Question",
                "Diagram Intelligence",
                "Blueprint",
                "Compiler",
                "SVG Diagram",
              ].map((step, idx) => (
                <div key={step} className="flex flex-col items-center">
                  <div
                    className={`rounded-xl border px-6 py-3 text-sm font-medium whitespace-nowrap ${
                      idx === 1
                        ? "border-primary/30 bg-primary/5 text-primary"
                        : idx === 3
                          ? "border-[#CBD83B]/30 bg-[#CBD83B]/5 text-[#CBD83B]"
                          : "border-border bg-muted/30 text-foreground/70"
                    }`}
                  >
                    {step}
                  </div>
                  {idx < 4 && (
                    <ArrowRightIcon className="size-3.5 text-muted-foreground/30 my-1.5" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════ */}
      {/* REST OF PAGE                          */}
      {/* ══════════════════════════════════════ */}
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-24 px-4 py-16">
        {/* ── 2. ABOUT ── */}
        <section className="flex flex-col gap-6 max-w-3xl">
          <h2 className="text-2xl font-semibold tracking-tight">About</h2>
          <div className="flex flex-col gap-4 text-sm text-muted-foreground leading-relaxed">
            <p>
              VisualQ is a research-driven educational AI platform for
              generating Physics question papers and automatically creating the
              diagrams required to solve them.
            </p>
            <p>
              The system uses a deterministic rendering approach: instead of
              generating images directly with AI, it produces structured
              blueprints that are compiled into accurate SVG diagrams through
              dedicated Physics rendering engines.
            </p>
            <p>
              Each diagram family — Ray optics, Circuits, Free Body Diagrams,
              Magnetic fields, Semiconductors, and Graphs — has its own
              compiler, ensuring physics-correct, reproducible output every
              time.
            </p>
          </div>
        </section>

        {/* ── 3. METRICS ── */}
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { value: "267+", label: "Questions" },
            { value: "6", label: "Diagram Families" },
            { value: "8", label: "Architecture Iterations" },
            { value: "100%", label: "SVG Rendering" },
          ].map((m) => (
            <Card key={m.label} className="text-center">
              <CardContent className="py-6">
                <p className="text-3xl font-bold text-foreground">{m.value}</p>
                <p className="text-sm text-muted-foreground mt-1">{m.label}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        {/* ── 4. DIAGRAM FAMILIES ── */}
        <section className="flex flex-col gap-6">
          <h2 className="text-2xl font-semibold tracking-tight">
            Diagram Families
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {DIAGRAM_FAMILIES.map((f) => (
              <Card key={f.name} className="text-center">
                <CardContent className="py-5">
                  <p className="text-sm font-semibold">{f.name}</p>
                  <p className="text-xs text-muted-foreground mt-1">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* ── 5. CURRENT ARCHITECTURE ── */}
        <section
          id="current-architecture"
          className="flex flex-col gap-6 rounded-xl border border-border bg-card p-8"
        >
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-2xl font-semibold tracking-tight">
              Current Architecture
            </h2>
            <div className="flex items-center gap-2">
              <Badge>Production Candidate</Badge>
              <Badge variant="outline" className="font-mono">
                Diagram Engine V2
              </Badge>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {[
              "Question",
              "Paper Engine",
              "Diagram Engine",
              "Revision Engine",
              "PDF Export",
              "Output",
            ].map((label, idx) => (
              <div key={label} className="flex items-center gap-2">
                <div className="rounded-lg border border-border bg-muted/50 px-4 py-2 text-sm font-medium">
                  {label}
                </div>
                {idx < 5 && (
                  <ArrowRightIcon className="size-3.5 text-muted-foreground/40 shrink-0" />
                )}
              </div>
            ))}
          </div>

          <p className="text-xs text-muted-foreground">
            End-to-end pipeline — from question input to final PDF output with
            diagram intelligence.
          </p>
        </section>

        {/* ── 6. APPROACHES (UNTOUCHED) ── */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold tracking-tight">
              Evolution Timeline
            </h2>
            {selectedApproach && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedApproach(null)}
              >
                <XIcon className="size-3.5" />
                Clear selection
              </Button>
            )}
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {APPROACHES.map((approach) => (
              <ApproachTimelineCard
                key={approach.id}
                approach={approach}
                isSelected={selectedApproach?.id === approach.id}
                onClick={() => setSelectedApproach(approach)}
              />
            ))}
          </div>
        </section>

        {/* ── APPROACH DETAIL (UNTOUCHED) ── */}
        {selectedApproach && (
          <section className="flex flex-col gap-6">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Badge variant="outline" className="font-mono">
                  v{selectedApproach.number}
                </Badge>
                <h2 className="text-xl font-semibold tracking-tight">
                  {selectedApproach.title}
                </h2>
                <Badge variant={selectedApproach.statusVariant}>
                  {selectedApproach.status}
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedApproach(null)}
              >
                <XIcon className="size-4" />
              </Button>
            </div>

            <div className="grid gap-6 lg:grid-cols-5">
              <div className="flex flex-col gap-6 lg:col-span-3">
                <Card>
                  <CardHeader>
                    <CardTitle>Overview</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {selectedApproach.overview}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Architecture</CardTitle>
                    <CardDescription>Data flow through the system</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-col gap-1">
                      {selectedApproach.flow.map((step, idx) => (
                        <FlowBlock
                          key={step.label}
                          label={step.label}
                          description={step.description}
                          isLast={idx === selectedApproach.flow.length - 1}
                        />
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Final Outcome</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {selectedApproach.outcome}
                    </p>
                  </CardContent>
                </Card>
              </div>

              <div className="flex flex-col gap-6 lg:col-span-2">
                {selectedApproach.advantages.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Advantages</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="flex flex-col gap-2 text-sm text-muted-foreground">
                        {selectedApproach.advantages.map((item) => (
                          <li key={item} className="flex items-start gap-2">
                            <span className="text-primary mt-0.5 shrink-0">+</span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {selectedApproach.problems.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Problems Faced</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="flex flex-col gap-2 text-sm text-muted-foreground">
                        {selectedApproach.problems.map((item) => (
                          <li key={item} className="flex items-start gap-2">
                            <span className="text-destructive mt-0.5 shrink-0">−</span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {selectedApproach.lessons.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Lessons Learned</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="flex flex-col gap-2 text-sm text-muted-foreground">
                        {selectedApproach.lessons.map((item) => (
                          <li key={item} className="flex items-start gap-2">
                            <span className="text-primary mt-0.5 shrink-0">~</span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </section>
        )}

        {/* ── Footer ── */}
        <footer className="border-t border-border pt-8 text-center text-xs text-muted-foreground">
          VisualQ — Diagram Engine V2
        </footer>
      </main>
    </div>
  );
}
