# VisualQ Pilot — Complete Project Knowledge Base & Handover Document

## Project Goal
**VisualQ Pilot** is an AI-powered CBSE Class 12 Physics Question Paper Generator. It integrates a curated PYQ (Previous Year Questions) question bank, the NCERT Physics Part-1 (Electromagnetism) knowledge base, LLMs (Gemini API), and a rule-based diagram intelligence layer.

The system performs:
- CBSE-compliant question paper generation
- Balanced mix of PYQ retrieval and AI-generated questions
- Automated diagram requirement detection for physics questions
- Deterministic diagram blueprint schema generation and rendering to SVGs
- Evaluation metrics, chapter coverage reports, and PDF exports

---

## Architectural Philosophy & Core Decisions

### Selected Diagram Architecture: Deterministic SVG Compiler (Approach 2)
The project evaluated two approaches for diagram generation:
1. **Approach 1: LLM/Image Model Generation (FLUX/Gemini/OpenRouter)**
   - *Result:* **Rejected**.
   - *Reason:* Unreliable geometry, incorrect text labels, and poor adherence to CBSE's precise diagram requirements.
2. **Approach 2: Physics → Blueprint → SVG Renderer (Selected)**
   - *Result:* **Adopted**.
   - *Reason:* Completely explainable, deterministic, reusable, and ensures CBSE-compliant accuracy for labels, coordinate spaces, and physical optics.

```
Question 
  ↳ Diagram Detection / Taxonomy Lookup
  ↳ Diagram Schema & Blueprint Customization
  ↳ Math Solver & Rule Validation (e.g., Lens Equation)
  ↳ SVG Compiler & Renderer
  ↳ Output SVG Vector Graphic
```

---

## Complete Project Directory & File Index

### Root Workspace Directory: `c:\CODES\VQP`

