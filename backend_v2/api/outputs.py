"""
Outputs discovery API — scans backend directories for generated artifacts.
"""

import os
import time
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

API_DIR = Path(__file__).resolve().parent
BACKEND_V2 = API_DIR.parent
REPO_ROOT = BACKEND_V2.parent
BACKEND_DIR = REPO_ROOT / "archive" / "backend"
APPROCH2_DIR = REPO_ROOT / "approch2"

router = APIRouter()

_cache = {"timestamp": 0, "data": None, "ttl": 30}

# Subtrees with one folder per paper/question (e.g.
# outputv2/diagram_runs/PAPER001/Q07/) would otherwise produce one
# "directory" filter button per question - collapse anything under
# these prefixes to the prefix itself.
_COLLAPSE_DIRECTORY_PREFIXES = (
    "backend_v2/outputv2/diagram_runs",
)


def _directory_label(fpath: Path) -> str:
    """Relative directory path (from repo root) used as the gallery's
    per-directory filter button label."""
    try:
        rel = fpath.parent.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(fpath.parent)

    for prefix in _COLLAPSE_DIRECTORY_PREFIXES:
        if rel == prefix or rel.startswith(prefix + "/"):
            return prefix
    return rel


class OutputFile(BaseModel):
    name: str
    path: str
    type: str
    size: str
    created_at: str
    source: str
    directory: str


class OutputCategory(BaseModel):
    name: str
    count: int
    files: list[OutputFile]


class OutputsResponse(BaseModel):
    categories: list[OutputCategory]
    total_files: int


def _human_size(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    elif bytes_ < 1024 ** 2:
        return f"{bytes_ / 1024:.1f} KB"
    return f"{bytes_ / 1024 ** 2:.1f} MB"


def _scan_dir(root: Path, source: str) -> list[OutputFile]:
    files = []
    image_exts = {".svg", ".png", ".jpg", ".jpeg", ".webp"}
    doc_exts = {".pdf", ".json"}
    exts = image_exts | doc_exts

    if not root.exists():
        return files

    for fpath in root.rglob("*"):
        if not fpath.is_file():
            continue
        if fpath.suffix.lower() not in exts:
            continue
        try:
            stat = fpath.stat()
            files.append(OutputFile(
                name=fpath.name,
                path=str(fpath.resolve()),
                type=fpath.suffix[1:].lower(),
                size=_human_size(stat.st_size),
                created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                source=source,
                directory=_directory_label(fpath),
            ))
        except OSError:
            continue
    return files


def _categorise(files: list[OutputFile]) -> list[OutputCategory]:
    categories = {
        "Question Papers": [],
        "Ray Diagrams": [],
        "Circuit Diagrams": [],
        "FBD Diagrams": [],
        "Magnetic Diagrams": [],
        "Semiconductor Diagrams": [],
        "Graph Diagrams": [],
        "PDF Exports": [],
        "Validation Reports": [],
        "Test Outputs": [],
        "Other Assets": [],
    }

    for f in files:
        name_lower = f.name.lower()
        path_lower = f.path.lower()

        if f.type == "pdf":
            categories["PDF Exports"].append(f)
        elif f.type == "json":
            if "evaluation" in name_lower or "report" in name_lower:
                categories["Validation Reports"].append(f)
            elif "paper" in name_lower or name_lower.startswith("paper") or name_lower.startswith("verify"):
                categories["Question Papers"].append(f)
            else:
                categories["Other Assets"].append(f)
        elif f.type == "svg":
            if "ray" in path_lower or "ray" in name_lower:
                categories["Ray Diagrams"].append(f)
            elif "circuit" in path_lower or name_lower.startswith("c") and name_lower[1:2].isdigit():
                categories["Circuit Diagrams"].append(f)
            elif "fbd" in path_lower or name_lower.startswith("f") and name_lower[1:2].isdigit():
                categories["FBD Diagrams"].append(f)
            elif "magnetic" in path_lower:
                categories["Magnetic Diagrams"].append(f)
            elif "semiconductor" in path_lower or name_lower.startswith("s") and name_lower[1:2].isdigit():
                categories["Semiconductor Diagrams"].append(f)
            elif "graph" in path_lower or name_lower.startswith("g") and name_lower[1:2].isdigit():
                categories["Graph Diagrams"].append(f)
            elif "test" in path_lower:
                categories["Test Outputs"].append(f)
            else:
                categories["Other Assets"].append(f)
        elif f.type in ("png", "jpg", "jpeg", "webp"):
            categories["Other Assets"].append(f)
        else:
            categories["Other Assets"].append(f)

    result = []
    for name, flist in categories.items():
        if flist:
            result.append(OutputCategory(name=name, count=len(flist), files=flist))
    return result


@router.get("/api/outputs", response_model=OutputsResponse)
def list_outputs(refresh: bool = Query(False)):
    now = time.time()
    if not refresh and _cache["data"] and (now - _cache["timestamp"]) < _cache["ttl"]:
        return _cache["data"]

    all_files = []

    all_files.extend(_scan_dir(BACKEND_V2 / "outputv2", "backend_v2"))
    all_files.extend(_scan_dir(BACKEND_V2 / "compiled_output", "backend_v2"))
    all_files.extend(_scan_dir(BACKEND_V2 / "test_output", "backend_v2"))
    all_files.extend(_scan_dir(BACKEND_V2 / "generated_diagrams", "backend_v2"))

    for family in ("circuit", "fbd", "graph", "magnetic_field", "ray", "semiconductor", "extras"):
        # Scan the whole family folder, not just family/output - families
        # like circuit also keep generated assets under assets/, opcompos1/,
        # output1/, output2/, etc.
        family_dir = APPROCH2_DIR / family
        if family_dir.exists():
            all_files.extend(_scan_dir(family_dir, "approch2"))

    categories = _categorise(all_files)
    total = len(all_files)

    response = OutputsResponse(categories=categories, total_files=total)
    _cache["data"] = response
    _cache["timestamp"] = now
    return response


@router.get("/api/outputs/file")
def serve_output_file(path: str = Query(...)):
    from fastapi.responses import FileResponse
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    media_map = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
        ".json": "application/json",
    }
    media = media_map.get(p.suffix.lower(), "application/octet-stream")
    return FileResponse(path=str(p), media_type=media)
