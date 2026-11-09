"""Task success tracker persisted as JSON."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class TaskRecord:
    """One finished task."""

    task: str
    success: bool
    takeover: bool = False
    steps: int = 0
    timestamp: float = field(default_factory=time.time)


class SuccessTracker:
    """Record outcomes and compute success / takeover rates."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.records: list[TaskRecord] = []

    def record(self, rec: TaskRecord) -> None:
        """Add a record and persist if a path is configured."""
        self.records.append(rec)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps([asdict(r) for r in self.records], indent=2), encoding="utf-8"
            )

    @property
    def success_rate(self) -> float:
        """Fraction of tasks that succeeded (0.0 when none)."""
        if not self.records:
            return 0.0
        return sum(int(r.success) for r in self.records) / len(self.records)

    @property
    def takeover_rate(self) -> float:
        """Fraction of tasks that needed a human (0.0 when none)."""
        if not self.records:
            return 0.0
        return sum(int(r.takeover) for r in self.records) / len(self.records)
