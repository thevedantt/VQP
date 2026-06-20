"""
Timing and logging for a single diagram generation run (Phase 4.4).

Usage as a context manager:

    with GenerationManager("Q07", "circuit") as gm:
        ...
    print(gm.summary())
"""

import time
from datetime import datetime


class GenerationManager:

    def __init__(self, question_id=None, family=None):
        self.question_id = question_id
        self.family = family
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.status = None

    def __enter__(self):
        self.start_time = time.time()
        self._start_dt = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = round(self.end_time - self.start_time, 1)
        if exc_type is not None:
            self.status = "FAILED"
        else:
            self.status = "SUCCESS"

    def timing(self):
        return {
            "start_time": self._start_dt.isoformat(),
            "duration_seconds": self.duration,
        }

    def summary(self):
        lines = [
            "[DIAGRAM ENGINE]",
            f"  Question ID:    {self.question_id or '?'}",
            f"  Family:         {self.family or '?'}",
            f"  Status:         {self.status or '?'}",
        ]
        if self.duration is not None:
            lines.append(f"  Generation Time: {self.duration} sec")
        return "\n".join(lines)

    def print_report(self, svg_path=None):
        print()
        print("=" * 60)
        print(self.summary())
        if svg_path:
            print(f"  SVG:            {Path(svg_path).name}")
        print("=" * 60)

from pathlib import Path
