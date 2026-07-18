"""Append-only JSON Lines result logging."""

from __future__ import annotations

from pathlib import Path

from edge_cloud_router.schemas import BenchmarkRecord


class JsonlRequestLogger:
    """Write one validated benchmark record per line."""

    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path)

    def append(self, record: BenchmarkRecord) -> None:
        """Append a record and create the parent directory when necessary."""

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = record.model_dump_json(exclude_none=False)
        with self.output_path.open("a", encoding="utf-8", newline="\n") as file:
            file.write(payload)
            file.write("\n")
