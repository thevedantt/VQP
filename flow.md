# VisualQ (VQP) System Architecture & Control Flow

This document details the system architecture, control flow, LLM orchestration, and generation engines of the VisualQ educational assessment platform.

---

## 1. High-Level System Architecture

VisualQ is structured as a decoupled web application with a **Next.js frontend** and a **FastAPI backend** managing a multi-stage **Diagram Intelligence & Question Paper Generation Engine**.

```mermaid
graph TD
    %% Define Styles
    classDef client fill:#e8f0fe,stroke:#4285f4,stroke-width:2px,color:#1a73e8;
    classDef api fill:#e6f4ea,stroke:#34a853,stroke-width:2px,color:#137333;
    classDef engine fill:#fef7e0,stroke:#fbbc05,stroke-width:2px,color:#b06000;
    classDef external fill:#fce8e6,stroke:#ea4335,stroke-width:2px,color:#c5221f;
    
    %% Nodes
    subgraph Frontend [Next.js Client Application]
        UI["React SPA Dashboard<br>(Paper Creation & Diagram Gallery)"]:::client
        RevModal["Improve Diagram Modal<br>(Feedback & Suggestions)"]:::client
    end

    subgraph Backend [FastAPI Backend Service]
        PaperAPI["[paper_api.py](file:///c:/CODES/VQP/backend_v2/pipeline/paper_api.py)<br>(Routing & HTTP Endpoints)"]:::api
        PaperBuilder["[paper_builder.py](file:///c:/CODES/VQP/backend_v2/pipeline/paper_builder.py)<br>(Quota & Structure Orchestrator)"]:::engine
        QSelector["[question_selector.py](file:///c:/CODES/VQP/backend_v2/pipeline/question_selector.py)<br>(PYQ Pool & AI Top-Up Controller)"]:::engine
        DiagramEngine["[diagram_engine.py](file:///c:/CODES/VQP/backend_v2/diagram_engine/diagram_engine.py)<br>(Unified Diagram Interface)"]:::engine
        DiagramPipeline["[diagram_generation_pipeline.py](file:///c:/CODES/VQP/backend_v2/diagram_generation/diagram_generation_pipeline.py)<br>(Hybrid Generation Pipeline)"]:::engine
        RevisionEngine["[revision_engine.py](file:///c:/CODES/VQP/backend_v2/diagram_revision/revision_engine.py)<br>(Feedback & Modification Engine)"]:::engine
        CompilerRouter["[diagram_pipeline.py](file:///c:/CODES/VQP/backend_v2/pipeline/diagram_pipeline.py)<br>(Adapters & Rendering Compilers)"]:::engine
    end

    subgraph External [External APIs & Services]
        OpenRouter["OpenRouter API<br>(gpt-oss-120b)"]:::external
        GeminiAPI["Google Gemini API<br>(gemini-3.5-flash)"]:::external
    end

    %% Connections
    UI -->|POST /api/generate-paper| PaperAPI
    UI -->|POST /api/generate-all-diagrams| PaperAPI
    RevModal -->|POST /api/diagrams/.../revise| PaperAPI
    
    PaperAPI --> PaperBuilder
    PaperAPI --> DiagramEngine
    PaperAPI --> RevisionEngine
    
    PaperBuilder --> QSelector
    QSelector -->|Generate AI Question| OpenRouter
    
    DiagramEngine --> DiagramPipeline
    DiagramPipeline -->|Retrieve & Match| ModeA[Mode A: Example-Based]
    DiagramPipeline -->|Generate from Schema| ModeB[Mode B: Schema-Based]
    DiagramPipeline -->|Refine & Verify Blueprint| GeminiAPI
    DiagramPipeline --> CompilerRouter
    
    RevisionEngine -->|Modify Blueprint| GeminiAPI
    RevisionEngine --> CompilerRouter
```

---

## 2. LLM Call Orchestration

VisualQ selectively utilizes different Large Language Models (LLMs) depending on the task's latency, reasoning depth, and cost requirements.

