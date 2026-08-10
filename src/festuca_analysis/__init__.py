"""Reproducible analyses for the Festuca nitrogen-timing experiment.

The canonical CSV loader remains importable without importing the Bayesian stack. The
notebook controllers are resolved lazily so the classical workflow does not
depend on PyMC at import time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from festuca_analysis.source_data import (
    ExperimentData,
    ExperimentSpec,
    load_experiment_data,
    source_provenance_table,
)

if TYPE_CHECKING:
    from festuca_analysis.annex import ProbabilisticAnnex
    from festuca_analysis.longitudinal import LongitudinalNotebook

__all__ = [
    "ExperimentData",
    "ExperimentSpec",
    "LongitudinalNotebook",
    "ProbabilisticAnnex",
    "load_experiment_data",
    "source_provenance_table",
]


def __getattr__(name: str) -> Any:
    if name == "LongitudinalNotebook":
        from festuca_analysis.longitudinal import LongitudinalNotebook

        return LongitudinalNotebook
    if name == "ProbabilisticAnnex":
        from festuca_analysis.annex import ProbabilisticAnnex

        return ProbabilisticAnnex
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
