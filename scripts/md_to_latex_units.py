#!/usr/bin/env python3
"""Convert Markdown to LaTeX with optional LaTeX-friendly unit normalization.

Usage:
  python scripts/md_to_latex_units.py tesis.md -o tesis.tex

The script:
- preserves code blocks and math ($...$, $$...$$),
- converts plain text measurements like "12 kg ha^-1" into "\\SI{12}{kg\\,ha^{-1}}" when siunitx is enabled,
- can replace figure markdown links by a LaTeX \figure block using sidecar artifacts:
- <name>.png           (figure with captions/titles for review in markdown)
- <name>_plot.pdf      (publication-ready plot only)
- <name>_meta.json     (metadata: title/caption/label/placement/width)
  where <name> is the same stem as the source PNG or stem without a configured full suffix.

Requires: pandoc in PATH.
Optional: one of pdflatex/xelatex/lualatex in PATH if --compile is enabled.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, cast

NUM_RE = r"[+-]?(?:\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,]\d+)?(?:[eE][+-]?\d+)?"

KNOWN_UNITS = [
    r"°C",
    r"ppm",
    r"ppb",
    r"kg",
    r"g",
    r"mg",
    r"ug",
    r"µg",
    r"ng",
    r"t",
    r"ha",
    r"km",
    r"m",
    r"cm",
    r"mm",
    r"µm",
    r"nm",
    r"L",
    r"mL",
    r"s",
    r"min",
    r"h",
    r"d",
    r"%",
    r"‰",
]

# Unit matching pattern
UNIT_ATOM = "|".join(sorted((re.escape(u) for u in KNOWN_UNITS), key=len, reverse=True))
UNIT_GROUP = rf"(?:{UNIT_ATOM})(?:\s*(?:/|\*|x|×|·|\s|per)\s*(?:{UNIT_ATOM}|\d+))*"
MEAS_RE = re.compile(
    rf"(?<!\w)(?P<num>{NUM_RE})(?P<sep>\s+)(?P<unit>{UNIT_GROUP})(?!\w)"
)
SINGLE_UNIT_CTX_RE = re.compile(r"^\s*[A-Za-zÁÉÍÓÚáéíóúÜüÑñ]")

# Common markdown regions we should leave untouched when performing textual substitutions.
PROTECT_RE = re.compile(r"(```.*?```|`[^`]*`|\$\$.*?\$\$|\$.*?\$)", re.DOTALL)

# Image syntax: ![alt](path "title")
IMAGE_RE = re.compile(
    r"!\[(?P<alt>[^\]\n]*)\]\((?P<src>[^)\s]+)(?:\s+\"(?P<title>[^\"]+)\")?\)"
)

# Convert unicode exponents and minus to textual patterns that can be wrapped in siunitx units
SUPERSCRIPTS = str.maketrans(
    {
        "⁰": "0",
        "¹": "1",
        "²": "2",
        "³": "3",
        "⁴": "4",
        "⁵": "5",
        "⁶": "6",
        "⁷": "7",
        "⁸": "8",
        "⁹": "9",
        "⁻": "-",
    }
)


def escape_latex(text: str) -> str:
    """Minimal LaTeX escaping for text inserted into captions/labels."""
    replacements = {
        "\\": r"\\\\",
        "{": r"\\{",
        "}": r"\\}",
        "$": r"\\$",
        "_": r"\\_",
        "^": r"\\^{}",
        "~": r"\\~{}",
        "&": r"\\&",
        "%": r"\\%",
        "#": r"\\#",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def normalize_unit_expression(unit: str) -> str:
    """Convert plain unit strings to a siunitx-friendly unit argument."""
    u = unit.strip()

    # normalize unicode minus and exponents
    u = u.translate(SUPERSCRIPTS)
    u = u.replace("−", "-")

    # allow writing "per" as an alias for division in units
    u = re.sub(r"\s+per\s+", " / ", u)

    # convert forms like "ha^-1" -> "ha^{-1}"
    u = re.sub(r"\^(-?\d+)", r"^{\\1}", u)

    # convert forms like "ha-1" -> "ha^{-1}" when it looks like exponent
    u = re.sub(r"\b([A-Za-z%°]+)-(\d+)\b", r"\\1^{-\\2}", u)

    # standardize operator tokens
    u = re.sub(r"\s*/\s*", " / ", u)
    u = re.sub(r"\s*(?:x|×|·|\*)\s*", " * ", u)
    u = re.sub(r"\s+", " ", u).strip()

    # division and multiplication operators in units
    u = u.replace(" / ", " \\per ")
    u = u.replace(" * ", " \\cdot ")

    # common symbols in LaTeX
    u = u.replace("°C", r"\degree C")
    u = u.replace("‰", r"\textperthousand")
    u = u.replace("%", r"\%")

    # compact spacing between unit tokens
    u = re.sub(r"\s+", r"\\,", u)
    return u


def replace_units_in_text(text: str) -> str:
    def _rep(match: re.Match[str]) -> str:
        num = match.group("num").replace(",", ".")
        unit_raw = match.group("unit")
        if len(unit_raw) == 1:
            tail = text[match.end("unit") : match.end("unit") + 16]
            if SINGLE_UNIT_CTX_RE.match(tail):
                return match.group(0)

        unit = normalize_unit_expression(unit_raw)
        return rf"\SI{{{num}}}{{{unit}}}"

    return MEAS_RE.sub(_rep, text)


def preprocess_markdown(
    md: str,
    transform_units: bool,
    transform_figures: bool,
    md_dir: Path,
    figure_pdf_suffix: str,
    figure_meta_suffix: str,
    figure_full_suffixes: tuple[str, ...],
    figure_width_default: str,
    figure_placement_default: str,
) -> str:
    """Apply unit normalization and optional figure expansion only outside math/code."""

    if transform_figures:
        md = _apply_figure_rewrite(
            md,
            md_dir,
            figure_pdf_suffix,
            figure_meta_suffix,
            figure_full_suffixes,
            figure_width_default,
            figure_placement_default,
        )

    if transform_units:
        return _apply_outside_protected(md, replace_units_in_text)

    return md


def _apply_outside_protected(md: str, fn: Callable[[str], str]) -> str:
    out: list[str] = []
    last = 0
    for match in PROTECT_RE.finditer(md):
        out.append(fn(md[last : match.start()]))
        out.append(match.group(0))
        last = match.end()
    out.append(fn(md[last:]))
    return "".join(out)


def _apply_figure_rewrite(
    md: str,
    md_dir: Path,
    figure_pdf_suffix: str,
    figure_meta_suffix: str,
    figure_full_suffixes: tuple[str, ...],
    figure_width_default: str,
    figure_placement_default: str,
) -> str:
    def _replace(match: re.Match[str]) -> str:
        return _replace_figure(
            match,
            md_dir=md_dir,
            figure_pdf_suffix=figure_pdf_suffix,
            figure_meta_suffix=figure_meta_suffix,
            figure_full_suffixes=figure_full_suffixes,
            figure_width_default=figure_width_default,
            figure_placement_default=figure_placement_default,
        )

    return IMAGE_RE.sub(_replace, md)


def _replace_figure(
    match: re.Match[str],
    *,
    md_dir: Path,
    figure_pdf_suffix: str,
    figure_meta_suffix: str,
    figure_full_suffixes: tuple[str, ...],
    figure_width_default: str,
    figure_placement_default: str,
) -> str:
    alt = (match.group("alt") or "").strip()
    src = (match.group("src") or "").strip()
    title_attr = (match.group("title") or "").strip()
    if "://" in src or src.startswith("http"):
        return match.group(0)

    bundle = _resolve_figure_assets(
        (md_dir / src).resolve(),
        figure_pdf_suffix,
        figure_meta_suffix,
        figure_full_suffixes,
    )
    if bundle is None:
        return match.group(0)

    meta, pdf_path = bundle
    return _render_figure(
        meta=meta,
        source=src,
        plot_pdf=_latex_path(pdf_path, md_dir),
        alt=alt,
        title_attr=title_attr,
        figure_width_default=figure_width_default,
        figure_placement_default=figure_placement_default,
    )


def _figure_captions(
    meta: dict[str, Any], alt: str, title_attr: str
) -> tuple[str, str]:
    meta_title = str(meta.get("title", "")).strip()
    meta_caption = str(meta.get("caption", "")).strip()
    if "|" in alt:
        md_title, md_caption = [part.strip() for part in alt.split("|", 1)]
        md_caption = md_caption or md_title
    else:
        md_title, md_caption = alt, ""
    md_title = md_title or title_attr
    return meta_title or md_title, meta_caption or md_caption or md_title


def _figure_include_options(meta: dict[str, Any], default_width: str) -> str:
    width = str(meta.get("width", default_width))
    options = str(meta.get("includegraphics", "")).strip()
    if not width:
        return options
    return f"{options}, width={width}" if options else f"width={width}"


def _render_figure(
    *,
    meta: dict[str, Any],
    source: str,
    plot_pdf: str,
    alt: str,
    title_attr: str,
    figure_width_default: str,
    figure_placement_default: str,
) -> str:
    caption_short, caption_text = _figure_captions(meta, alt, title_attr)
    placement = str(meta.get("placement", figure_placement_default))
    options = _figure_include_options(meta, figure_width_default)
    base_label = Path(source).stem.replace("_", "-").removesuffix("-full")
    label = str(meta.get("label", f"fig:{base_label}"))
    include = (
        f"\\includegraphics[{options}]{{{escape_latex(plot_pdf)}}}"
        if options
        else f"\\includegraphics{{{escape_latex(plot_pdf)}}}"
    )
    lines = [
        f"\\begin{{figure}}[{escape_latex(placement)}]",
        "\\centering",
        include,
    ]
    if caption_text:
        caption = escape_latex(caption_text)
        if caption_short and caption_short != caption_text:
            caption = f"[{escape_latex(caption_short)}]{{{caption}}}"
        else:
            caption = f"{{{caption}}}"
        lines.append(f"\\caption{caption}")
    if label:
        lines.append(f"\\label{{{escape_latex(label)}}}")
    lines.append("\\end{figure}")
    return "\n" + "\n".join(lines) + "\n"


def _resolve_figure_assets(
    image_path: Path,
    figure_pdf_suffix: str,
    figure_meta_suffix: str,
    figure_full_suffixes: tuple[str, ...],
) -> tuple[dict[str, Any], Path] | None:
    if not image_path.exists():
        return None

    stem = image_path.stem
    candidates: list[str] = _dedup(
        [stem] + [stem[: -len(s)] for s in figure_full_suffixes if stem.endswith(s)]
    )

    for base in candidates:
        pdf_candidate = image_path.with_name(f"{base}{figure_pdf_suffix}.pdf")
        if pdf_candidate.exists():
            meta = (
                _load_figure_metadata(
                    image_path.with_name(f"{base}{figure_meta_suffix}.json")
                )
                or {}
            )
            return meta, pdf_candidate

    # Optional fallback: if plot PDF exists with exact stem.
    fallback_pdf = image_path.with_suffix(".pdf")
    if fallback_pdf.exists():
        meta = (
            _load_figure_metadata(
                image_path.with_name(f"{stem}{figure_meta_suffix}.json")
            )
            or {}
        )
        return meta, fallback_pdf

    return None


def _load_figure_metadata(json_path: Path) -> dict[str, Any] | None:
    if not json_path.exists():
        return None

    try:
        raw: object = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if isinstance(raw, dict):
        data = cast(dict[str, Any], raw)
        metadata: dict[str, Any] = {}
        for key, value in data.items():
            metadata[key] = value
        return metadata
    return None


def _dedup(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def _latex_path(path: Path, reference_dir: Path) -> str:
    try:
        return path.resolve().relative_to(reference_dir.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run_pandoc(
    md_text: str,
    output: Path | None,
    standalone: bool,
    use_siunitx: bool,
    use_citeproc: bool,
) -> str:
    if not shutil.which("pandoc"):
        raise RuntimeError(
            "No se encontró pandoc en PATH. Instálalo para convertir md -> LaTeX."
        )

    cmd = [
        "pandoc",
        "-f",
        "markdown+tex_math_dollars+smart",
        "-t",
        "latex",
    ]
    if standalone:
        cmd.append("-s")
    if use_citeproc:
        cmd.append("--citeproc")

    tmp_header = None
    if use_siunitx:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tex", delete=False
        ) as header:
            header.write("\\usepackage{siunitx}\n")
            tmp_header = Path(header.name)
        cmd.extend(["--include-in-header", str(tmp_header)])

    try:
        result = subprocess.run(
            cmd,
            input=md_text,
            text=True,
            check=True,
            capture_output=True,
        )
    finally:
        if tmp_header is not None:
            tmp_header.unlink(missing_ok=True)

    if output is None:
        return result.stdout

    output.write_text(result.stdout, encoding="utf-8")
    return str(output)


def _select_latex_engine(engine: str) -> str:
    preferred = (
        "pdflatex",
        "xelatex",
        "lualatex",
        "tectonic",
    )

    if engine == "auto":
        engine = next(
            (candidate for candidate in preferred if shutil.which(candidate)),
            "",
        )
    if not engine:
        raise RuntimeError(
            "No se encontró un compilador LaTeX disponible en PATH "
            "(pdflatex/xelatex/lualatex/tectonic). Instalá uno o usá --no-compile."
        )
    return engine


def _run_latex_passes(
    command: list[str],
    *,
    cwd: Path,
    engine: str,
    passes: int,
    env: dict[str, str] | None = None,
) -> None:
    for _ in range(max(1, passes)):
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            check=False,
            capture_output=True,
            env=env,
        )
        if result.returncode:
            details = result.stderr.strip() or result.stdout.strip()
            suffix = f"\n{details}" if details else ""
            raise RuntimeError(
                f"Error al compilar LaTeX con {engine}: código {result.returncode}{suffix}"
            )


def _compile_tectonic(tex_path: Path, engine: str) -> None:
    with tempfile.TemporaryDirectory(prefix="tectonic-cache-") as cache_dir:
        env = os.environ.copy()
        env.setdefault("TECTONIC_CACHE_DIR", cache_dir)
        _run_latex_passes(
            [engine, str(tex_path)],
            cwd=tex_path.parent,
            engine=engine,
            passes=1,
            env=env,
        )


def compile_latex(tex_path: Path, *, engine: str, passes: int = 2) -> Path:
    if not tex_path.exists():
        raise RuntimeError(f"El archivo TeX no existe: {tex_path}")

    selected_engine = _select_latex_engine(engine)
    if selected_engine == "tectonic":
        _compile_tectonic(tex_path, selected_engine)
    else:
        _run_latex_passes(
            [
                selected_engine,
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
                str(tex_path),
            ],
            cwd=tex_path.parent,
            engine=selected_engine,
            passes=passes,
        )

    return tex_path.with_suffix(".pdf")


def _parse_suffix_list(raw: str) -> tuple[str, ...]:
    if not raw.strip():
        return ()
    items = tuple(s.strip() for s in raw.split(",") if s.strip())
    normalized = tuple({*items})
    return tuple(sorted(normalized, key=len, reverse=True))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convierte markdown a LaTeX, con normalización LaTeX de unidades y "
            "reeplanteo de imágenes por sidecars: PNG completo + JSON + PDF limpio."
        )
    )
    parser.add_argument("input", type=Path, help="Archivo Markdown de entrada")
    parser.add_argument(
        "-o", "--output", type=Path, default=None, help="Archivo LaTeX de salida"
    )
    parser.add_argument(
        "--no-standalone",
        action="store_true",
        help="Salida solo del cuerpo LaTeX (sin preámbulo completo)",
    )
    parser.add_argument(
        "--no-siunitx",
        action="store_true",
        help="No convertir unidades automáticamente ni agregar siunitx",
    )
    parser.add_argument(
        "--no-figure-rewrite",
        action="store_true",
        help="No reemplazar imágenes de markdown por bloques de figura LaTeX",
    )
    parser.add_argument(
        "--figure-pdf-suffix",
        default="_plot",
        help="Sufijo del PDF limpio asociado al PNG completo (por defecto: _plot)",
    )
    parser.add_argument(
        "--figure-meta-suffix",
        default="_meta",
        help="Sufijo del JSON con metadatos asociado al PNG completo (por defecto: _meta)",
    )
    parser.add_argument(
        "--figure-full-suffixes",
        default="_full,-full",
        help="Sufijos para reconocer el PNG completo a partir del stem (coma separada)",
    )
    parser.add_argument(
        "--figure-width",
        default="\\linewidth",
        help="Anchura por defecto para includegraphics en figura (default: \\linewidth)",
    )
    parser.add_argument(
        "--figure-placement",
        default="h",
        help="Lugar por defecto de figuras LaTeX (default: h)",
    )
    parser.add_argument(
        "--only-preprocess",
        action="store_true",
        help="Solo preprocesar Markdown y mostrar resultado en stdout",
    )
    parser.add_argument(
        "--no-compile",
        action="store_true",
        help="No compilar el archivo .tex generado a PDF.",
    )
    parser.add_argument(
        "--no-citeproc",
        action="store_true",
        help=r"No procesar citas y bibliografía de estilo CSL/`\\@...`.",
    )
    parser.add_argument(
        "--latex-compiler",
        default="auto",
        choices=("auto", "pdflatex", "xelatex", "lualatex", "tectonic"),
        help="Compilador LaTeX a usar (default: auto).",
    )
    parser.add_argument(
        "--latex-passes",
        type=int,
        default=2,
        help="Cantidad de pasadas de compilación (default: 2).",
    )

    args = parser.parse_args()
    md_path: Path = args.input
    if not md_path.exists():
        print(f"No existe el archivo: {md_path}", file=sys.stderr)
        return 2

    md_text = md_path.read_text(encoding="utf-8")
    output = args.output

    processed = preprocess_markdown(
        md_text,
        transform_units=not args.no_siunitx,
        transform_figures=not args.no_figure_rewrite,
        md_dir=md_path.parent,
        figure_pdf_suffix=args.figure_pdf_suffix,
        figure_meta_suffix=args.figure_meta_suffix,
        figure_full_suffixes=_parse_suffix_list(args.figure_full_suffixes),
        figure_width_default=args.figure_width,
        figure_placement_default=args.figure_placement,
    )

    if args.only_preprocess:
        sys.stdout.write(processed)
        return 0

    if output is None:
        output = md_path.with_suffix(".tex")

    result = run_pandoc(
        processed,
        output,
        standalone=not args.no_standalone,
        use_siunitx=not args.no_siunitx,
        use_citeproc=not args.no_citeproc,
    )

    print(f"TeX generado en: {result}")
    if not args.no_compile:
        pdf_path = compile_latex(
            Path(result),
            engine=args.latex_compiler,
            passes=max(1, args.latex_passes),
        )
        print(f"PDF generado en: {pdf_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