| Call Source | Targeted File | Model Used | API Client / Key | Role & Functional Description |
| :--- | :--- | :--- | :--- | :--- |
| **Question Generation** | [[ai_question_generator.py](file:///c:/CODES/VQP/backend_v2/pipeline/ai_question_generator.py)] | `gpt-oss-120b` (Primary)<br>`fallback-model` (Fallback) | OpenRouter API<br>`OPENROUTER_API_KEY` | Generates unique syllabus-aligned CBSE physics questions tailored by marks, difficulty, and diagram constraints. |
| **Diagram Classification** | [[llm_classifier.py](file:///c:/CODES/VQP/backend_v2/diagram_intelligence/classifier/llm_classifier.py)] | `gpt-oss-120b` | OpenRouter API<br>`OPENROUTER_API_KEY` | Classifies questions to determine if a diagram is required and maps it to one of the 6 diagram families. |
| **Diagram Explanation** | [[diagram_explainer.py](file:///c:/CODES/VQP/backend_v2/diagram_generation/diagram_explainer.py)] | `gpt-oss-120b` | OpenRouter API<br>`OPENROUTER_API_KEY` | Produces a question-specific, single-sentence explanation (max 25 words) justifying why the diagram is necessary. |
| **Blueprint Modifying** (Mode A) | [[blueprint_modifier.py](file:///c:/CODES/VQP/backend_v2/diagram_generation/blueprint_modifier.py)] | `gpt-oss-120b` | OpenRouter API<br>`OPENROUTER_API_KEY` | Takes a retrieved example blueprint and adapts its coordinates, labels, and parameters to match the new question. |
| **Blueprint Generator** (Mode B) | [[schema_blueprint_generator.py](file:///c:/CODES/VQP/backend_v2/diagram_generation/schema_blueprint_generator.py)] | `gpt-oss-120b` | OpenRouter API<br>`OPENROUTER_API_KEY` | Generates a fresh blueprint from raw JSON schemas when no matching example is found in the database. |
| **Blueprint Evaluation** | [[gemini_evaluator.py](file:///c:/CODES/VQP/backend_v2/llm/gemini_evaluator.py)] | `gemini-3.5-flash` | Gemini SDK<br>`GEMINI_API_KEY` | Evaluates raw blueprints against schemas, finding structural/physics errors and supplying a corrected blueprint. |
| **Diagram Revision** | [[revision_engine.py](file:///c:/CODES/VQP/backend_v2/diagram_revision/revision_engine.py)] | `gemini-3.5-flash` | Gemini SDK<br>`GEMINI_API_KEY2` | Modifies an existing working blueprint to accommodate user feedback and direct correction instructions. |
| **Suggestion Generation** | [[suggestion_engine.py](file:///c:/CODES/VQP/backend_v2/diagram_revision/suggestion_engine.py)] | `gemini-3.5-flash` | Gemini SDK<br>`GEMINI_API_KEY2` | Audits the current diagram state to present 3-5 concrete, actionable improvements to the user. |

---

## 3. Question Paper Generation Flow

Paper generation combines Past Year Questions (PYQ) with real-time AI-generated questions to form structured assessments based on configured ratios.

```mermaid
sequenceDiagram
    autonumber
    actor User as Teacher (Client)
    participant API as [paper_api.py](file:///c:/CODES/VQP/backend_v2/pipeline/paper_api.py)
    participant Builder as [paper_builder.py](file:///c:/CODES/VQP/backend_v2/pipeline/paper_builder.py)
    participant Selector as [question_selector.py](file:///c:/CODES/VQP/backend_v2/pipeline/question_selector.py)
    participant LLM as [ai_question_generator.py](file:///c:/CODES/VQP/backend_v2/pipeline/ai_question_generator.py)

    User->>API: POST /api/generate-paper (template, PYQ/AI ratio, difficulty)
    API->>Builder: build_paper()
    Builder->>Selector: select_for_template()
    
    Note over Selector: Load static datasets:<br>descriptive_questions.json & mcq_questions.json
    
    loop For Each Template Section & Block
        Selector->>Selector: Filter candidates (difficulty, chapter, type)
        Selector->>Selector: Stable sort by least-used chapter in paper (balanced)
        
        alt Diagram Quota > 0 (Fill diagrams first)
            Selector->>Selector: Pull diagram-required PYQs
            alt PYQ pool exhausted
                Selector->>LLM: Generate diagram-required AI Question (OpenRouter)
            end
        end
        
        Selector->>Selector: Fill remaining slots based on PYQ/AI ratio
        alt AI slot required
            Selector->>LLM: Generate normal AI Question (OpenRouter)
        end
    end
    
    Builder->>Selector: enforce_overall_diagram_ratio() (Top-up to meet target 20-30%)
    Builder->>Selector: enforce_overall_pyq_ratio() (Swap AI/PYQ to hit exact target split)
    
    Note over Builder: Run quality checks & lock question list (Q01, Q02, ...)
    Builder-->>API: Save paper to outputv2/papers/{id}.json
    API-->>User: Return paper JSON
```

<p align="center">
  <img src="./frontend/public/AI-Driven_Question_Paper_Architecture.png" alt="AI-Driven Question Paper Architecture" width="100%">
</p>

---

## 4. Diagram Generation Pipeline

Once the paper is locked, diagram-required questions pass through the Diagram Intelligence Engine. Diagram generation is **deterministic**; instead of generating pixels, the LLM generates a structured **Blueprint**, which is compiled into vector graphics.

```mermaid
flowchart TD
    %% Node Definitions
    Start([Question with diagram_required=True])
    Classifier{"[llm_classifier.py](file:///c:/CODES/VQP/backend_v2/diagram_intelligence/classifier/llm_classifier.py)<br>Classify Family"}
    Validator{"[family_validator.py](file:///c:/CODES/VQP/backend_v2/diagram_generation/family_validator.py)<br>Valid?"}
    Explainer["[diagram_explainer.py](file:///c:/CODES/VQP/backend_v2/diagram_generation/diagram_explainer.py)<br>Generate specific explanation"]
    Retriever["[example_retriever.py](file:///c:/CODES/VQP/backend_v2/diagram_generation/example_retriever.py)<br>Search vector similarity"]
    Threshold{"Similarity >= 0.85?"}
    
    Modifier["[blueprint_modifier.py](file:///c:/CODES/VQP/backend_v2/diagram_generation/blueprint_modifier.py)<br><b>Mode A: Example-Based</b><br>Adapt existing example"]
    Generator["[schema_blueprint_generator.py](file:///c:/CODES/VQP/backend_v2/diagram_generation/schema_blueprint_generator.py)<br><b>Mode B: Schema-Based</b><br>Generate from raw schema"]
    
    Evaluator["[gemini_evaluator.py](file:///c:/CODES/VQP/backend_v2/llm/gemini_evaluator.py)<br>Gemini validation & correction"]
    Adapter["Adapter Mapping Layer<br>(Translates general blueprint to compiler formats)"]
    Compiler["[diagram_pipeline.py](file:///c:/CODES/VQP/backend_v2/pipeline/diagram_pipeline.py)<br>Run family-specific compiler"]
    SVGCheck{"SVG Check<br>(Stale cleanup, blank detection)"}
    Traceability["Save run artifacts<br>(outputv2/diagram_runs/{paper}/{question}/)"]
    Success([SVG Diagram generated])

    %% Layout Connectors
    Start --> Classifier
    Classifier --> Validator
    Validator -- Yes --> Explainer
    Validator -- No/Auto-corrected --> Explainer
    Explainer --> Retriever
    Retriever --> Threshold
    
    Threshold -- Yes --> Modifier
    Threshold -- No --> Generator
    
    Modifier --> Evaluator
    Generator --> Evaluator
    
    Evaluator --> Adapter
    Adapter --> Compiler
    Compiler --> SVGCheck
    SVGCheck --> Traceability
    Traceability --> Success
```

---

## 5. Diagram Revision & Suggestion Flow

Teachers can iteratively modify and improve generated diagrams via the UI. Feedback processes go through a feedback processor and are executed using Gemini to adjust blueprint nodes.

```mermaid
sequenceDiagram
    autonumber
    actor User as Teacher (Client)
    participant UI as Next.js Gallery Frontend
    participant API as [diagram.py](file:///c:/CODES/VQP/backend_v2/api/diagram.py)
    participant Sugg as [suggestion_engine.py](file:///c:/CODES/VQP/backend_v2/diagram_revision/suggestion_engine.py)
    participant Rev as [revision_engine.py](file:///c:/CODES/VQP/backend_v2/diagram_revision/revision_engine.py)
    participant Proc as [feedback_processor.py](file:///c:/CODES/VQP/backend_v2/diagram_revision/feedback_processor.py)
    participant Gemini as Gemini API (gemini-3.5-flash)
    participant Compiler as [diagram_pipeline.py](file:///c:/CODES/VQP/backend_v2/pipeline/diagram_pipeline.py)

    UI->>API: GET /api/diagrams/{paper_id}/{question_id}/suggestions
    API->>Sugg: generate_suggestions()
    Sugg->>Gemini: Predict improvements based on current blueprint & validator reports
    Sugg-->>UI: Return 3-5 suggestions (e.g. "Add current direction", "Increase lens size")

    User->>UI: Select suggestions & write custom feedback
    UI->>API: POST /api/diagrams/{paper_id}/{question_id}/revise
    API->>Rev: revise_diagram(feedback, selected_suggestions)
    
    Note over Rev: Fetch latest blueprint and revision version (v1, v2, ...)
    
    alt User wrote custom feedback
        Rev->>Proc: process()
        Proc->>Gemini: Parse feedback text into discrete requested changes
    end
    
    Rev->>Gemini: _revise_blueprint(current_blueprint, changes)
    Gemini-->>Rev: Return revised blueprint structure
    
    Rev->>Compiler: compile_and_check(revised_blueprint)
    Note over Compiler: Adapter transforms blueprint & renders new SVG
    Compiler-->>Rev: Validate SVG (size, elements)
    
    Note over Rev: Save versioned files (blueprint_v2.json, diagram_v2.svg, metadata)
    Rev-->>UI: Return Success & SVG path
```

---

## 6. Diagram Compiler System

The compiler system translates the high-level schema blueprint into a final SVG output using specialized, deterministic python modules:

1. **Ray Diagrams (`ray`)**
   - **Compiler:** `approch2/ray/ray_compiler.py`
   - **Concepts:** Convex lens scenarios (`beyond_2f`, `at_2f`, `between_f_and_2f`, `inside_f`). Computes focal points, object positions, and traces light paths (`parallel_ray`, `optical_center_ray`, `focal_ray`) intersecting at focal points.
2. **Circuit Diagrams (`circuit`)**
   - **Compiler:** `approch2/circuit/circuit_compiler.py`
   - **Concepts:** Passive networks containing cells, batteries, switches, resistors, ammeters, voltmeters. Supports component compatibility checks and rerouting loops.
3. **Free Body Diagrams (`fbd`)**
   - **Compiler:** `approch2/fbd/fbd_layout.py` & `approch2/fbd/fbd_renderer.py`
   - **Concepts:** Force vectors acting on bodies. Generates a physical layout representing normal force, weight, tension, friction, and applied force vectors.
4. **Magnetic Fields (`magnetic`)**
   - **Compiler:** `approch2/magnetic_field/mf_layout.py` & `approch2/magnetic_field/mf_renderer.py`
   - **Concepts:** Field patterns around current-carrying wires, solenoids, and magnetic bar poles.
5. **Semiconductor Diagrams (`semiconductor`)**
   - **Compiler:** `approch2/semiconductor/semi_layout.py` & `approch2/semiconductor/semi_renderer.py`
   - **Concepts:** Biasing setups, PN junctions, depletion region indicators, forward/reverse circuit configurations.
6. **Graphs (`graph`)**
   - **Compiler:** `approch2/graph/graph_renderer.py`
   - **Concepts:** Physics quantity relationships (V-I curves, frequency plots, wave functions).
