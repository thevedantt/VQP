"""
Paper Generation API (Phase 3A).

Diagram rendering is explicitly out of scope - the only diagram-related
field in the response is the detected `diagram_required` flag per
question. No classifier/schema_router/blueprint_generator/
blueprint_evaluator/compiler_router import happens anywhere in this
phase's code path.

Run:
    uvicorn pipeline.paper_api:app --reload --port 8000
"""

import itertools
import json
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

PIPELINE_DIR = Path(__file__).resolve().parent
BACKEND_V2 = PIPELINE_DIR.parent
sys.path.insert(0, str(BACKEND_V2))

from pipeline.paper_builder import build_paper
from pipeline.paper_templates import list_templates
from pipeline.pdf_export import export_paper_to_pdf
from api.diagram import router as diagram_router

app = FastAPI(title="VisualQ Paper Generation Engine", version="3a")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagram_router)

PAPERS_DIR = BACKEND_V2 / "outputv2" / "papers"

_paper_id_counter = itertools.count(1)


class GeneratePaperRequest(BaseModel):
    paper_type: str
    pyq_ratio: float = 60
    ai_ratio: float = 40
    chapter_filters: Optional[List[str]] = None
    difficulty: Optional[str] = None
    paper_id: Optional[str] = None


@app.get("/api/templates")
def get_templates():
    return {"templates": list_templates()}


@app.post("/api/generate-paper")
def generate_paper(req: GeneratePaperRequest):
    if req.paper_type not in list_templates():
        raise HTTPException(
            status_code=400,
            detail=f"Unknown paper_type '{req.paper_type}'. Available: {list_templates()}",
        )

    paper_id = req.paper_id or f"PAPER{next(_paper_id_counter):03d}"

    try:
        paper_output, _ = build_paper(
            paper_id=paper_id,
            template_name=req.paper_type,
            pyq_ratio=req.pyq_ratio,
            ai_ratio=req.ai_ratio,
            chapter_filters=req.chapter_filters,
            difficulty=req.difficulty,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return paper_output


@app.get("/api/papers")
def list_papers():
    papers = []
    for f in sorted(PAPERS_DIR.glob("*.json")):
        papers.append({"id": f.stem, "path": str(f.relative_to(BACKEND_V2))})
    return papers


@app.get("/api/papers/{paper_id}/export")
def export_paper(paper_id: str):
    paper_path = PAPERS_DIR / f"{paper_id}.json"
    if not paper_path.exists():
        raise HTTPException(status_code=404, detail="Paper not found")
    try:
        pdf_path = export_paper_to_pdf(str(paper_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    return FileResponse(
        path=pdf_path,
        filename=f"{paper_id}.pdf",
        media_type="application/pdf",
    )