- [AppFlow.md](file:///c:/CODES/VQP/AppFlow.md) - Outlines the high-level step-by-step program execution flow of the application.
- [Design.md](file:///c:/CODES/VQP/Design.md) - Details core UI/UX style guidelines, visual layout rules, and component specs.
- [Image prompt.txt](file:///c:/CODES/VQP/Image%20prompt.txt) - Contains prompt engineering attempts and test cases for text-to-image models.
- [ImplementationPlan.md](file:///c:/CODES/VQP/ImplementationPlan.md) - Tracks development milestones and technical execution stages.
- [PRD.md](file:///c:/CODES/VQP/PRD.md) - Product Requirements Document listing user personas, core features, and success metrics.
- [Rules.md](file:///c:/CODES/VQP/Rules.md) - Developer guidelines, constraints, and coding standards.
- [Schemas.md](file:///c:/CODES/VQP/Schemas.md) - Data models and database schemas (documents, chunks, knowledge graph, papers, diagrams, logs).
- [TechSpec.md](file:///c:/CODES/VQP/TechSpec.md) - System architecture design specification and API boundaries.
- [Tracker.md](file:///c:/CODES/VQP/Tracker.md) - Living status checklist tracking done, in-progress, and planned features.
- [schema prompt.txt](file:///c:/CODES/VQP/schema%20prompt.txt) - Prompt definitions and rules for generating compliant blueprint schemas.
- [scratch_inspect.py](file:///c:/CODES/VQP/scratch_inspect.py) - Ad-hoc Python script for examining generated database outputs and local JSON structures.
- [test_classification.py](file:///c:/CODES/VQP/test_classification.py) - Script containing tests to verify question taxonomy and diagram category mapping.
- [test_selection.py](file:///c:/CODES/VQP/test_selection.py) - Tests for validating question selection and retrieval weightage.

---

### Backend Service: `c:\CODES\VQP\backend`
FastAPI server managing paper orchestration, question generation, and diagram pipeline.

- [backend/.env.example](file:///c:/CODES/VQP/backend/.env.example) - Template file containing environment configuration keys.
- [backend/requirements.txt](file:///c:/CODES/VQP/backend/requirements.txt) - List of Python package dependencies for the backend.
- [backend/ray.py](file:///c:/CODES/VQP/backend/ray.py) - Standalone sandbox script prototyping ray optics math calculations and SVG markup.
- [backend/app/main.py](file:///c:/CODES/VQP/backend/app/main.py) - FastAPI application initialization, middleware registration, and router imports.

#### 1. API Endpoints (`backend/app/api/`)
- [debug.py](file:///c:/CODES/VQP/backend/app/api/debug.py) - Developer API endpoints to test intermediate steps of generators and retrievers.
- [dependencies.py](file:///c:/CODES/VQP/backend/app/api/dependencies.py) - Dependency injection setup for configuration, services, and model clients.
- [diagram.py](file:///c:/CODES/VQP/backend/app/api/diagram.py) - API routes managing diagram detection, schema generation, and rendering requests.
- [health.py](file:///c:/CODES/VQP/backend/app/api/health.py) - Health-check endpoint returning API server health, config, and dataset metrics.
- [paper.py](file:///c:/CODES/VQP/backend/app/api/paper.py) - Handles the paper generation request payload and triggers orchestration.

#### 2. Core Config & Logger (`backend/app/core/`)
- [config.py](file:///c:/CODES/VQP/backend/app/core/config.py) - Global settings configurations loaded from `.env` using Pydantic.
- [exceptions.py](file:///c:/CODES/VQP/backend/app/core/exceptions.py) - Custom application exception classes and standard HTTP exception handlers.
- [logging_config.py](file:///c:/CODES/VQP/backend/app/core/logging_config.py) - Sets up logging levels and formats for backend logs.

#### 3. Data Models (`backend/app/models/`)
- [enums.py](file:///c:/CODES/VQP/backend/app/models/enums.py) - Common Enum declarations (e.g. Difficulty, DiagramType).
- [requests.py](file:///c:/CODES/VQP/backend/app/models/requests.py) - Pydantic structures for validating request body payloads.
- [responses.py](file:///c:/CODES/VQP/backend/app/models/responses.py) - Pydantic structures validating response schemas.

#### 4. Logic Services (`backend/app/services/`)
- [allocation.py](file:///c:/CODES/VQP/backend/app/services/allocation.py) - Computes optimal distribution of marks and questions based on weightage.
- [book_service.py](file:///c:/CODES/VQP/backend/app/services/book_service.py) - Serves NCERT chapter content and performs keyword search/grounding.
- [diagram_generators.py](file:///c:/CODES/VQP/backend/app/services/diagram_generators.py) - Contains spec/blueprint generators for the 5 physics diagram families.
- [diagram_retrieval_service.py](file:///c:/CODES/VQP/backend/app/services/diagram_retrieval_service.py) - Logic to query and extract matches from the diagram library.
- [diagram_router.py](file:///c:/CODES/VQP/backend/app/services/diagram_router.py) - Dispatches incoming requests to the specific diagram-type service.
- [diagram_service.py](file:///c:/CODES/VQP/backend/app/services/diagram_service.py) - High-level service managing diagram pipeline integration.
- [diagram_svg.py](file:///c:/CODES/VQP/backend/app/services/diagram_svg.py) - Maps schema blueprints to compiled SVG XML strings.
- [diagram_taxonomy_service.py](file:///c:/CODES/VQP/backend/app/services/diagram_taxonomy_service.py) - Inspects physics concepts and classifies them into families.
- [diagram_template_service.py](file:///c:/CODES/VQP/backend/app/services/diagram_template_service.py) - Ingests and provides default templates for SVG layouts.
- [diagram_validation_service.py](file:///c:/CODES/VQP/backend/app/services/diagram_validation_service.py) - Verifies if blueprints meet coordinate boundaries and physical rules.
- [export_service.py](file:///c:/CODES/VQP/backend/app/services/export_service.py) - Transforms question paper objects into download-friendly formats.
- [gemini_service.py](file:///c:/CODES/VQP/backend/app/services/gemini_service.py) - Interfaces with Google Gemini API for AI question generation and editing.
- [local_question_generator.py](file:///c:/CODES/VQP/backend/app/services/local_question_generator.py) - Fallback/stub generator providing offline questions if API keys are absent.
- [magnetic_field_engine.py](file:///c:/CODES/VQP/backend/app/services/magnetic_field_engine.py) - Math solver for magnetic field lines (solenoids, coils, wires).
- [magnetic_field_renderer.py](file:///c:/CODES/VQP/backend/app/services/magnetic_field_renderer.py) - Coordinates SVG drawing commands for magnetic fields.
- [matplotlib_renderer.py](file:///c:/CODES/VQP/backend/app/services/matplotlib_renderer.py) - Renders mathematical graphs as SVG using Matplotlib.
- [orchestrator_service.py](file:///c:/CODES/VQP/backend/app/services/orchestrator_service.py) - Coordinates paper selection, weightage, AI generation, diagram linking, and final assembly.
- [paper_evaluator.py](file:///c:/CODES/VQP/backend/app/services/paper_evaluator.py) - Evaluates generated question papers for quality, syllabus alignment, and CBSE rules.
- [paper_service.py](file:///c:/CODES/VQP/backend/app/services/paper_service.py) - Manages raw generated paper assembly and formatting.
- [physics_knowledge_retriever.py](file:///c:/CODES/VQP/backend/app/services/physics_knowledge_retriever.py) - Pulls formula sheets and concept definitions.
- [physics_understanding_service.py](file:///c:/CODES/VQP/backend/app/services/physics_understanding_service.py) - Extracts variables, constants, and target unknowns from raw questions.
- [prompt_builder.py](file:///c:/CODES/VQP/backend/app/services/prompt_builder.py) - Renders structured prompt strings for Gemini API calls.
- [question_service.py](file:///c:/CODES/VQP/backend/app/services/question_service.py) - Filters and returns items from the offline PYQ question bank.
- [schema_adaptation_service.py](file:///c:/CODES/VQP/backend/app/services/schema_adaptation_service.py) - Adapts static templates with dynamically calculated physics variables.
- [schema_population_service.py](file:///c:/CODES/VQP/backend/app/services/schema_population_service.py) - Injects numerical constraints into schemas.
- [schemdraw_renderer.py](file:///c:/CODES/VQP/backend/app/services/schemdraw_renderer.py) - Renders electrical circuits utilizing the PySchemdraw library.
- [weightage_service.py](file:///c:/CODES/VQP/backend/app/services/weightage_service.py) - Calculates dynamic chapter weightage distributions.

#### 5. Data & JSON Files (`backend/app/data/`)
- `Book/` - Standard NCERT Class 12 Physics Part-1 chapter contents and metadata index.
- `Physics/` - Core physics formulas and relation datasets.
- `diagram_library/` - Curated database of seed questions and structural properties for circuits, graphs, ray optics, magnetic fields, and FB-diagrams.
- `diagram_taxonomy/` - Taxonomical hierarchy mapping CBSE question descriptions to diagram families.
- `diagram_templates/` - Configurable baseline blueprints for the 18 main physics diagrams.
- `question_bank/` - Offline JSON file stores for the 214 pre-labeled PYQs.

---

### Diagram Compiler: `c:\CODES\VQP\approch2`
Isolated system implementing deterministic SVG generation using mathematics solvers and ray rules.

- [approch2/blueprint_builder.py](file:///c:/CODES/VQP/approch2/blueprint_builder.py) - Builds custom blueprints mapping to physics renderer requirements.
- [approch2/classifier.py](file:///c:/CODES/VQP/approch2/classifier.py) - Categorizes question text into designated physics diagram families.
- [approch2/main.py](file:///c:/CODES/VQP/approch2/main.py) - Test entrypoint loading blueprints, calling the SVG renderer, and outputting SVGs.
- [approch2/physics_solver.py](file:///c:/CODES/VQP/approch2/physics_solver.py) - Resolves physics formulas (e.g. Lens formula $1/f = 1/v - 1/u$).
- [approch2/ray_math.py](file:///c:/CODES/VQP/approch2/ray_math.py) - Coordinate calculations for ray vector intersections, reflections, and refractions.
- [approch2/ray_rules.py](file:///c:/CODES/VQP/approch2/ray_rules.py) - System constraints containing rules and standard focal ratios for ray diagrams.
- [approch2/renderer.py](file:///c:/CODES/VQP/approch2/renderer.py) - Primary dispatch wrapper routing blueprint items to their respective sub-renderers.
- [approch2/retriever.py](file:///c:/CODES/VQP/approch2/retriever.py) - Retrieves reference blueprint specifications matching a target question category.
- [approch2/schema_adapter.py](file:///c:/CODES/VQP/approch2/schema_adapter.py) - Overwrites generic template values with question variables.
- [approch2/renderers/ray_renderer.py](file:///c:/CODES/VQP/approch2/renderers/ray_renderer.py) - Renders precise, multi-ray optics diagrams for concave/convex lenses/mirrors as standard SVG text.

---

### Frontend Interface: `c:\CODES\VQP\frontend`
Next.js client allowing users to configure, generate, preview, and export test papers.

- [frontend/package.json](file:///c:/CODES/VQP/frontend/package.json) - Node package specifications and build/run scripts.
- [frontend/tsconfig.json](file:///c:/CODES/VQP/frontend/tsconfig.json) - TypeScript compiler setup rules.
- [frontend/next.config.ts](file:///c:/CODES/VQP/frontend/next.config.ts) - Next.js framework configuration.
- [frontend/src/app/layout.tsx](file:///c:/CODES/VQP/frontend/src/app/layout.tsx) - Base layout defining default styling, theme support, and typography.
- [frontend/src/app/page.tsx](file:///c:/CODES/VQP/frontend/src/app/page.tsx) - Main page containing visual headers, side-by-side builder, and renderer view.
- [frontend/src/components/paper-form.tsx](file:///c:/CODES/VQP/frontend/src/components/paper-form.tsx) - Renders interactive controls (difficulty selectors, question counters, and chapter checklist).
- [frontend/src/components/question-list.tsx](file:///c:/CODES/VQP/frontend/src/components/question-list.tsx) - Renders generated test questions, solutions, and inline vector SVGs.
- [frontend/src/components/results-summary.tsx](file:///c:/CODES/VQP/frontend/src/components/results-summary.tsx) - Visual dashboards displaying chapter percentages, difficulty weightage, and test metrics.
- [frontend/src/lib/api.ts](file:///c:/CODES/VQP/frontend/src/lib/api.ts) - Wrapper functions communicating with backend FastAPI endpoints.
- [frontend/src/lib/types.ts](file:///c:/CODES/VQP/frontend/src/lib/types.ts) - Type interfaces matching request and response formats.
- [frontend/src/lib/utils.ts](file:///c:/CODES/VQP/frontend/src/lib/utils.ts) - Utility functions (e.g. `cn` wrapper for Tailwind CSS classes).
- `frontend/src/components/ui/` - Contains 16 reusable visual components powered by Tailwind and Radix UI (buttons, cards, badges, dialogs, sliders, tabs, tables).

---

### Data Ingestion Pipeline: `c:\CODES\VQP\datapipeline`
Script suite used during ingestion phase to clean, audit, label, and validate the source corpus.

- [datapipeline/model.py](file:///c:/CODES/VQP/datapipeline/model.py) - Baseline ingestion models.
- [datapipeline/src/main.py](file:///c:/CODES/VQP/datapipeline/src/main.py) - Entrypoint pipeline script automating extraction, classification, and validation.

---

### Evaluation Sandbox: `c:\CODES\VQP\flux`
Evaluates text-to-image models for diagram generation (used for early testing, now deprecated).

- [flux/flux_service.py](file:///c:/CODES/VQP/flux/flux_service.py) - API interface wrapper calling Replicate's FLUX endpoints.
- [flux/main.py](file:///c:/CODES/VQP/flux/main.py) - Script to send test prompts and save output image assets.

---

### Helper Scripts: `c:\CODES\VQP\scripts`
- [scripts/build_seed_diagram_questions.py](file:///c:/CODES/VQP/scripts/build_seed_diagram_questions.py) - Script compiling base question sets to build seed datasets.
- [scripts/copypaste.py](file:///c:/CODES/VQP/scripts/copypaste.py) - Small development helper script for moving files.
