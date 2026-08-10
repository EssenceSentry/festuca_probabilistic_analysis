"""CSV-first classical and longitudinal analysis for the Festuca thesis.

The notebook-facing API keeps presentation cells short.  Every observed value is
loaded from the canonical CSV bundle; equations and inferential choices live in code and
notebook markdown.  Generated tables are ordinary pandas DataFrames and can be
exported as CSV after review.
"""

from __future__ import annotations

# Scientific libraries still expose incomplete typing information.
# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
import json
import math
import platform
import zlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Final, Literal, cast

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import patsy
import scipy
import statsmodels
import statsmodels.api as sm
import statsmodels.formula.api as smf
from IPython.display import display
from scipy import stats
from statsmodels.stats.libqsturng import psturng, qsturng

from festuca_analysis.plotting import (
    ERRORBAR_CAPSIZE,
    INTERVAL_LINEWIDTH,
    MARKER_SIZE,
    REFERENCE_LINEWIDTH,
    FigureExporter,
    apply_plot_theme,
    plot_horizontal_interval,
)
from festuca_analysis.source_data import (
    DryMatterPolicy,
    ExperimentData,
    load_experiment_data,
    source_provenance_table,
)
from festuca_analysis.statistics import (
    benjamini_hochberg,
    fit_mixedlm_best,
    likelihood_ratio,
    parametric_bootstrap_lrt,
    rcbd_missing_cell_estimate,
)

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_DIR: Final = PROJECT_ROOT / "festuca_thesis_analysis_outputs"
DEFAULT_FIGURES_DIR: Final = PROJECT_ROOT / "festuca_thesis_figures"
PRIMARY_NNI_COEFFICIENT: Final = 3.93
PRIMARY_NNI_EXPONENT: Final = -0.42
SENSITIVITY_NNI_COEFFICIENT: Final = 4.8
SENSITIVITY_NNI_EXPONENT: Final = -0.32
LONGITUDINAL_FIGURE_STEMS: Final = (
    "figura_01_calendario_experimental_desde_csv",
    "figura_02_agua_desde_csv",
    "trayectorias_observadas_biomass_kg_ha",
    "trayectorias_observadas_n_pct",
    "figura_03_rendimiento_observado",
    "figura_componentes_nulo_reconstruccion",
    "diagnostico_residuos_rendimiento_secano",
    "diagnostico_residuos_rendimiento_riego",
    "modelo_mixto_biomass_kg_ha",
    "modelo_mixto_n_pct",
)
SPANISH_MONTH_ABBREVIATIONS: Final = {
    1: "ene",
    2: "feb",
    3: "mar",
    4: "abr",
    5: "may",
    6: "jun",
    7: "jul",
    8: "ago",
    9: "sep",
    10: "oct",
    11: "nov",
    12: "dic",
}


def _stable_seed(*parts: object, base: int) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return base + zlib.crc32(payload) % 1_000_000


def _as_float(value: object) -> float:
    return float(cast(Any, value))


def _as_timestamp(value: object) -> pd.Timestamp:
    return pd.Timestamp(cast(Any, value))


def _student_t_critical(count: object) -> float:
    count_value = int(cast(Any, count))
    return float(stats.t.ppf(0.975, count_value - 1)) if count_value > 1 else np.nan


def _short_spanish_date(value: pd.Timestamp) -> str:
    return f"{value.day:02d} {SPANISH_MONTH_ABBREVIATIONS[value.month]}"


def _experimental_n_step_table(
    schedule: pd.DataFrame,
    treatments: Sequence[str],
    *,
    view_start: pd.Timestamp,
    view_end: pd.Timestamp,
) -> pd.DataFrame:
    """Build the canonical experimental-N step geometry used by the schedule."""
    rows: list[dict[str, object]] = []
    for treatment in treatments:
        treatment_schedule = schedule.loc[
            schedule["treatment"].astype(str).eq(treatment)
        ]
        if treatment_schedule.empty:
            raise ValueError(f"Falta el calendario experimental de {treatment}.")
        record = treatment_schedule.iloc[0]
        applications = sorted(
            pd.Timestamp(value)
            for value in (
                record["first_application"],
                record["second_application"],
            )
            if pd.notna(value)
        )
        dates = [view_start, *applications, view_end]
        cumulative = [
            0.0,
            *[100.0 * index for index in range(1, len(applications) + 1)],
            100.0 * len(applications),
        ]
        for date, value in zip(dates, cumulative, strict=True):
            rows.append(
                {
                    "treatment": treatment,
                    "date": date,
                    "cumulative_experimental_n_kg_ha": value,
                }
            )
    return pd.DataFrame(rows)


LONGITUDINAL_STEPS: Final = (
    "configuration",
    "load_data",
    "source_provenance",
    "source_audit",
    "variable_lineage",
    "flagged_dry_matter",
    "baseline_summary",
    "schedule",
    "water_inputs",
    "longitudinal_anova",
    "observed_trajectories",
    "final_outcomes",
    "dry_matter_sensitivity",
    "yield_analysis",
    "yield_overview",
    "yield_contrasts",
    "yield_components",
    "component_correlations",
    "seed_weight_precision",
    "model_diagnostics",
    "primary_residual_diagnostics",
    "missing_n_sensitivity",
    "joint_sector_analysis",
    "correlation_audit",
    "mixed_models",
    "mixed_estimates",
    "september_sensitivity",
    "figure_manifest",
    "automatic_summary",
    "export_artifacts",
)


@dataclass(frozen=True)
class RCBDResult:
    """One randomized-complete-block analysis."""

    fit: Any
    anova: pd.DataFrame
    marginal_means: pd.DataFrame
    pairwise: pd.DataFrame
    global_p: float
    question: str
    sector: str
    outcome: str
    date: pd.Timestamp | None


@dataclass(frozen=True)
class MixedModelResult:
    """Nested mixed-model fits and one interaction test."""

    sector: str
    outcome: str
    scale: str
    frame: pd.DataFrame
    additive_fit: Any
    interaction_fit: Any
    summary: dict[str, object]


