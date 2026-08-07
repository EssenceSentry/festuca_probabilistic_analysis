from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib.colors import to_hex

from festuca_analysis.annex import (
    TREATMENTS,
    logp_log_tau,
    make_design,
    prior_predictive_summary,
    prior_specification_table,
)
from festuca_analysis.longitudinal import (
    COMMON_N_APPLICATIONS,
    COMMON_N_TOTAL_KG_HA,
    EXPERIMENTAL_N_TOTAL_KG_HA,
)
from festuca_analysis.plotting import (
    DATA_LINEWIDTH,
    ERRORBAR_CAPSIZE,
    GRID_LINEWIDTH,
    INTERVAL_LINEWIDTH,
    PLOT_FONT_FAMILY,
    REFERENCE_LINEWIDTH,
    apply_plot_theme,
)
from festuca_analysis.statistics import (
    benjamini_hochberg,
    fit_mixedlm_best,
    likelihood_ratio,
    rcbd_missing_cell_estimate,
)


class PlotThemeTests(unittest.TestCase):
    def test_seaborn_theme_exposes_inferno_palette_and_line_hierarchy(self) -> None:
        mpl_api = cast(Any, mpl)
        with mpl_api.rc_context():
            palette = apply_plot_theme()
            cycle = mpl_api.rcParams["axes.prop_cycle"].by_key()["color"]
            self.assertEqual(len(palette), 9)
            self.assertEqual([to_hex(color) for color in cycle[:9]], palette)
            self.assertEqual(mpl_api.rcParams["axes.grid.axis"], "y")
            self.assertEqual(mpl_api.rcParams["font.family"], [PLOT_FONT_FAMILY])
            self.assertEqual(mpl_api.rcParams["lines.linewidth"], DATA_LINEWIDTH)
            self.assertEqual(mpl_api.rcParams["errorbar.capsize"], ERRORBAR_CAPSIZE)
            self.assertEqual(mpl_api.rcParams["grid.linewidth"], GRID_LINEWIDTH)
            self.assertGreater(DATA_LINEWIDTH, INTERVAL_LINEWIDTH)
            self.assertGreater(INTERVAL_LINEWIDTH, REFERENCE_LINEWIDTH)
            self.assertFalse(mpl_api.rcParams["axes.spines.top"])
            self.assertFalse(mpl_api.rcParams["axes.spines.right"])


class NitrogenScheduleTests(unittest.TestCase):
    def test_common_schedule_includes_april_july_and_august_applications(self) -> None:
        self.assertEqual(
            COMMON_N_APPLICATIONS,
            (
                ("2025-04-01", "2025-05-01", 60.0),
                ("2025-07-01", "2025-07-01", 52.0),
                ("2025-08-01", "2025-09-01", 52.0),
            ),
        )
        self.assertEqual(COMMON_N_TOTAL_KG_HA, 164.0)
        self.assertEqual(COMMON_N_TOTAL_KG_HA + EXPERIMENTAL_N_TOTAL_KG_HA, 364.0)


class MultiplicityTests(unittest.TestCase):
    def test_benjamini_hochberg_preserves_order_and_monotonicity(self) -> None:
        adjusted = benjamini_hochberg([0.04, 0.001, 0.03, 0.20])
        np.testing.assert_allclose(adjusted, [0.05333333, 0.004, 0.05333333, 0.20])


class MissingCellTests(unittest.TestCase):
    def test_rcbd_estimate_weights_totals_by_their_denominators(self) -> None:
        frame = pd.DataFrame(
            {
                "treatment": ["A"] * 3 + ["B"] * 3 + ["C"] * 3 + ["D"] * 3,
                "block": ["R1", "R2", "R3"] * 4,
                "value": [
                    10.0,
                    12.0,
                    np.nan,
                    13.0,
                    12.0,
                    15.0,
                    9.0,
                    11.0,
                    10.0,
                    16.0,
                    15.0,
                    17.0,
                ],
            }
        )
        estimate = rcbd_missing_cell_estimate(
            frame,
            value_column="value",
            missing_treatment="A",
            missing_block="R3",
            r_blocks=3,
            t_treatments=4,
        )
        self.assertAlmostEqual(estimate, 12.333333333333334)


class MixedOptimizerTests(unittest.TestCase):
    def test_selects_highest_likelihood_among_converged_fits(self) -> None:
        fits = {
            "first": SimpleNamespace(llf=-12.0, converged=False),
            "second": SimpleNamespace(llf=-10.0, converged=True),
            "third": SimpleNamespace(llf=-9.0, converged=True),
        }

        def fake_fit(**kwargs: Any) -> SimpleNamespace:
            return fits[str(kwargs["method"])]

        fake_model = SimpleNamespace(fit=fake_fit)
        frame = pd.DataFrame({"y": [0.0, 1.0], "plot_id": ["a", "b"]})
        with patch(
            "festuca_analysis.statistics.smf.mixedlm",
            return_value=fake_model,
        ):
            selected = fit_mixedlm_best(
                "y ~ 1",
                frame,
                methods=("first", "second", "third"),
            )
        self.assertIs(selected, fits["third"])
        self.assertEqual(selected._audit_optimizer, "third")
        self.assertEqual(selected._audit_selection, "best_converged")

    def test_likelihood_ratio_uses_nested_parameter_difference(self) -> None:
        reduced = SimpleNamespace(llf=-10.0, df_modelwc=4)
        full = SimpleNamespace(llf=-7.0, df_modelwc=6)
        result = likelihood_ratio(reduced, full)
        self.assertEqual(result.statistic, 6.0)
        self.assertEqual(result.degrees_freedom, 2)
        self.assertGreater(result.p_asymptotic, 0.0)
        self.assertLess(result.p_asymptotic, 0.1)


class SamplerSpecificationTests(unittest.TestCase):
    @staticmethod
    def _frame() -> pd.DataFrame:
        rows: list[dict[str, float | str]] = []
        for block_index, block in enumerate(["R1", "R2", "R3", "R4"]):
            for treatment_index, treatment in enumerate(TREATMENTS):
                rows.append(
                    {
                        "block": block,
                        "treatment": treatment,
                        "clean_yield_kg_ha": 700.0
                        + 100.0 * treatment_index
                        + 10.0 * block_index,
                    }
                )
        return pd.DataFrame(rows)

    def test_design_maps_treatments_and_has_centered_timing_basis(self) -> None:
        design = make_design(self._frame())
        self.assertEqual(design.X.shape, (24, 9))
        self.assertEqual(design.X_group.shape, (6, 9))
        np.testing.assert_allclose(
            design.X_group[1:, design.timing_slice].sum(axis=0), 0, atol=1e-12
        )
        np.testing.assert_allclose(design.y_z.mean(), 0.0, atol=1e-12)

    def test_tau_log_density_is_finite(self) -> None:
        coefficients = np.array([0.2, -0.1, 0.05, -0.15])
        self.assertTrue(np.isfinite(logp_log_tau(-1.0, coefficients, 0.5)))

    def test_priors_are_numeric_and_prior_predictive_is_reproducible(self) -> None:
        table = prior_specification_table()
        self.assertIn("sigma^2", set(table["parameter"]))
        first = prior_predictive_summary(
            self._frame(), timing_prior_scale=0.5, draws=250, seed=123
        )
        second = prior_predictive_summary(
            self._frame(), timing_prior_scale=0.5, draws=250, seed=123
        )
        pd.testing.assert_frame_equal(first, second)
        self.assertTrue(np.isfinite(first.select_dtypes("number").to_numpy()).all())


if __name__ == "__main__":
    unittest.main()
