"""Source-reproducible probabilistic annex for the Festuca experiment.

No posterior summaries are imported from historical runs.  Every model reads the
current XLSX workbook through :mod:`festuca_analysis.source_data`.  The model uses
observed response centering and scaling for numerical stability; consequently,
its predictive audit is explicitly labelled conditional/data-scaled rather than
as a pre-data prior predictive analysis.
"""

from __future__ import annotations

# Pyright cannot fully infer the scientific stack's labelled-array APIs.
# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
import json
import platform
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal, cast

import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt
import scipy
import statsmodels.api as sm
import statsmodels.formula.api as smf
import xarray as xr
from IPython.display import display
from patsy import build_design_matrices, dmatrix
from scipy import stats
from scipy.linalg import helmert

from festuca_analysis.plotting import (
    DATA_LINEWIDTH,
    EMPHASIS_LINEWIDTH,
    ERRORBAR_CAPSIZE,
    INTERVAL_LINEWIDTH,
    MARKER_SIZE,
    REFERENCE_LINEWIDTH,
    SECONDARY_LINEWIDTH,
    FigureExporter,
    apply_plot_theme,
    plot_horizontal_interval,
)
from festuca_analysis.source_data import (
    ExperimentData,
    load_experiment_data,
    source_provenance_table,
)

pt_api = cast(Any, pt)

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_DIR: Final = PROJECT_ROOT / "results"
RANDOM_SEED: Final = 20260807
STUDENT_T_DF: Final = 5.0
PRIMARY_TIMING_PRIOR_SCALE: Final = 0.50
TIMING_PRIOR_SCALES: Final = {
    "strong_regularization": 0.25,
    "primary": PRIMARY_TIMING_PRIOR_SCALE,
    "weak_regularization": 1.00,
}
PROBABILISTIC_FIGURE_STEMS: Final = (
    "01_yield_observed_posterior",
    "02_margin_prior_sensitivity",
    "03_posterior_predictive_anova",
    "longitudinal_biomass_kg_ha_raw",
    "longitudinal_n_pct_raw",
    "reconstruction_null",
)


@dataclass(frozen=True)
class YieldDesign:
    frame: pd.DataFrame
    center: float
    scale: float
    extra_n: np.ndarray
    timing: np.ndarray
    block: np.ndarray
    group_timing: np.ndarray
    treatments: tuple[str, ...]
    blocks: tuple[str, ...]


@dataclass(frozen=True)
class LongitudinalDesign:
    frame: pd.DataFrame
    center: float
    scale: float
    response_scale: Literal["raw", "log"]
    fixed_formula: str
    design_info: Any
    x_main: np.ndarray
    x_interaction: np.ndarray
    main_names: tuple[str, ...]
    interaction_names: tuple[str, ...]
    plot_index: np.ndarray
    plots: tuple[str, ...]
    prediction_grid: pd.DataFrame
    prediction_main: np.ndarray
    prediction_interaction: np.ndarray
    treatments: tuple[str, ...]
    date_levels: tuple[str, ...]
    blocks: tuple[str, ...]


@dataclass(frozen=True)
class FittedModel:
    model_id: str
    sector: str
    outcome: str
    specification: str
    inference_data: az.InferenceData
    design: YieldDesign | LongitudinalDesign


def _stable_seed(*parts: object, base: int = RANDOM_SEED) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return base + zlib.crc32(payload) % 1_000_000


def _flatten_posterior(data: xr.DataArray) -> np.ndarray:
    stacked = data.stack(sample=("chain", "draw"))
    remaining = [dimension for dimension in stacked.dims if dimension != "sample"]
    ordered = stacked.transpose("sample", *remaining)
    return np.asarray(ordered)


def _quantile_summary(values: np.ndarray) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "posterior_mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "lower_95": float(np.quantile(array, 0.025)),
        "upper_95": float(np.quantile(array, 0.975)),
    }


def _observed_rcbd_p(frame: pd.DataFrame) -> float:
    subset = frame.loc[frame["treatment"].astype(str).ne("M0")].copy()
    subset = subset.assign(
        treatment=subset["treatment"].astype(str),
        block=subset["block"].astype(str),
    )
    fit = smf.ols(
        "clean_yield_kg_ha ~ C(treatment) + C(block)",
        data=subset,
    ).fit()
    anova = sm.stats.anova_lm(fit, typ=2)
    row = next(name for name in anova.index if str(name).startswith("C(treatment)"))
    return float(cast(Any, anova.loc[row, "PR(>F)"]))


def _rcbd_anova_p_values(
    y_rep: np.ndarray,
    treatment: np.ndarray,
    block: np.ndarray,
) -> np.ndarray:
    """Vectorized M1–M5 block-adjusted treatment F tests."""

    fertilized = [f"M{i}" for i in range(1, 6)]
    mask = np.isin(treatment, fertilized)
    treatment_sub = treatment[mask]
    block_sub = block[mask]
    y_sub = y_rep[:, mask]

    block_levels = sorted(np.unique(block_sub).tolist())
    treatment_dummy = np.column_stack(
        [(treatment_sub == level).astype(float) for level in fertilized[1:]]
    )
    block_dummy = np.column_stack(
        [(block_sub == level).astype(float) for level in block_levels[1:]]
    )
    intercept = np.ones((len(treatment_sub), 1))
    x_full = np.column_stack([intercept, treatment_dummy, block_dummy])
    x_reduced = np.column_stack([intercept, block_dummy])

    residual_projection_full = np.eye(len(treatment_sub)) - x_full @ np.linalg.pinv(
        x_full
    )
    residual_projection_reduced = np.eye(
        len(treatment_sub)
    ) - x_reduced @ np.linalg.pinv(x_reduced)
    sse_full = np.sum((y_sub @ residual_projection_full) ** 2, axis=1)
    sse_reduced = np.sum((y_sub @ residual_projection_reduced) ** 2, axis=1)
    df_num = x_full.shape[1] - x_reduced.shape[1]
    df_den = len(treatment_sub) - x_full.shape[1]
    f_values = np.maximum(
        ((sse_reduced - sse_full) / df_num) / (sse_full / df_den),
        0.0,
    )
    return stats.f.sf(f_values, df_num, df_den)


