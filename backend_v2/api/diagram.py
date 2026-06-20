"""
Diagram generation API (Phase 4.4 — refactored to use DiagramEngine).

All pipeline steps go through DiagramEngine, never directly.
"""

import asyncio
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

API_DIR = Path(__file__).resolve().parent
BACKEND_V2 = API_DIR.parent
sys.path.insert(0, str(BACKEND_V2))

from diagram_engine import DiagramEngine
from diagram_revision import RevisionEngine, SuggestionEngine
from diagram_revision import revision_history
from diagram_generation.diagram_scanner import scan_paper, PAPERS_DIR
from pipeline.diagram_pipeline import resolve_compiled_svg


router = APIRouter()
engine = DiagramEngine()
revision_engine = RevisionEngine()
suggestion_engine = SuggestionEngine()

# Gemini's free tier caps gemini-3.5-flash at 5 requests/minute. Each
# diagram generation makes its own Gemini call (blueprint evaluator), so
# firing every diagram in a paper at once reliably 429s several of them
# once a paper has more than a handful of diagram questions. Capping
# concurrency keeps generation parallel (still much faster than fully
# sequential) without blowing through the per-minute quota.
_MAX_CONCURRENT_DIAGRAM_GENERATIONS = 4
_diagram_generation_semaphore = asyncio.Semaphore(_MAX_CONCURRENT_DIAGRAM_GENERATIONS)


async def _generate_diagram_throttled(question, question_id, paper_id):
    async with _diagram_generation_semaphore:
        return await asyncio.to_thread(
            engine.generate_diagram,
            question=question,
            question_id=question_id,
            paper_id=paper_id,
        )


class GenerateAllDiagramsRequest(BaseModel):
    paper_id: str


@router.post("/api/generate-all-diagrams")
async def generate_all_diagrams(req: GenerateAllDiagramsRequest):
    paper_path = PAPERS_DIR / f"{req.paper_id}.json"
    if not paper_path.exists():
        raise HTTPException(status_code=404, detail=f"Paper not found: {req.paper_id}")

    try:
        scan = scan_paper(req.paper_id)

        # Phase 4.8, Issue 5: generate diagram questions concurrently
        # instead of one-by-one, capped at _MAX_CONCURRENT_DIAGRAM_GENERATIONS
        # to stay under Gemini's free-tier per-minute rate limit.
        results = list(await asyncio.gather(*(
            _generate_diagram_throttled(
                question=entry["question"],
                question_id=entry["question_id"],
                paper_id=req.paper_id,
            )
            for entry in scan["diagram_questions"]
        )))

        generated = sum(1 for r in results if r["status"] == "SUCCESS")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        svg_files = [r["svg_path"] for r in results if r.get("svg_path")]

        return {
            "paper_id": req.paper_id,
            "generated": generated,
            "failed": failed,
            "svg_files": svg_files,
            "results": results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ReviseDiagramRequest(BaseModel):
    feedback: str = ""
    selected_suggestions: list[str] = []


@router.post("/api/diagrams/{paper_id}/{question_id}/revise")
def revise_diagram(paper_id: str, question_id: str, req: ReviseDiagramRequest):
    try:
        result = revision_engine.revise_diagram(
            paper_id=paper_id,
            question_id=question_id,
            feedback=req.feedback,
            selected_suggestions=req.selected_suggestions,
        )

        if not result["success"]:
            raise HTTPException(status_code=422, detail=result.get("error", "Revision failed"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/papers/{paper_id}/diagrams/{question_id}")
def get_diagram_svg(paper_id: str, question_id: str):
    svg_path = resolve_compiled_svg(paper_id, question_id)
    if not svg_path:
        raise HTTPException(status_code=404, detail="Diagram not found")

    return FileResponse(path=svg_path, media_type="image/svg+xml")


@router.get("/api/diagrams/{paper_id}/{question_id}/suggestions")
def get_diagram_suggestions(paper_id: str, question_id: str):
    try:
        result = suggestion_engine.generate_suggestions(paper_id, question_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "No diagram found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/diagrams/{paper_id}/{question_id}/versions")
def get_diagram_versions(paper_id: str, question_id: str):
    return {"versions": revision_history.list_versions(paper_id, question_id)}
