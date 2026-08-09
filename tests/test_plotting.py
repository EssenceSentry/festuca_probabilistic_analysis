"""Contracts for the retained Festuca figure system."""

from __future__ import annotations

# Matplotlib's collection and save APIs are only partially typed.
# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

from festuca_analysis.annex import PROBABILISTIC_FIGURE_STEMS
from festuca_analysis.longitudinal import (
    LONGITUDINAL_FIGURE_STEMS,
    _experimental_n_step_table,  # pyright: ignore[reportPrivateUsage]
)
from festuca_analysis.plotting import (
    FONT_DIRECTORY,
    INTERVAL_LINEWIDTH,
    PLOT_FONT_FAMILY,
    FigureExporter,
    apply_plot_theme,
    plot_horizontal_interval,
)

EXPECTED_PALETTE = (
    "#160b39",
    "#420a68",
    "#6a176e",
    "#932667",
    "#bc3754",
    "#dd513a",
    "#f37819",
    "#fca50a",
    "#f6d746",
)


class PlotThemeTests(unittest.TestCase):
    def test_libertinus_is_bundled_registered_and_active(self) -> None:
        apply_plot_theme()
        bundled_families = {
            font_manager.FontProperties(fname=str(path)).get_name()
            for path in FONT_DIRECTORY.glob("*.otf")
        }
        self.assertIn(PLOT_FONT_FAMILY, bundled_families)
        self.assertIn(PLOT_FONT_FAMILY, mpl.rcParams["font.family"])
        resolved = cast(Any, font_manager).findfont(
            PLOT_FONT_FAMILY,
            fallback_to_default=False,
        )
        self.assertTrue(Path(resolved).is_file())

    def test_treatment_palette_is_stable(self) -> None:
        self.assertEqual(tuple(apply_plot_theme()), EXPECTED_PALETTE)

    def test_horizontal_interval_retains_caps_and_marker_geometry(self) -> None:
        fig, axis = plt.subplots()
        try:
            marker = plot_horizontal_interval(
                axis,
                estimate=1.5,
                lower=0.5,
                upper=2.5,
                y=3.0,
                color=EXPECTED_PALETTE[1],
            )
            interval_collection = cast(Any, axis.collections[0])
            cap_collection = cast(Any, axis.collections[1])
            interval_segments = interval_collection.get_segments()
            cap_segments = cap_collection.get_segments()
            np.testing.assert_allclose(interval_segments[0], [[0.5, 3.0], [2.5, 3.0]])
            self.assertEqual(len(cap_segments), 2)
            np.testing.assert_allclose(marker.get_offsets(), [[1.5, 3.0]])
            np.testing.assert_allclose(
                interval_collection.get_linewidths(),
                [INTERVAL_LINEWIDTH],
            )
        finally:
            plt.close(fig)


class ExperimentalSchedulePlotTests(unittest.TestCase):
    def test_schedule_uses_only_zero_one_hundred_and_two_hundred_endpoints(
        self,
    ) -> None:
        treatments = tuple(f"M{index}" for index in range(6))
        schedule = pd.DataFrame(
            {
                "treatment": treatments,
                "first_application": [pd.NaT] + [pd.Timestamp("2025-06-12")] * 5,
                "second_application": [pd.NaT] + [pd.Timestamp("2025-09-20")] * 5,
            }
        )
        steps = _experimental_n_step_table(
            schedule,
            treatments,
            view_start=pd.Timestamp("2025-06-01"),
            view_end=pd.Timestamp("2025-10-31"),
        )
        control = steps.loc[steps["treatment"].eq("M0")]
        self.assertEqual(
            set(control["cumulative_experimental_n_kg_ha"].to_numpy(float)),
            {0.0},
        )
        for treatment in treatments[1:]:
            values = steps.loc[
                steps["treatment"].eq(treatment),
                "cumulative_experimental_n_kg_ha",
            ].to_numpy(float)
            np.testing.assert_allclose(values, [0.0, 100.0, 200.0, 200.0])


class FigureExporterTests(unittest.TestCase):
    def test_thesis_export_is_clean_then_decorated_and_keeps_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            exporter = FigureExporter(Path(directory), profile="thesis", dpi=80)
            fig, axis = plt.subplots()
            axis.plot([0.0, 1.0], [0.0, 1.0])
            exporter.add_header(fig, "Título retenido", subtitle="Subtítulo actual")
            exporter.add_note(fig, "Nota metodológica actual")

            states: list[tuple[str, str | None]] = []
            original_savefig = fig.savefig

            def recording_savefig(filename: Any, *args: Any, **kwargs: Any) -> Any:
                title_artist = getattr(fig, "_suptitle", None)
                title = None if title_artist is None else str(title_artist.get_text())
                states.append((Path(filename).name, title))
                return original_savefig(filename, *args, **kwargs)

            try:
                with patch.object(fig, "savefig", side_effect=recording_savefig):
                    payload = exporter.save(fig, "retained_figure")
            finally:
                plt.close(fig)

            output = Path(directory) / "thesis"
            self.assertTrue((output / "retained_figure.pdf").is_file())
            self.assertTrue((output / "retained_figure_full.png").is_file())
            metadata_path = output / "retained_figure.json"
            self.assertTrue(metadata_path.is_file())
            metadata: object = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertIsInstance(metadata, dict)
            self.assertEqual(payload["title"], "Título retenido")
            self.assertEqual(states[0], ("retained_figure.pdf", None))
            self.assertEqual(
                states[-1], ("retained_figure_full.png", "Título retenido")
            )


class FigureManifestTests(unittest.TestCase):
    def test_retained_figure_manifests_are_exact(self) -> None:
        self.assertEqual(len(LONGITUDINAL_FIGURE_STEMS), 10)
        self.assertEqual(len(PROBABILISTIC_FIGURE_STEMS), 6)
        self.assertEqual(len(set(LONGITUDINAL_FIGURE_STEMS)), 10)
        self.assertEqual(len(set(PROBABILISTIC_FIGURE_STEMS)), 6)

    def test_removed_figures_do_not_return(self) -> None:
        retained = " ".join(
            (*LONGITUDINAL_FIGURE_STEMS, *PROBABILISTIC_FIGURE_STEMS)
        ).casefold()
        for removed_fragment in (
            "near_optimal",
            "early_late",
            "leave_one",
            "targeted",
            "accumulated_n",
            "nni",
            "model_b",
            "zoom",
        ):
            self.assertNotIn(removed_fragment, retained)


if __name__ == "__main__":
    unittest.main()
