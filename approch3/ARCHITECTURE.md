# VisualQ Diagram Engine — Architecture

Scientific SVG diagram engine for NCERT-level physics illustrations.
Designed for reuse across all diagram types produced by the VisualQ Pilot platform.

---

## Pipeline

```
YAML Template
     │
     ▼
TemplateLoader  ──────────────────  loads & caches .yaml from templates/
     │
     ▼
YAMLParser      ──────────────────  parses raw dict, resolves includes
     │
     ▼
LayoutResolver  ──────────────────  reads layout: block, computes geometry
     │  SemiconductorLayout          proportion-based region boxes
     │  CircuitLayout                arm positions, component x/y
     │  ConstraintSolver             resolves place_below / align_center_y …
     │  CollisionDetector            warns on overlapping regions
     │
     ▼
DiagramValidator  ────────────────  checks required fields, known types
     │
     ▼
SceneBuilder    ──────────────────  YAML objects → SceneNode instances
     │
     ▼
Scene Graph     ──────────────────  Scene → Layer[] → SceneNode[]
     │
     ▼
SVGRenderer     ──────────────────  iterates layers, calls node.render()
     │
     ▼
SVGCanvas       ──────────────────  wraps svgwrite.Drawing
     │
     ▼
SVG / PNG output
```

**Key invariant:** each stage receives a fully resolved input from the previous stage.
The renderer never computes positions; the LayoutResolver never draws.

---

## Package layout

```
visualq_diagram_engine/
├── core/
│   ├── scene.py            SceneNode ABC, Layer, Scene
│   ├── compiler.py         DiagramCompiler (orchestrator)
│   ├── renderer.py         SVGRenderer
│   ├── svg_canvas.py       thin svgwrite wrapper
│   ├── validator.py        DiagramValidator
│   └── export.py           Exporter (SVG + optional PNG)
│
├── compiler/
│   ├── template_loader.py  TemplateLoader
│   ├── yaml_parser.py      YAMLParser + helpers
│   ├── scene_builder.py    SceneBuilder — YAML dict → SceneNode
│   └── layout_resolver.py  LayoutResolver — injects positions before build
│
├── primitives/             Low-level SceneNode subclasses
│   ├── rectangle.py
│   ├── line.py
│   ├── text.py
│   ├── circle.py
│   ├── carrier_grid.py     grid of electron/hole circles
│   ├── ion_grid.py         grid of + / - ion symbols
│   ├── field_arrow.py      vector field arrow with auto-placed label
│   └── wire_path.py        ordered waypoint wire
│
├── circuit/                Circuit symbols (SceneNode subclasses)
│   ├── battery_symbol.py
│   ├── resistor_symbol.py
│   └── switch_symbol.py
│
├── layout/                 Constraint-based layout engine (Phase 5)
│   ├── bounding_box.py     BoundingBox — 9 named anchors, spatial helpers
│   ├── alignment.py        HAlign / VAlign enums + align helpers
│   ├── base_layout.py      LayoutNode ABC, LeafNode, Spacer
│   ├── hbox.py             HBox — horizontal container
│   ├── vbox.py             VBox — vertical container
│   ├── grid_layout.py      GridLayout — rows × cols
│   ├── anchor_layout.py    AnchorLayout — relative positioning
│   ├── padding.py          Padding / Margin wrappers
│   ├── spacing.py          distribute_h / distribute_v helpers
│   ├── constraint_solver.py ConstraintSolver — topological position resolution
│   └── layout_manager.py   LayoutManager — façade for constraints + containers
│
├── layouts/                Domain layout models (Phase 4, kept for compatibility)
│   ├── layout_engine.py    Box, hstack_fractional, vstack, union_boxes
│   ├── semiconductor_layout.py  SemiconductorLayout + CircuitLayout
│   ├── collision_detector.py    CollisionDetector
│   └── wire_router.py      Port + WireRouter
│
├── theme/                  Theme system (Phase 5)
│   ├── base_theme.py       BaseTheme — all styling constants
│   ├── ncert_theme.py      NCERTTheme — NCERT textbook style
│   └── default_theme.py    DefaultTheme — heavier strokes for screen
│
└── templates/
    └── pn_forward.yaml     Forward-biased PN junction spec
```

---

## Theme system

Themes are **class objects** (not instances) — constants are class-level attributes.
This lets modules read `NCERTTheme.hole_radius` without instantiation.

```python
from visualq_diagram_engine.theme.ncert_theme import NCERTTheme

# All styling via theme
stroke = NCERTTheme.stroke_default
font   = NCERTTheme.font_family
```

To switch themes globally:

```python
from visualq_diagram_engine.theme import set_theme
from visualq_diagram_engine.theme.default_theme import DefaultTheme
set_theme(DefaultTheme)
```

Or per-compiler:

```python
compiler = DiagramCompiler(config, theme=DefaultTheme)
```

---

## Constraint layout

The `ConstraintSolver` resolves 15 spatial constraints through dependency-ordered iteration:

| Category   | Constraints                                                        |
|------------|--------------------------------------------------------------------|
| Placement  | `place_below`, `place_above`, `place_right_of`, `place_left_of`    |
| Alignment  | `align_top`, `align_bottom`, `align_left`, `align_right`          |
|            | `align_center_x`, `align_center_y`                                |
| Centering  | `center_in`, `center_h`, `center_v`                               |
| Size       | `match_width`, `match_height`                                     |

Usage:

```python
from visualq_diagram_engine.layout import LayoutManager, BoundingBox

mgr = LayoutManager(theme=NCERTTheme)
mgr.register("semiconductor", BoundingBox(85, 75, 730, 165))
mgr.register_size("caption", width=400, height=12)
mgr.add_constraint("caption", "place_below", target="semiconductor", gap=200)
mgr.add_constraint("caption", "center_h",    target="semiconductor")
result = mgr.solve()   # {node_id: BoundingBox}
```

---

## Adding a new diagram type

1. Create `templates/<name>.yaml` — use `layout:` section for auto-positioning.
2. If new YAML object types are needed, add a `SceneNode` subclass in `primitives/`.
3. Register the new type in `SceneBuilder._build_node()` and `DiagramValidator.KNOWN_OBJECT_TYPES`.
4. If new circuit/semiconductor geometry is needed, extend `LayoutResolver._resolve_object()`.
5. Run `python main.py` with the new template name passed to `compiler.compile("<name>")`.

No changes to the renderer, canvas, or export pipeline are needed.

---

## Performance targets

| Stage          | Target  |
|----------------|---------|
| Scene build    | < 20 ms |
| Layout solve   | < 30 ms |
| SVG render     | < 50 ms |
| PNG export     | < 200 ms (requires cairosvg + Cairo) |

---

## Security

- `.env` at project root stores real API keys (Gemini, OpenRouter). **Never commit it.**
- `python-dotenv` loads it at runtime via `load_dotenv()` in `main.py`.
- No key material is read inside the diagram engine itself.
