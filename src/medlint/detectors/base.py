"""The intentionally small internal detector contract."""

from __future__ import annotations

from typing import Protocol

from medlint.catalog import DatasetCatalog
from medlint.evidence import DetectorResult


class Detector(Protocol):
    @property
    def detector_id(self) -> str:
        """Stable identifier used in configuration and coverage."""

        ...

    def run(self, catalog: DatasetCatalog) -> DetectorResult:
        """Evaluate a catalog without changing it or its source files."""
