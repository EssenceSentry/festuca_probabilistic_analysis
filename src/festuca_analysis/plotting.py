"""Shared Seaborn styling for Festuca report figures."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

# Seaborn does not currently ship complete type information.
# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
from pathlib import Path
from typing import Any, Final, Literal, cast

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
CATEGORICAL_ERRORBAR_CAPSIZE: Final = 0.30
HORIZONTAL_CAP_HALF_HEIGHT: Final = 0.065
HORIZONTAL_INTERVAL_ALPHA: Final = 0.62
HORIZONTAL_MARKER_AREA: Final = 54.0
FIGURE_LEFT: Final = 0.07
FIGURE_TITLE_Y: Final = 0.985
FIGURE_NOTE_Y: Final = 0.018
HEADER_GAP_POINTS: Final = 8.0
FigureProfile = Literal["standalone", "thesis"]

_LATEX_TEXT_REPLACEMENTS: Final = {
    "⁻¹": r"\ensuremath{^{-1}}",
    "⁻²": r"\ensuremath{^{-2}}",
    "±": r"\ensuremath{\pm}",
    "≈": r"\ensuremath{\approx}",
    "×": r"\ensuremath{\times}",
    "·": r"\ensuremath{\cdot}",
    "≤": r"\ensuremath{\leq}",
    "≥": r"\ensuremath{\geq}",
    "²": r"\ensuremath{^{2}}",
    "–": "--",
    "—": "---",
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_LATEX_TEXT_PATTERN: Final = re.compile(
    "|".join(
        re.escape(token)
        for token in sorted(_LATEX_TEXT_REPLACEMENTS, key=len, reverse=True)
    )
)


def _to_latex(text: str) -> str:
    return _LATEX_TEXT_PATTERN.sub(
        lambda match: _LATEX_TEXT_REPLACEMENTS[match.group(0)],
        text,
    )


_MATHTEXT_REPLACEMENTS: Final = {
    "⁻¹": r"$^{-1}$",
    "⁻²": r"$^{-2}$",
    "±": r"$\pm$",
    "≈": r"$\approx$",
    "×": r"$\times$",
    "·": r"$\cdot$",
    "≤": r"$\leq$",
    "≥": r"$\geq$",
    "²": r"$^{2}$",
}
_MATHTEXT_PATTERN: Final = re.compile(
    "|".join(
        re.escape(token)
        for token in sorted(_MATHTEXT_REPLACEMENTS, key=len, reverse=True)
    )
)


def _to_mathtext(text: str) -> str:
    return _MATHTEXT_PATTERN.sub(
        lambda match: _MATHTEXT_REPLACEMENTS[match.group(0)],
        text,
    )


def _caption_fragment(text: str) -> str:
    normalized = " ".join(text.split())
    if normalized.endswith((".", "!", "?", ":", ";")):
        return normalized
    return f"{normalized}."


@dataclass
class _PendingFigureMetadata:
    title: str | None = None
    subtitle: str | None = None
    note: str | None = None
    annotations: list[str] = field(default_factory=list)
    latex_title: str | None = None
    latex_subtitle: str | None = None
    latex_note: str | None = None
    latex_annotations: list[str | None] = field(default_factory=list)


class FigureExporter:
    """Render standalone figures or clean thesis PDFs with JSON sidecars."""

    def __init__(
        self,
        output_directory: Path,
        *,
        profile: FigureProfile = "standalone",
        dpi: int = 300,
        print_json: bool = False,
    ) -> None:
        self.output_root = output_directory
        self.profile = profile
        self.dpi = dpi
        self.print_json = print_json
        self._metadata: dict[int, _PendingFigureMetadata] = {}

    @property
    def output_directory(self) -> Path:
        if self.profile == "thesis":
            return self.output_root / "thesis"
        return self.output_root

    def _pending(self, fig: Any) -> _PendingFigureMetadata:
        return self._metadata.setdefault(id(fig), _PendingFigureMetadata())

    def add_header(
        self,
        fig: Any,
        title: str,
        *,
        subtitle: str | None = None,
        latex_title: str | None = None,
        latex_subtitle: str | None = None,
        left: float = FIGURE_LEFT,
        title_y: float = FIGURE_TITLE_Y,
        subtitle_y: float | None = None,
    ) -> None:
        pending = self._pending(fig)
        pending.title = title
        pending.subtitle = subtitle
        pending.latex_title = latex_title
        pending.latex_subtitle = latex_subtitle
        if self.profile == "standalone":
            add_figure_header(
                fig,
                _to_mathtext(title),
                subtitle=_to_mathtext(subtitle) if subtitle is not None else None,
                left=left,
                title_y=title_y,
                subtitle_y=subtitle_y,
            )

    def add_note(
        self,
        fig: Any,
        text: str,
        *,
        latex_text: str | None = None,
        left: float = FIGURE_LEFT,
        y: float = FIGURE_NOTE_Y,
    ) -> None:
        pending = self._pending(fig)
        pending.note = text
        pending.latex_note = latex_text
        if self.profile == "standalone":
            add_figure_note(fig, _to_mathtext(text), left=left, y=y)

    def add_annotation(
        self,
        fig: Any,
        text: str,
        *,
        latex_text: str | None = None,
        x: float,
        y: float,
        ha: str = "left",
        va: str = "top",
        fontsize: float = 9.25,
        color: str | None = None,
        linespacing: float = 1.35,
    ) -> None:
        pending = self._pending(fig)
        pending.annotations.append(text)
        pending.latex_annotations.append(latex_text)
        if self.profile == "standalone":
            fig.text(
                x,
                y,
                _to_mathtext(text),
                ha=ha,
                va=va,
                fontsize=fontsize,
                color=color,
                linespacing=linespacing,
            )

    def _payload(
        self,
        *,
        filename_stem: str,
        pending: _PendingFigureMetadata,
    ) -> dict[str, object]:
        if pending.title is None:
            raise ValueError(
                f"La figura {filename_stem!r} no tiene un título registrado."
            )
        title = pending.latex_title or _to_latex(pending.title)
        subtitle = (
            pending.latex_subtitle
            if pending.latex_subtitle is not None
            else _to_latex(pending.subtitle) if pending.subtitle is not None else None
        )
        note = (
            pending.latex_note
            if pending.latex_note is not None
            else _to_latex(pending.note) if pending.note is not None else None
        )
        annotations = [
            latex_annotation or _to_latex(annotation)
            for annotation, latex_annotation in zip(
                pending.annotations,
                pending.latex_annotations,
                strict=True,
            )
        ]
        caption_parts = [title]
        if subtitle is not None:
            caption_parts.append(subtitle)
        caption_parts.extend(annotations)
        if note is not None:
            caption_parts.append(note)
        return {
            "schema_version": 1,
            "id": filename_stem,
            "profile": self.profile,
            "text_format": "latex",
            "pdf_file": f"{filename_stem}.pdf",
            "title": title,
            "subtitle": subtitle,
            "caption": " ".join(_caption_fragment(part) for part in caption_parts),
            "note": note,
            "annotations": annotations,
            "latex": {
                "label": f"fig:{filename_stem.replace('_', '-')}",
                "width": "\\textwidth",
            },
        }

    def _decorate_for_display(
        self,
        fig: Any,
        pending: _PendingFigureMetadata,
    ) -> None:
        """Add standalone context after a clean thesis export is complete."""
        if self.profile != "thesis" or pending.title is None:
            return
        add_figure_header(
            fig,
            _to_mathtext(pending.title),
            subtitle=(
                _to_mathtext(pending.subtitle) if pending.subtitle is not None else None
            ),
        )
        if pending.note is not None:
            add_figure_note(fig, _to_mathtext(pending.note))

    def save(self, fig: Any, filename_stem: str) -> dict[str, object]:
        """Save a clean thesis PDF and a fully decorated display image."""
        pending = self._metadata.pop(id(fig), _PendingFigureMetadata())
        payload = self._payload(filename_stem=filename_stem, pending=pending)
        output_directory = self.output_directory
        output_directory.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            output_directory / f"{filename_stem}.pdf",
            bbox_inches="tight",
        )
        if self.profile == "standalone":
            fig.savefig(
                output_directory / f"{filename_stem}.png",
                dpi=self.dpi,
                bbox_inches="tight",
            )
        if self.profile != "standalone":
            serialized = json.dumps(payload, ensure_ascii=False, indent=2)
            (output_directory / f"{filename_stem}.json").write_text(
                f"{serialized}\n",
                encoding="utf-8",
            )
            if self.print_json:
                print(serialized)
            self._decorate_for_display(fig, pending)
            fig.savefig(
                output_directory / f"{filename_stem}_full.png",
                dpi=self.dpi,
                bbox_inches="tight",
            )
        return payload

    def discard(self, fig: Any) -> None:
        """Decorate a displayed figure even when file export is disabled."""
        pending = self._metadata.pop(id(fig), _PendingFigureMetadata())
        self._decorate_for_display(fig, pending)


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
            title_size_points = font_manager.FontProperties(
                size=mpl.rcParams["figure.titlesize"]
            ).get_size_in_points()
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
