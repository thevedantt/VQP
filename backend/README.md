# VisualQ Pilot - Backend

AI-powered CBSE Class 12 Physics (Part 1 - Electromagnetism) unit test
generator. Combines a curated PYQ question bank, the NCERT Physics Part-1
knowledge base, the Gemini API, and a rule-based diagram intelligence layer
through a `PaperGenerationOrchestrator`.

## Setup

```bash
cd backend
python -m venv myenv          # if not already created
myenv\Scripts\activate         # Windows
pip install -r requirements.txt

cp .env.example .env
# edit .env and set GEMINI_API_KEY=<your key>
```

`GEMINI_API_KEY` is optional for development: if unset, the AI question
generator runs in "stub mode" and returns clearly-labeled placeholder
questions so the rest of the pipeline (weightage, PYQ selection, diagram
detection/generation, paper assembly) remains fully testable offline.

## Run

```bash
uvicorn app.main:app --reload --app-dir backend
```

The API will be available at `http://127.0.0.1:8000`, with interactive docs
at `http://127.0.0.1:8000/docs`.

## Datasets used

| File | Purpose |
|---|---|
| `app/data/question_bank/labeled_questions.json` | 214 AI-labeled PYQ questions (chapter, concept, difficulty, marks, type, diagram label) - the PYQ pool. |
| `app/data/question_bank/diagram_dataset.json` | Diagram requirement/type labels for the 214 PYQ questions - used for diagram detection lookups. |
| `app/data/Book/chapters/*.json` | NCERT Physics Part-1 chapter text (8 chapters) - grounding for AI question generation. |
| `app/data/Book/chapter_index.json` | Chapter number / word-count index. |

The Gemini model defaults to `gemini-3.5-flash` (override via `GEMINI_MODEL` in `.env`).

Paper generation is scoped to the 8 NCERT Part-1 chapters (Electric Charges
and Fields ... Electromagnetic Waves), since these are the only chapters the
AI generator can be grounded in. Chapter weightage is computed dynamically
from the marks distribution of PYQ questions within that scope.

## API Endpoints

### `GET /api/health`

Returns service status, Gemini configuration state, and dataset sizes.

### `POST /api/generate-paper`

```json
{
  "difficulty": "medium",
  "pyq_percentage": 60,
  "ai_percentage": 40,
  "include_diagrams": true,
  "total_questions": 16,
  "chapters": null
}
```

Returns a `GeneratedPaperResponse`:

```json
{
  "paper_id": "...",
  "generated_at": "...",
  "difficulty": "medium",
  "total_questions": 16,
  "total_marks": 35,
  "pyq_percentage": 60,
  "ai_percentage": 40,
  "chapter_weightage": {"Current Electricity": 15, "...": "..."},
  "chapter_distribution": {"Current Electricity": 2, "...": "..."},
  "type_distribution": {"MCQ": 8, "...": "..."},
  "questions": [...],
  "generated_questions": [...],
  "diagrams": [...]
}
```

### `POST /api/detect-diagram`

```json
{"question": "Draw the magnetic field lines due to a current carrying solenoid."}
```

```json
{"requires_diagram": true, "diagram_type": "magnetic_field", "confidence": 0.85, "reason": "..."}
```

### `POST /api/generate-diagram`

```json
{"diagram_type": "circuit", "question": "In the given circuit, two resistors R1 and R2 are connected..."}
```

```json
{"diagram_type": "circuit", "diagram_specification": {"diagram_type": "circuit", "elements": [...], "...": "..."}}
```

## Architecture

```
app/
├── api/            FastAPI routers (health, paper, diagram) + DI providers
├── core/           settings, logging, exception handlers
├── models/         Pydantic request/response schemas + shared enums
├── services/
│   ├── question_service.py     PYQ question bank access/filtering
│   ├── book_service.py         NCERT chapter content & excerpts
│   ├── weightage_service.py     Chapter weightage engine
│   ├── gemini_service.py        Gemini-backed question generation
│   ├── diagram_service.py       Diagram detection
│   ├── diagram_generators.py    5 diagram spec generators
│   ├── paper_service.py         Balanced PYQ/AI question allocation
│   ├── orchestrator_service.py  Full pipeline coordinator
│   └── export_service.py        JSON/text paper export helpers
└── data/           JSON datasets (question bank + NCERT knowledge base)
```
