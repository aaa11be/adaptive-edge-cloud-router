"""Client-side process and system metric collection."""

from __future__ import annotations

import os

import psutil

from edge_cloud_router.schemas import SystemSnapshot

_MEBIBYTE = 1024 * 1024


class SystemMetricsCollector:
    """Collect snapshots without mixing process and system-wide measurements."""

    def __init__(self, pid: int | None = None) -> None:
        self._process = psutil.Process(pid or os.getpid())
        self._warmed_up = False

    def warm_up(self) -> None:
        """Prime APIs whose first non-blocking value is otherwise meaningless."""

        self._process.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None)
        self._warmed_up = True

    def snapshot(self) -> SystemSnapshot:
        """Return a point-in-time client process/system snapshot."""

        if not self._warmed_up:
            self.warm_up()

        return SystemSnapshot(
            process_cpu_percent=max(0.0, self._process.cpu_percent(interval=None)),
            process_rss_mb=self._process.memory_info().rss / _MEBIBYTE,
            system_cpu_percent=max(0.0, psutil.cpu_percent(interval=None)),
            system_memory_percent=psutil.virtual_memory().percent,
        )
