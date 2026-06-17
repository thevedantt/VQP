# Approach 2 — Physics Diagram SVG Compiler (Detailed Handover & Knowledge Base)

## Objective
The objective of **Approach 2** is to generate CBSE-compliant physics diagrams using a deterministic SVG compiler. By separating the mathematical physics calculations from the visual rendering step, this system guarantees precise alignments, correct scaling, accurate label placements, and standard coordinate systems without relying on probabilistic machine learning models.

---

## Final Architecture
The compilation of a diagram from a question follows a strict deterministic pipeline:

```
[ Question Text ]
       ↓
[ Classification ] (Identify Physics & Diagram Family)
       ↓
[ Template Retrieval ] (Load structural JSON template from library)
       ↓
[ Schema Generation ] (Compute physical constraints and quantities)
       ↓
[ Physics Blueprint ] (Create a declarative parameter blueprint)
       ↓
[ Physics Solver ] (Apply mathematical lens/circuit formulas to resolve dimensions)
       ↓
[ Ray Math & Rules ] (Compute light ray path intersections, reflections, refractions)
       ↓
[ SVG Renderer ] (Compile SVG markup using structural coordinates)
       ↓
[ SVG Output ] (Vector graphic returned to caller / embedded in paper)
```

---

## Directory & File Index (`c:\CODES\VQP\approch2`)

Below is the directory map of the compiler module, detailing each file's specific responsibility.

- [blueprint_builder.py](file:///c:/CODES/VQP/approch2/blueprint_builder.py) - Combines physics parameters and template schemas to build a structured visual blueprint containing coordinates, objects, and light source parameters.
- [classifier.py](file:///c:/CODES/VQP/approch2/classifier.py) - Classifies the raw physics question text into its respective diagram family (e.g., ray optics, electrical circuits) and concept.
- [main.py](file:///c:/CODES/VQP/approch2/main.py) - CLI driver script that reads test blueprints from `data/physics_blueprints.json`, invokes the SVG compiler, saves output files, and records results.
- [physics_solver.py](file:///c:/CODES/VQP/approch2/physics_solver.py) - High-level coordinator implementing optical equations (e.g., lens equation) to resolve object positions ($u$), focal lengths ($f$), image distances ($v$), magnification ($m$), orientation, and type.
- [ray_math.py](file:///c:/CODES/VQP/approch2/ray_math.py) - Contains calculations implementing Cartesian sign conventions to solve core equations ($1/f = 1/v - 1/u$, $m = v/u$, image height, focus coordinate offsets).
- [ray_rules.py](file:///c:/CODES/VQP/approch2/ray_rules.py) - Stores physical rules and focal bounds for Ray Optics scenarios (e.g., standard object distances relative to focal lengths for convex lenses).
- [renderer.py](file:///c:/CODES/VQP/approch2/renderer.py) - Primary dispatch router that parses the incoming blueprint’s `renderer_type` and routes it to the specific sub-renderer (e.g., RayRenderer).
- [retriever.py](file:///c:/CODES/VQP/approch2/retriever.py) - Queries the diagram library (`diagram_library.json`) to fetch suitable JSON configurations matching the classified taxonomy.
- [schema_adapter.py](file:///c:/CODES/VQP/approch2/schema_adapter.py) - Modifies and overrides parameters of generic blueprint templates using question-specific numerical values.

### Subdirectories

#### 1. Data Store (`approch2/data/`)
- [classified_questions.json](file:///c:/CODES/VQP/approch2/data/classified_questions.json) - Contains test outputs from the question classifier showing taxonomy mappings.
- [compiled_diagrams.json](file:///c:/CODES/VQP/approch2/data/compiled_diagrams.json) - Stores log state of the compiled diagram outputs.
- [diagram_library.json](file:///c:/CODES/VQP/approch2/data/diagram_library.json) - Database of structural diagrams mapped by family, concept, and required tags.
- [generated_schemas.json](file:///c:/CODES/VQP/approch2/data/generated_schemas.json) - Contains blueprint templates mapped by query index.
- [physics_blueprints.json](file:///c:/CODES/VQP/approch2/data/physics_blueprints.json) - A collection of 8+ full test blueprints (convex lens cases) used to validate the renderer.
- [questions.json](file:///c:/CODES/VQP/approch2/data/questions.json) - List of raw input questions.
- [rendered_diagrams.json](file:///c:/CODES/VQP/approch2/data/rendered_diagrams.json) - Final index mapping question IDs to generated SVG file paths and renderer status.
- [retrieved_templates.json](file:///c:/CODES/VQP/approch2/data/retrieved_templates.json) - Logs intermediate template retrieval outputs.

#### 2. Renderers Core (`approch2/renderers/`)
- [ray_renderer.py](file:///c:/CODES/VQP/approch2/renderers/ray_renderer.py) - Deterministically renders high-quality ray diagrams. It plots the principal axis, convex lens paths, focal marker tick labels ($F_1$, $F_2$, $2F_1$, $2F_2$), object arrows, real/virtual images, and individual light ray lines (including dashed virtual back-projections for case 4).

#### 3. Compilation Outputs (`approch2/output/`)
- Directory where compiled `.svg` files are saved when running `main.py`.

---

## Convex Lens Cases Implemented

The Ray Optics module supports the four primary standard convex lens cases taught in the CBSE Class 12 curriculum:

| Case | Object Location | Expected Image Location | Image Type | Orientation | Relative Size |
|---|---|---|---|---|---|
| **1** | Beyond $2F$ | Between $F$ and $2F$ | Real | Inverted | Diminished |
| **2** | At $2F$ | At $2F$ | Real | Inverted | Same Size |
| **3** | Between $F$ and $2F$ | Beyond $2F$ | Real | Inverted | Magnified |
| **4** | Between Lens and $F$ | Same side as Object | Virtual | Erect | Magnified |

---

## Core Development Principles
> [!IMPORTANT]
> **Separation of Physics and Rendering**
> The SVG renderer must never guess coordinates or compute physical relationships. 
> - **Physics Solver (`physics_solver.py` / `ray_math.py`)** determines all physical attributes (magnification, image distance, height, real vs. virtual).
> - **Renderer (`ray_renderer.py`)** remains a stateless drawing routine that reads the coordinate positions from the blueprint parameters and draws vectors, labels, lines, and markers.

---

## Next Steps for Expansion
Following the completion of the Ray Module, future diagram categories (circuits, graphs, magnetic fields, free body diagrams) must follow this exact architecture:

1. **Circuits (`circuits/`)**
   - `circuit_solver.py` - Calculates currents, node voltages, resistor coordinates using Kirchoff's/Ohm's laws.
   - `circuit_validation.py` - Assures loop integrity and correct parallel/series component connections.
   - `renderers/circuit_renderer.py` - Calls Schemdraw/SVG components to compile circuit elements.
2. **Graphs / Electromagnetism / Free-Body Diagrams**
   - Implemented using dedicated solvers (e.g. `magnetic_field_engine.py`) and standard vector output compilers.