class ProbabilisticAnnex:
    """Notebook-facing controller for all source-reproducible Bayesian analyses."""

    def __init__(
        self,
        *,
        project_root: Path | None = None,
        workbook_path: Path | str | None = None,
        draws: int = 2000,
        tune: int = 2000,
        chains: int = 4,
        cores: int | None = None,
        target_accept: float = 0.95,
        random_seed: int = RANDOM_SEED,
        export_results: bool = True,
        export_figures: bool = True,
        figure_profile: Literal["standalone", "thesis"] = "thesis",
        print_figure_json: bool = False,
    ) -> None:
        self.project_root = (project_root or PROJECT_ROOT).resolve()
        self.workbook_path = workbook_path
        self.draws = draws
        self.tune = tune
        self.chains = chains
        self.cores = cores
        self.target_accept = target_accept
        self.random_seed = random_seed
        self.export_results = export_results
        self.export_figures = export_figures
        self.results_dir = self.project_root / DEFAULT_RESULTS_DIR.name
        self.tables_dir = self.results_dir / "tables"
        self.figures_dir = self.results_dir / "figures"
        self.posteriors_dir = self.results_dir / "posteriors"
        self.data: ExperimentData | None = None
        self.tables: dict[str, pd.DataFrame] = {}
        self.figure_metadata: list[dict[str, object]] = []
        self.yield_models: dict[str, FittedModel] = {}
        self.longitudinal_models: dict[str, FittedModel] = {}
        self.palette = apply_plot_theme()
        self.figure_exporter = FigureExporter(
            self.figures_dir,
            profile=figure_profile,
            dpi=300,
            print_json=print_figure_json,
        )
        pd.set_option("display.max_columns", 100)
        pd.set_option("display.width", 180)

    def _require_data(self) -> ExperimentData:
        if self.data is None:
            raise RuntimeError("Ejecute annex.load_data() antes de esta sección.")
        return self.data

    def _show(self, name: str, frame: pd.DataFrame) -> pd.DataFrame:
        table = frame.copy()
        self.tables[name] = table
        display(table)
        return table

    def _save_figure(
        self,
        fig: Any,
        stem: str,
        *,
        title: str,
        subtitle: str | None = None,
        note: str | None = None,
    ) -> None:
        self.figure_exporter.add_header(fig, title, subtitle=subtitle)
        if note:
            self.figure_exporter.add_note(fig, note)
        if self.export_figures:
            payload = self.figure_exporter.save(fig, stem)
            self.figure_metadata.append(payload)
        else:
            self.figure_exporter.discard(fig)
        plt.show()
        plt.close(fig)

    # ------------------------------------------------------------------
    # Configuration and source
    # ------------------------------------------------------------------

    def configuration(self) -> pd.DataFrame:
        frame = pd.DataFrame(
            [
                ("Python", platform.python_version()),
                ("pymc", pm.__version__),
                ("arviz", az.__version__),
                ("numpy", np.__version__),
                ("scipy", scipy.__version__),
                ("draws", self.draws),
                ("tune", self.tune),
                ("chains", self.chains),
                ("cores", self.cores if self.cores is not None else "PyMC default"),
                ("target_accept", self.target_accept),
                ("random_seed", self.random_seed),
            ],
            columns=["setting", "value"],
        )
        return self._show("probabilistic_configuration", frame)

    def load_data(self) -> pd.DataFrame:
        self.data = load_experiment_data(
            self.workbook_path,
            project_root=self.project_root,
            dry_matter_policy="recorded",
            include_estimated_quality=False,
        )
        return self._show("probabilistic_source_qa", self.data.qa)

    def source_provenance(self) -> pd.DataFrame:
        return self._show(
            "probabilistic_source_provenance",
            source_provenance_table(self._require_data()),
        )

    def source_audit(self) -> pd.DataFrame:
        return self._show(
            "probabilistic_source_audit",
            self._require_data().spec.source_audit,
        )

    def variable_lineage(self) -> pd.DataFrame:
        return self._show(
            "probabilistic_variable_lineage",
            self._require_data().variable_lineage,
        )

    def model_specification(self) -> pd.DataFrame:
        rows = [
            {
                "model": "yield",
                "component": "response",
                "specification": "Student-t",
                "parameter": f"nu={STUDENT_T_DF:g}",
                "scale": "standardized within sector",
            },
            {
                "model": "yield",
                "component": "intercept",
                "specification": "Normal",
                "parameter": "sd=1.5",
                "scale": "standardized",
            },
            {
                "model": "yield",
                "component": "M1-M5 average minus M0",
                "specification": "Normal",
                "parameter": "sd=2.0",
                "scale": "standardized",
            },
            {
                "model": "yield",
                "component": "orthonormal M1-M5 timing contrasts",
                "specification": "Normal(0, tau_timing)",
                "parameter": "tau_timing ~ HalfNormal(scale)",
                "scale": "standardized",
            },
            {
                "model": "yield",
                "component": "block contrasts",
                "specification": "Normal",
                "parameter": "sd=0.75",
                "scale": "standardized",
            },
            {
                "model": "longitudinal",
                "component": "response",
                "specification": "Student-t with plot random intercept",
                "parameter": f"nu={STUDENT_T_DF:g}",
                "scale": "standardized within sector/outcome",
            },
            {
                "model": "longitudinal",
                "component": "treatment x date coefficients",
                "specification": "Normal(0, tau_interaction)",
                "parameter": "tau_interaction ~ HalfNormal(0.5)",
                "scale": "standardized",
            },
            {
                "model": "all",
                "component": "centering and scaling",
                "specification": "empirical numerical transformation",
                "parameter": "observed mean and SD",
                "scale": "not a pre-data prior",
            },
        ]
        return self._show("probabilistic_model_specification", pd.DataFrame(rows))

    # ------------------------------------------------------------------
    # Yield model
    # ------------------------------------------------------------------

    def _yield_design(self, sector: str) -> YieldDesign:
        data = self._require_data()
        frame = data.harvest.loc[
            data.harvest["sector"].astype(str).eq(sector),
            ["sector", "block", "treatment", "clean_yield_kg_ha"],
        ].copy()
        frame = frame.assign(
            block=frame["block"].astype(str),
            treatment=frame["treatment"].astype(str),
        ).reset_index(drop=True)
        treatments = tuple(data.spec.treatments)
        blocks = tuple(sorted(frame["block"].unique()))
        treatment_index = pd.Categorical(
            frame["treatment"],
            categories=list(treatments),
            ordered=True,
        ).codes
        block_index = pd.Categorical(
            frame["block"],
            categories=list(blocks),
            ordered=True,
        ).codes
        timing_basis = helmert(5, full=False).T
        block_basis = helmert(len(blocks), full=False).T
        extra_n = (treatment_index > 0).astype(float)
        timing = np.zeros((len(frame), 4), dtype=float)
        fertilized = treatment_index > 0
        timing[fertilized] = timing_basis[treatment_index[fertilized] - 1]
        block = block_basis[block_index]
        group_timing = np.zeros((len(treatments), 4), dtype=float)
        group_timing[1:] = timing_basis
        y = frame["clean_yield_kg_ha"].to_numpy(float)
        center = float(y.mean())
        scale = float(y.std(ddof=1))
        if not np.isfinite(scale) or scale <= 0.0:
            raise ValueError(f"No se puede estandarizar rendimiento en {sector}.")
        return YieldDesign(
            frame=frame,
            center=center,
            scale=scale,
            extra_n=extra_n,
            timing=timing,
            block=block,
            group_timing=group_timing,
            treatments=treatments,
            blocks=blocks,
        )

    def conditional_prior_predictive(self, *, draws: int = 20000) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        data = self._require_data()
        for sector in data.spec.sectors:
            design = self._yield_design(sector)
            for specification, timing_scale in TIMING_PRIOR_SCALES.items():
                rng = np.random.default_rng(
                    _stable_seed(
                        sector,
                        specification,
                        "conditional_prior",
                        base=self.random_seed,
                    )
                )
                intercept = rng.normal(0.0, 1.5, draws)
                extra = rng.normal(0.0, 2.0, draws)
                tau = np.abs(rng.normal(0.0, timing_scale, draws))
                timing = rng.normal(0.0, tau[:, None], size=(draws, 4))
                group_z = intercept[:, None] + np.column_stack(
                    [
                        np.zeros(draws),
                        np.repeat(extra[:, None], 5, axis=1),
                    ]
                )
                group_z = group_z + timing @ design.group_timing.T
                group_means = design.center + design.scale * group_z
                sigma_z = np.abs(rng.normal(0.0, 1.0, draws))
                replicated = group_means + design.scale * sigma_z[
                    :, None
                ] * rng.standard_t(
                    STUDENT_T_DF,
                    size=group_means.shape,
                )
                spread = np.ptp(group_means[:, 1:], axis=1)
                rows.append(
                    {
                        "sector": sector,
                        "specification": specification,
                        "timing_prior_scale_z": timing_scale,
                        "draws": draws,
                        "observed_center_kg_ha": design.center,
                        "observed_scale_kg_ha": design.scale,
                        "conditional_on_observed_scaling": True,
                        "treatment_mean_lower_95": float(
                            np.quantile(group_means, 0.025)
                        ),
                        "treatment_mean_upper_95": float(
                            np.quantile(group_means, 0.975)
                        ),
                        "p_any_treatment_mean_below_zero": float(
                            np.mean(np.any(group_means < 0.0, axis=1))
                        ),
                        "p_replicated_yield_below_zero": float(
                            np.mean(replicated < 0.0)
                        ),
                        "p_replicated_yield_above_3000": float(
                            np.mean(replicated > 3000.0)
                        ),
                        "median_prior_range_m1_m5": float(np.median(spread)),
                        "range_upper_95_m1_m5": float(np.quantile(spread, 0.95)),
                    }
                )
        return self._show("conditional_prior_predictive_audit", pd.DataFrame(rows))

    def _sample_yield_model(
        self,
        *,
        sector: str,
        specification: str,
        timing_prior_scale: float,
    ) -> FittedModel:
        design = self._yield_design(sector)
        y_z = (
            design.frame["clean_yield_kg_ha"].to_numpy(float) - design.center
        ) / design.scale
        coords = {
            "observation": np.arange(len(design.frame)),
            "timing_contrast": [f"timing_{index + 1}" for index in range(4)],
            "block_contrast": [
                f"block_{index + 1}" for index in range(design.block.shape[1])
            ],
            "treatment": list(design.treatments),
        }
        with pm.Model(coords=coords):
            intercept = pm.Normal("intercept", 0.0, 1.5)
            extra_n = pm.Normal("extra_n", 0.0, 2.0)
            tau_timing = pm.HalfNormal("tau_timing", timing_prior_scale)
            timing_raw = pm.Normal(
                "timing_raw",
                0.0,
                1.0,
                dims="timing_contrast",
            )
            timing_coefficient = pm.Deterministic(
                "timing_coefficient",
                timing_raw * tau_timing,
                dims="timing_contrast",
            )
            block_coefficient = pm.Normal(
                "block_coefficient",
                0.0,
                0.75,
                dims="block_contrast",
            )
            sigma = pm.HalfNormal("sigma", 1.0)
            mu = (
                intercept
                + extra_n * design.extra_n
                + pt_api.dot(design.timing, timing_coefficient)
                + pt_api.dot(design.block, block_coefficient)
            )
            group_z = (
                intercept
                + extra_n * np.asarray([0.0, 1.0, 1.0, 1.0, 1.0, 1.0])
                + pt_api.dot(design.group_timing, timing_coefficient)
            )
            pm.Deterministic(
                "mean_yield",
                design.center + design.scale * group_z,
                dims="treatment",
            )
            pm.StudentT(
                "y_obs",
                nu=STUDENT_T_DF,
                mu=mu,
                sigma=sigma,
                observed=y_z,
                dims="observation",
            )
            inference = pm.sample(
                draws=self.draws,
                tune=self.tune,
                chains=self.chains,
                cores=self.cores,
                target_accept=self.target_accept,
                random_seed=_stable_seed(sector, specification, base=self.random_seed),
                return_inferencedata=True,
                idata_kwargs={"log_likelihood": True},
            )
            posterior_predictive = pm.sample_posterior_predictive(
                inference,
                var_names=["y_obs"],
                random_seed=_stable_seed(
                    sector,
                    specification,
                    "posterior_predictive",
                    base=self.random_seed,
                ),
                return_inferencedata=True,
            )
        inference.extend(posterior_predictive)
        model_id = f"yield_{sector.casefold()}_{specification}"
        return FittedModel(
            model_id=model_id,
            sector=sector,
            outcome="clean_yield_kg_ha",
            specification=specification,
            inference_data=inference,
            design=design,
        )

    def fit_yield_models(self) -> pd.DataFrame:
        data = self._require_data()
        rows: list[dict[str, object]] = []
        for sector in data.spec.sectors:
            for specification, scale in TIMING_PRIOR_SCALES.items():
                fitted = self._sample_yield_model(
                    sector=sector,
                    specification=specification,
                    timing_prior_scale=scale,
                )
                self.yield_models[fitted.model_id] = fitted
                rows.append(
                    {
                        "model_id": fitted.model_id,
                        "sector": sector,
                        "specification": specification,
                        "timing_prior_scale_z": scale,
                        "draws": self.draws,
                        "tune": self.tune,
                        "chains": self.chains,
                    }
                )
        return self._show("yield_model_runs", pd.DataFrame(rows))

    @staticmethod
    def _diagnostic_summary(fitted: FittedModel) -> dict[str, object]:
        inference = fitted.inference_data
        summary = az.summary(
            inference,
            var_names=[
                "intercept",
                "extra_n",
                "tau_timing",
                "timing_coefficient",
                "block_coefficient",
                "sigma",
            ],
            round_to=None,
        )
        divergences = int(np.asarray(inference.sample_stats["diverging"]).sum())
        return {
            "model_id": fitted.model_id,
            "sector": fitted.sector,
            "outcome": fitted.outcome,
            "specification": fitted.specification,
            "max_rhat": float(summary["r_hat"].max()),
            "min_ess_bulk": float(summary["ess_bulk"].min()),
            "min_ess_tail": float(summary["ess_tail"].min()),
            "divergences": divergences,
            "accepted": bool(
                summary["r_hat"].max() <= 1.01
                and summary["ess_bulk"].min() >= 400
                and divergences == 0
            ),
        }

    def yield_diagnostics(self) -> pd.DataFrame:
        if not self.yield_models:
            self.fit_yield_models()
        rows = [self._diagnostic_summary(model) for model in self.yield_models.values()]
        return self._show("yield_model_diagnostics", pd.DataFrame(rows))

    def _yield_summaries_for_model(
        self,
        fitted: FittedModel,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        means = _flatten_posterior(fitted.inference_data.posterior["mean_yield"])
        design = cast(YieldDesign, fitted.design)
        fertilized = means[:, 1:]
        spread = np.ptp(fertilized, axis=1)
        extra_n = fertilized.mean(axis=1) - means[:, 0]
        early_late = fertilized[:, :2].mean(axis=1) - fertilized[:, 3:5].mean(axis=1)
        m5_others = fertilized[:, 4] - fertilized[:, :4].mean(axis=1)
        best = np.argmax(fertilized, axis=1)
        worst = np.argmin(fertilized, axis=1)

        treatment_rows: list[dict[str, object]] = []
        for index, treatment in enumerate(design.treatments):
            treatment_rows.append(
                {
                    "sector": fitted.sector,
                    "specification": fitted.specification,
                    "treatment": treatment,
                    **_quantile_summary(means[:, index]),
                }
            )

        estimands = {
            "mean_M1_M5_minus_M0": extra_n,
            "mean_M1_M2_minus_mean_M4_M5": early_late,
            "M5_minus_mean_M1_M4": m5_others,
            "range_M1_M5": spread,
        }
        estimand_rows: list[dict[str, object]] = []
        for name, values in estimands.items():
            estimand_rows.append(
                {
                    "sector": fitted.sector,
                    "specification": fitted.specification,
                    "estimand": name,
                    **_quantile_summary(values),
                    "p_gt_0": float(np.mean(values > 0.0)),
                    "p_abs_gt_100": float(np.mean(np.abs(values) > 100.0)),
                }
            )

        rank_rows: list[dict[str, object]] = []
        for index, treatment in enumerate(design.treatments[1:]):
            rank_rows.append(
                {
                    "sector": fitted.sector,
                    "specification": fitted.specification,
                    "treatment": treatment,
                    "p_best": float(np.mean(best == index)),
                    "p_worst": float(np.mean(worst == index)),
                    "p_within_50_of_best": float(
                        np.mean(fertilized[:, index] >= fertilized.max(axis=1) - 50.0)
                    ),
                    "p_within_100_of_best": float(
                        np.mean(fertilized[:, index] >= fertilized.max(axis=1) - 100.0)
                    ),
                    "p_within_150_of_best": float(
                        np.mean(fertilized[:, index] >= fertilized.max(axis=1) - 150.0)
                    ),
                }
            )

        margin_rows: list[dict[str, object]] = []
        for margin in np.arange(0.0, 301.0, 5.0):
            margin_rows.append(
                {
                    "sector": fitted.sector,
                    "specification": fitted.specification,
                    "margin_kg_ha": margin,
                    "p_range_gt_margin": float(np.mean(spread > margin)),
                    "p_all_within_margin": float(np.mean(spread <= margin)),
                }
            )
        return (
            pd.DataFrame(treatment_rows),
            pd.DataFrame(estimand_rows),
            pd.DataFrame(rank_rows),
            pd.DataFrame(margin_rows),
        )

    def yield_posterior_summaries(self) -> pd.DataFrame:
        if not self.yield_models:
            self.fit_yield_models()
        treatment_tables: list[pd.DataFrame] = []
        estimand_tables: list[pd.DataFrame] = []
        rank_tables: list[pd.DataFrame] = []
        margin_tables: list[pd.DataFrame] = []
        for fitted in self.yield_models.values():
            treatment, estimand, rank, margin = self._yield_summaries_for_model(fitted)
            treatment_tables.append(treatment)
            estimand_tables.append(estimand)
            rank_tables.append(rank)
            margin_tables.append(margin)
        treatments = pd.concat(treatment_tables, ignore_index=True)
        estimands = pd.concat(estimand_tables, ignore_index=True)
        ranks = pd.concat(rank_tables, ignore_index=True)
        margins = pd.concat(margin_tables, ignore_index=True)
        self.tables["yield_posterior_estimands"] = estimands
        self.tables["yield_rank_probabilities"] = ranks
        self.tables["yield_margin_curves"] = margins
        self._show("yield_posterior_treatment_means", treatments)

        primary = treatments.loc[treatments["specification"].eq("primary")]
        data = self._require_data()
        treatment_order = list(data.spec.treatments)
        treatment_colors = dict(
            zip(
                treatment_order,
                self.palette[: len(treatment_order)],
                strict=True,
            )
        )
        rng = np.random.default_rng(self.random_seed)
        fig, axes = plt.subplots(
            1, len(data.spec.sectors), figsize=(12.2, 5.2), sharey=True
        )
        axes_array = np.atleast_1d(axes)
        for axis, sector in zip(axes_array, data.spec.sectors, strict=True):
            posterior = (
                primary.loc[primary["sector"].eq(sector)]
                .set_index("treatment")
                .reindex(treatment_order)
            )
            observed_sector = data.harvest.loc[
                data.harvest["sector"].astype(str).eq(sector)
            ]
            for index, treatment in enumerate(treatment_order):
                values = observed_sector.loc[
                    observed_sector["treatment"].astype(str).eq(treatment),
                    "clean_yield_kg_ha",
                ].to_numpy(float)
                jitter = rng.normal(0.0, 0.035, size=len(values))
                axis.scatter(
                    np.full(len(values), index) + jitter,
                    values,
                    color=treatment_colors[treatment],
                    alpha=0.45,
                    s=26,
                    linewidths=0,
                    zorder=2,
                )
                row = cast(Any, posterior.loc[treatment])
                axis.errorbar(
                    index,
                    row["posterior_mean"],
                    yerr=np.asarray(
                        [
                            [row["posterior_mean"] - row["lower_95"]],
                            [row["upper_95"] - row["posterior_mean"]],
                        ]
                    ),
                    color=treatment_colors[treatment],
                    marker="o",
                    linestyle="none",
                    markerfacecolor=(
                        "white" if treatment == "M0" else treatment_colors[treatment]
                    ),
                    markeredgecolor=treatment_colors[treatment],
                    markersize=MARKER_SIZE,
                    capsize=ERRORBAR_CAPSIZE,
                    elinewidth=INTERVAL_LINEWIDTH,
                    zorder=4,
                    label="Media posterior e IC 95 %" if index == 0 else None,
                )
            axis.set_xticks(np.arange(len(treatment_order)), treatment_order)
            axis.set_title(sector.upper())
            axis.set_xlabel("Tratamiento")
            axis.grid(axis="y", alpha=0.25)
        axes_array[0].set_ylabel("Rendimiento limpio (kg ha⁻¹)")
        handles, labels = axes_array[-1].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="upper center",
            ncol=2,
            bbox_to_anchor=(0.5, 0.83),
        )
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.15, top=0.70, wspace=0.12)
        self._save_figure(
            fig,
            "01_yield_observed_posterior",
            title="Rendimiento observado y estimación posterior corregida",
            subtitle=(
                "Puntos claros: parcelas observadas. Círculos y barras: media posterior "
                "e intervalo creíble del 95 % del modelo principal robusto."
            ),
        )
        return treatments

    def margin_sensitivity(self) -> pd.DataFrame:
        if "yield_margin_curves" not in self.tables:
            self.yield_posterior_summaries()
        margins = self.tables["yield_margin_curves"]
        fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.0), sharey=True)
        for axis, sector in zip(axes, self._require_data().spec.sectors, strict=True):
            sector_data = margins.loc[margins["sector"].eq(sector)]
            principal = sector_data.loc[sector_data["specification"].eq("primary")]
            axis.plot(
                principal["margin_kg_ha"],
                principal["p_range_gt_margin"],
                color=self.palette[3],
                linewidth=EMPHASIS_LINEWIDTH,
                zorder=3,
            )
            alternatives = sector_data.loc[sector_data["specification"].ne("primary")]
            for _, group in alternatives.groupby("specification", sort=False):
                axis.plot(
                    group["margin_kg_ha"],
                    group["p_range_gt_margin"],
                    color="0.48",
                    alpha=0.52,
                    linewidth=SECONDARY_LINEWIDTH,
                    zorder=2,
                )
            axis.axvline(
                100.0,
                color=self.palette[5],
                linestyle="--",
                linewidth=REFERENCE_LINEWIDTH,
            )
            axis.axhline(
                0.5,
                color=self.palette[5],
                linestyle=":",
                linewidth=REFERENCE_LINEWIDTH,
            )
            axis.set_title(sector.upper())
            axis.set_xlabel("Margen práctico δ (kg ha⁻¹)")
            axis.set_ylim(-0.02, 1.02)
            axis.grid(alpha=0.22)
        axes[0].set_ylabel("P(rango M1–M5 > δ | datos)")
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.15, top=0.70, wspace=0.12)
        self._save_figure(
            fig,
            "02_margin_prior_sensitivity",
            title="La conclusión depende del margen práctico y de la regularización",
            subtitle=(
                "Curva principal destacada; curvas grises: sensibilidades alternativas. "
                "Las guías marcan 100 kg ha⁻¹ y probabilidad 0,5; no declaran equivalencia."
            ),
        )
        return self._show("yield_margin_sensitivity", margins)

    def posterior_predictive_checks(self) -> pd.DataFrame:
        if not self.yield_models:
            self.fit_yield_models()
        rows: list[dict[str, object]] = []
        draws_rows: list[pd.DataFrame] = []
        for fitted in self.yield_models.values():
            if fitted.specification != "primary":
                continue
            design = cast(YieldDesign, fitted.design)
            posterior_predictive_z = _flatten_posterior(
                fitted.inference_data.posterior_predictive["y_obs"]
            )
            posterior_predictive = design.center + design.scale * posterior_predictive_z
            observed_p = _observed_rcbd_p(design.frame)
            p_values = _rcbd_anova_p_values(
                posterior_predictive,
                design.frame["treatment"].to_numpy(str),
                design.frame["block"].to_numpy(str),
            )
            mean_yield = _flatten_posterior(
                fitted.inference_data.posterior["mean_yield"]
            )
            latent_range = np.ptp(mean_yield[:, 1:], axis=1)
            count = min(len(p_values), len(latent_range))
            p_values = p_values[:count]
            latent_range = latent_range[:count]
            rows.append(
                {
                    "sector": fitted.sector,
                    "observed_p_m1_m5": observed_p,
                    "p_rep_anova_non_significant": float(np.mean(p_values > 0.05)),
                    "p_rep_anova_p_le_observed": float(np.mean(p_values <= observed_p)),
                    "p_latent_range_gt_100": float(np.mean(latent_range > 100.0)),
                    "p_non_significant_given_range_gt_100": float(
                        np.mean(p_values[latent_range > 100.0] > 0.05)
                        if np.any(latent_range > 100.0)
                        else np.nan
                    ),
                    "n_replications": count,
                }
            )
            draws_rows.append(
                pd.DataFrame(
                    {
                        "sector": fitted.sector,
                        "p_value_m1_m5": p_values,
                        "latent_range_m1_m5": latent_range,
                    }
                )
            )
        summary = pd.DataFrame(rows)
        draws = pd.concat(draws_rows, ignore_index=True)
        self.tables["yield_posterior_predictive_draws"] = draws
        self._show("yield_posterior_predictive_summary", summary)

        fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.0), sharey=True)
        for axis, sector in zip(axes, self._require_data().spec.sectors, strict=True):
            sector_draws = draws.loc[draws["sector"].eq(sector)]
            axis.hist(
                sector_draws["p_value_m1_m5"],
                bins=np.linspace(0.0, 1.0, 31),
                density=True,
                color=self.palette[0],
                alpha=0.75,
            )
            observed = float(
                summary.loc[summary["sector"].eq(sector), "observed_p_m1_m5"].iloc[0]
            )
            axis.axvline(
                0.05,
                color=self.palette[5],
                linestyle="--",
                linewidth=REFERENCE_LINEWIDTH,
                label="0,05",
            )
            axis.axvline(
                observed,
                color=self.palette[3],
                linestyle=":",
                linewidth=DATA_LINEWIDTH,
                label="p observado",
            )
            axis.set_title(sector.upper())
            axis.set_xlabel("p del ANOVA M1–M5 en un ensayo replicado")
            axis.grid(axis="y", alpha=0.18)
        axes[0].set_ylabel("Densidad")
        handles, labels = axes[-1].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.83),
            ncol=2,
        )
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.17, top=0.69, wspace=0.12)
        self._save_figure(
            fig,
            "03_posterior_predictive_anova",
            title="Qué produciría nuevamente el análisis convencional",
            subtitle=(
                "Distribución posterior predictiva del p del ANOVA M1–M5; el umbral "
                "0,05 y el p observado se recalculan desde el XLSX."
            ),
        )
        return summary

    def sector_pattern_comparison(self) -> pd.DataFrame:
        if not self.yield_models:
            self.fit_yield_models()
        primary = {
            fitted.sector: fitted
            for fitted in self.yield_models.values()
            if fitted.specification == "primary"
        }
        if set(primary) != set(self._require_data().spec.sectors):
            raise RuntimeError("Falta el modelo principal de algún sector.")
        draws_by_sector: dict[str, np.ndarray] = {}
        for sector, fitted in primary.items():
            means = _flatten_posterior(fitted.inference_data.posterior["mean_yield"])
            fertilized = means[:, 1:]
            draws_by_sector[sector] = fertilized[:, :2].mean(axis=1) - fertilized[
                :, 3:5
            ].mean(axis=1)
        sectors = list(self._require_data().spec.sectors)
        count = min(len(draws_by_sector[sector]) for sector in sectors)
        difference = (
            draws_by_sector[sectors[1]][:count] - draws_by_sector[sectors[0]][:count]
        )
        rows = [
            {
                "estimand": f"early_late_{sectors[1]}_minus_{sectors[0]}",
                **_quantile_summary(difference),
                "p_gt_0": float(np.mean(difference > 0.0)),
                "p_abs_gt_50": float(np.mean(np.abs(difference) > 50.0)),
                "p_abs_gt_100": float(np.mean(np.abs(difference) > 100.0)),
                "causal_interpretation": False,
                "reason": "one physical sector per hydric condition",
            }
        ]
        return self._show("probabilistic_sector_pattern_comparison", pd.DataFrame(rows))

    # ------------------------------------------------------------------
    # Longitudinal model
    # ------------------------------------------------------------------

    def _longitudinal_design(
        self,
        *,
        sector: str,
        outcome: str,
        response_scale: Literal["raw", "log"],
    ) -> LongitudinalDesign:
        data = self._require_data()
        treatments = tuple(value for value in data.spec.treatments if value != "M0")
        frame = (
            data.longitudinal.loc[
                data.longitudinal["sector"].astype(str).eq(sector)
                & data.longitudinal["treatment"].astype(str).isin(treatments),
                ["plot_id", "block", "treatment", "date_label", outcome],
            ]
            .dropna(subset=[outcome])
            .copy()
        )
        blocks = tuple(sorted(frame["block"].astype(str).unique()))
        date_levels = tuple(
            str(value) for value in frame["date_label"].drop_duplicates()
        )
        frame = frame.assign(
            block=pd.Categorical(
                frame["block"].astype(str), categories=list(blocks), ordered=True
            ),
            treatment=pd.Categorical(
                frame["treatment"].astype(str),
                categories=list(treatments),
                ordered=True,
            ),
            date_label=pd.Categorical(
                frame["date_label"].astype(str),
                categories=list(date_levels),
                ordered=True,
            ),
        ).reset_index(drop=True)
        response = frame[outcome].to_numpy(float)
        if response_scale == "log":
            if np.any(response <= 0.0):
                raise ValueError(f"{outcome} contiene valores no positivos.")
            transformed = np.log(response)
        else:
            transformed = response
        center = float(transformed.mean())
        scale = float(transformed.std(ddof=1))
        if not np.isfinite(scale) or scale <= 0.0:
            raise ValueError(
                f"No se puede estandarizar {outcome} en {sector} ({response_scale})."
            )
        frame["y_z"] = (transformed - center) / scale

        fixed_formula = "1 + C(block, Sum) + C(treatment, Sum) * C(date_label, Sum)"
        matrix = dmatrix(fixed_formula, frame, return_type="dataframe")
        names = list(matrix.columns)
        interaction_mask = np.asarray([":" in name for name in names], dtype=bool)
        main_mask = ~interaction_mask
        x_main = np.asarray(matrix.loc[:, main_mask], dtype=float)
        x_interaction = np.asarray(matrix.loc[:, interaction_mask], dtype=float)
        main_names = tuple(np.asarray(names)[main_mask].tolist())
        interaction_names = tuple(np.asarray(names)[interaction_mask].tolist())

        plots = tuple(sorted(frame["plot_id"].astype(str).unique()))
        plot_index = pd.Categorical(
            frame["plot_id"].astype(str),
            categories=list(plots),
            ordered=True,
        ).codes
        prediction_grid = pd.DataFrame(
            [
                {"treatment": treatment, "date_label": date_label, "block": block}
                for treatment in treatments
                for date_label in date_levels
                for block in blocks
            ]
        )
        prediction_grid["block"] = pd.Categorical(
            prediction_grid["block"], categories=list(blocks), ordered=True
        )
        prediction_grid["treatment"] = pd.Categorical(
            prediction_grid["treatment"], categories=list(treatments), ordered=True
        )
        prediction_grid["date_label"] = pd.Categorical(
            prediction_grid["date_label"], categories=list(date_levels), ordered=True
        )
        prediction_matrix = np.asarray(
            build_design_matrices(
                [matrix.design_info],
                prediction_grid,
                return_type="dataframe",
            )[0],
            dtype=float,
        )
        group_count = len(blocks)
        prediction_main_rows: list[np.ndarray] = []
        prediction_interaction_rows: list[np.ndarray] = []
        compact_grid_rows: list[dict[str, str]] = []
        for treatment in treatments:
            for date_label in date_levels:
                mask = (
                    prediction_grid["treatment"].astype(str).eq(treatment)
                    & prediction_grid["date_label"].astype(str).eq(date_label)
                ).to_numpy()
                if int(mask.sum()) != group_count:
                    raise AssertionError("Prediction grid is not balanced over blocks.")
                averaged = prediction_matrix[mask].mean(axis=0)
                prediction_main_rows.append(averaged[main_mask])
                prediction_interaction_rows.append(averaged[interaction_mask])
                compact_grid_rows.append(
                    {"treatment": treatment, "date_label": date_label}
                )
        return LongitudinalDesign(
            frame=frame,
            center=center,
            scale=scale,
            response_scale=response_scale,
            fixed_formula=fixed_formula,
            design_info=matrix.design_info,
            x_main=x_main,
            x_interaction=x_interaction,
            main_names=main_names,
            interaction_names=interaction_names,
            plot_index=plot_index,
            plots=plots,
            prediction_grid=pd.DataFrame(compact_grid_rows),
            prediction_main=np.vstack(prediction_main_rows),
            prediction_interaction=np.vstack(prediction_interaction_rows),
            treatments=treatments,
            date_levels=date_levels,
            blocks=blocks,
        )

    def _sample_longitudinal_model(
        self,
        *,
        sector: str,
        outcome: str,
        response_scale: Literal["raw", "log"],
    ) -> FittedModel:
        design = self._longitudinal_design(
            sector=sector,
            outcome=outcome,
            response_scale=response_scale,
        )
        main_prior_sd = np.asarray(
            [
                1.5 if name == "Intercept" else 0.75 if "block" in name else 1.0
                for name in design.main_names
            ],
            dtype=float,
        )
        coords = {
            "observation": np.arange(len(design.frame)),
            "main_coefficient": list(design.main_names),
            "interaction_coefficient": list(design.interaction_names),
            "plot": list(design.plots),
            "prediction_cell": np.arange(len(design.prediction_grid)),
        }
        with pm.Model(coords=coords):
            beta_main = pm.Normal(
                "beta_main",
                0.0,
                main_prior_sd,
                dims="main_coefficient",
            )
            tau_interaction = pm.HalfNormal("tau_interaction", 0.5)
            interaction_raw = pm.Normal(
                "interaction_raw",
                0.0,
                1.0,
                dims="interaction_coefficient",
            )
            beta_interaction = pm.Deterministic(
                "beta_interaction",
                interaction_raw * tau_interaction,
                dims="interaction_coefficient",
            )
            plot_sd = pm.HalfNormal("plot_sd", 0.75)
            plot_raw = pm.Normal("plot_raw", 0.0, 1.0, dims="plot")
            plot_effect = pm.Deterministic(
                "plot_effect",
                plot_raw * plot_sd,
                dims="plot",
            )
            sigma = pm.HalfNormal("sigma", 1.0)
            fixed_mu = pt_api.dot(design.x_main, beta_main) + pt_api.dot(
                design.x_interaction, beta_interaction
            )
            mu = fixed_mu + plot_effect[design.plot_index]
            pm.StudentT(
                "y_obs",
                nu=STUDENT_T_DF,
                mu=mu,
                sigma=sigma,
                observed=design.frame["y_z"].to_numpy(float),
                dims="observation",
            )
            prediction_z = pt_api.dot(design.prediction_main, beta_main) + pt_api.dot(
                design.prediction_interaction, beta_interaction
            )
            transformed = design.center + design.scale * prediction_z
            prediction = (
                pt_api.exp(transformed) if response_scale == "log" else transformed
            )
            pm.Deterministic(
                "typical_value",
                prediction,
                dims="prediction_cell",
            )
            inference = pm.sample(
                draws=self.draws,
                tune=self.tune,
                chains=self.chains,
                cores=self.cores,
                target_accept=self.target_accept,
                random_seed=_stable_seed(
                    sector,
                    outcome,
                    response_scale,
                    base=self.random_seed,
                ),
                return_inferencedata=True,
                idata_kwargs={"log_likelihood": True},
            )
            posterior_predictive = pm.sample_posterior_predictive(
                inference,
                var_names=["y_obs"],
                random_seed=_stable_seed(
                    sector,
                    outcome,
                    response_scale,
                    "posterior_predictive",
                    base=self.random_seed,
                ),
                return_inferencedata=True,
            )
        inference.extend(posterior_predictive)
        model_id = f"longitudinal_{sector.casefold()}_{outcome}_{response_scale}"
        return FittedModel(
            model_id=model_id,
            sector=sector,
            outcome=outcome,
            specification=response_scale,
            inference_data=inference,
            design=design,
        )

    def fit_longitudinal_models(self) -> pd.DataFrame:
        data = self._require_data()
        specifications: list[tuple[str, Literal["raw", "log"]]] = [
            ("biomass_kg_ha", "raw"),
            ("biomass_kg_ha", "log"),
            ("n_pct", "raw"),
        ]
        rows: list[dict[str, object]] = []
        for sector in data.spec.sectors:
            for outcome, response_scale in specifications:
                fitted = self._sample_longitudinal_model(
                    sector=sector,
                    outcome=outcome,
                    response_scale=response_scale,
                )
                self.longitudinal_models[fitted.model_id] = fitted
                rows.append(
                    {
                        "model_id": fitted.model_id,
                        "sector": sector,
                        "outcome": outcome,
                        "response_scale": response_scale,
                        "draws": self.draws,
                        "tune": self.tune,
                        "chains": self.chains,
                    }
                )
        return self._show("longitudinal_model_runs", pd.DataFrame(rows))

    @staticmethod
    def _longitudinal_diagnostic_summary(fitted: FittedModel) -> dict[str, object]:
        summary = az.summary(
            fitted.inference_data,
            var_names=[
                "beta_main",
                "tau_interaction",
                "beta_interaction",
                "plot_sd",
                "sigma",
            ],
            round_to=None,
        )
        divergences = int(
            np.asarray(fitted.inference_data.sample_stats["diverging"]).sum()
        )
        return {
            "model_id": fitted.model_id,
            "sector": fitted.sector,
            "outcome": fitted.outcome,
            "response_scale": fitted.specification,
            "max_rhat": float(summary["r_hat"].max()),
            "min_ess_bulk": float(summary["ess_bulk"].min()),
            "min_ess_tail": float(summary["ess_tail"].min()),
            "divergences": divergences,
            "accepted": bool(
                summary["r_hat"].max() <= 1.01
                and summary["ess_bulk"].min() >= 400
                and divergences == 0
            ),
        }

    def longitudinal_diagnostics(self) -> pd.DataFrame:
        if not self.longitudinal_models:
            self.fit_longitudinal_models()
        rows = [
            self._longitudinal_diagnostic_summary(model)
            for model in self.longitudinal_models.values()
        ]
        return self._show("longitudinal_model_diagnostics", pd.DataFrame(rows))

    def _longitudinal_summary_for_model(
        self,
        fitted: FittedModel,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        design = cast(LongitudinalDesign, fitted.design)
        values = _flatten_posterior(fitted.inference_data.posterior["typical_value"])
        trajectory_rows: list[dict[str, object]] = []
        for index, (_, row) in enumerate(
            design.prediction_grid.reset_index(drop=True).iterrows()
        ):
            trajectory_rows.append(
                {
                    "sector": fitted.sector,
                    "outcome": fitted.outcome,
                    "response_scale": fitted.specification,
                    "treatment": row["treatment"],
                    "date_label": row["date_label"],
                    "estimand": (
                        "geometric_typical_value"
                        if fitted.specification == "log"
                        else "arithmetic_mean_location"
                    ),
                    **_quantile_summary(values[:, index]),
                }
            )

        cell_index = {
            (str(row.treatment), str(row.date_label)): index
            for index, row in enumerate(design.prediction_grid.itertuples(index=False))
        }
        contrast_rows: list[dict[str, object]] = []
        early_late_by_date: dict[str, np.ndarray] = {}
        for date_label in design.date_levels:
            early = 0.5 * (
                values[:, cell_index[("M1", date_label)]]
                + values[:, cell_index[("M2", date_label)]]
            )
            late = 0.5 * (
                values[:, cell_index[("M4", date_label)]]
                + values[:, cell_index[("M5", date_label)]]
            )
            difference = early - late
            early_late_by_date[date_label] = difference
            contrast_rows.append(
                {
                    "sector": fitted.sector,
                    "outcome": fitted.outcome,
                    "response_scale": fitted.specification,
                    "estimand": "mean_M1_M2_minus_mean_M4_M5",
                    "date_label": date_label,
                    **_quantile_summary(difference),
                    "p_gt_0": float(np.mean(difference > 0.0)),
                }
            )
        first = early_late_by_date[design.date_levels[0]]
        last = early_late_by_date[design.date_levels[-1]]
        change = last - first
        contrast_rows.append(
            {
                "sector": fitted.sector,
                "outcome": fitted.outcome,
                "response_scale": fitted.specification,
                "estimand": "change_in_early_late_first_to_last",
                "date_label": f"{design.date_levels[-1]} minus {design.date_levels[0]}",
                **_quantile_summary(change),
                "p_gt_0": float(np.mean(change > 0.0)),
            }
        )
        return pd.DataFrame(trajectory_rows), pd.DataFrame(contrast_rows)

    def longitudinal_summaries(self) -> pd.DataFrame:
        if not self.longitudinal_models:
            self.fit_longitudinal_models()
        trajectories: list[pd.DataFrame] = []
        contrasts: list[pd.DataFrame] = []
        for fitted in self.longitudinal_models.values():
            trajectory, contrast = self._longitudinal_summary_for_model(fitted)
            trajectories.append(trajectory)
            contrasts.append(contrast)
        trajectory_table = pd.concat(trajectories, ignore_index=True)
        contrast_table = pd.concat(contrasts, ignore_index=True)
        self.tables["longitudinal_posterior_contrasts"] = contrast_table
        self._show("longitudinal_posterior_trajectories", trajectory_table)

        data = self._require_data()
        for outcome, response_scale in [
            ("biomass_kg_ha", "raw"),
            ("n_pct", "raw"),
        ]:
            subset = trajectory_table.loc[
                trajectory_table["outcome"].eq(outcome)
                & trajectory_table["response_scale"].eq(response_scale)
            ]
            fig, axes = plt.subplots(
                1, len(data.spec.sectors), figsize=(12.2, 5.2), sharey=True
            )
            axes_array = np.atleast_1d(axes)
            colors = dict(
                zip([f"M{i}" for i in range(1, 6)], self.palette[1:6], strict=True)
            )
            for axis, sector in zip(axes_array, data.spec.sectors, strict=True):
                sector_data = subset.loc[subset["sector"].eq(sector)]
                date_levels = sector_data["date_label"].drop_duplicates().tolist()
                date_centers = np.arange(len(date_levels), dtype=float)
                positions = dict(zip(date_levels, date_centers, strict=True))
                treatment_offsets = dict(
                    zip(
                        colors,
                        np.linspace(-0.28, 0.28, len(colors)),
                        strict=True,
                    )
                )
                for treatment, color in colors.items():
                    treatment_data = sector_data.loc[
                        sector_data["treatment"].eq(treatment)
                    ]
                    x = [
                        positions[label] + treatment_offsets[treatment]
                        for label in treatment_data["date_label"]
                    ]
                    axis.errorbar(
                        x,
                        treatment_data["median"],
                        yerr=np.vstack(
                            [
                                treatment_data["median"] - treatment_data["lower_95"],
                                treatment_data["upper_95"] - treatment_data["median"],
                            ]
                        ),
                        marker="o",
                        linestyle="none",
                        markersize=MARKER_SIZE,
                        capsize=ERRORBAR_CAPSIZE,
                        elinewidth=INTERVAL_LINEWIDTH,
                        label=treatment,
                        color=color,
                    )
                treatment_positions = [
                    center + treatment_offsets[treatment]
                    for center in date_centers
                    for treatment in colors
                ]
                axis.set_xticks(
                    treatment_positions,
                    list(colors) * len(date_centers),
                    minor=True,
                )
                axis.tick_params(axis="x", which="minor", pad=5, length=0)
                axis.set_xticks(date_centers, date_levels)
                axis.tick_params(axis="x", which="major", pad=25, length=0)
                axis.set_title(sector.upper())
                axis.set_xlabel("")
                axis.grid(alpha=0.22)
            y_label = (
                "Biomasa posterior (kg MS ha⁻¹)"
                if outcome == "biomass_kg_ha"
                else "Concentración posterior de N (%)"
            )
            axes_array[0].set_ylabel(y_label)
            fig.subplots_adjust(
                left=0.08,
                right=0.98,
                bottom=0.23,
                top=0.72,
                wspace=0.12,
            )
            self._save_figure(
                fig,
                f"longitudinal_{outcome}_{response_scale}",
                title=(
                    "Biomasa posterior en las tres fechas de muestreo"
                    if outcome == "biomass_kg_ha"
                    else "Concentración de N posterior en las tres fechas de muestreo"
                ),
                subtitle=(
                    "Mediana posterior e intervalo creíble del 95 % para M1–M5; "
                    "bloque fijo e intercepto aleatorio por parcela."
                ),
                note=(
                    "Las fechas son categorías equidistantes; los tratamientos se agrupan "
                    "dentro de cada fecha y los puntos no se conectan. M0 no forma parte del modelo."
                ),
            )
        return trajectory_table

    # ------------------------------------------------------------------
    # Reconstruction null and synthesis
    # ------------------------------------------------------------------

    @staticmethod
    def _reconstruction_null_table(
        harvest: pd.DataFrame,
        *,
        permutations: int,
        seed: int,
    ) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        rows: list[dict[str, object]] = []
        for sector in harvest["sector"].astype(str).drop_duplicates():
            sector_frame = harvest.loc[harvest["sector"].astype(str).eq(sector)].copy()
            for pattern, include_m0 in (("all_m0_m5", True), ("timing_m1_m5", False)):
                subset = (
                    sector_frame
                    if include_m0
                    else sector_frame.loc[
                        sector_frame["treatment"].astype(str).ne("M0")
                    ]
                )
                observed = float(
                    stats.pearsonr(
                        subset["panicle_density_m2"],
                        subset["estimated_seeds_per_panicle"],
                    ).statistic
                )
                panicle_density = subset["panicle_density_m2"].to_numpy(float)
                panicle_count = subset["panicle_count"].to_numpy(float)
                estimated_seed_count = subset["estimated_seed_count"].to_numpy(float)
                null = np.empty(permutations)
                for index in range(permutations):
                    reconstructed = (
                        rng.permutation(estimated_seed_count) / panicle_count
                    )
                    null[index] = float(
                        stats.pearsonr(panicle_density, reconstructed).statistic
                    )
                median = float(np.median(null))
                rows.append(
                    {
                        "sector": sector,
                        "pattern": pattern,
                        "n": len(subset),
                        "permutations": permutations,
                        "observed_correlation": observed,
                        "null_median": median,
                        "null_lower_95": float(np.quantile(null, 0.025)),
                        "null_upper_95": float(np.quantile(null, 0.975)),
                        "observed_percentile_in_null": float(np.mean(null <= observed)),
                        "two_sided_tail_around_null_median": float(
                            (
                                1
                                + np.sum(
                                    np.abs(null - median) >= abs(observed - median)
                                )
                            )
                            / (permutations + 1)
                        ),
                    }
                )
        return pd.DataFrame(rows)

    def reconstruction_null(self, *, permutations: int = 10000) -> pd.DataFrame:
        table = self._reconstruction_null_table(
            self._require_data().harvest,
            permutations=permutations,
            seed=_stable_seed("reconstruction_null", base=self.random_seed),
        )
        self._show("reconstruction_null", table)
        plot_table = table.iloc[::-1].reset_index(drop=True)
        fig, axis = plt.subplots(figsize=(10.4, 5.2))
        y = np.arange(len(plot_table))
        null_y = y + 0.09
        observed_y = y - 0.09
        for index, (_, row) in enumerate(plot_table.iterrows()):
            plot_horizontal_interval(
                axis,
                estimate=float(row["null_median"]),
                lower=float(row["null_lower_95"]),
                upper=float(row["null_upper_95"]),
                y=float(null_y[index]),
                color=self.palette[1],
                label=(
                    "Nulo de reconstrucción: mediana e IC 95 %" if index == 0 else None
                ),
            )
        axis.scatter(
            plot_table["observed_correlation"],
            observed_y,
            marker="o",
            s=62,
            facecolors="white",
            edgecolors="0.20",
            linewidths=DATA_LINEWIDTH,
            zorder=4,
            label="Correlación observada",
        )
        axis.axvline(0.0, linewidth=REFERENCE_LINEWIDTH)
        axis.set_yticks(
            y,
            plot_table["sector"].astype(str)
            + " — "
            + plot_table["pattern"].map(
                {"all_m0_m5": "M0–M5", "timing_m1_m5": "M1–M5"}
            ),
        )
        axis.set_xlabel("Correlación panojas–semillas estimadas por panoja")
        axis.grid(axis="x", alpha=0.22)
        axis.legend(loc="lower right", bbox_to_anchor=(1.0, 1.02), ncol=2)
        fig.subplots_adjust(left=0.30, right=0.98, bottom=0.17, top=0.72)
        self._save_figure(
            fig,
            "reconstruction_null",
            title="Asociación observada frente al nulo de reconstrucción",
            subtitle=(
                "Círculos llenos y barras: mediana e intervalo nulo del 95 %. "
                "Círculos vacíos: correlación observada."
            ),
            note="El nulo de cuatro filas se vuelve a generar desde las mediciones actuales del XLSX.",
        )
        return table

    def synthesis(self) -> pd.DataFrame:
        yield_diagnostics = self.tables.get("yield_model_diagnostics")
        if yield_diagnostics is None:
            yield_diagnostics = self.yield_diagnostics()
        longitudinal_diagnostics = self.tables.get("longitudinal_model_diagnostics")
        if longitudinal_diagnostics is None:
            longitudinal_diagnostics = self.longitudinal_diagnostics()
        if "yield_posterior_estimands" not in self.tables:
            self.yield_posterior_summaries()
        if "longitudinal_posterior_contrasts" not in self.tables:
            self.longitudinal_summaries()
        if "reconstruction_null" not in self.tables:
            self.reconstruction_null()

        accepted_yield = set(
            yield_diagnostics.loc[
                yield_diagnostics["specification"].eq("primary")
                & yield_diagnostics["accepted"],
                "sector",
            ]
        )
        accepted_longitudinal = {
            (record.sector, record.outcome, record.response_scale)
            for record in longitudinal_diagnostics.loc[
                longitudinal_diagnostics["accepted"]
            ].itertuples(index=False)
        }
        rows: list[dict[str, object]] = []

        yield_estimands = self.tables["yield_posterior_estimands"]
        for record in yield_estimands.loc[
            yield_estimands["specification"].eq("primary")
        ].itertuples(index=False):
            rows.append(
                {
                    "domain": "yield",
                    "sector": record.sector,
                    "estimand": record.estimand,
                    "median": record.median,
                    "lower_95": record.lower_95,
                    "upper_95": record.upper_95,
                    "probability": record.p_gt_0,
                    "usable": record.sector in accepted_yield,
                    "interpretation_rule": (
                        "do_not_claim_equivalence_without_prespecified_margin"
                        if record.estimand == "range_M1_M5"
                        else "report_posterior_interval_and_probability"
                    ),
                }
            )

        longitudinal = self.tables["longitudinal_posterior_contrasts"]
        for record in longitudinal.itertuples(index=False):
            key = (record.sector, record.outcome, record.response_scale)
            rows.append(
                {
                    "domain": "trajectory",
                    "sector": record.sector,
                    "estimand": (
                        f"{record.outcome}|{record.response_scale}|"
                        f"{record.estimand}|{record.date_label}"
                    ),
                    "median": record.median,
                    "lower_95": record.lower_95,
                    "upper_95": record.upper_95,
                    "probability": record.p_gt_0,
                    "usable": key in accepted_longitudinal,
                    "interpretation_rule": (
                        "date_specific_posterior_contrast_on_declared_scale"
                        if record.estimand == "mean_M1_M2_minus_mean_M4_M5"
                        else "posterior_change_in_targeted_contrast_not_global_interaction_test"
                    ),
                }
            )

        reconstruction = self.tables["reconstruction_null"]
        for record in reconstruction.itertuples(index=False):
            rows.append(
                {
                    "domain": "yield_components",
                    "sector": record.sector,
                    "estimand": f"reconstruction_null_{record.pattern}",
                    "median": record.observed_correlation,
                    "lower_95": record.null_lower_95,
                    "upper_95": record.null_upper_95,
                    "probability": record.two_sided_tail_around_null_median,
                    "usable": True,
                    "interpretation_rule": (
                        "not_independent_evidence_of_compensation_when_inside_null"
                    ),
                }
            )
        rows.append(
            {
                "domain": "scope",
                "sector": "both_observed_sectors",
                "estimand": "hydric_condition",
                "median": np.nan,
                "lower_95": np.nan,
                "upper_95": np.nan,
                "probability": np.nan,
                "usable": True,
                "interpretation_rule": (
                    "descriptive_not_causal_one_sector_per_condition"
                ),
            }
        )
        return self._show("probabilistic_synthesis", pd.DataFrame(rows))

    def export_artifacts(self) -> pd.DataFrame:
        if not self.export_results:
            return self._show(
                "probabilistic_export_manifest",
                pd.DataFrame(
                    [{"status": "export_disabled", "directory": str(self.results_dir)}]
                ),
            )
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        self.posteriors_dir.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, object]] = []
        for name, table in sorted(self.tables.items()):
            path = self.tables_dir / f"{name}.csv"
            table.to_csv(path, index=False)
            rows.append(
                {
                    "artifact_type": "table",
                    "name": name,
                    "path": str(path),
                    "rows": len(table),
                }
            )
        for fitted in [*self.yield_models.values(), *self.longitudinal_models.values()]:
            path = self.posteriors_dir / f"{fitted.model_id}.nc"
            fitted.inference_data.to_netcdf(path)
            rows.append(
                {
                    "artifact_type": "posterior",
                    "name": fitted.model_id,
                    "path": str(path),
                    "rows": np.nan,
                }
            )
        if self.figure_metadata:
            path = self.results_dir / "figure_manifest.json"
            path.write_text(
                json.dumps(self.figure_metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            rows.append(
                {
                    "artifact_type": "figure_manifest",
                    "name": "figure_manifest",
                    "path": str(path),
                    "rows": len(self.figure_metadata),
                }
            )
        return self._show("probabilistic_export_manifest", pd.DataFrame(rows))

    def run_all(self) -> None:
        self.configuration()
        self.load_data()
        self.source_provenance()
        self.source_audit()
        self.variable_lineage()
        self.model_specification()
        self.conditional_prior_predictive()
        self.fit_yield_models()
        self.yield_diagnostics()
        self.yield_posterior_summaries()
        self.margin_sensitivity()
        self.posterior_predictive_checks()
        self.sector_pattern_comparison()
        self.fit_longitudinal_models()
        self.longitudinal_diagnostics()
        self.longitudinal_summaries()
        self.reconstruction_null()
        self.synthesis()
        self.export_artifacts()


def run_all() -> ProbabilisticAnnex:
    """Compatibility entry point used by the command-line wrapper."""

    annex = ProbabilisticAnnex(figure_profile="standalone")
    annex.run_all()
    return annex


def run_all_cli() -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    run_all()


if __name__ == "__main__":
    run_all_cli()