class LongitudinalNotebook:
    """Stateful report object used by ``festuca_estudio_longitudinal.ipynb``."""

    def __init__(
        self,
        *,
        project_root: Path | None = None,
        data_dir: Path | str | None = None,
        dry_matter_policy: DryMatterPolicy = "recorded",
        bootstrap_replicates: int = 199,
        random_seed: int = 20260807,
        alpha: float = 0.05,
        export_results: bool = True,
        export_figures: bool = True,
        figure_profile: Literal["standalone", "thesis"] = "thesis",
        print_figure_json: bool = False,
    ) -> None:
        self.project_root = (project_root or PROJECT_ROOT).resolve()
        self.data_dir = data_dir
        self.dry_matter_policy = dry_matter_policy
        self.bootstrap_replicates = bootstrap_replicates
        self.random_seed = random_seed
        self.alpha = alpha
        self.export_results = export_results
        self.export_figures = export_figures
        self.results_dir = self.project_root / DEFAULT_RESULTS_DIR.name
        self.figures_dir = self.project_root / DEFAULT_FIGURES_DIR.name
        self.figure_profile = figure_profile
        self.print_figure_json = print_figure_json
        self.data: ExperimentData | None = None
        self.tables: dict[str, pd.DataFrame] = {}
        self.figure_metadata: list[dict[str, object]] = []
        self.rcbd_results: dict[str, RCBDResult] = {}
        self.mixed_results: dict[str, MixedModelResult] = {}
        self.palette = apply_plot_theme()
        self.figure_exporter = FigureExporter(
            self.figures_dir,
            profile=figure_profile,
            dpi=300,
            print_json=print_figure_json,
        )
        pd.set_option("display.max_columns", 100)
        pd.set_option("display.width", 180)

    # ------------------------------------------------------------------
    # Presentation and state helpers
    # ------------------------------------------------------------------

    def _require_data(self) -> ExperimentData:
        if self.data is None:
            raise RuntimeError("Ejecute analysis.load_data() antes de esta sección.")
        return self.data

    def _show(
        self, name: str, frame: pd.DataFrame, *, copy: bool = True
    ) -> pd.DataFrame:
        table = frame.copy() if copy else frame
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

    @staticmethod
    def _display_date(value: pd.Timestamp | None) -> str:
        return "final" if value is None else pd.Timestamp(value).date().isoformat()

    @staticmethod
    def _date_level(frame: pd.DataFrame, value: object) -> str:
        date = _as_timestamp(value)
        labels = frame.loc[
            pd.to_datetime(frame["date"].astype(str)).eq(date), "date_label"
        ]
        if labels.empty:
            return date.date().isoformat()
        return str(labels.iloc[0])

    # ------------------------------------------------------------------
    # Source and reconstruction
    # ------------------------------------------------------------------

    def configuration(self) -> pd.DataFrame:
        frame = pd.DataFrame(
            [
                ("Python", platform.python_version()),
                ("pandas", pd.__version__),
                ("numpy", np.__version__),
                ("scipy", scipy.__version__),
                ("statsmodels", statsmodels.__version__),
                ("dry_matter_policy", self.dry_matter_policy),
                ("bootstrap_replicates", self.bootstrap_replicates),
                ("random_seed", self.random_seed),
                ("alpha", self.alpha),
                (
                    "NNI primary curve",
                    f"{PRIMARY_NNI_COEFFICIENT} * W^{PRIMARY_NNI_EXPONENT}",
                ),
                (
                    "NNI sensitivity curve",
                    f"{SENSITIVITY_NNI_COEFFICIENT} * W^{SENSITIVITY_NNI_EXPONENT}",
                ),
            ],
            columns=["setting", "value"],
        )
        return self._show("configuration", frame)

    def load_data(self) -> pd.DataFrame:
        self.data = load_experiment_data(
            self.data_dir,
            project_root=self.project_root,
            dry_matter_policy=cast(DryMatterPolicy, self.dry_matter_policy),
            include_estimated_quality=False,
            nni_primary_coefficient=PRIMARY_NNI_COEFFICIENT,
            nni_primary_exponent=PRIMARY_NNI_EXPONENT,
            nni_sensitivity_coefficient=SENSITIVITY_NNI_COEFFICIENT,
            nni_sensitivity_exponent=SENSITIVITY_NNI_EXPONENT,
        )
        return self._show("qa", self.data.qa)

    def source_provenance(self) -> pd.DataFrame:
        return self._show(
            "source_provenance",
            source_provenance_table(self._require_data()),
        )

    def source_audit(self) -> pd.DataFrame:
        return self._show("source_audit", self._require_data().spec.source_audit)

    def variable_lineage(self) -> pd.DataFrame:
        return self._show("variable_lineage", self._require_data().variable_lineage)

    def flagged_dry_matter(self) -> pd.DataFrame:
        data = self._require_data()
        columns = [
            "sample_id",
            "sector",
            "block",
            "treatment",
            "date",
            "dm_pct_recorded",
            "dm_ratio_pct",
            "dm_abs_difference_pp",
            "dm_relative_difference",
            "biomass_kg_ha_materialized",
            "biomass_kg_ha",
            "kgms_materialized_status",
        ]
        flagged = data.longitudinal.loc[data.longitudinal["dm_issue"], columns]
        return self._show("dry_matter_records_to_verify", flagged)

    def baseline_summary(self) -> pd.DataFrame:
        data = self._require_data()
        biomass = (
            data.baseline_biomass.groupby("sector", observed=True)["biomass_kg_ha"]
            .agg(["count", "mean", "std", "min", "max"])
            .reset_index()
            .rename(
                columns={
                    "count": "n_biomass",
                    "mean": "biomass_mean_kg_ha",
                    "std": "biomass_sd_kg_ha",
                    "min": "biomass_min_kg_ha",
                    "max": "biomass_max_kg_ha",
                }
            )
        )
        tillers = (
            data.baseline_tillers.groupby("sector", observed=True)["tillers_m2"]
            .agg(["count", "mean", "std", "min", "max"])
            .reset_index()
            .rename(
                columns={
                    "count": "n_tillers",
                    "mean": "tillers_mean_m2",
                    "std": "tillers_sd_m2",
                    "min": "tillers_min_m2",
                    "max": "tillers_max_m2",
                }
            )
        )
        return self._show(
            "baseline_summary",
            biomass.merge(tillers, on="sector", how="outer", validate="one_to_one"),
        )

    def schedule(self) -> pd.DataFrame:
        data = self._require_data()
        schedule = data.spec.schedule.copy()
        self._show("experimental_n_schedule", schedule)
        self._show("recorded_management", data.spec.management)

        treatment_order = list(data.spec.treatments)
        application_values = schedule[
            ["first_application", "second_application"]
        ].stack()
        sampling_dates = pd.to_datetime(data.longitudinal["date"].astype(str))
        view_start = min(
            _as_timestamp(application_values.min()),
            _as_timestamp(sampling_dates.min()),
        ) - timedelta(days=14)
        view_end = max(
            _as_timestamp(application_values.max()),
            _as_timestamp(sampling_dates.max()),
        ) + timedelta(days=14)
        step_table = _experimental_n_step_table(
            schedule,
            treatment_order,
            view_start=view_start,
            view_end=view_end,
        )

        fig, axis = plt.subplots(figsize=(11.5, 6.1))
        y_positions = np.arange(len(treatment_order))[::-1]
        colors = dict(
            zip(treatment_order, self.palette[: len(treatment_order)], strict=True)
        )
        for y, treatment in zip(y_positions, treatment_order, strict=True):
            treatment_steps = step_table.loc[
                step_table["treatment"].astype(str).eq(treatment)
            ]
            cumulative = treatment_steps["cumulative_experimental_n_kg_ha"].to_numpy(
                float
            )
            row_curve = y - 0.27 + 0.54 * cumulative / 200.0
            cast(Any, axis).step(
                treatment_steps["date"],
                row_curve,
                where="post",
                color=colors[treatment],
                linewidth=2.4,
                zorder=3,
            )
            terminal_value = int(cumulative[-1])
            cast(Any, axis).text(
                view_end,
                row_curve[-1],
                f" {terminal_value}",
                color=colors[treatment],
                ha="left",
                va="center",
                fontsize=8.5,
                fontweight="bold",
            )
            treatment_schedule = schedule.loc[
                schedule["treatment"].astype(str).eq(treatment)
            ].iloc[0]
            for number, application_date in enumerate(
                (
                    treatment_schedule["first_application"],
                    treatment_schedule["second_application"],
                ),
                start=1,
            ):
                if pd.isna(application_date):
                    continue
                date = pd.Timestamp(application_date)
                cast(Any, axis).scatter(
                    [date],
                    [y - 0.27 + 0.54 * number / 2.0],
                    s=36,
                    color=colors[treatment],
                    edgecolor="white",
                    linewidth=0.7,
                    zorder=4,
                )
                axis.annotate(
                    _short_spanish_date(date),
                    (date, y - 0.27 + 0.54 * number / 2.0),
                    xytext=(0, 7),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=7.5,
                    color=colors[treatment],
                )
        sample_dates = sorted(pd.Timestamp(value) for value in sampling_dates.unique())
        for sample_date in sample_dates:
            cast(Any, axis).axvline(
                sample_date,
                color=self.palette[5],
                linestyle="--",
                linewidth=REFERENCE_LINEWIDTH,
                alpha=0.60,
                zorder=1,
            )
        for boundary in np.arange(len(treatment_order) - 1) + 0.5:
            axis.axhline(
                boundary,
                color=mpl.rcParams["grid.color"],
                linewidth=0.6,
                alpha=0.55,
                zorder=0,
            )
        axis.set_yticks(y_positions, treatment_order)
        axis.set_ylim(-0.6, len(treatment_order) - 0.4)
        cast(Any, axis).set_xlim(view_start, view_end + timedelta(days=10))
        month_ticks = pd.date_range(
            view_start.replace(day=1),
            view_end + timedelta(days=10),
            freq="MS",
        )
        cast(Any, axis).set_xticks(
            month_ticks,
            [SPANISH_MONTH_ABBREVIATIONS[date.month].title() for date in month_ticks],
        )
        axis.set_xlabel("Fecha")
        axis.set_ylabel("Tratamiento · altura del escalón = N experimental acumulado")
        axis.grid(axis="x", alpha=0.20)
        axis.grid(axis="y", visible=False)
        fig.subplots_adjust(left=0.12, right=0.95, bottom=0.15, top=0.75)
        self._save_figure(
            fig,
            "figura_01_calendario_experimental_desde_csv",
            title="Calendario y N experimental acumulado desde los datos canónicos",
            subtitle="M0 permanece en 0; M1–M5 avanzan de 0 a 100 y 200 kg N ha⁻¹.",
            note=(
                "Solo se representa el N experimental respaldado por el libro. Las líneas "
                "punteadas indican fechas de muestreo; el manejo común permanece en su tabla."
            ),
        )
        return schedule

    def water_inputs(self) -> pd.DataFrame:
        data = self._require_data()
        water = data.spec.water_monthly.copy()
        totals = data.spec.water_period_totals.copy()
        self._show("water_monthly", water)
        self._show("water_period_totals", totals)

        included = water.loc[water["included_in_study_months"]].copy()
        included["irrigated_total_mm"] = (
            included["rainfall_mm"] + included["supplemental_irrigation_mm"]
        )
        positions = np.arange(len(included), dtype=float)
        bar_width = 0.28
        bar_offset = 0.18
        rainfall_color = self.palette[0]
        irrigation_color = self.palette[6]
        fig, axis = plt.subplots(figsize=(10.8, 5.7))
        axis.bar(
            positions - bar_offset,
            included["rainfall_mm"],
            width=bar_width,
            color=rainfall_color,
            label="Precipitación (ambos sectores)",
        )
        axis.bar(
            positions + bar_offset,
            included["supplemental_irrigation_mm"],
            width=bar_width,
            bottom=included["rainfall_mm"],
            color=irrigation_color,
            label="Riego suplementario",
        )
        for position, rainfall, irrigation, total in zip(
            positions,
            included["rainfall_mm"].to_numpy(float),
            included["supplemental_irrigation_mm"].to_numpy(float),
            included["irrigated_total_mm"].to_numpy(float),
            strict=True,
        ):
            if irrigation > 0:
                axis.text(
                    position - bar_offset,
                    rainfall + 3,
                    f"{rainfall:.0f}",
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                    color=rainfall_color,
                )
                axis.text(
                    position + bar_offset,
                    rainfall + irrigation / 2.0,
                    f"+{irrigation:.0f}",
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color="white",
                )
            axis.text(
                position,
                total + 5,
                f"{total:.0f}",
                ha="center",
                va="bottom",
                fontsize=9.5,
            )
        rainfall_total = float(included["rainfall_mm"].sum())
        irrigation_total = float(included["supplemental_irrigation_mm"].sum())
        axis.text(
            0.02,
            0.96,
            (
                f"Secano: {rainfall_total:.0f} mm\n"
                f"Riego: {rainfall_total + irrigation_total:.0f} mm "
                f"({irrigation_total:.0f} mm adicionales)"
            ),
            transform=axis.transAxes,
            ha="left",
            va="top",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": mpl.rcParams["axes.edgecolor"],
                "alpha": 0.90,
            },
        )
        axis.set_xticks(positions, included["month_label"])
        axis.set_ylabel("Agua aportada (mm mes⁻¹)")
        axis.set_xlabel("Mes del período experimental")
        axis.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
        fig.subplots_adjust(left=0.09, right=0.98, bottom=0.25, top=0.80)
        self._save_figure(
            fig,
            "figura_02_agua_desde_csv",
            title="Entradas brutas de agua registradas en los datos canónicos",
            subtitle="Precipitación y riego suplementario por mes incluido en el período experimental.",
            note=(
                "Estas entradas no son un balance hídrico ni una estimación del agua consumida. "
                "La comparación entre sectores sigue siendo descriptiva."
            ),
        )
        return water

    # ------------------------------------------------------------------
    # RCBD utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _question_treatments(data: ExperimentData, question: str) -> list[str]:
        if question == "timing_m1_m5":
            return [value for value in data.spec.treatments if value != "M0"]
        if question == "all_m0_m5":
            return list(data.spec.treatments)
        raise ValueError(f"Pregunta desconocida: {question}")

    @staticmethod
    def _design_matrix(fit: Any, grid: pd.DataFrame) -> np.ndarray:
        return np.asarray(
            patsy.build_design_matrices(
                [fit.model.data.design_info],
                grid,
                return_type="dataframe",
            )[0],
            dtype=float,
        )

    def _marginal_mean_vectors(
        self,
        fit: Any,
        *,
        treatments: Sequence[str],
        blocks: Sequence[str],
    ) -> dict[str, np.ndarray]:
        vectors: dict[str, np.ndarray] = {}
        for treatment in treatments:
            grid = pd.DataFrame(
                {
                    "treatment": [treatment] * len(blocks),
                    "block": list(blocks),
                }
            )
            vectors[treatment] = self._design_matrix(fit, grid).mean(axis=0)
        return vectors

    @staticmethod
    def _linear_estimate(
        fit: Any,
        vector: np.ndarray,
    ) -> tuple[float, float, float, float, float]:
        beta = np.asarray(fit.params, dtype=float)
        covariance = np.asarray(fit.cov_params(), dtype=float)
        estimate = float(vector @ beta)
        variance = float(vector @ covariance @ vector)
        standard_error = math.sqrt(max(variance, 0.0))
        df = float(fit.df_resid)
        critical = float(stats.t.ppf(0.975, df))
        if standard_error == 0.0:
            statistic = np.inf if estimate != 0.0 else 0.0
            p_value = 0.0 if estimate != 0.0 else 1.0
        else:
            statistic = estimate / standard_error
            p_value = float(2.0 * stats.t.sf(abs(statistic), df))
        return (
            estimate,
            standard_error,
            estimate - critical * standard_error,
            estimate + critical * standard_error,
            p_value,
        )

    def _fit_rcbd(
        self,
        frame: pd.DataFrame,
        *,
        outcome: str,
        sector: str,
        date: pd.Timestamp | None,
        question: str,
    ) -> RCBDResult:
        data = self._require_data()
        treatments = self._question_treatments(data, question)
        subset = frame.loc[
            frame["sector"].astype(str).eq(sector)
            & frame["treatment"].astype(str).isin(treatments),
            ["block", "treatment", outcome],
        ].dropna(subset=[outcome])
        if subset.empty:
            raise ValueError(
                f"Sin observaciones para {sector}, {outcome}, {question}, {date}."
            )
        subset = subset.copy()
        subset["block"] = subset["block"].astype(str)
        subset["treatment"] = pd.Categorical(
            subset["treatment"].astype(str),
            categories=treatments,
            ordered=True,
        )
        fit = smf.ols(f"{outcome} ~ C(treatment) + C(block)", data=subset).fit()
        anova = sm.stats.anova_lm(fit, typ=2)
        treatment_row = next(
            name for name in anova.index if str(name).startswith("C(treatment)")
        )
        global_p = _as_float(anova.loc[treatment_row, "PR(>F)"])
        blocks = sorted(subset["block"].unique().tolist())
        vectors = self._marginal_mean_vectors(
            fit,
            treatments=treatments,
            blocks=blocks,
        )
        mean_rows: list[dict[str, object]] = []
        for treatment in treatments:
            estimate, se, low, high, _ = self._linear_estimate(fit, vectors[treatment])
            mean_rows.append(
                {
                    "sector": sector,
                    "date": date,
                    "outcome": outcome,
                    "question": question,
                    "treatment": treatment,
                    "estimate": estimate,
                    "standard_error": se,
                    "ci_low": low,
                    "ci_high": high,
                    "n": int(subset["treatment"].astype(str).eq(treatment).sum()),
                }
            )
        marginal_means = pd.DataFrame(mean_rows)

        pairwise_rows: list[dict[str, object]] = []
        treatment_count = len(treatments)
        tukey_critical = float(qsturng(1.0 - self.alpha, treatment_count, fit.df_resid))
        covariance = np.asarray(fit.cov_params(), dtype=float)
        beta = np.asarray(fit.params, dtype=float)
        for left_index, left in enumerate(treatments):
            for right in treatments[left_index + 1 :]:
                vector = vectors[left] - vectors[right]
                estimate = float(vector @ beta)
                variance = float(vector @ covariance @ vector)
                se_difference = math.sqrt(max(variance, 0.0))
                if se_difference == 0.0:
                    q_statistic = np.inf if estimate != 0.0 else 0.0
                else:
                    q_statistic = abs(estimate) * math.sqrt(2.0) / se_difference
                p_value = float(
                    np.asarray(
                        psturng(q_statistic, treatment_count, fit.df_resid)
                    ).reshape(-1)[0]
                )
                half_width = tukey_critical * se_difference / math.sqrt(2.0)
                pairwise_rows.append(
                    {
                        "sector": sector,
                        "date": date,
                        "outcome": outcome,
                        "question": question,
                        "left": left,
                        "right": right,
                        "difference": estimate,
                        "ci_low_tukey": estimate - half_width,
                        "ci_high_tukey": estimate + half_width,
                        "p_tukey": p_value,
                        "global_treatment_p": global_p,
                        "display_as_confirmatory": bool(global_p < self.alpha),
                    }
                )
        pairwise = pd.DataFrame(pairwise_rows)
        result = RCBDResult(
            fit=fit,
            anova=anova,
            marginal_means=marginal_means,
            pairwise=pairwise,
            global_p=global_p,
            question=question,
            sector=sector,
            outcome=outcome,
            date=date,
        )
        key = f"{sector}|{self._display_date(date)}|{outcome}|{question}"
        self.rcbd_results[key] = result
        return result

    def _planned_extra_n_contrast(
        self,
        frame: pd.DataFrame,
        *,
        outcome: str,
        sector: str,
        date: pd.Timestamp | None,
    ) -> dict[str, object]:
        data = self._require_data()
        result = self._fit_rcbd(
            frame,
            outcome=outcome,
            sector=sector,
            date=date,
            question="all_m0_m5",
        )
        treatments = list(data.spec.treatments)
        blocks = list(data.spec.blocks)
        vectors = self._marginal_mean_vectors(
            result.fit,
            treatments=treatments,
            blocks=blocks,
        )
        fertilized = [treatment for treatment in treatments if treatment != "M0"]
        vector = (
            np.mean([vectors[treatment] for treatment in fertilized], axis=0)
            - vectors["M0"]
        )
        estimate, se, low, high, p_value = self._linear_estimate(result.fit, vector)
        return {
            "sector": sector,
            "date": date,
            "outcome": outcome,
            "contrast": "mean_M1_M5_minus_M0",
            "estimate": estimate,
            "standard_error": se,
            "ci_low": low,
            "ci_high": high,
            "p_value": p_value,
        }

    # ------------------------------------------------------------------
    # Date-specific and final analyses
    # ------------------------------------------------------------------

    def longitudinal_anova(self) -> pd.DataFrame:
        data = self._require_data()
        outcomes = [
            ("biomass_kg_ha", "secondary"),
            ("n_pct", "secondary"),
            ("q_kg_n_ha", "supporting_derived"),
            ("nni_primary", "supporting_derived"),
        ]
        rows: list[dict[str, object]] = []
        pairwise_rows: list[pd.DataFrame] = []
        means_rows: list[pd.DataFrame] = []
        dates = [
            pd.Timestamp(value) for value in data.longitudinal["date"].cat.categories
        ]
        for sector in data.spec.sectors:
            for date in dates:
                date_frame = data.longitudinal.loc[
                    pd.to_datetime(data.longitudinal["date"].astype(str)).eq(date)
                ]
                for outcome, hierarchy in outcomes:
                    for question in ("timing_m1_m5", "all_m0_m5"):
                        result = self._fit_rcbd(
                            date_frame,
                            outcome=outcome,
                            sector=sector,
                            date=date,
                            question=question,
                        )
                        treatment_row = next(
                            name
                            for name in result.anova.index
                            if str(name).startswith("C(treatment)")
                        )
                        rows.append(
                            {
                                "hierarchy": hierarchy,
                                "sector": sector,
                                "date": date,
                                "outcome": outcome,
                                "question": question,
                                "n": int(result.fit.nobs),
                                "df_treatment": _as_float(
                                    result.anova.loc[treatment_row, "df"]
                                ),
                                "f_statistic": _as_float(
                                    result.anova.loc[treatment_row, "F"]
                                ),
                                "p_raw": result.global_p,
                            }
                        )
                        means_rows.append(result.marginal_means)
                        pairwise_rows.append(result.pairwise)
        summary = pd.DataFrame(rows)
        summary["family"] = (
            summary["hierarchy"].astype(str) + "|" + summary["question"].astype(str)
        )
        summary["p_fdr"] = np.nan
        for indices in summary.groupby("family").groups.values():
            index_list = list(indices)
            summary.loc[index_list, "p_fdr"] = benjamini_hochberg(
                summary.loc[index_list, "p_raw"].to_numpy(float)
            )
        summary["decision_fdr"] = np.where(
            summary["p_fdr"] < self.alpha, "detected", "not_detected"
        )
        self.tables["anova_by_date_marginal_means"] = pd.concat(
            means_rows, ignore_index=True
        )
        self.tables["anova_by_date_pairwise_tukey"] = pd.concat(
            pairwise_rows, ignore_index=True
        )
        return self._show("anova_by_date", summary)

    def observed_trajectories(self) -> pd.DataFrame:
        data = self._require_data()
        outcomes = ["biomass_kg_ha", "n_pct", "q_kg_n_ha", "nni_primary"]
        rows: list[pd.DataFrame] = []
        for outcome in outcomes:
            summary = (
                data.longitudinal.groupby(
                    ["sector", "treatment", "date", "date_label"],
                    observed=True,
                )[outcome]
                .agg(["count", "mean", "std"])
                .reset_index()
            )
            summary["standard_error"] = summary["std"] / np.sqrt(summary["count"])
            critical = summary["count"].map(_student_t_critical)
            summary["ci_low"] = summary["mean"] - critical * summary["standard_error"]
            summary["ci_high"] = summary["mean"] + critical * summary["standard_error"]
            summary["outcome"] = outcome
            rows.append(summary)
        trajectories = pd.concat(rows, ignore_index=True)
        self._show("observed_trajectories", trajectories)

        labels = {
            "biomass_kg_ha": "Biomasa (kg MS ha⁻¹)",
            "n_pct": "N (%)",
        }
        treatment_colors = dict(
            zip(
                data.spec.treatments,
                self.palette[: len(data.spec.treatments)],
                strict=True,
            )
        )
        for outcome, ylabel in labels.items():
            subset = trajectories.loc[trajectories["outcome"].eq(outcome)]
            fig, axes = plt.subplots(
                1, len(data.spec.sectors), figsize=(12.2, 5.3), sharey=True
            )
            axes_array = np.atleast_1d(axes)
            for axis, sector in zip(axes_array, data.spec.sectors, strict=True):
                sector_data = subset.loc[subset["sector"].astype(str).eq(sector)]
                date_table = (
                    sector_data[["date", "date_label"]]
                    .drop_duplicates()
                    .sort_values("date")
                )
                date_levels = date_table["date_label"].astype(str).tolist()
                date_centers = np.arange(len(date_levels), dtype=float)
                positions = dict(zip(date_levels, date_centers, strict=True))
                treatment_offsets = dict(
                    zip(
                        data.spec.treatments,
                        np.linspace(-0.31, 0.31, len(data.spec.treatments)),
                        strict=True,
                    )
                )
                for treatment in data.spec.treatments:
                    treatment_data = sector_data.loc[
                        sector_data["treatment"].astype(str).eq(treatment)
                    ].sort_values("date")
                    x = [
                        positions[str(label)] + treatment_offsets[treatment]
                        for label in treatment_data["date_label"]
                    ]
                    axis.errorbar(
                        x,
                        treatment_data["mean"],
                        yerr=np.vstack(
                            [
                                treatment_data["mean"] - treatment_data["ci_low"],
                                treatment_data["ci_high"] - treatment_data["mean"],
                            ]
                        ),
                        marker="o",
                        markerfacecolor=(
                            "white"
                            if treatment == "M0"
                            else treatment_colors[treatment]
                        ),
                        markeredgecolor=treatment_colors[treatment],
                        markersize=MARKER_SIZE,
                        linestyle="none",
                        capsize=ERRORBAR_CAPSIZE,
                        elinewidth=INTERVAL_LINEWIDTH,
                        label=treatment,
                        color=treatment_colors[treatment],
                    )
                treatment_positions = [
                    center + treatment_offsets[treatment]
                    for center in date_centers
                    for treatment in data.spec.treatments
                ]
                axis.set_xticks(
                    treatment_positions,
                    list(data.spec.treatments) * len(date_centers),
                    minor=True,
                )
                axis.tick_params(axis="x", which="minor", pad=5, length=0)
                axis.set_xticks(date_centers, date_levels)
                axis.tick_params(axis="x", which="major", pad=25, length=0)
                axis.set_title(sector.upper())
                axis.set_xlabel("")
            axes_array[0].set_ylabel(ylabel)
            fig.subplots_adjust(
                left=0.08,
                right=0.98,
                bottom=0.23,
                top=0.69,
                wspace=0.10,
            )
            self._save_figure(
                fig,
                f"trayectorias_observadas_{outcome}",
                title=f"Trayectorias observadas: {ylabel}",
                subtitle="Media e intervalo t del 95 % por tratamiento, fecha y sector.",
                note=(
                    "Fechas equidistantes en orden cronológico; los puntos no se conectan. "
                    "M0 no recibió N experimental adicional; M1–M5 recibieron igual dosis total."
                ),
            )
        return trajectories

    def final_outcomes(self) -> pd.DataFrame:
        data = self._require_data()
        outcome_metadata = pd.DataFrame(
            [
                (
                    "clean_yield_kg_ha",
                    "primary",
                    "primitive-derived",
                    "Rendimiento limpio",
                ),
                (
                    "dirty_yield_kg_ha",
                    "supporting",
                    "primitive-derived",
                    "Rendimiento sin limpiar",
                ),
                (
                    "panicle_density_m2",
                    "supporting",
                    "primitive-derived",
                    "Densidad de panojas",
                ),
                (
                    "w1000_g",
                    "supporting",
                    "technical-replicate-derived",
                    "Peso de mil semillas",
                ),
                (
                    "estimated_seeds_per_panicle",
                    "supporting_derived",
                    "reconstructed",
                    "Semillas estimadas por panoja",
                ),
                (
                    "cleaning_loss_pct",
                    "supporting_derived",
                    "deterministic",
                    "Merma de limpieza",
                ),
                (
                    "harvest_index_pct",
                    "supporting_derived",
                    "deterministic",
                    "Índice de cosecha",
                ),
                (
                    "agronomic_efficiency",
                    "descriptive_derived",
                    "deterministic",
                    "Eficiencia agronómica",
                ),
                (
                    "apparent_water_productivity",
                    "descriptive_derived",
                    "deterministic",
                    "Productividad aparente del agua",
                ),
            ],
            columns=["outcome", "hierarchy", "lineage", "label"],
        )
        self._show("final_outcome_hierarchy", outcome_metadata)
        primitive_columns = [
            "sample_id",
            "sector",
            "block",
            "treatment",
            "panicle_count",
            "dirty_mass_g",
            "clean_mass_g",
            "w100_1_g",
            "w100_2_g",
            "w100_3_g",
        ]
        return self._show(
            "harvest_primitive_measurements", data.harvest[primitive_columns]
        )

    def dry_matter_sensitivity(self) -> pd.DataFrame:
        policies: tuple[DryMatterPolicy, ...] = ("recorded", "ratio", "exclude")
        rows: list[dict[str, object]] = []
        for policy in policies:
            policy_data = load_experiment_data(
                self.data_dir,
                project_root=self.project_root,
                dry_matter_policy=policy,
                include_estimated_quality=False,
                nni_primary_coefficient=PRIMARY_NNI_COEFFICIENT,
                nni_primary_exponent=PRIMARY_NNI_EXPONENT,
                nni_sensitivity_coefficient=SENSITIVITY_NNI_COEFFICIENT,
                nni_sensitivity_exponent=SENSITIVITY_NNI_EXPONENT,
            )
            final_date = max(
                pd.Timestamp(value)
                for value in policy_data.longitudinal["date"].cat.categories
            )
            final_frame = policy_data.longitudinal.loc[
                pd.to_datetime(policy_data.longitudinal["date"].astype(str)).eq(
                    final_date
                )
            ]
            for sector in policy_data.spec.sectors:
                subset = final_frame.loc[
                    final_frame["sector"].astype(str).eq(sector)
                    & final_frame["treatment"]
                    .astype(str)
                    .isin(
                        [
                            value
                            for value in policy_data.spec.treatments
                            if value != "M0"
                        ]
                    )
                ].dropna(subset=["biomass_kg_ha"])
                fit = smf.ols(
                    "biomass_kg_ha ~ C(treatment) + C(block)",
                    data=subset.assign(
                        treatment=subset["treatment"].astype(str),
                        block=subset["block"].astype(str),
                    ),
                ).fit()
                anova = sm.stats.anova_lm(fit, typ=2)
                treatment_row = next(
                    name for name in anova.index if str(name).startswith("C(treatment)")
                )
                treatment_means = subset.groupby("treatment", observed=True)[
                    "biomass_kg_ha"
                ].mean()
                harvest_index = policy_data.harvest.loc[
                    policy_data.harvest["sector"].astype(str).eq(sector)
                    & policy_data.harvest["treatment"].astype(str).ne("M0")
                ].dropna(subset=["harvest_index_pct"])
                hi_fit = smf.ols(
                    "harvest_index_pct ~ C(treatment) + C(block)",
                    data=harvest_index.assign(
                        treatment=harvest_index["treatment"].astype(str),
                        block=harvest_index["block"].astype(str),
                    ),
                ).fit()
                hi_anova = sm.stats.anova_lm(hi_fit, typ=2)
                hi_treatment_row = next(
                    name
                    for name in hi_anova.index
                    if str(name).startswith("C(treatment)")
                )
                rows.append(
                    {
                        "policy": policy,
                        "sector": sector,
                        "final_date": final_date,
                        "n_biomass": len(subset),
                        "biomass_timing_p": _as_float(
                            anova.loc[treatment_row, "PR(>F)"]
                        ),
                        "biomass_observed_treatment_mean_min": float(
                            treatment_means.min()
                        ),
                        "biomass_observed_treatment_mean_max": float(
                            treatment_means.max()
                        ),
                        "harvest_index_timing_p": _as_float(
                            hi_anova.loc[hi_treatment_row, "PR(>F)"]
                        ),
                    }
                )
        return self._show("dry_matter_sensitivity", pd.DataFrame(rows))

    def _final_rcbd_bundle(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        data = self._require_data()
        outcomes = [
            ("clean_yield_kg_ha", "primary"),
            ("dirty_yield_kg_ha", "supporting"),
            ("panicle_density_m2", "supporting"),
            ("w1000_g", "supporting"),
            ("estimated_seeds_per_panicle", "supporting_derived"),
            ("cleaning_loss_pct", "supporting_derived"),
            ("harvest_index_pct", "supporting_derived"),
        ]
        rows: list[dict[str, object]] = []
        means: list[pd.DataFrame] = []
        pairwise: list[pd.DataFrame] = []
        for sector in data.spec.sectors:
            for outcome, hierarchy in outcomes:
                for question in ("timing_m1_m5", "all_m0_m5"):
                    result = self._fit_rcbd(
                        data.harvest,
                        outcome=outcome,
                        sector=sector,
                        date=None,
                        question=question,
                    )
                    treatment_row = next(
                        name
                        for name in result.anova.index
                        if str(name).startswith("C(treatment)")
                    )
                    rows.append(
                        {
                            "hierarchy": hierarchy,
                            "sector": sector,
                            "outcome": outcome,
                            "question": question,
                            "n": int(result.fit.nobs),
                            "f_statistic": _as_float(
                                result.anova.loc[treatment_row, "F"]
                            ),
                            "p_raw": result.global_p,
                        }
                    )
                    means.append(result.marginal_means)
                    pairwise.append(result.pairwise)
        summary = pd.DataFrame(rows)
        summary["family"] = (
            summary["hierarchy"].astype(str) + "|" + summary["question"].astype(str)
        )
        summary["p_fdr"] = np.nan
        for indices in summary.groupby("family").groups.values():
            index_list = list(indices)
            summary.loc[index_list, "p_fdr"] = benjamini_hochberg(
                summary.loc[index_list, "p_raw"].to_numpy(float)
            )
        return (
            summary,
            pd.concat(means, ignore_index=True),
            pd.concat(pairwise, ignore_index=True),
        )

    def yield_analysis(self) -> pd.DataFrame:
        summary, means, pairwise = self._final_rcbd_bundle()
        self.tables["final_outcome_marginal_means"] = means
        self.tables["final_outcome_pairwise_tukey"] = pairwise
        return self._show("final_outcome_anova", summary)

    def _yield_overview_model_geometry(
        self,
        data: ExperimentData,
        row_specs: Sequence[tuple[Sequence[str], str, str]],
    ) -> tuple[dict[tuple[str, str], RCBDResult], list[tuple[float, float]]]:
        panel_results: dict[tuple[str, str], RCBDResult] = {}
        row_limits: list[tuple[float, float]] = []
        for treatments, question, _ in row_specs:
            values = data.harvest.loc[
                data.harvest["treatment"].astype(str).isin(treatments),
                "clean_yield_kg_ha",
            ].dropna()
            interval_limits: list[float] = []
            for sector in data.spec.sectors:
                result = self._fit_rcbd(
                    data.harvest,
                    outcome="clean_yield_kg_ha",
                    sector=sector,
                    date=None,
                    question=question,
                )
                panel_results[(sector, question)] = result
                interval_limits.extend(result.marginal_means["ci_low"].tolist())
                interval_limits.extend(result.marginal_means["ci_high"].tolist())
            lower = min(float(values.min()), min(interval_limits))
            upper = max(float(values.max()), max(interval_limits))
            padding = 0.10 * (upper - lower)
            row_limits.append((max(0.0, lower - padding), upper + padding))
        return panel_results, row_limits

    def _plot_yield_overview_panel(
        self,
        axis: Any,
        *,
        data: ExperimentData,
        treatments: Sequence[str],
        question: str,
        sector: str,
        result: RCBDResult,
        row_limit: tuple[float, float],
        treatment_colors: dict[str, str],
        block_offsets: dict[str, float],
        show_y_label: bool,
    ) -> None:
        positions = np.arange(len(treatments), dtype=float)
        sector_data = data.harvest.loc[
            data.harvest["sector"].astype(str).eq(sector)
            & data.harvest["treatment"].astype(str).isin(treatments)
        ]
        means = result.marginal_means.set_index("treatment")
        for position, treatment in zip(positions, treatments, strict=True):
            observations = sector_data.loc[
                sector_data["treatment"].astype(str).eq(treatment)
            ].sort_values("block")
            observed_x = np.asarray(
                [
                    position + block_offsets[str(block)]
                    for block in observations["block"]
                ]
            )
            axis.scatter(
                observed_x,
                observations["clean_yield_kg_ha"],
                color=treatment_colors[treatment],
                alpha=0.34,
                s=27,
                linewidths=0,
                zorder=2,
            )
            mean_row = cast(Any, means.loc[treatment])
            axis.errorbar(
                position,
                mean_row["estimate"],
                yerr=[
                    [mean_row["estimate"] - mean_row["ci_low"]],
                    [mean_row["ci_high"] - mean_row["estimate"]],
                ],
                color=treatment_colors[treatment],
                marker="o",
                markerfacecolor=(
                    "white" if treatment == "M0" else treatment_colors[treatment]
                ),
                markeredgecolor=treatment_colors[treatment],
                linestyle="none",
                markersize=MARKER_SIZE,
                elinewidth=INTERVAL_LINEWIDTH,
                capsize=ERRORBAR_CAPSIZE,
                zorder=4,
            )
        p_text = (
            "< 0,0001"
            if result.global_p < 0.0001
            else f"= {result.global_p:.4f}".replace(".", ",")
        )
        axis.text(
            0.02,
            1.015,
            f"ANOVA de tratamiento: p {p_text}",
            transform=axis.transAxes,
            ha="left",
            va="bottom",
            fontsize=9.25,
            clip_on=False,
        )
        axis.set_xticks(positions, treatments)
        axis.set_ylim(*row_limit)
        axis.set_xlabel("Tratamiento")
        if show_y_label:
            axis.set_ylabel("Rendimiento limpio (kg ha⁻¹)")
        if question == "all_m0_m5":
            axis.axvline(
                0.5,
                color=self.palette[5],
                linestyle=":",
                linewidth=REFERENCE_LINEWIDTH,
                alpha=0.70,
            )

    def yield_overview(self) -> pd.DataFrame:
        data = self._require_data()
        summary = (
            data.harvest.groupby(["sector", "treatment"], observed=True)[
                "clean_yield_kg_ha"
            ]
            .agg(["count", "mean", "std"])
            .reset_index()
        )
        summary["standard_error"] = summary["std"] / np.sqrt(summary["count"])
        summary["critical"] = summary["count"].map(
            lambda value: stats.t.ppf(0.975, value - 1)
        )
        summary["ci_low"] = (
            summary["mean"] - summary["critical"] * summary["standard_error"]
        )
        summary["ci_high"] = (
            summary["mean"] + summary["critical"] * summary["standard_error"]
        )
        self._show("yield_observed_summary", summary)

        row_specs = [
            (
                list(data.spec.treatments),
                "all_m0_m5",
                "Respuesta al N experimental adicional",
            ),
            (
                [value for value in data.spec.treatments if value != "M0"],
                "timing_m1_m5",
                "Comparación entre calendarios",
            ),
        ]
        panel_results, row_limits = self._yield_overview_model_geometry(
            data,
            row_specs,
        )

        treatment_colors = dict(
            zip(
                data.spec.treatments,
                self.palette[: len(data.spec.treatments)],
                strict=True,
            )
        )
        block_offsets = dict(
            zip(
                data.spec.blocks,
                np.linspace(-0.12, 0.12, len(data.spec.blocks)),
                strict=True,
            )
        )
        fig, axes = plt.subplots(2, len(data.spec.sectors), figsize=(12.2, 8.8))
        axes_array = np.asarray(axes)
        for row_index, (treatments, question, _) in enumerate(row_specs):
            for column_index, sector in enumerate(data.spec.sectors):
                axis = axes_array[row_index, column_index]
                result = panel_results[(sector, question)]
                self._plot_yield_overview_panel(
                    axis,
                    data=data,
                    treatments=treatments,
                    question=question,
                    sector=sector,
                    result=result,
                    row_limit=row_limits[row_index],
                    treatment_colors=treatment_colors,
                    block_offsets=block_offsets,
                    show_y_label=column_index == 0,
                )
        fig.subplots_adjust(
            left=0.08,
            right=0.98,
            bottom=0.10,
            top=0.72,
            hspace=0.70,
            wspace=0.12,
        )
        for column_index, sector in enumerate(data.spec.sectors):
            panel_position = axes_array[0, column_index].get_position()
            fig.text(
                (panel_position.x0 + panel_position.x1) / 2.0,
                panel_position.y1 + 0.075,
                sector.upper(),
                ha="center",
                va="bottom",
                fontsize=12.5,
                fontweight="bold",
            )
        for row_index, (_, _, row_title) in enumerate(row_specs):
            panel_position = axes_array[row_index, 0].get_position()
            fig.text(
                panel_position.x0,
                panel_position.y1 + 0.04,
                row_title,
                ha="left",
                va="bottom",
                fontsize=11,
                fontweight="bold",
            )
        self._save_figure(
            fig,
            "figura_03_rendimiento_observado",
            title="Rendimiento de semilla limpia: dos preguntas y dos escalas",
            subtitle=(
                "Parcelas individuales y media ajustada por bloque con IC puntual del 95 %; "
                "las preguntas M0–M5 y M1–M5 se prueban por separado."
            ),
            note=(
                "La fila superior incluye M0; la inferior amplía M1–M5 para que la gran "
                "respuesta frente a M0 no comprima las diferencias entre calendarios."
            ),
        )
        return summary

    def yield_contrasts(self) -> pd.DataFrame:
        data = self._require_data()
        rows = [
            self._planned_extra_n_contrast(
                data.harvest,
                outcome="clean_yield_kg_ha",
                sector=sector,
                date=None,
            )
            for sector in data.spec.sectors
        ]
        # Early versus late is a secondary descriptive contrast within M1–M5.
        for sector in data.spec.sectors:
            result = self._fit_rcbd(
                data.harvest,
                outcome="clean_yield_kg_ha",
                sector=sector,
                date=None,
                question="timing_m1_m5",
            )
            treatments = [value for value in data.spec.treatments if value != "M0"]
            vectors = self._marginal_mean_vectors(
                result.fit,
                treatments=treatments,
                blocks=data.spec.blocks,
            )
            vector = 0.5 * (vectors["M1"] + vectors["M2"]) - 0.5 * (
                vectors["M4"] + vectors["M5"]
            )
            estimate, se, low, high, p_value = self._linear_estimate(result.fit, vector)
            rows.append(
                {
                    "sector": sector,
                    "date": None,
                    "outcome": "clean_yield_kg_ha",
                    "contrast": "mean_M1_M2_minus_mean_M4_M5",
                    "estimate": estimate,
                    "standard_error": se,
                    "ci_low": low,
                    "ci_high": high,
                    "p_value": p_value,
                }
            )
        contrasts = pd.DataFrame(rows)
        return self._show("yield_planned_contrasts", contrasts)

    def yield_components(self) -> pd.DataFrame:
        data = self._require_data()
        components = [
            "panicle_density_m2",
            "w1000_g",
            "estimated_seeds_per_panicle",
            "cleaning_loss_pct",
        ]
        summary = (
            data.harvest.groupby(["sector", "treatment"], observed=True)[components]
            .agg(["count", "mean", "std"])
            .reset_index()
        )
        summary.columns = [
            (
                "_".join(str(part) for part in column if str(part))
                if isinstance(column, tuple)
                else str(column)
            )
            for column in summary.columns
        ]
        return self._show("yield_component_summary", summary)

    @staticmethod
    def _reconstruction_null(
        harvest: pd.DataFrame,
        *,
        permutations: int,
        seed: int,
    ) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        rows: list[dict[str, object]] = []
        patterns: dict[str, Callable[[pd.DataFrame], np.ndarray]] = {
            "all_m0_m5": lambda frame: np.ones(len(frame), dtype=bool),
            "timing_m1_m5": lambda frame: frame["treatment"]
            .astype(str)
            .ne("M0")
            .to_numpy(),
        }
        for sector in harvest["sector"].astype(str).drop_duplicates():
            sector_frame = harvest.loc[harvest["sector"].astype(str).eq(sector)].copy()
            for pattern, selector in patterns.items():
                subset = sector_frame.loc[selector(sector_frame)].copy()
                observed = float(
                    stats.pearsonr(
                        subset["panicle_density_m2"],
                        subset["estimated_seeds_per_panicle"],
                    ).statistic
                )
                panicle_count = subset["panicle_count"].to_numpy(float)
                panicle_density = subset["panicle_density_m2"].to_numpy(float)
                seed_count = subset["estimated_seed_count"].to_numpy(float)
                null = np.empty(permutations, dtype=float)
                for index in range(permutations):
                    permuted = rng.permutation(seed_count) / panicle_count
                    null[index] = float(
                        stats.pearsonr(panicle_density, permuted).statistic
                    )
                median = float(np.median(null))
                tail = float(
                    (1 + np.sum(np.abs(null - median) >= abs(observed - median)))
                    / (permutations + 1)
                )
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
                        "two_sided_tail_around_null_median": tail,
                    }
                )
        return pd.DataFrame(rows)

    def component_correlations(self) -> pd.DataFrame:
        data = self._require_data()
        null = self._reconstruction_null(
            data.harvest,
            permutations=10000,
            seed=self.random_seed,
        )
        self._show("component_reconstruction_null", null)

        fig, axis = plt.subplots(figsize=(10.4, 5.2))
        table = null.iloc[::-1].reset_index(drop=True)
        y = np.arange(len(table))
        null_y = y + 0.09
        observed_y = y - 0.09
        for index, (_, row) in enumerate(table.iterrows()):
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
            table["observed_correlation"],
            observed_y,
            marker="o",
            s=62,
            facecolors="white",
            edgecolors="0.20",
            linewidths=1.8,
            zorder=4,
            label="Correlación observada",
        )
        axis.axvline(0.0, linewidth=REFERENCE_LINEWIDTH)
        axis.set_yticks(
            y,
            table["sector"].astype(str)
            + " — "
            + table["pattern"].map({"all_m0_m5": "M0–M5", "timing_m1_m5": "M1–M5"}),
        )
        axis.set_xlabel("Correlación panojas–semillas estimadas por panoja")
        axis.grid(axis="x", alpha=0.22)
        axis.legend(loc="lower right", bbox_to_anchor=(1.0, 1.02), ncol=2)
        fig.subplots_adjust(left=0.30, right=0.98, bottom=0.17, top=0.72)
        self._save_figure(
            fig,
            "figura_componentes_nulo_reconstruccion",
            title="Correlación observada frente al nulo de reconstrucción",
            subtitle="El numerador estimado se permuta y la división por panojas se vuelve a calcular.",
            note="El procedimiento evalúa información adicional a la identidad matemática; no descarta mecanismos biológicos no medidos.",
        )
        return null

    def seed_weight_precision(self) -> pd.DataFrame:
        data = self._require_data()
        wide = data.harvest[
            [
                "sample_id",
                "sector",
                "block",
                "treatment",
                "w100_1_g",
                "w100_2_g",
                "w100_3_g",
            ]
        ].copy()
        values = wide[["w100_1_g", "w100_2_g", "w100_3_g"]]
        wide["technical_mean_g"] = values.mean(axis=1)
        wide["technical_sd_g"] = values.std(axis=1, ddof=1)
        wide["technical_cv_pct"] = (
            100.0 * wide["technical_sd_g"] / wide["technical_mean_g"]
        )
        summary = pd.DataFrame(
            [
                {
                    "n_samples": len(wide),
                    "median_cv_pct": float(wide["technical_cv_pct"].median()),
                    "cv_upper_95_pct": float(wide["technical_cv_pct"].quantile(0.95)),
                    "max_cv_pct": float(wide["technical_cv_pct"].max()),
                    "max_abs_w1000_recompute_difference_g": float(
                        (data.harvest["w1000_g"] - data.harvest["w1000_materialized_g"])
                        .abs()
                        .max()
                    ),
                }
            ]
        )
        self.tables["seed_weight_technical_precision_by_sample"] = wide
        return self._show("seed_weight_technical_precision_summary", summary)

    # ------------------------------------------------------------------
    # Diagnostics, missingness, correlations
    # ------------------------------------------------------------------

    def _diagnostic_row(
        self,
        result: RCBDResult,
    ) -> dict[str, object]:
        residuals = np.asarray(result.fit.resid, dtype=float)
        shapiro_p = (
            float(stats.shapiro(residuals).pvalue) if len(residuals) >= 3 else np.nan
        )
        frame = result.fit.model.data.frame.copy()
        groups = [
            group[result.outcome].to_numpy(float)
            for _, group in frame.groupby("treatment", observed=True)
            if len(group) >= 2
        ]
        levene_p = (
            float(stats.levene(*groups, center="median").pvalue)
            if len(groups) >= 2
            else np.nan
        )
        influence = result.fit.get_influence()
        cooks = np.asarray(influence.cooks_distance[0], dtype=float)
        return {
            "sector": result.sector,
            "date": result.date,
            "outcome": result.outcome,
            "question": result.question,
            "n": int(result.fit.nobs),
            "shapiro_p": shapiro_p,
            "levene_median_p": levene_p,
            "max_cooks_distance": float(cooks.max()),
            "count_cooks_gt_4_over_n": int(np.sum(cooks > 4.0 / len(cooks))),
        }

    def model_diagnostics(self) -> pd.DataFrame:
        if not self.rcbd_results:
            self.longitudinal_anova()
            self.yield_analysis()
        rows = [self._diagnostic_row(result) for result in self.rcbd_results.values()]
        return self._show("rcbd_diagnostics", pd.DataFrame(rows))

    def primary_residual_diagnostics(self) -> pd.DataFrame:
        data = self._require_data()
        rows: list[dict[str, object]] = []
        for sector in data.spec.sectors:
            result = self._fit_rcbd(
                data.harvest,
                outcome="clean_yield_kg_ha",
                sector=sector,
                date=None,
                question="timing_m1_m5",
            )
            residuals = np.asarray(result.fit.resid, dtype=float)
            fitted = np.asarray(result.fit.fittedvalues, dtype=float)
            fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.6))
            residual_axis, qq_axis = np.asarray(axes).ravel()
            residual_axis.scatter(
                fitted,
                residuals,
                color=self.palette[0],
                alpha=0.80,
            )
            residual_axis.axhline(
                0.0,
                color=self.palette[5],
                linestyle="--",
                linewidth=REFERENCE_LINEWIDTH,
            )
            residual_axis.set_xlabel("Valores ajustados")
            residual_axis.set_ylabel("Residuos")
            residual_axis.set_title("Residuos frente a valores ajustados")
            (theoretical, ordered), (slope, intercept, _) = stats.probplot(
                residuals,
                dist="norm",
            )
            qq_axis.scatter(theoretical, ordered, color=self.palette[0])
            qq_axis.plot(
                theoretical,
                slope * theoretical + intercept,
                color=self.palette[5],
            )
            qq_axis.set_xlabel("Cuantiles teóricos")
            qq_axis.set_ylabel("Residuos ordenados")
            qq_axis.set_title("Gráfico Q–Q normal")
            fig.subplots_adjust(
                left=0.08,
                right=0.98,
                bottom=0.14,
                top=0.70,
                wspace=0.28,
            )
            self._save_figure(
                fig,
                f"diagnostico_residuos_rendimiento_{sector.casefold()}",
                title=f"Diagnóstico del modelo primario de rendimiento — {sector}",
                subtitle="Comparación M1–M5 con bloque fijo.",
            )
            rows.append(self._diagnostic_row(result))
        return self._show("primary_yield_diagnostics", pd.DataFrame(rows))

    def missing_n_sensitivity(self) -> pd.DataFrame:
        data = self._require_data()
        frame = data.longitudinal.copy()
        missing = frame.loc[frame["n_pct"].isna()].copy()
        rows: list[dict[str, object]] = []
        if missing.empty:
            return self._show(
                "missing_n_sensitivity",
                pd.DataFrame(
                    [
                        {
                            "status": "no_missing_primary_n_values",
                            "detail": "No se detectaron valores de N excluidos del análisis primario.",
                        }
                    ]
                ),
            )

        for index, record in missing.iterrows():
            date = pd.Timestamp(str(record["date"]))
            sector = str(record["sector"])
            subset = frame.loc[
                frame["sector"].astype(str).eq(sector)
                & pd.to_datetime(frame["date"].astype(str)).eq(date)
            ].copy()
            estimate = rcbd_missing_cell_estimate(
                subset,
                value_column="n_pct",
                missing_treatment=str(record["treatment"]),
                missing_block=str(record["block"]),
                r_blocks=data.spec.repetitions,
                t_treatments=len(data.spec.treatments),
            )
            primary_result = self._fit_rcbd(
                subset,
                outcome="n_pct",
                sector=sector,
                date=date,
                question="all_m0_m5",
            )
            imputed = subset.copy()
            imputed.loc[imputed.index == index, "n_pct"] = estimate
            imputed_result = self._fit_rcbd(
                imputed,
                outcome="n_pct",
                sector=sector,
                date=date,
                question="all_m0_m5",
            )
            rows.append(
                {
                    "sample_id": record["sample_id"],
                    "sector": sector,
                    "date": date,
                    "treatment": str(record["treatment"]),
                    "block": str(record["block"]),
                    "data_origin": record["data_origin"],
                    "rcbd_missing_cell_estimate_n_pct": estimate,
                    "primary_complete_case_p": primary_result.global_p,
                    "single_imputation_sensitivity_p": imputed_result.global_p,
                    "primary_policy": "estimated canonical row excluded",
                }
            )
        return self._show("missing_n_sensitivity", pd.DataFrame(rows))

    def joint_sector_analysis(self) -> pd.DataFrame:
        data = self._require_data()
        frame = data.harvest.copy()
        frame = frame.loc[frame["treatment"].astype(str).ne("M0")].dropna(
            subset=["clean_yield_kg_ha"]
        )
        frame = frame.assign(
            sector=frame["sector"].astype(str),
            treatment=frame["treatment"].astype(str),
            block=frame["block"].astype(str),
        )
        additive = smf.ols(
            "clean_yield_kg_ha ~ C(sector) + C(sector):C(block) + C(treatment)",
            data=frame,
        ).fit()
        interaction = smf.ols(
            "clean_yield_kg_ha ~ C(sector) + C(sector):C(block) + C(treatment) + C(sector):C(treatment)",
            data=frame,
        ).fit()
        comparison = sm.stats.anova_lm(additive, interaction)
        rows = pd.DataFrame(
            [
                {
                    "estimand": "descriptive_sector_by_treatment_pattern",
                    "f_statistic": float(comparison.iloc[1]["F"]),
                    "p_value": float(comparison.iloc[1]["Pr(>F)"]),
                    "df_difference": float(comparison.iloc[1]["df_diff"]),
                    "causal_interpretation": False,
                    "reason": "one physical sector per water condition",
                }
            ]
        )
        return self._show("joint_sector_descriptive_model", rows)

    @staticmethod
    def _partial_correlation_from_regression(
        frame: pd.DataFrame,
        *,
        x: str,
        y: str,
        controls: Sequence[str],
    ) -> tuple[float, float, int]:
        needed = [x, y, *controls]
        subset = frame[needed].dropna().copy()
        if len(subset) < 5:
            return np.nan, np.nan, len(subset)
        formula_terms = [x] + [f"C({column})" for column in controls]
        fit = smf.ols(f"{y} ~ " + " + ".join(formula_terms), data=subset).fit()
        t_value = float(fit.tvalues[x])
        df = float(fit.df_resid)
        partial_r = math.copysign(math.sqrt(t_value**2 / (t_value**2 + df)), t_value)
        return partial_r, float(fit.pvalues[x]), len(subset)

    def correlation_audit(self) -> pd.DataFrame:
        data = self._require_data()
        final_longitudinal = data.longitudinal.loc[
            pd.to_datetime(data.longitudinal["date"].astype(str)).eq(
                max(
                    pd.Timestamp(value)
                    for value in data.longitudinal["date"].cat.categories
                )
            ),
            ["plot_id", "biomass_kg_ha", "n_pct", "q_kg_n_ha", "nni_primary"],
        ]
        frame = data.harvest.merge(
            final_longitudinal,
            on="plot_id",
            how="left",
            validate="one_to_one",
            suffixes=("", "_final"),
        )
        pairs = [
            (
                "biomass_kg_ha_final",
                "clean_yield_kg_ha",
                False,
                "distinct measurements, shared plot",
            ),
            ("n_pct", "clean_yield_kg_ha", False, "distinct measurements, shared plot"),
            ("q_kg_n_ha", "clean_yield_kg_ha", True, "N accumulated contains biomass"),
            ("nni_primary", "clean_yield_kg_ha", True, "deterministic index"),
            (
                "panicle_density_m2",
                "clean_yield_kg_ha",
                False,
                "component and outcome share harvest process",
            ),
            (
                "w1000_g",
                "clean_yield_kg_ha",
                False,
                "component and outcome share harvest process",
            ),
            (
                "estimated_seeds_per_panicle",
                "clean_yield_kg_ha",
                True,
                "clean mass occurs in both variables",
            ),
            (
                "harvest_index_pct",
                "clean_yield_kg_ha",
                True,
                "yield is the numerator of harvest index",
            ),
            (
                "panicle_density_m2",
                "estimated_seeds_per_panicle",
                True,
                "panicle count occurs in denominator",
            ),
        ]
        rows: list[dict[str, object]] = []
        for sector in data.spec.sectors:
            sector_frame = frame.loc[frame["sector"].astype(str).eq(sector)].copy()
            for x, y, coupled, reason in pairs:
                for population, selector in (
                    ("all_m0_m5", np.ones(len(sector_frame), dtype=bool)),
                    (
                        "timing_m1_m5",
                        sector_frame["treatment"].astype(str).ne("M0").to_numpy(),
                    ),
                ):
                    subset = sector_frame.loc[selector].dropna(subset=[x, y])
                    if len(subset) >= 3:
                        pearson = stats.pearsonr(subset[x], subset[y])
                        raw_r = float(pearson.statistic)
                        raw_p = float(pearson.pvalue)
                    else:
                        raw_r = raw_p = np.nan
                    partial_r, partial_p, partial_n = (
                        self._partial_correlation_from_regression(
                            subset.assign(
                                treatment=subset["treatment"].astype(str),
                                block=subset["block"].astype(str),
                            ),
                            x=x,
                            y=y,
                            controls=["treatment", "block"],
                        )
                    )
                    rows.append(
                        {
                            "sector": sector,
                            "population": population,
                            "x": x,
                            "y": y,
                            "n_raw": len(subset),
                            "pearson_r": raw_r,
                            "pearson_p": raw_p,
                            "n_adjusted": partial_n,
                            "partial_r_controlling_treatment_block": partial_r,
                            "regression_p_for_x": partial_p,
                            "mathematical_coupling": coupled,
                            "coupling_or_design_note": reason,
                            "role": "exploratory",
                        }
                    )
        return self._show("correlation_audit", pd.DataFrame(rows))

    # ------------------------------------------------------------------
    # Mixed models
    # ------------------------------------------------------------------

    def _prepare_mixed_frame(
        self,
        *,
        sector: str,
        outcome: str,
        scale: Literal["raw", "log"],
        source: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        data = self._require_data()
        frame = (source if source is not None else data.longitudinal).copy()
        treatments = [value for value in data.spec.treatments if value != "M0"]
        subset = frame.loc[
            frame["sector"].astype(str).eq(sector)
            & frame["treatment"].astype(str).isin(treatments),
            ["plot_id", "block", "treatment", "date", "date_label", outcome],
        ].dropna(subset=[outcome])
        subset = subset.assign(
            block=subset["block"].astype(str),
            treatment=pd.Categorical(
                subset["treatment"].astype(str),
                categories=treatments,
                ordered=True,
            ),
            date_label=pd.Categorical(
                subset["date_label"].astype(str),
                categories=[
                    str(value) for value in frame["date_label"].drop_duplicates()
                ],
                ordered=True,
            ),
        )
        y = subset[outcome].to_numpy(float)
        if scale == "log":
            if np.any(y <= 0.0):
                raise ValueError(
                    f"{outcome} contiene valores no positivos; no puede usarse log."
                )
            transformed = np.log(y)
        else:
            transformed = y
        center = float(np.mean(transformed))
        standard_deviation = float(np.std(transformed, ddof=1))
        if not np.isfinite(standard_deviation) or standard_deviation <= 0.0:
            raise ValueError(f"No se puede estandarizar {outcome} en {sector}.")
        subset["y_z"] = (transformed - center) / standard_deviation
        subset.attrs["transform_center"] = center
        subset.attrs["transform_scale"] = standard_deviation
        subset.attrs["response_scale"] = scale
        subset.attrs["outcome"] = outcome
        return subset

    def _fit_mixed_model(
        self,
        *,
        sector: str,
        outcome: str,
        scale: Literal["raw", "log"],
        source: pd.DataFrame | None = None,
        bootstrap_replicates: int | None = None,
    ) -> MixedModelResult:
        frame = self._prepare_mixed_frame(
            sector=sector,
            outcome=outcome,
            scale=scale,
            source=source,
        )
        additive_formula = "y_z ~ C(block) + C(treatment) + C(date_label)"
        interaction_formula = "y_z ~ C(block) + C(treatment) * C(date_label)"
        additive_fit = fit_mixedlm_best(additive_formula, frame)
        interaction_fit = fit_mixedlm_best(interaction_formula, frame)
        asymptotic = likelihood_ratio(additive_fit, interaction_fit)
        requested = (
            self.bootstrap_replicates
            if bootstrap_replicates is None
            else bootstrap_replicates
        )
        bootstrap = parametric_bootstrap_lrt(
            frame,
            reduced_formula=additive_formula,
            full_formula=interaction_formula,
            reduced_fit=additive_fit,
            full_fit=interaction_fit,
            response_column="y_z",
            replicates=requested,
            seed=_stable_seed(
                sector, outcome, scale, "bootstrap", base=self.random_seed
            ),
        )
        residuals = frame.assign(
            _residual=np.asarray(interaction_fit.resid, dtype=float)
        )
        residual_sd = residuals.groupby("date_label", observed=True)["_residual"].std()
        positive = residual_sd.loc[residual_sd.gt(0.0)]
        residual_sd_ratio = (
            float(positive.max() / positive.min()) if len(positive) > 1 else np.nan
        )
        summary: dict[str, object] = {
            "sector": sector,
            "outcome": outcome,
            "scale": scale,
            "n": len(frame),
            "plots": frame["plot_id"].nunique(),
            "lrt_statistic": asymptotic.statistic,
            "lrt_df": asymptotic.degrees_freedom,
            "p_asymptotic": asymptotic.p_asymptotic,
            "p_parametric_bootstrap": bootstrap.p_bootstrap,
            "bootstrap_successful": bootstrap.successful_replicates,
            "bootstrap_requested": bootstrap.requested_replicates,
            "additive_optimizer": getattr(additive_fit, "_audit_optimizer", pd.NA),
            "interaction_optimizer": getattr(
                interaction_fit, "_audit_optimizer", pd.NA
            ),
            "additive_converged": bool(additive_fit.converged),
            "interaction_converged": bool(interaction_fit.converged),
            "random_intercept_variance": float(interaction_fit.cov_re.iloc[0, 0]),
            "residual_variance": float(interaction_fit.scale),
            "residual_sd_max_min_ratio": residual_sd_ratio,
        }
        result = MixedModelResult(
            sector=sector,
            outcome=outcome,
            scale=scale,
            frame=frame,
            additive_fit=additive_fit,
            interaction_fit=interaction_fit,
            summary=summary,
        )
        self.mixed_results[f"{sector}|{outcome}|{scale}"] = result
        return result

    def mixed_models(self) -> pd.DataFrame:
        data = self._require_data()
        specifications = [
            ("biomass_kg_ha", "raw"),
            ("biomass_kg_ha", "log"),
            ("n_pct", "raw"),
        ]
        rows: list[dict[str, object]] = []
        for sector in data.spec.sectors:
            for outcome, scale in specifications:
                result = self._fit_mixed_model(
                    sector=sector,
                    outcome=outcome,
                    scale=cast(Literal["raw", "log"], scale),
                )
                rows.append(result.summary)
        summary = pd.DataFrame(rows)
        summary["family"] = np.where(
            summary["outcome"].eq("biomass_kg_ha"),
            "biomass_scale_sensitivity",
            "n_concentration",
        )
        summary["p_fdr"] = np.nan
        for indices in summary.groupby("family").groups.values():
            index_list = list(indices)
            summary.loc[index_list, "p_fdr"] = benjamini_hochberg(
                summary.loc[index_list, "p_parametric_bootstrap"].to_numpy(float)
            )
        return self._show("mixed_model_interaction_tests", summary)

    @staticmethod
    def _backtransform(
        value: np.ndarray, *, center: float, scale: float, response_scale: str
    ) -> np.ndarray:
        transformed = center + scale * value
        return np.exp(transformed) if response_scale == "log" else transformed

    def _mixed_predictions(
        self, result: MixedModelResult
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        fit = result.interaction_fit
        frame = result.frame
        treatments = [str(value) for value in frame["treatment"].cat.categories]
        date_levels = [str(value) for value in frame["date_label"].cat.categories]
        blocks = sorted(frame["block"].unique().tolist())
        beta = np.asarray(fit.fe_params, dtype=float)
        covariance = np.asarray(fit.cov_params(), dtype=float)[: len(beta), : len(beta)]
        rng = np.random.default_rng(
            _stable_seed(
                result.sector,
                result.outcome,
                result.scale,
                "pred",
                base=self.random_seed,
            )
        )
        draws = rng.multivariate_normal(beta, covariance, size=20000)
        center = float(frame.attrs["transform_center"])
        response_scale_value = float(frame.attrs["transform_scale"])
        grid_vectors: dict[tuple[str, str], np.ndarray] = {}
        prediction_rows: list[dict[str, object]] = []
        for treatment in treatments:
            for date_label in date_levels:
                grid = pd.DataFrame(
                    {
                        "treatment": [treatment] * len(blocks),
                        "date_label": [date_label] * len(blocks),
                        "block": blocks,
                    }
                )
                vector = self._design_matrix(fit, grid).mean(axis=0)
                grid_vectors[(treatment, date_label)] = vector
                z_draws = draws @ vector
                raw_draws = self._backtransform(
                    z_draws,
                    center=center,
                    scale=response_scale_value,
                    response_scale=result.scale,
                )
                prediction_rows.append(
                    {
                        "sector": result.sector,
                        "outcome": result.outcome,
                        "scale": result.scale,
                        "treatment": treatment,
                        "date_label": date_label,
                        "estimate": float(
                            np.median(raw_draws)
                            if result.scale == "log"
                            else np.mean(raw_draws)
                        ),
                        "ci_low": float(np.quantile(raw_draws, 0.025)),
                        "ci_high": float(np.quantile(raw_draws, 0.975)),
                        "estimand": (
                            "geometric_typical_value"
                            if result.scale == "log"
                            else "arithmetic_mean"
                        ),
                    }
                )

        contrast_rows: list[dict[str, object]] = []
        for date_label in date_levels:
            early_z = 0.5 * (
                draws @ grid_vectors[("M1", date_label)]
                + draws @ grid_vectors[("M2", date_label)]
            )
            late_z = 0.5 * (
                draws @ grid_vectors[("M4", date_label)]
                + draws @ grid_vectors[("M5", date_label)]
            )
            early = self._backtransform(
                early_z,
                center=center,
                scale=response_scale_value,
                response_scale=result.scale,
            )
            late = self._backtransform(
                late_z,
                center=center,
                scale=response_scale_value,
                response_scale=result.scale,
            )
            difference = early - late
            contrast_rows.append(
                {
                    "sector": result.sector,
                    "outcome": result.outcome,
                    "scale": result.scale,
                    "date_label": date_label,
                    "contrast": "mean_M1_M2_minus_mean_M4_M5",
                    "estimate": float(
                        np.median(difference)
                        if result.scale == "log"
                        else np.mean(difference)
                    ),
                    "ci_low": float(np.quantile(difference, 0.025)),
                    "ci_high": float(np.quantile(difference, 0.975)),
                    "approx_probability_positive": float(np.mean(difference > 0.0)),
                    "interval_method": "asymptotic_fixed_effect_draws",
                }
            )
        return pd.DataFrame(prediction_rows), pd.DataFrame(contrast_rows)

    def mixed_estimates(self) -> pd.DataFrame:
        if not self.mixed_results:
            self.mixed_models()
        predictions: list[pd.DataFrame] = []
        contrasts: list[pd.DataFrame] = []
        for result in self.mixed_results.values():
            prediction, contrast = self._mixed_predictions(result)
            predictions.append(prediction)
            contrasts.append(contrast)
        prediction_table = pd.concat(predictions, ignore_index=True)
        contrast_table = pd.concat(contrasts, ignore_index=True)
        self.tables["mixed_model_targeted_contrasts"] = contrast_table
        self._show("mixed_model_predictions", prediction_table)

        # Plot only one primary scale per outcome; the alternative biomass scale
        # remains visible in the sensitivity table.
        plot_table = prediction_table.loc[
            (
                prediction_table["outcome"].eq("biomass_kg_ha")
                & prediction_table["scale"].eq("raw")
            )
            | (
                prediction_table["outcome"].eq("n_pct")
                & prediction_table["scale"].eq("raw")
            )
        ]
        data = self._require_data()
        treatment_colors = dict(
            zip(
                [value for value in data.spec.treatments if value != "M0"],
                self.palette[1:6],
                strict=True,
            )
        )
        for outcome in ["biomass_kg_ha", "n_pct"]:
            subset = plot_table.loc[plot_table["outcome"].eq(outcome)]
            fig, axes = plt.subplots(
                1, len(data.spec.sectors), figsize=(12.2, 5.3), sharey=True
            )
            axes_array = np.atleast_1d(axes)
            for axis, sector in zip(axes_array, data.spec.sectors, strict=True):
                sector_data = subset.loc[subset["sector"].eq(sector)]
                date_levels = sector_data["date_label"].drop_duplicates().tolist()
                date_centers = np.arange(len(date_levels), dtype=float)
                positions = dict(zip(date_levels, date_centers, strict=True))
                treatment_offsets = dict(
                    zip(
                        treatment_colors,
                        np.linspace(-0.28, 0.28, len(treatment_colors)),
                        strict=True,
                    )
                )
                block_offsets = dict(
                    zip(
                        data.spec.blocks,
                        np.linspace(-0.016, 0.016, len(data.spec.blocks)),
                        strict=True,
                    )
                )
                model_result = self.mixed_results[f"{sector}|{outcome}|raw"]
                for treatment, color in treatment_colors.items():
                    treatment_data = sector_data.loc[
                        sector_data["treatment"].eq(treatment)
                    ]
                    observed = model_result.frame.loc[
                        model_result.frame["treatment"].astype(str).eq(treatment)
                    ]
                    observed_x = np.asarray(
                        [
                            positions[str(date_label)]
                            + treatment_offsets[treatment]
                            + block_offsets[str(block)]
                            for date_label, block in zip(
                                observed["date_label"], observed["block"], strict=True
                            )
                        ]
                    )
                    axis.scatter(
                        observed_x,
                        observed[outcome],
                        color=color,
                        alpha=0.18,
                        s=19,
                        linewidths=0,
                        zorder=1,
                    )
                    x = [
                        positions[label] + treatment_offsets[treatment]
                        for label in treatment_data["date_label"]
                    ]
                    axis.errorbar(
                        x,
                        treatment_data["estimate"],
                        yerr=np.vstack(
                            [
                                treatment_data["estimate"] - treatment_data["ci_low"],
                                treatment_data["ci_high"] - treatment_data["estimate"],
                            ]
                        ),
                        marker="o",
                        linestyle="none",
                        markersize=MARKER_SIZE,
                        capsize=ERRORBAR_CAPSIZE,
                        elinewidth=INTERVAL_LINEWIDTH,
                        label=treatment,
                        color=color,
                        zorder=3,
                    )
                treatment_positions = [
                    center + treatment_offsets[treatment]
                    for center in date_centers
                    for treatment in treatment_colors
                ]
                axis.set_xticks(
                    treatment_positions,
                    list(treatment_colors) * len(date_centers),
                    minor=True,
                )
                axis.tick_params(axis="x", which="minor", pad=5, length=0)
                axis.set_xticks(date_centers, date_levels)
                axis.tick_params(axis="x", which="major", pad=25, length=0)
                axis.set_title(sector.upper())
                axis.set_xlabel("")
            y_label = (
                "Biomasa (kg MS ha⁻¹)"
                if outcome == "biomass_kg_ha"
                else "Concentración de N (%)"
            )
            axes_array[0].set_ylabel(y_label)
            fig.subplots_adjust(
                left=0.09,
                right=0.98,
                bottom=0.23,
                top=0.69,
                wspace=0.12,
            )
            self._save_figure(
                fig,
                f"modelo_mixto_{outcome}",
                title=(
                    "Estimaciones del modelo mixto: biomasa aérea"
                    if outcome == "biomass_kg_ha"
                    else "Estimaciones del modelo mixto: concentración de N"
                ),
                subtitle=(
                    "Puntos claros: parcelas individuales. Círculos: estimación marginal "
                    "del modelo completo e intervalo del 95 %."
                ),
                note=(
                    "Fechas equidistantes; M1–M5 se agrupan dentro de cada fecha y las "
                    "estimaciones no se conectan. La interacción se calibra por bootstrap."
                ),
            )
        return prediction_table

    def september_sensitivity(self) -> pd.DataFrame:
        data = self._require_data()
        sample_dates = [
            pd.Timestamp(value) for value in data.longitudinal["date"].cat.categories
        ]
        schedule = data.spec.schedule.copy()
        rows: list[dict[str, object]] = []
        for record in schedule.itertuples(index=False):
            for application_number, application_date in enumerate(
                [record.first_application, record.second_application], start=1
            ):
                if pd.isna(application_date):
                    continue
                application = _as_timestamp(application_date)
                rows.append(
                    {
                        "treatment": record.treatment,
                        "application_number": application_number,
                        "application_date": application,
                        "same_day_as_sampling": application in set(sample_dates),
                        "interpretation_rule": (
                            "do_not_attribute_same_day_sample_to_application_without_field_chronology"
                            if application in set(sample_dates)
                            else "chronology_unambiguous_at_day_resolution"
                        ),
                    }
                )
        chronology = pd.DataFrame(rows)
        self._show("application_sampling_chronology", chronology)

        if not self.mixed_results:
            self.mixed_models()
        sensitivity = pd.DataFrame(
            [result.summary for result in self.mixed_results.values()]
        )
        sensitivity = sensitivity.loc[
            sensitivity["outcome"].eq("biomass_kg_ha"),
            [
                "sector",
                "outcome",
                "scale",
                "p_asymptotic",
                "p_parametric_bootstrap",
                "residual_sd_max_min_ratio",
            ],
        ]
        return self._show("biomass_scale_sensitivity", sensitivity)

    # ------------------------------------------------------------------
    # Synthesis and export
    # ------------------------------------------------------------------

    def figure_manifest(self) -> pd.DataFrame:
        manifest = pd.DataFrame(self.figure_metadata)
        return self._show("figure_manifest", manifest)

    def automatic_summary(self) -> pd.DataFrame:
        data = self._require_data()
        rows: list[dict[str, object]] = []

        if "yield_planned_contrasts" not in self.tables:
            self.yield_contrasts()
        contrasts = self.tables["yield_planned_contrasts"]
        for record in contrasts.itertuples(index=False):
            rows.append(
                {
                    "domain": "yield",
                    "sector": record.sector,
                    "estimand": record.contrast,
                    "estimate": record.estimate,
                    "interval_low": record.ci_low,
                    "interval_high": record.ci_high,
                    "p_value": record.p_value,
                    "interpretation_template": (
                        "report_estimate_and_interval; do_not_convert_nonsignificance_to_equivalence"
                    ),
                }
            )

        if "mixed_model_interaction_tests" not in self.tables:
            self.mixed_models()
        mixed = self.tables["mixed_model_interaction_tests"]
        for record in mixed.itertuples(index=False):
            p_value = _as_float(record.p_parametric_bootstrap)
            rows.append(
                {
                    "domain": "trajectory",
                    "sector": record.sector,
                    "estimand": f"{record.outcome}|{record.scale}|treatment_by_date",
                    "estimate": record.lrt_statistic,
                    "interval_low": np.nan,
                    "interval_high": np.nan,
                    "p_value": p_value,
                    "interpretation_template": (
                        "trajectory_evidence_on_declared_scale"
                        if p_value < self.alpha
                        else "trajectory_difference_not_detected_on_declared_scale"
                    ),
                }
            )

        if "component_reconstruction_null" not in self.tables:
            self.component_correlations()
        reconstruction = self.tables["component_reconstruction_null"]
        for record in reconstruction.itertuples(index=False):
            lower = _as_float(record.null_lower_95)
            observed = _as_float(record.observed_correlation)
            upper = _as_float(record.null_upper_95)
            rows.append(
                {
                    "domain": "yield_components",
                    "sector": record.sector,
                    "estimand": f"reconstruction_null|{record.pattern}",
                    "estimate": observed,
                    "interval_low": lower,
                    "interval_high": upper,
                    "p_value": record.two_sided_tail_around_null_median,
                    "interpretation_template": (
                        "association_not_independent_evidence_of_compensation"
                        if lower <= observed <= upper
                        else "association_more_extreme_than_reconstruction_null"
                    ),
                }
            )

        rows.append(
            {
                "domain": "scope",
                "sector": "both_observed_sectors",
                "estimand": "water_condition",
                "estimate": np.nan,
                "interval_low": np.nan,
                "interval_high": np.nan,
                "p_value": np.nan,
                "interpretation_template": "descriptive_only_one_physical_sector_per_condition",
            }
        )
        rows.append(
            {
                "domain": "source",
                "sector": "all",
                "estimand": "canonical_data_sha256",
                "estimate": data.spec.source_sha256,
                "interval_low": pd.NA,
                "interval_high": pd.NA,
                "p_value": np.nan,
                "interpretation_template": "all_observed_values_read_from_canonical_csv",
            }
        )
        return self._show("automatic_summary", pd.DataFrame(rows))

    def export_artifacts(self) -> pd.DataFrame:
        if not self.export_results:
            frame = pd.DataFrame(
                [{"status": "export_disabled", "directory": str(self.results_dir)}]
            )
            return self._show("export_manifest", frame)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, object]] = []
        for name, table in sorted(self.tables.items()):
            path = self.results_dir / f"{name}.csv"
            table.to_csv(path, index=False)
            rows.append(
                {
                    "artifact_type": "table",
                    "name": name,
                    "path": str(path),
                    "rows": len(table),
                    "columns": len(table.columns),
                }
            )
        if self.figure_metadata:
            manifest_path = self.results_dir / "figure_manifest.json"
            manifest_path.write_text(
                json.dumps(self.figure_metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            rows.append(
                {
                    "artifact_type": "figure_manifest",
                    "name": "figure_manifest",
                    "path": str(manifest_path),
                    "rows": len(self.figure_metadata),
                    "columns": np.nan,
                }
            )
        return self._show("export_manifest", pd.DataFrame(rows))

    # Compatibility no-op retained for the former notebook section.
    def rcbd_functions(self) -> pd.DataFrame:
        frame = pd.DataFrame(
            [
                {
                    "model": "Y ~ treatment + block",
                    "anova": "Type II",
                    "marginal_means": "averaged over observed block levels",
                    "pairwise": "Tukey-adjusted after the global treatment test",
                }
            ]
        )
        return self._show("rcbd_method", frame)


def run_all_longitudinal() -> None:
    """Execute the full report from the command line."""

    import matplotlib

    matplotlib.use("Agg", force=True)
    analysis = LongitudinalNotebook(
        figure_profile="standalone", print_figure_json=False
    )
    for method_name in LONGITUDINAL_STEPS:
        getattr(analysis, method_name)()


if __name__ == "__main__":
    run_all_longitudinal()
