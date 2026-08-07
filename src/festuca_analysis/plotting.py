"""Shared Seaborn styling for Festuca report figures."""

from __future__ import annotations

# Seaborn does not currently ship complete type information.
# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
from pathlib import Path
from typing import Any, Final, cast

import matplotlib as mpl
import seaborn as sns
from matplotlib import font_manager

PALETTE_SIZE: Final = 9
FONT_DIRECTORY: Final = Path(__file__).with_name("fonts")
PLOT_FONT_FAMILY: Final = "Libertinus Serif"
DATA_LINEWIDTH: Final = 1.8
EMPHASIS_LINEWIDTH: Final = 2.4
INTERVAL_LINEWIDTH: Final = 1.4
SECONDARY_LINEWIDTH: Final = 1.2
REFERENCE_LINEWIDTH: Final = 1.0
GRID_LINEWIDTH: Final = 0.7
MARKER_SIZE: Final = 6.0
ERRORBAR_CAPSIZE: Final = 4.0
HORIZONTAL_CAP_HALF_HEIGHT: Final = 0.065
HORIZONTAL_INTERVAL_ALPHA: Final = 0.62
HORIZONTAL_MARKER_AREA: Final = 54.0
FIGURE_LEFT: Final = 0.07
FIGURE_TITLE_Y: Final = 0.985
FIGURE_NOTE_Y: Final = 0.018
HEADER_GAP_POINTS: Final = 8.0


def _register_bundled_fonts() -> None:
    """Register the project fonts without requiring a system installation."""
    for font_path in sorted(FONT_DIRECTORY.glob("*.otf")):
        font_manager.fontManager.addfont(str(font_path))


def apply_plot_theme() -> list[str]:
    """Apply the repository-wide paper theme and return its categorical palette."""
    _register_bundled_fonts()
    sns_api = cast(Any, sns)
    palette = cast(
        list[str],
        sns_api.color_palette("inferno", n_colors=PALETTE_SIZE).as_hex(),
    )
    sns_api.set_theme(
        context="paper",
        style="whitegrid",
        palette=palette,
        font=PLOT_FONT_FAMILY,
        font_scale=1.0,
        rc={
            "axes.axisbelow": True,
            "axes.formatter.use_mathtext": True,
            "axes.formatter.useoffset": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.labelpad": 6,
            "axes.labelsize": 10.5,
            "axes.linewidth": 0.8,
            "axes.spines.left": False,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.titlelocation": "left",
            "axes.titlepad": 9,
            "axes.titlesize": 12.5,
            "axes.titleweight": "bold",
            "errorbar.capsize": ERRORBAR_CAPSIZE,
            "figure.dpi": 120,
            "figure.facecolor": "white",
            "figure.titlesize": 16,
            "figure.titleweight": "bold",
            "font.size": 10.5,
            "mathtext.fontset": "stix",
            "legend.fontsize": 9.5,
            "legend.frameon": False,
            "legend.title_fontsize": 9.5,
            "grid.linewidth": GRID_LINEWIDTH,
            "lines.linewidth": DATA_LINEWIDTH,
            "lines.markersize": MARKER_SIZE,
            "savefig.bbox": "tight",
            "savefig.dpi": 300,
            "savefig.facecolor": "white",
            "savefig.pad_inches": 0.06,
            "savefig.transparent": False,
            "xtick.labelsize": 9,
            "xtick.major.pad": 5,
            "ytick.labelsize": 9,
            "ytick.major.pad": 4,
        },
    )
    return palette


def add_figure_header(
    fig: Any,
    title: str,
    *,
    subtitle: str | None = None,
    left: float = FIGURE_LEFT,
    title_y: float = FIGURE_TITLE_Y,
    subtitle_y: float | None = None,
) -> None:
    """Add a consistent, left-aligned title and optional subtitle."""
    fig.suptitle(title, x=left, y=title_y, ha="left", va="top")
    if subtitle is not None:
        if subtitle_y is None:
            title_size_points = float(mpl.rcParams["figure.titlesize"])
            figure_height_points = float(fig.get_figheight()) * 72.0
            subtitle_y = (
                title_y - (title_size_points + HEADER_GAP_POINTS) / figure_height_points
            )
        fig.text(
            left,
            subtitle_y,
            subtitle,
            ha="left",
            va="top",
            fontsize=10.5,
            color=mpl.rcParams["axes.labelcolor"],
            linespacing=1.25,
        )


def add_figure_note(
    fig: Any,
    text: str,
    *,
    left: float = FIGURE_LEFT,
    y: float = FIGURE_NOTE_Y,
) -> None:
    """Place a readable source or interpretation note below the axes."""
    fig.text(
        left,
        y,
        text,
        ha="left",
        va="bottom",
        fontsize=8.75,
        color=mpl.rcParams["axes.labelcolor"],
        linespacing=1.25,
    )


def plot_horizontal_interval(
    ax: Any,
    *,
    estimate: float,
    lower: float,
    upper: float,
    y: float,
    color: str,
    label: str | None = None,
    zorder: int = 3,
) -> Any:
    """Draw a restrained forest-plot interval with explicit end caps."""
    ax.hlines(
        y,
        lower,
        upper,
        color=color,
        linewidth=INTERVAL_LINEWIDTH,
        alpha=HORIZONTAL_INTERVAL_ALPHA,
        zorder=zorder,
    )
    ax.vlines(
        [lower, upper],
        y - HORIZONTAL_CAP_HALF_HEIGHT,
        y + HORIZONTAL_CAP_HALF_HEIGHT,
        color=color,
        linewidth=INTERVAL_LINEWIDTH,
        alpha=0.82,
        zorder=zorder,
    )
    return ax.scatter(
        [estimate],
        [y],
        color=color,
        edgecolor="white",
        linewidth=0.8,
        s=HORIZONTAL_MARKER_AREA,
        label=label,
        zorder=zorder + 1,
    )
