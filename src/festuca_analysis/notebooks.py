"""Small presentation helpers used by the report notebooks."""

from pathlib import Path
from typing import Any, cast

import pandas as pd
from IPython.display import (
    SVG,
    Markdown,
    display,  # pyright: ignore[reportUnknownVariableType]
)

display_output = cast(Any, display)


def reproduce_annex() -> None:
    """Recalculate the annex tables and figures used by the report notebook."""
    from festuca_analysis.annex import run_all

    run_all()


def project_root(start: Path | None = None) -> Path:
    """Locate the repository root from a notebook or an installed module."""
    candidates = [
        (start or Path.cwd()).resolve(),
        Path(__file__).resolve().parents[2],
        Path("/mnt/data/festuca_anexo_probabilistico_tesis_v2"),
    ]
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() or (
            candidate / "sources" / "Datos_Ema_Serrana_INN.xlsx"
        ).is_file():
            return candidate
    attempted = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        f"No se encontró la raíz del proyecto. Se probó: {attempted}"
    )


def show_annex_figure(filename: str, *, root: Path | None = None) -> SVG:
    """Render one generated annex SVG in a notebook."""
    path = project_root(root) / "results" / "figures" / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"No se encontró {path}. Ejecute primero `uv run festuca-annex`."
        )
    return SVG(filename=str(path))


def show_annex_table(filename: str, *, root: Path | None = None) -> pd.DataFrame:
    """Load one generated annex table for display in a report notebook."""
    path = project_root(root) / "results" / "tables" / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"No se encontró {path}. Ejecute primero `uv run festuca-annex`."
        )
    return pd.read_csv(path)


def show_annex_methodology_tables(*, root: Path | None = None) -> None:
    """Display the prior specification and prior-predictive audit."""
    display_output(
        Markdown("**Especificación numérica de las distribuciones a priori**")
    )
    display_output(show_annex_table("prior_specification.csv", root=root))
    display_output(
        Markdown("**Chequeo predictivo a priori por sector y regularización**")
    )
    display_output(show_annex_table("prior_predictive_summary.csv", root=root))
