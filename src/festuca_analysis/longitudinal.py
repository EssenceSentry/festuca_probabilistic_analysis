from __future__ import annotations

"""Classical and longitudinal analyses behind the thesis report.

The public class intentionally exposes one method per report section so the
notebook remains a readable orchestration layer. The generator preserves the
original section order and in-memory statistical objects without duplicating
analysis logic in notebook cells.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Literal

LONGITUDINAL_STEPS = (
    "configuration",
    "load_data",
    "flagged_dry_matter",
    "baseline_summary",
    "schedule",
    "water_inputs",
    "rcbd_functions",
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

# Start and end coincide when the application date is known. A non-zero interval
# records the documented month without inventing an exact day.
COMMON_N_APPLICATIONS = (
    ("2025-04-01", "2025-05-01", 60.0),
    ("2025-07-01", "2025-07-01", 52.0),
    ("2025-08-01", "2025-09-01", 52.0),
)
COMMON_N_TOTAL_KG_HA = sum(dose for _start, _end, dose in COMMON_N_APPLICATIONS)
EXPERIMENTAL_N_TOTAL_KG_HA = 200.0


class LongitudinalNotebook:
    """Stateful, section-by-section API for the longitudinal report."""

    def __init__(
        self,
        *,
        project_root: Path | None = None,
        dry_matter_policy: Literal["recorded", "ratio", "exclude"] = "recorded",
        export_results: bool = True,
        export_figures: bool = True,
    ) -> None:
        root = (project_root or Path.cwd()).resolve()
        self._steps = _analysis_steps(
            project_root=root,
            dry_matter_policy=dry_matter_policy,
            export_results=export_results,
            export_figures=export_figures,
        )
        self._completed: list[str] = []

    @property
    def completed_steps(self) -> tuple[str, ...]:
        return tuple(self._completed)

    def _advance(self, expected: str) -> None:
        try:
            actual = next(self._steps)
        except StopIteration as error:
            raise RuntimeError("El análisis longitudinal ya terminó.") from error
        if actual != expected:
            raise RuntimeError(
                f"Orden de ejecución inválido: se esperaba {expected!r} y se obtuvo {actual!r}."
            )
        self._completed.append(actual)

    def configuration(self) -> None:
        """Execute the configuration report section."""
        self._advance("configuration")

    def load_data(self) -> None:
        """Execute the load data report section."""
        self._advance("load_data")

    def flagged_dry_matter(self) -> None:
        """Execute the flagged dry matter report section."""
        self._advance("flagged_dry_matter")

    def baseline_summary(self) -> None:
        """Execute the baseline summary report section."""
        self._advance("baseline_summary")

    def schedule(self) -> None:
        """Execute the schedule report section."""
        self._advance("schedule")

    def water_inputs(self) -> None:
        """Execute the water inputs report section."""
        self._advance("water_inputs")

    def rcbd_functions(self) -> None:
        """Execute the rcbd functions report section."""
        self._advance("rcbd_functions")

    def longitudinal_anova(self) -> None:
        """Execute the longitudinal anova report section."""
        self._advance("longitudinal_anova")

    def observed_trajectories(self) -> None:
        """Execute the observed trajectories report section."""
        self._advance("observed_trajectories")

    def final_outcomes(self) -> None:
        """Execute the final outcomes report section."""
        self._advance("final_outcomes")

    def dry_matter_sensitivity(self) -> None:
        """Execute the registered/ratio/exclusion dry-matter sensitivity."""
        self._advance("dry_matter_sensitivity")

    def yield_analysis(self) -> None:
        """Execute the yield analysis report section."""
        self._advance("yield_analysis")

    def yield_overview(self) -> None:
        """Execute the yield overview report section."""
        self._advance("yield_overview")

    def yield_contrasts(self) -> None:
        """Execute the yield contrasts report section."""
        self._advance("yield_contrasts")

    def yield_components(self) -> None:
        """Execute the yield components report section."""
        self._advance("yield_components")

    def component_correlations(self) -> None:
        """Execute the component correlations report section."""
        self._advance("component_correlations")

    def seed_weight_precision(self) -> None:
        """Execute the seed weight precision report section."""
        self._advance("seed_weight_precision")

    def model_diagnostics(self) -> None:
        """Execute the model diagnostics report section."""
        self._advance("model_diagnostics")

    def primary_residual_diagnostics(self) -> None:
        """Execute the primary residual diagnostics report section."""
        self._advance("primary_residual_diagnostics")

    def missing_n_sensitivity(self) -> None:
        """Execute the missing n sensitivity report section."""
        self._advance("missing_n_sensitivity")

    def joint_sector_analysis(self) -> None:
        """Execute the joint sector analysis report section."""
        self._advance("joint_sector_analysis")

    def correlation_audit(self) -> None:
        """Execute the correlation audit report section."""
        self._advance("correlation_audit")

    def mixed_models(self) -> None:
        """Execute the mixed models report section."""
        self._advance("mixed_models")

    def mixed_estimates(self) -> None:
        """Execute the mixed estimates report section."""
        self._advance("mixed_estimates")

    def september_sensitivity(self) -> None:
        """Execute the september sensitivity report section."""
        self._advance("september_sensitivity")

    def figure_manifest(self) -> None:
        """Execute the figure manifest report section."""
        self._advance("figure_manifest")

    def automatic_summary(self) -> None:
        """Execute the automatic summary report section."""
        self._advance("automatic_summary")

    def export_artifacts(self) -> None:
        """Execute the export artifacts report section."""
        self._advance("export_artifacts")


def run_all_longitudinal() -> None:
    """Execute every longitudinal report section headlessly from the CLI."""
    import matplotlib

    matplotlib.use("Agg", force=True)
    analysis = LongitudinalNotebook()
    for step in LONGITUDINAL_STEPS:
        getattr(analysis, step)()


def _analysis_steps(
    *,
    project_root: Path,
    dry_matter_policy: Literal["recorded", "ratio", "exclude"],
    export_results: bool,
    export_figures: bool,
) -> Iterator[str]:

    # Notebook step: configuration
    import math
    import platform
    from collections.abc import Sequence
    from dataclasses import dataclass
    from importlib import import_module
    from itertools import combinations
    from pathlib import Path
    from typing import Any, cast

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import patsy  # pyright: ignore[reportMissingTypeStubs]
    import scipy
    import seaborn as sns  # pyright: ignore[reportMissingTypeStubs]
    import statsmodels  # pyright: ignore[reportMissingTypeStubs]
    import statsmodels.api as sm  # pyright: ignore[reportMissingTypeStubs]
    import statsmodels.formula.api as smf  # pyright: ignore[reportMissingTypeStubs]
    from IPython.display import (
        Markdown,
        display,  # pyright: ignore[reportUnknownVariableType]
    )
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from scipy import stats

    from festuca_analysis.plotting import (
        CATEGORICAL_ERRORBAR_CAPSIZE,
        DATA_LINEWIDTH,
        ERRORBAR_CAPSIZE,
        INTERVAL_LINEWIDTH,
        MARKER_SIZE,
        REFERENCE_LINEWIDTH,
        SECONDARY_LINEWIDTH,
        add_figure_header,
        add_figure_note,
        apply_plot_theme,
        plot_horizontal_interval,
    )
    from festuca_analysis.statistics import (
        benjamini_hochberg,
        fit_mixedlm_best,
        likelihood_ratio,
        parametric_bootstrap_lrt,
        rcbd_missing_cell_estimate,
    )

    libqsturng = import_module("statsmodels.stats.libqsturng")
    libqsturng_api = cast(Any, libqsturng)
    mpl = cast(Any, plt)
    patsy_api = cast(Any, patsy)
    sns_api = cast(Any, sns)
    sm_api = cast(Any, sm)
    smf_api = cast(Any, smf)
    statsmodels_api = cast(Any, statsmodels)
    display_output = cast(Any, display)
    psturng_fn = libqsturng_api.psturng
    qsturng_fn = libqsturng_api.qsturng

    def format_display_float(value: float) -> str:
        return f"{value:,.4f}"

    pd.set_option("display.max_columns", 80)
    pd.set_option("display.width", 180)
    pd.set_option("display.float_format", format_display_float)

    ALPHA = 0.05
    BOOTSTRAP_REPLICATES = 199
    RANDOM_SEED = 20260807
    DRY_MATTER_POLICY = dry_matter_policy
    EXPORT_RESULTS = export_results
    PROJECT_ROOT = project_root
    RESULTS_DIR = PROJECT_ROOT / "festuca_thesis_analysis_outputs"
    EXPORT_FIGURES = export_figures
    FIGURES_DIR = PROJECT_ROOT / "festuca_thesis_figures"
    FIGURE_DPI = 300

    PLOT_PALETTE = apply_plot_theme()

    def save_figure(fig: Any, filename_stem: str) -> None:
        if not EXPORT_FIGURES:
            return
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            FIGURES_DIR / f"{filename_stem}.png",
            dpi=FIGURE_DPI,
            bbox_inches="tight",
        )
        fig.savefig(
            FIGURES_DIR / f"{filename_stem}.pdf",
            bbox_inches="tight",
        )

    TREATMENTS = ["M0", "M1", "M2", "M3", "M4", "M5"]
    FERTILIZED = ["M1", "M2", "M3", "M4", "M5"]
    SECTORS = ["Secano", "Riego"]
    BLOCKS = ["R1", "R2", "R3", "R4"]
    DATES = pd.to_datetime(["2025-09-16", "2025-10-20", "2025-11-12"])
    DATE_LABELS = {
        pd.Timestamp("2025-09-16"): "16 sep",
        pd.Timestamp("2025-10-20"): "20 oct",
        pd.Timestamp("2025-11-12"): "12 nov",
    }

    TREATMENT_COLORS = dict(zip(TREATMENTS, PLOT_PALETTE[:6], strict=True))
    TREATMENT_MARKERS = dict.fromkeys(TREATMENTS, "o")
    SECTOR_COLORS = dict(zip(SECTORS, (PLOT_PALETTE[1], PLOT_PALETTE[6]), strict=True))
    # Only the component-correlation plot overlays both sectors on one axis.
    SECTOR_MARKERS = {"Secano": "o", "Riego": "s"}

    OUTCOME_LABELS = {
        "biomass_kg_ha_used": "Biomasa aérea (kg MS ha⁻¹)",
        "n_pct": "N en biomasa (%)",
        "q_kg_n_ha": "N presente en biomasa aérea (kg N ha⁻¹)",
        "nni_revised": "INN revisado",
        "nni_historical": "INN histórico",
        "panicle_density_m2": "Panojas m⁻²",
        "estimated_seeds_per_panicle": "Semillas estimadas por panoja",
        "w1000_g": "Peso de mil semillas (g)",
        "dirty_yield_kg_ha": "Rendimiento sin limpiar (kg ha⁻¹)",
        "clean_yield_kg_ha": "Rendimiento limpio (kg ha⁻¹)",
        "harvest_index_pct": "Índice de cosecha (%)",
        "cleaning_loss_pct": "Merma de limpieza (%)",
        "agronomic_efficiency": "Eficiencia agronómica (kg semilla kg⁻¹ N)",
        "apparent_water_productivity": "Productividad aparente del agua (kg ha⁻¹ mm⁻¹)",
    }
    OBSERVED_BY_DATE_TITLES = {
        "biomass_kg_ha_used": (
            "Biomasa aérea observada en las tres fechas de muestreo"
        ),
        "n_pct": "Concentración de N observada en las tres fechas de muestreo",
        "q_kg_n_ha": ("N presente en biomasa aérea en las tres fechas de muestreo"),
        "nni_revised": "INN revisado en las tres fechas de muestreo",
    }

    print("Python", platform.python_version())
    print("pandas", pd.__version__)
    print("numpy", np.__version__)
    print("scipy", scipy.__version__)
    print("statsmodels", statsmodels_api.__version__)
    yield "configuration"

    # Notebook step: load_data
    HARVEST_AREA_M2 = 0.76
    BIOMASS_AREA_M2 = 0.38
    DM_ISSUE_SAMPLE_IDS = {150, 152}

    CANONICAL_SCHEDULE = {
        "M0": (),
        "M1": ("2025-06-12", "2025-07-31"),
        "M2": ("2025-06-26", "2025-07-31"),
        "M3": ("2025-07-10", "2025-08-21"),
        "M4": ("2025-07-31", "2025-09-04"),
        "M5": ("2025-08-21", "2025-09-20"),
    }

    def locate_workbook(filename: str = "Datos_Ema_Serrana_INN.xlsx") -> Path:
        candidates = [
            PROJECT_ROOT / "sources" / filename,
            PROJECT_ROOT / filename,
            Path("/mnt/data") / filename,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()
        raise FileNotFoundError(
            f"No se encontró {filename!r}. Se probó: "
            + ", ".join(str(path) for path in candidates)
        )

    def normalize_design_columns(frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        result["Condición"] = result["Condición"].astype(str).str.strip()
        result["Tratamiento"] = (
            result["Tratamiento"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({"MO": "M0"})
        )
        result["Repetición"] = result["Repetición"].astype(str).str.strip().str.upper()
        return result

    def categorical(series: pd.Series, levels: Sequence[str]) -> pd.Categorical:
        return pd.Categorical(series.astype(str), categories=list(levels), ordered=True)

    def coerce_numeric_columns(
        frame: pd.DataFrame,
        columns: Sequence[str],
    ) -> pd.DataFrame:
        result = frame.copy()
        for column in columns:
            if column in result:
                result[column] = pd.to_numeric(result[column], errors="coerce")
        return result

    @dataclass(frozen=True)
    class ExperimentData:
        workbook_path: Path
        longitudinal: pd.DataFrame
        harvest: pd.DataFrame
        seed_weight_long: pd.DataFrame
        baseline_biomass: pd.DataFrame
        baseline_tillers: pd.DataFrame
        schedule: pd.DataFrame
        qa: pd.DataFrame

    def load_experiment_data(
        workbook_path: Path,
        *,
        dry_matter_policy: str = "recorded",
    ) -> ExperimentData:
        if dry_matter_policy not in {"recorded", "ratio", "exclude"}:
            raise ValueError("dry_matter_policy debe ser recorded, ratio o exclude")

        raw_ms = pd.read_excel(  # pyright: ignore[reportUnknownMemberType]
            workbook_path, sheet_name="Datos_MS", header=4
        )
        raw_quality = pd.read_excel(  # pyright: ignore[reportUnknownMemberType]
            workbook_path, sheet_name="Calidad", header=0
        )
        raw_harvest = pd.read_excel(  # pyright: ignore[reportUnknownMemberType]
            workbook_path, sheet_name="Datos_Rto", header=4
        )

        ms = normalize_design_columns(raw_ms)
        ms["Muestra"] = pd.to_numeric(ms["Muestra"], errors="coerce").astype("Int64")
        ms["Fecha"] = pd.to_datetime(ms["Fecha"], errors="coerce")
        ms = coerce_numeric_columns(
            ms,
            [
                "Peso verde (1m)",
                "Peso verde (muestra)",
                "Peso Seco",
                "%MS",
                "KgMS/ha",
                "Macollos/30 cm",
                "Macollos/m2",
            ],
        )

        # Las filas sin M0–M5 son la caracterización general del 12 de junio.
        baseline_ms = ms.loc[~ms["Tratamiento"].isin(TREATMENTS)].copy()
        experimental_ms = ms.loc[ms["Tratamiento"].isin(TREATMENTS)].copy()

        experimental_ms["dm_ratio_pct"] = (
            100.0
            * experimental_ms["Peso Seco"]
            / experimental_ms["Peso verde (muestra)"]
        )
        experimental_ms["dm_issue"] = experimental_ms["Muestra"].isin(
            DM_ISSUE_SAMPLE_IDS
        )
        experimental_ms["dm_pct_used"] = experimental_ms["%MS"]
        experimental_ms["biomass_kg_ha_used"] = experimental_ms["KgMS/ha"]

        if dry_matter_policy == "ratio":
            mask = experimental_ms["dm_issue"]
            experimental_ms.loc[mask, "dm_pct_used"] = experimental_ms.loc[
                mask, "dm_ratio_pct"
            ]
            experimental_ms.loc[mask, "biomass_kg_ha_used"] = (
                experimental_ms.loc[mask, "Peso verde (1m)"]
                * experimental_ms.loc[mask, "dm_pct_used"]
                / 100.0
                * 10.0
                / BIOMASS_AREA_M2
            )
        elif dry_matter_policy == "exclude":
            mask = experimental_ms["dm_issue"]
            experimental_ms.loc[mask, ["dm_pct_used", "biomass_kg_ha_used"]] = np.nan

        quality = normalize_design_columns(raw_quality)
        quality["Muestra"] = pd.to_numeric(quality["Muestra"], errors="coerce").astype(
            "Int64"
        )
        quality["Fecha"] = pd.to_datetime(quality["Fecha"], errors="coerce")
        quality = coerce_numeric_columns(quality, ["% N", "% FDA ", "% FDN "])
        experimental_quality = quality.loc[
            quality["Tratamiento"].isin(TREATMENTS)
        ].copy()

        key = ["Fecha", "Muestra", "Condición", "Tratamiento", "Repetición"]
        longitudinal = experimental_ms[
            key
            + [
                "%MS",
                "dm_ratio_pct",
                "dm_pct_used",
                "KgMS/ha",
                "biomass_kg_ha_used",
                "dm_issue",
            ]
        ].merge(
            experimental_quality[
                key + ["% N", "% FDA ", "% FDN ", "REG. DE LAB.", "Origen del dato"]
            ],
            on=key,
            how="left",
            validate="one_to_one",
        )

        longitudinal = longitudinal.rename(
            columns={
                "Fecha": "date",
                "Muestra": "sample_id",
                "Condición": "sector",
                "Tratamiento": "treatment",
                "Repetición": "block",
                "%MS": "dm_pct_recorded",
                "KgMS/ha": "biomass_kg_ha_recorded",
                "% N": "n_pct",
                "% FDA ": "adf_pct",
                "% FDN ": "ndf_pct",
                "REG. DE LAB.": "lab_id",
                "Origen del dato": "data_origin",
            }
        )
        longitudinal["q_kg_n_ha"] = (
            longitudinal["biomass_kg_ha_used"] * longitudinal["n_pct"] / 100.0
        )
        biomass_t_ha = longitudinal["biomass_kg_ha_used"] / 1000.0
        longitudinal["nni_revised"] = longitudinal["n_pct"] / (
            3.93 * biomass_t_ha.pow(-0.42)
        )
        longitudinal["nni_historical"] = longitudinal["n_pct"] / (
            4.8 * biomass_t_ha.pow(-0.32)
        )
        longitudinal["plot_id"] = (
            longitudinal["sector"]
            + "_"
            + longitudinal["block"]
            + "_"
            + longitudinal["treatment"]
        )
        longitudinal["date_label"] = longitudinal["date"].map(DATE_LABELS)

        # Cosecha final: se renombran las columnas por posición porque las tres
        # submuestras de 100 semillas tienen encabezados duplicados/inconsistentes.
        harvest = normalize_design_columns(raw_harvest)
        harvest = harvest.loc[harvest["Tratamiento"].isin(TREATMENTS)].copy()
        harvest["Muestra"] = pd.to_numeric(harvest["Muestra"], errors="coerce").astype(
            "Int64"
        )
        harvest["Fecha"] = pd.to_datetime(harvest["Fecha"], errors="coerce")
        cols = list(harvest.columns)
        rename_by_position = {
            cols[0]: "date",
            cols[1]: "sample_id",
            cols[2]: "sector",
            cols[3]: "treatment",
            cols[4]: "block",
            cols[5]: "panicle_count",
            cols[6]: "dirty_mass_g",
            cols[7]: "clean_mass_g",
            cols[8]: "w100_1_g",
            cols[9]: "w100_2_g",
            cols[10]: "w100_3_g",
            cols[11]: "w1000_workbook_g",
        }
        harvest = harvest.rename(columns=rename_by_position)[
            list(rename_by_position.values())
        ].copy()
        harvest = coerce_numeric_columns(
            harvest,
            [
                "panicle_count",
                "dirty_mass_g",
                "clean_mass_g",
                "w100_1_g",
                "w100_2_g",
                "w100_3_g",
                "w1000_workbook_g",
            ],
        )

        harvest["w1000_g"] = (
            harvest[["w100_1_g", "w100_2_g", "w100_3_g"]].mean(axis=1) * 10.0
        )
        harvest["panicle_density_m2"] = harvest["panicle_count"] / HARVEST_AREA_M2
        harvest["dirty_yield_kg_ha"] = harvest["dirty_mass_g"] * 10.0 / HARVEST_AREA_M2
        harvest["clean_yield_kg_ha"] = harvest["clean_mass_g"] * 10.0 / HARVEST_AREA_M2
        harvest["clean_recovery"] = harvest["clean_mass_g"] / harvest["dirty_mass_g"]
        harvest["cleaning_loss_pct"] = 100.0 * (1.0 - harvest["clean_recovery"])
        harvest["estimated_seeds_per_panicle"] = (
            1000.0
            * harvest["clean_mass_g"]
            / (harvest["w1000_g"] * harvest["panicle_count"])
        )
        harvest["plot_id"] = (
            harvest["sector"] + "_" + harvest["block"] + "_" + harvest["treatment"]
        )

        final_biomass = longitudinal.loc[
            longitudinal["date"].eq(DATES[-1]),
            ["plot_id", "biomass_kg_ha_used", "dm_issue"],
        ]
        harvest = harvest.merge(
            final_biomass,
            on="plot_id",
            how="left",
            validate="one_to_one",
        )
        harvest["harvest_index_pct"] = (
            100.0 * harvest["clean_yield_kg_ha"] / harvest["biomass_kg_ha_used"]
        )
        water_mm = harvest["sector"].map({"Secano": 510.0, "Riego": 675.0})
        harvest["apparent_water_productivity"] = harvest["clean_yield_kg_ha"] / water_mm

        m0_reference = harvest.loc[
            harvest["treatment"].eq("M0"),
            ["sector", "block", "clean_yield_kg_ha"],
        ].rename(columns={"clean_yield_kg_ha": "m0_yield_same_block"})
        harvest = harvest.merge(
            m0_reference,
            on=["sector", "block"],
            how="left",
            validate="many_to_one",
        )
        harvest["agronomic_efficiency"] = np.where(
            harvest["treatment"].eq("M0"),
            np.nan,
            (harvest["clean_yield_kg_ha"] - harvest["m0_yield_same_block"]) / 200.0,
        )

        for frame in [longitudinal, harvest]:
            frame["sector"] = categorical(frame["sector"], SECTORS)
            frame["block"] = categorical(frame["block"], BLOCKS)
            frame["treatment"] = categorical(frame["treatment"], TREATMENTS)
        longitudinal["date"] = pd.Categorical(
            longitudinal["date"], categories=DATES, ordered=True
        )

        seed_weight_long = harvest.melt(
            id_vars=["plot_id", "sector", "block", "treatment", "sample_id"],
            value_vars=["w100_1_g", "w100_2_g", "w100_3_g"],
            var_name="technical_replicate",
            value_name="w100_g",
        )

        baseline_biomass = baseline_ms.loc[
            baseline_ms["KgMS/ha"].notna(),
            ["Fecha", "Muestra", "Condición", "Repetición", "KgMS/ha"],
        ].rename(
            columns={
                "Fecha": "date",
                "Muestra": "sample_id",
                "Condición": "sector",
                "Repetición": "block",
                "KgMS/ha": "biomass_kg_ha",
            }
        )
        baseline_tillers = baseline_ms.loc[
            baseline_ms["Macollos/m2"].notna(),
            ["Fecha", "Muestra", "Condición", "Repetición", "Macollos/m2"],
        ].rename(
            columns={
                "Fecha": "date",
                "Muestra": "sample_id",
                "Condición": "sector",
                "Repetición": "replicate_label",
                "Macollos/m2": "tillers_m2",
            }
        )

        schedule_rows: list[dict[str, object]] = []
        for treatment, date_strings in CANONICAL_SCHEDULE.items():
            dates = pd.to_datetime(list(date_strings))
            schedule_rows.append(
                {
                    "treatment": treatment,
                    "first_application": dates.min() if len(dates) else pd.NaT,
                    "second_application": dates.max() if len(dates) else pd.NaT,
                    "extra_n_kg_ha": 0 if treatment == "M0" else 200,
                }
            )
        schedule = pd.DataFrame(schedule_rows)

        qa_rows = [
            ("filas longitudinales", len(longitudinal), 144),
            ("parcelas longitudinales", longitudinal["plot_id"].nunique(), 48),
            (
                "fechas por parcela",
                int(
                    longitudinal.groupby("plot_id", observed=True)["date"]
                    .nunique()
                    .min()
                ),
                3,
            ),
            ("filas de cosecha", len(harvest), 48),
            ("parcelas de cosecha", harvest["plot_id"].nunique(), 48),
            (
                "duplicados parcela-fecha",
                int(
                    longitudinal.duplicated(
                        ["date", "sector", "block", "treatment"]
                    ).sum()
                ),
                0,
            ),
            (
                "duplicados de cosecha",
                int(harvest.duplicated(["sector", "block", "treatment"]).sum()),
                0,
            ),
            ("resultados N faltantes", int(longitudinal["n_pct"].isna().sum()), 1),
            ("registros %MS señalados", int(longitudinal["dm_issue"].sum()), 2),
            (
                "máxima diferencia PMS recalculado-libro",
                float((harvest["w1000_g"] - harvest["w1000_workbook_g"]).abs().max()),
                0.0,
            ),
        ]
        qa = pd.DataFrame(qa_rows, columns=["check", "observed", "expected"])
        qa["passes"] = np.isclose(
            pd.to_numeric(qa["observed"]),
            pd.to_numeric(qa["expected"]),
            equal_nan=True,
        )
        if not qa["passes"].all():
            raise AssertionError(qa.loc[~qa["passes"]].to_string(index=False))

        return ExperimentData(
            workbook_path=workbook_path,
            longitudinal=longitudinal.sort_values(
                ["sector", "block", "treatment", "date"]
            ).reset_index(drop=True),
            harvest=harvest.sort_values(["sector", "block", "treatment"]).reset_index(
                drop=True
            ),
            seed_weight_long=seed_weight_long.reset_index(drop=True),
            baseline_biomass=baseline_biomass.reset_index(drop=True),
            baseline_tillers=baseline_tillers.reset_index(drop=True),
            schedule=schedule,
            qa=qa,
        )

    WORKBOOK_PATH = locate_workbook()
    data = load_experiment_data(
        WORKBOOK_PATH,
        dry_matter_policy=DRY_MATTER_POLICY,
    )
    print("Libro:", data.workbook_path)
    print("Política de materia seca:", DRY_MATTER_POLICY)
    display_output(data.qa)
    yield "load_data"

    # Notebook step: flagged_dry_matter
    flagged_dm = data.longitudinal.loc[
        data.longitudinal["dm_issue"],
        [
            "sample_id",
            "sector",
            "block",
            "treatment",
            "date",
            "dm_pct_recorded",
            "dm_ratio_pct",
            "biomass_kg_ha_recorded",
            "biomass_kg_ha_used",
        ],
    ].copy()
    display_output(flagged_dm)
    yield "flagged_dry_matter"

    # Notebook step: baseline_summary
    baseline_summary = pd.DataFrame(
        {
            "biomass_t_ha": (
                data.baseline_biomass.groupby("sector", observed=True)[
                    "biomass_kg_ha"
                ].mean()
                / 1000.0
            ),
            "tillers_m2": data.baseline_tillers.groupby("sector", observed=True)[
                "tillers_m2"
            ].mean(),
            "n_biomass_samples": data.baseline_biomass.groupby(
                "sector", observed=True
            ).size(),
            "n_tiller_samples": data.baseline_tillers.groupby(
                "sector", observed=True
            ).size(),
        }
    )
    display_output(baseline_summary.round(2))
    yield "baseline_summary"

    # Notebook step: schedule
    display_output(data.schedule)

    def plot_schedule_and_cumulative_n() -> None:
        study_start = pd.Timestamp("2025-04-01")
        study_end = pd.Timestamp("2025-11-30")
        common_n_periods = [
            (pd.Timestamp(start), pd.Timestamp(end), dose)
            for start, end, dose in COMMON_N_APPLICATIONS
        ]
        common_n_uncertain_periods = [
            (start, end, dose, f"≈{dose:.0f} común")
            for start, end, dose in common_n_periods
            if start != end
        ]
        exact_common_events = {
            start: dose for start, end, dose in common_n_periods if start == end
        }
        if set(exact_common_events) != {pd.Timestamp("2025-07-01")}:
            raise AssertionError(
                "Se esperaba una aplicación común fechada el 1.º de julio."
            )
        grazing_closure = next(iter(exact_common_events))
        exact_common_n = exact_common_events[grazing_closure]
        common_n_total = COMMON_N_TOTAL_KG_HA
        fertilized_n_total = common_n_total + EXPERIMENTAL_N_TOTAL_KG_HA
        row_height = 0.66
        dose_scale = row_height / fertilized_n_total
        common_color = "0.58"
        uncertainty_color = "0.62"
        separator_color = "0.82"
        row_positions = {
            treatment: float(len(TREATMENTS) - index - 1)
            for index, treatment in enumerate(TREATMENTS)
        }

        def common_ramp_n(moment: pd.Timestamp) -> float:
            accumulated = 0.0
            for start, end, dose, _label in common_n_uncertain_periods:
                if moment >= end:
                    accumulated += dose
                elif moment > start:
                    elapsed = (moment - start) / (end - start)
                    accumulated += dose * float(elapsed)
            return accumulated

        def treatment_path(
            application_dates: list[pd.Timestamp],
        ) -> tuple[list[pd.Timestamp], np.ndarray, np.ndarray]:
            exact_events: dict[pd.Timestamp, tuple[float, float]] = {
                date: (dose, 0.0) for date, dose in exact_common_events.items()
            }
            for application_date in application_dates:
                common_delta, experimental_delta = exact_events.get(
                    application_date, (0.0, 0.0)
                )
                exact_events[application_date] = (
                    common_delta,
                    experimental_delta + 100.0,
                )

            knots = {
                study_start,
                study_end,
                *[start for start, _end, _dose, _label in common_n_uncertain_periods],
                *[end for _start, end, _dose, _label in common_n_uncertain_periods],
                *exact_events,
            }
            ordered_knots = sorted(knots)
            x_path: list[pd.Timestamp] = []
            common_path: list[float] = []
            total_path: list[float] = []
            exact_common_accumulated = 0.0
            experimental_accumulated = 0.0

            for moment in ordered_knots:
                common_before = common_ramp_n(moment) + exact_common_accumulated
                x_path.append(moment)
                common_path.append(common_before)
                total_path.append(common_before + experimental_accumulated)

                common_delta, experimental_delta = exact_events.get(moment, (0.0, 0.0))
                if common_delta or experimental_delta:
                    exact_common_accumulated += common_delta
                    experimental_accumulated += experimental_delta
                    x_path.append(moment)
                    common_path.append(common_ramp_n(moment) + exact_common_accumulated)
                    total_path.append(
                        common_ramp_n(moment)
                        + exact_common_accumulated
                        + experimental_accumulated
                    )

            return x_path, np.asarray(common_path), np.asarray(total_path)

        fig, ax = mpl.subplots(figsize=(13.6, 8.2))

        for start, end, _dose, _label in common_n_uncertain_periods:
            ax.axvspan(start, end, color="0.88", alpha=0.34, linewidth=0, zorder=0)

        for boundary in [0.83, 1.83, 2.83, 3.83, 4.83]:
            ax.axhline(
                boundary,
                color=separator_color,
                linestyle=(0, (1.2, 4.0)),
                linewidth=REFERENCE_LINEWIDTH,
                zorder=0,
            )

        for sample_date in DATES:
            ax.axvline(
                sample_date,
                color=uncertainty_color,
                linestyle=(0, (2.0, 3.0)),
                linewidth=REFERENCE_LINEWIDTH,
                alpha=0.85,
                zorder=1,
            )

        ax.axvline(
            grazing_closure,
            color="0.48",
            linewidth=REFERENCE_LINEWIDTH,
            alpha=0.9,
            zorder=1,
        )

        application_labels: dict[int, str] = {6: "jun", 7: "jul", 8: "ago", 9: "sep"}
        treatment_colors = dict(zip(FERTILIZED, PLOT_PALETTE[1:6], strict=True))

        for treatment in TREATMENTS:
            baseline = row_positions[treatment]
            row = data.schedule.loc[data.schedule["treatment"].eq(treatment)].iloc[0]
            application_dates = (
                []
                if treatment == "M0"
                else [
                    pd.Timestamp(row["first_application"]),
                    pd.Timestamp(row["second_application"]),
                ]
            )
            x_path, common_path, total_path = treatment_path(application_dates)
            scaled_common = baseline + common_path * dose_scale
            scaled_total = baseline + total_path * dose_scale
            line_color = (
                common_color if treatment == "M0" else treatment_colors[treatment]
            )

            ax.fill_between(
                x_path,
                baseline,
                scaled_common,
                color=common_color,
                alpha=0.29,
                linewidth=0,
                zorder=2,
            )
            if treatment != "M0":
                ax.fill_between(
                    x_path,
                    scaled_common,
                    scaled_total,
                    color=line_color,
                    alpha=0.11,
                    linewidth=0,
                    zorder=2,
                )
            ax.plot(
                x_path,
                scaled_total,
                color=line_color,
                linewidth=DATA_LINEWIDTH,
                solid_capstyle="round",
                zorder=4,
            )

            for index in range(len(x_path) - 1):
                start = x_path[index]
                end = x_path[index + 1]
                if start == end:
                    continue
                midpoint = start + (end - start) / 2
                if any(
                    uncertain_start <= midpoint <= uncertain_end
                    for uncertain_start, uncertain_end, _dose, _label in common_n_uncertain_periods
                ):
                    ax.plot(
                        [start, end],
                        [scaled_total[index], scaled_total[index + 1]],
                        color=uncertainty_color,
                        linestyle=(0, (2.1, 2.3)),
                        linewidth=SECONDARY_LINEWIDTH,
                        zorder=5,
                    )

            july_common_before_n = common_ramp_n(grazing_closure)
            july_common_before = baseline + july_common_before_n * dose_scale
            july_common_after = (
                baseline + (july_common_before_n + exact_common_n) * dose_scale
            )
            ax.vlines(
                grazing_closure,
                july_common_before,
                july_common_after,
                color=common_color,
                linewidth=DATA_LINEWIDTH,
                zorder=6,
            )

            label_x = study_start - pd.Timedelta(days=5)
            row_center = baseline + row_height / 2
            final_total = common_n_total if treatment == "M0" else fertilized_n_total
            ax.text(
                label_x,
                row_center + 0.13,
                treatment,
                ha="right",
                va="center",
                fontsize=11,
                fontweight="bold",
                clip_on=False,
            )
            ax.text(
                label_x,
                row_center - 0.08,
                f"≈{final_total:.0f} kg",
                ha="right",
                va="center",
                fontsize=9.5,
                clip_on=False,
            )
            ax.text(
                label_x,
                row_center - 0.26,
                "solo común" if treatment == "M0" else "164 + 200",
                ha="right",
                va="center",
                fontsize=8.5,
                color="0.48",
                clip_on=False,
            )

            if treatment == "M0":
                ax.text(
                    pd.Timestamp("2025-04-03"),
                    baseline + 0.52,
                    "sin N experimental adicional",
                    ha="left",
                    va="center",
                    fontsize=9.25,
                    color="0.40",
                )
            else:
                for application_date in application_dates:
                    ax.text(
                        application_date,
                        baseline - 0.055,
                        f"{application_date.day} {application_labels[application_date.month]}",
                        ha="center",
                        va="top",
                        fontsize=8.75,
                        color="0.30",
                    )

        month_ticks = pd.date_range(
            "2025-04-01", "2025-11-01", freq="MS"
        ) + pd.Timedelta(days=14)
        month_labels = ["abr", "may", "jun", "jul", "ago", "sep", "oct", "nov"]
        ax.set_xticks(month_ticks, month_labels)
        ax.set_xlim(study_start, study_end)
        ax.set_ylim(-0.55, 5.82)
        ax.set_yticks([])
        ax.grid(False)
        ax.spines[["left", "right", "top"]].set_visible(False)

        bottom_event_y = -0.37
        for start, end, _dose, label in common_n_uncertain_periods:
            ax.text(
                start + (end - start) / 2,
                bottom_event_y,
                label,
                ha="center",
                va="top",
                fontsize=8.75,
                color="0.48",
            )
        ax.text(
            grazing_closure,
            bottom_event_y,
            "1 jul · +52 común\ncierre del pastoreo",
            ha="center",
            va="top",
            fontsize=8.75,
            color="0.38",
        )
        for sample_date in DATES:
            event_label = DATE_LABELS[sample_date]
            if sample_date == DATES[-1]:
                event_label += "\nmuestreo y cosecha"
            else:
                event_label += "\nmuestreo"
            ax.text(
                sample_date,
                bottom_event_y,
                event_label,
                ha="center",
                va="top",
                fontsize=8.75,
                color="0.38",
            )

        legend_handles = [
            Patch(
                facecolor=common_color,
                alpha=0.29,
                edgecolor="none",
                label="N común acumulado",
            ),
            Line2D(
                [0],
                [0],
                color=PLOT_PALETTE[3],
                linewidth=DATA_LINEWIDTH,
                label="N total aplicado",
            ),
            Line2D(
                [0],
                [0],
                color=uncertainty_color,
                linestyle=(0, (2.1, 2.3)),
                linewidth=SECONDARY_LINEWIDTH,
                label="tramo con fecha común no consignada",
            ),
        ]
        fig.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.52, 0.885),
            ncol=3,
            columnspacing=2.0,
            handlelength=2.3,
        )
        add_figure_header(
            fig,
            "Cronograma de aplicaciones y N aplicado acumulado por tratamiento",
            subtitle=("común ≈164 + experimental (0 o 200) = ≈164–364 kg N ha⁻¹"),
        )
        add_figure_note(
            fig,
            (
                "Las rampas ubican aplicaciones comunes dentro de intervalos con fecha no consignada; "
                "no representan liberación gradual. Al 16 sep: M1–M4 ≈364 y M5 ≈264 kg N ha⁻¹."
            ),
        )
        fig.subplots_adjust(
            left=0.15,
            right=0.985,
            bottom=0.145,
            top=0.80,
        )
        save_figure(fig, "figura_01_cronograma_y_n_acumulado")
        mpl.show()
        mpl.close(fig)

    plot_schedule_and_cumulative_n()
    yield "schedule"

    # Notebook step: water_inputs
    water_inputs = pd.DataFrame(
        {
            "month": ["Jun", "Jul", "Ago", "Sep", "Oct", "Nov"],
            "precipitation_mm": [43, 62, 101, 89, 141, 74],
            "supplemental_irrigation_mm": [15, 0, 0, 30, 90, 30],
        }
    )
    water_inputs["irrigated_total_mm"] = (
        water_inputs["precipitation_mm"] + water_inputs["supplemental_irrigation_mm"]
    )
    assert water_inputs["precipitation_mm"].sum() == 510
    assert water_inputs["supplemental_irrigation_mm"].sum() == 165
    assert water_inputs["irrigated_total_mm"].sum() == 675
    display_output(water_inputs)

    positions = np.arange(len(water_inputs), dtype=float)
    bar_width = 0.28
    bar_offset = 0.18
    precipitation_positions = positions - bar_offset
    irrigated_positions = positions + bar_offset
    precipitation_color = PLOT_PALETTE[0]
    irrigation_color = PLOT_PALETTE[6]
    fig, ax = mpl.subplots(figsize=(10.8, 5.7))
    ax.bar(
        precipitation_positions,
        water_inputs["precipitation_mm"],
        width=bar_width,
        color=precipitation_color,
        label="Precipitación (ambos sectores)",
    )
    ax.bar(
        irrigated_positions,
        water_inputs["supplemental_irrigation_mm"],
        width=bar_width,
        bottom=water_inputs["precipitation_mm"],
        color=irrigation_color,
        label="Riego suplementario",
    )
    for position, precipitation, irrigation, total in zip(
        positions,
        water_inputs["precipitation_mm"].to_numpy(dtype=float),
        water_inputs["supplemental_irrigation_mm"].to_numpy(dtype=float),
        water_inputs["irrigated_total_mm"].to_numpy(dtype=float),
        strict=True,
    ):
        if irrigation > 0:
            ax.text(
                position - bar_offset,
                precipitation + 3,
                f"{precipitation:.0f}",
                ha="center",
                va="bottom",
                fontsize=8.5,
                color=precipitation_color,
            )
            ax.text(
                position + bar_offset,
                precipitation + irrigation / 2,
                f"+{irrigation:.0f}",
                ha="center",
                va="center",
                fontsize=8.5,
                color="white",
            )
        ax.text(
            position,
            total + 5,
            f"{total:.0f}",
            ha="center",
            va="bottom",
            fontsize=9.5,
        )

    ax.text(
        0.02,
        0.96,
        "Secano: 510 mm\nRiego: 675 mm (165 mm adicionales)",
        transform=ax.transAxes,
        ha="left",
        va="top",
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": mpl.rcParams["axes.edgecolor"],
            "alpha": 0.90,
        },
    )
    ax.set_xticks(positions, water_inputs["month"])
    ax.set_ylabel("Agua aportada (mm mes⁻¹)")
    ax.set_xlabel("Mes de 2025")
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=2,
    )
    add_figure_header(
        fig,
        "Precipitación y riego suplementario, junio–noviembre",
    )
    add_figure_note(
        fig,
        (
            "La barra naranja desplazada representa exclusivamente el riego suplementario y comienza "
            "a la altura de la precipitación común. El total mensual del sector regado aparece centrado; "
            "cuando hubo riego también se indican por separado la precipitación y el aporte adicional. "
            "Los aportes brutos no equivalen al agua utilizada por el cultivo."
        ),
    )
    fig.subplots_adjust(
        left=0.09,
        right=0.98,
        bottom=0.25,
        top=0.87,
    )
    save_figure(fig, "figura_02_aportes_mensuales_de_agua")
    mpl.show()
    mpl.close(fig)
    yield "water_inputs"

    # Notebook step: rcbd_functions
    @dataclass
    class RCBDResult:
        outcome: str
        treatments: tuple[str, ...]
        frame: pd.DataFrame
        fit: Any
        anova: pd.DataFrame
        means: pd.DataFrame
        pairwise: pd.DataFrame
        cv_pct: float

    def scalar_psturng_fn(q_value: float, groups: int, df: float) -> float:
        value = psturng_fn(q_value, groups, df)
        return float(np.asarray(value).reshape(-1)[0])

    def maximal_nonsignificant_cliques(
        levels: Sequence[str],
        nonsignificant: dict[tuple[str, str], bool],
    ) -> list[set[str]]:
        nodes = list(levels)
        cliques: list[set[str]] = []
        for size in range(1, len(nodes) + 1):
            for subset_tuple in combinations(nodes, size):
                subset = set(subset_tuple)
                if all(
                    nonsignificant.get((a, b) if a <= b else (b, a), False)
                    for a, b in combinations(subset, 2)
                ):
                    cliques.append(subset)
        maximal = [
            clique for clique in cliques if not any(clique < other for other in cliques)
        ]
        # Eliminar duplicados preservando contenido.
        unique: list[set[str]] = []
        for clique in maximal:
            if clique not in unique:
                unique.append(clique)
        return unique

    def compact_letters(
        means: pd.DataFrame,
        pairwise: pd.DataFrame,
        *,
        alpha: float = ALPHA,
    ) -> dict[str, str]:
        ordered = means.sort_values("estimate", ascending=False)["treatment"].tolist()
        nonsig: dict[tuple[str, str], bool] = {}
        for raw_row in pairwise.itertuples(index=False):
            row = cast(Any, raw_row)
            nonsig[tuple(sorted((row.group1, row.group2)))] = row.p_tukey >= alpha
        cliques = maximal_nonsignificant_cliques(ordered, nonsig)
        cliques.sort(
            key=lambda clique: max(
                means.set_index("treatment").loc[list(clique), "estimate"]
            ),
            reverse=True,
        )
        alphabet = list("abcdefghijklmnopqrstuvwxyz")
        if len(cliques) > len(alphabet):
            raise RuntimeError("Demasiadas clases para el alfabeto compacto")
        letters = {level: "" for level in ordered}
        for letter, clique in zip(alphabet, cliques):
            for level in clique:
                letters[level] += letter
        return letters

    def adjusted_treatment_means(
        fit: Any,
        treatments: Sequence[str],
        blocks: Sequence[str] = BLOCKS,
    ) -> tuple[pd.DataFrame, dict[str, np.ndarray], np.ndarray]:
        beta = fit.params.to_numpy()
        covariance = fit.cov_params().to_numpy()
        design_info = fit.model.data.design_info

        vectors: dict[str, np.ndarray] = {}
        rows: list[dict[str, object]] = []
        for treatment in treatments:
            new = pd.DataFrame(
                {
                    "treatment": [treatment] * len(blocks),
                    "block": list(blocks),
                }
            )
            new["treatment"] = categorical(new["treatment"], treatments)
            new["block"] = categorical(new["block"], blocks)
            design = np.asarray(patsy_api.build_design_matrices([design_info], new)[0])
            xbar = design.mean(axis=0)
            estimate = float(xbar @ beta)
            se = float(np.sqrt(xbar @ covariance @ xbar))
            vectors[treatment] = xbar
            rows.append(
                {
                    "treatment": treatment,
                    "estimate": estimate,
                    "se": se,
                    "ci_low": estimate - stats.t.ppf(0.975, fit.df_resid) * se,
                    "ci_high": estimate + stats.t.ppf(0.975, fit.df_resid) * se,
                }
            )
        return pd.DataFrame(rows), vectors, covariance

    def fit_rcbd(
        frame: pd.DataFrame,
        *,
        outcome: str,
        treatments: Sequence[str],
    ) -> RCBDResult:
        subset = frame.loc[frame["treatment"].astype(str).isin(treatments)].copy()
        subset = subset.dropna(subset=[outcome, "block", "treatment"])
        subset["treatment"] = categorical(subset["treatment"], treatments)
        subset["block"] = categorical(subset["block"], BLOCKS)

        fit = smf_api.ols(f"{outcome} ~ C(treatment) + C(block)", data=subset).fit()
        anova = sm_api.stats.anova_lm(fit, typ=2)
        means, vectors, covariance = adjusted_treatment_means(
            fit, treatments=treatments
        )

        pairs: list[dict[str, object]] = []
        k = len(treatments)
        q_critical = float(qsturng_fn(1.0 - ALPHA, k, fit.df_resid))
        for group1, group2 in combinations(treatments, 2):
            contrast = vectors[group1] - vectors[group2]
            difference = float(contrast @ fit.params.to_numpy())
            se_difference = float(np.sqrt(contrast @ covariance @ contrast))
            q_stat = math.sqrt(2.0) * abs(difference) / se_difference
            p_tukey = scalar_psturng_fn(q_stat, k, fit.df_resid)
            half_width = q_critical * se_difference / math.sqrt(2.0)
            pairs.append(
                {
                    "group1": group1,
                    "group2": group2,
                    "difference": difference,
                    "se": se_difference,
                    "ci_low": difference - half_width,
                    "ci_high": difference + half_width,
                    "p_tukey": p_tukey,
                    "reject": p_tukey < ALPHA,
                }
            )
        pairwise = pd.DataFrame(pairs)
        global_p = float(anova.loc["C(treatment)", "PR(>F)"])
        if global_p < ALPHA:
            letters = compact_letters(means, pairwise)
            means["tukey_group"] = means["treatment"].map(letters)
        else:
            means["tukey_group"] = "—"
        means["n"] = means["treatment"].map(
            subset.groupby("treatment", observed=True)[outcome].count()
        )

        mse = float(anova.loc["Residual", "sum_sq"] / anova.loc["Residual", "df"])
        cv_pct = 100.0 * math.sqrt(mse) / float(cast(Any, subset[outcome].mean()))
        return RCBDResult(
            outcome=outcome,
            treatments=tuple(treatments),
            frame=subset,
            fit=fit,
            anova=anova,
            means=means,
            pairwise=pairwise,
            cv_pct=cv_pct,
        )

    def rcbd_result_row(
        result: RCBDResult,
        *,
        sector: str,
        date: pd.Timestamp | None,
        comparison: str,
    ) -> dict[str, object]:
        return {
            "outcome": result.outcome,
            "label": OUTCOME_LABELS.get(result.outcome, result.outcome),
            "sector": sector,
            "date": date,
            "comparison": comparison,
            "n": len(result.frame),
            "p_treatment": float(cast(Any, result.anova.loc["C(treatment)", "PR(>F)"])),
            "p_block": float(cast(Any, result.anova.loc["C(block)", "PR(>F)"])),
            "cv_pct": result.cv_pct,
        }

    def add_bh_within_families(
        frame: pd.DataFrame,
        *,
        p_column: str,
        family_columns: Sequence[str],
        output_column: str = "p_bh",
    ) -> pd.DataFrame:
        """Attach FDR-adjusted p-values without mixing inferential families."""
        result = frame.copy()
        result[output_column] = np.nan
        grouped = result.groupby(list(family_columns), observed=True, dropna=False)
        for indices in grouped.groups.values():
            index = list(indices)
            result.loc[index, output_column] = benjamini_hochberg(
                result.loc[index, p_column].astype(float).to_numpy()
            )
        return result

    yield "rcbd_functions"

    # Notebook step: longitudinal_anova
    LONGITUDINAL_OUTCOMES = [
        "biomass_kg_ha_used",
        "n_pct",
        "q_kg_n_ha",
        "nni_revised",
    ]

    longitudinal_rcbd_rows: list[dict[str, object]] = []
    longitudinal_rcbd_models: dict[tuple[str, pd.Timestamp, str, str], RCBDResult] = {}

    for outcome in LONGITUDINAL_OUTCOMES:
        for date in DATES:
            for sector in SECTORS:
                frame = data.longitudinal.loc[
                    data.longitudinal["date"].astype("datetime64[ns]").eq(date)
                    & data.longitudinal["sector"].astype(str).eq(sector)
                ].copy()
                for treatments, comparison in [
                    (FERTILIZED, "M1–M5"),
                    (TREATMENTS, "M0–M5"),
                ]:
                    result = fit_rcbd(
                        frame,
                        outcome=outcome,
                        treatments=treatments,
                    )
                    key = (outcome, date, sector, comparison)
                    longitudinal_rcbd_models[key] = result
                    longitudinal_rcbd_rows.append(
                        rcbd_result_row(
                            result,
                            sector=sector,
                            date=date,
                            comparison=comparison,
                        )
                    )

    longitudinal_rcbd = pd.DataFrame(longitudinal_rcbd_rows)
    longitudinal_rcbd["date_label"] = longitudinal_rcbd["date"].map(DATE_LABELS)
    longitudinal_rcbd["variable_family"] = np.where(
        longitudinal_rcbd["outcome"].isin(["biomass_kg_ha_used", "n_pct"]),
        "secundaria_primitiva",
        "apoyo_derivado",
    )
    longitudinal_rcbd["inference_tier"] = np.where(
        longitudinal_rcbd["comparison"].eq("M1–M5"),
        longitudinal_rcbd["variable_family"],
        "complementaria",
    )
    longitudinal_rcbd = add_bh_within_families(
        longitudinal_rcbd,
        p_column="p_treatment",
        family_columns=["sector", "comparison", "variable_family"],
    )

    display_output(
        longitudinal_rcbd[
            [
                "label",
                "date_label",
                "sector",
                "comparison",
                "n",
                "p_treatment",
                "p_bh",
                "p_block",
                "cv_pct",
            ]
        ].round(4)
    )
    yield "longitudinal_anova"

    # Notebook step: observed_trajectories
    def treatment_trajectory_plot(
        frame: pd.DataFrame,
        *,
        outcome: str,
        treatments: Sequence[str] = TREATMENTS,
        filename_stem: str | None = None,
    ) -> None:
        treatment_order = list(treatments)
        subset = (
            frame.loc[frame["treatment"].astype(str).isin(treatment_order)]
            .dropna(subset=[outcome])
            .copy()
        )
        counts = np.asarray(
            subset.groupby(["sector", "treatment", "date"], observed=True)[
                outcome
            ].count(),
            dtype=int,
        )
        counts = counts[counts > 0]
        minimum_n = int(counts.min())
        maximum_n = int(counts.max())
        sample_size_text = (
            f"n = {minimum_n} parcelas por punto"
            if minimum_n == maximum_n
            else f"n = {minimum_n}–{maximum_n} parcelas por punto"
        )

        def mean_t_interval(values: Any) -> tuple[float, float]:
            observed_values = np.asarray(values, dtype=float)
            mean = float(observed_values.mean())
            if len(observed_values) < 2:
                return mean, mean
            half_width = float(
                stats.t.ppf(0.975, len(observed_values) - 1)
                * stats.sem(observed_values)
            )
            return mean - half_width, mean + half_width

        date_centers = np.arange(len(DATES), dtype=float)
        date_center_by_date = dict(zip(DATES, date_centers, strict=True))
        treatment_offsets = dict(
            zip(
                treatment_order,
                np.linspace(-0.31, 0.31, len(treatment_order)),
                strict=True,
            )
        )
        subset["plot_position"] = subset["date"].astype("datetime64[ns]").map(
            date_center_by_date
        ).astype(float) + subset["treatment"].astype(str).map(treatment_offsets).astype(
            float
        )
        treatment_colors = {
            treatment: TREATMENT_COLORS[treatment] for treatment in treatment_order
        }
        treatment_positions = [
            center + treatment_offsets[treatment]
            for center in date_centers
            for treatment in treatment_order
        ]
        treatment_labels = treatment_order * len(DATES)

        fig, axes = mpl.subplots(1, 2, figsize=(12.2, 5.3), sharex=True, sharey=True)
        axes_array = np.asarray(axes).ravel()
        for panel_index, sector in enumerate(SECTORS):
            ax = axes_array[panel_index]
            sns_api.pointplot(
                data=subset.loc[subset["sector"].astype(str).eq(sector)],
                x="plot_position",
                y=outcome,
                hue="treatment",
                hue_order=treatment_order,
                estimator="mean",
                errorbar=mean_t_interval,
                palette=treatment_colors,
                markers="o",
                linestyles="none",
                native_scale=True,
                capsize=CATEGORICAL_ERRORBAR_CAPSIZE,
                err_kws={"linewidth": INTERVAL_LINEWIDTH},
                markersize=MARKER_SIZE,
                legend=False,
                ax=ax,
            )
            ax.set_title(sector.upper())
            ax.set_xticks(treatment_positions, treatment_labels, minor=True)
            ax.tick_params(axis="x", which="minor", pad=5, length=0)
            ax.set_xticks(date_centers, [DATE_LABELS[date] for date in DATES])
            ax.tick_params(axis="x", which="major", pad=25, length=0)
            ax.set_xlabel("")
            if panel_index == 0:
                ax.set_ylabel(OUTCOME_LABELS[outcome])
            else:
                ax.set_ylabel("")

        add_figure_header(
            fig,
            OBSERVED_BY_DATE_TITLES[outcome],
            subtitle=f"Media ± IC t del 95 % · {sample_size_text}",
        )
        add_figure_note(
            fig,
            (
                "Fechas equidistantes en orden cronológico; los puntos no se conectan.\n"
                "M0: sin N experimental adicional. M1–M5: igual dosis adicional, distinto calendario."
            ),
        )
        fig.subplots_adjust(left=0.07, right=0.98, bottom=0.23, top=0.76, wspace=0.1)
        if filename_stem is not None:
            save_figure(fig, filename_stem)
        mpl.show()
        mpl.close(fig)

    for outcome in LONGITUDINAL_OUTCOMES:
        treatment_trajectory_plot(
            data.longitudinal,
            outcome=outcome,
            filename_stem=f"anexo_trayectorias_observadas_{outcome}",
        )
    yield "observed_trajectories"

    # Notebook step: final_outcomes
    FINAL_OUTCOMES = [
        "panicle_density_m2",
        "estimated_seeds_per_panicle",
        "w1000_g",
        "clean_yield_kg_ha",
        "harvest_index_pct",
        "cleaning_loss_pct",
    ]

    final_rcbd_rows: list[dict[str, object]] = []
    final_rcbd_models: dict[tuple[str, str, str], RCBDResult] = {}
    for outcome in FINAL_OUTCOMES:
        for sector in SECTORS:
            frame = data.harvest.loc[
                data.harvest["sector"].astype(str).eq(sector)
            ].copy()
            for treatments, comparison in [
                (FERTILIZED, "M1–M5"),
                (TREATMENTS, "M0–M5"),
            ]:
                result = fit_rcbd(
                    frame,
                    outcome=outcome,
                    treatments=treatments,
                )
                final_rcbd_models[(outcome, sector, comparison)] = result
                final_rcbd_rows.append(
                    rcbd_result_row(
                        result,
                        sector=sector,
                        date=None,
                        comparison=comparison,
                    )
                )

    # Rendimiento sin limpiar se conserva solo como sensibilidad de medición.
    for outcome, treatment_sets in [
        (
            "dirty_yield_kg_ha",
            [(FERTILIZED, "M1–M5"), (TREATMENTS, "M0–M5")],
        )
    ]:
        for sector in SECTORS:
            frame = data.harvest.loc[
                data.harvest["sector"].astype(str).eq(sector)
            ].copy()
            for treatments, comparison in treatment_sets:
                result = fit_rcbd(frame, outcome=outcome, treatments=treatments)
                final_rcbd_models[(outcome, sector, comparison)] = result
                final_rcbd_rows.append(
                    rcbd_result_row(
                        result,
                        sector=sector,
                        date=None,
                        comparison=comparison,
                    )
                )

    final_rcbd = pd.DataFrame(final_rcbd_rows)
    final_rcbd["inference_tier"] = final_rcbd["outcome"].map(
        {
            "clean_yield_kg_ha": "primaria",
            "dirty_yield_kg_ha": "sensibilidad",
            "panicle_density_m2": "secundaria",
            "estimated_seeds_per_panicle": "apoyo_reconstruido",
            "w1000_g": "secundaria",
            "harvest_index_pct": "apoyo_derivado",
            "cleaning_loss_pct": "apoyo_derivado",
        }
    )
    final_rcbd = add_bh_within_families(
        final_rcbd,
        p_column="p_treatment",
        family_columns=["sector", "comparison", "inference_tier"],
    )
    final_rcbd.loc[final_rcbd["inference_tier"].eq("primaria"), "p_bh"] = (
        final_rcbd.loc[final_rcbd["inference_tier"].eq("primaria"), "p_treatment"]
    )

    # EAN y productividad aparente del agua son transformaciones deterministas
    # del rendimiento; se resumen, pero no generan pruebas inferenciales nuevas.
    derived_descriptive = (
        data.harvest.melt(
            id_vars=["sector", "treatment"],
            value_vars=["agronomic_efficiency", "apparent_water_productivity"],
            var_name="outcome",
            value_name="value",
        )
        .dropna(subset=["value"])
        .groupby(["outcome", "sector", "treatment"], observed=True)["value"]
        .agg(mean="mean", sd="std", n="count")
        .reset_index()
    )
    derived_descriptive["label"] = derived_descriptive["outcome"].map(OUTCOME_LABELS)
    derived_descriptive["analysis_role"] = "descriptivo; transformación del rendimiento"
    display_output(
        final_rcbd[
            [
                "label",
                "sector",
                "comparison",
                "inference_tier",
                "n",
                "p_treatment",
                "p_bh",
                "p_block",
                "cv_pct",
            ]
        ].round(4)
    )
    display_output(
        Markdown(
            "**EAN y productividad aparente del agua:** resumen descriptivo únicamente; "
            "no se vuelven a contar como desenlaces inferenciales independientes."
        )
    )
    display_output(derived_descriptive.round(3))
    yield "final_outcomes"

    # Sensibilidad formal de los dos registros de materia seca discordantes.
    dry_matter_rows: list[dict[str, object]] = []
    for policy in ["recorded", "ratio", "exclude"]:
        policy_data = (
            data
            if policy == DRY_MATTER_POLICY
            else load_experiment_data(WORKBOOK_PATH, dry_matter_policy=policy)
        )
        final_date = policy_data.longitudinal.loc[
            policy_data.longitudinal["date"].astype("datetime64[ns]").eq(DATES[-1])
        ]
        for outcome in ["biomass_kg_ha_used", "q_kg_n_ha", "nni_revised"]:
            for sector in SECTORS:
                sector_frame = final_date.loc[
                    final_date["sector"].astype(str).eq(sector)
                ].copy()
                for treatments, comparison in [
                    (FERTILIZED, "M1–M5"),
                    (TREATMENTS, "M0–M5"),
                ]:
                    result = fit_rcbd(
                        sector_frame,
                        outcome=outcome,
                        treatments=treatments,
                    )
                    estimates = result.means["estimate"].astype(float)
                    dry_matter_rows.append(
                        {
                            "policy": policy,
                            "primary_policy": policy == "recorded",
                            "outcome": outcome,
                            "label": OUTCOME_LABELS[outcome],
                            "sector": sector,
                            "comparison": comparison,
                            "n": len(result.frame),
                            "p_treatment": float(
                                cast(
                                    Any,
                                    result.anova.loc["C(treatment)", "PR(>F)"],
                                )
                            ),
                            "adjusted_mean_range": float(
                                estimates.max() - estimates.min()
                            ),
                        }
                    )
    dry_matter_sensitivity = pd.DataFrame(dry_matter_rows)
    display_output(dry_matter_sensitivity.round(4))
    yield "dry_matter_sensitivity"

    # Notebook step: yield_analysis
    yield_rows = final_rcbd.loc[final_rcbd["outcome"].eq("clean_yield_kg_ha")].copy()
    display_output(
        yield_rows[["sector", "comparison", "p_treatment", "cv_pct"]].round(6)
    )

    for sector in SECTORS:
        result = final_rcbd_models[("clean_yield_kg_ha", sector, "M0–M5")]
        display_output(
            Markdown(f"**{sector}: medias ajustadas y grupos de Tukey, M0–M5**")
        )
        display_output(result.means.round(2))
    yield "yield_analysis"

    # Notebook step: yield_overview
    def yield_row_limits(
        frame: pd.DataFrame,
        row_specs: Sequence[tuple[Sequence[str], str, str]],
    ) -> list[tuple[float, float]]:
        limits: list[tuple[float, float]] = []
        for treatments, comparison, _ in row_specs:
            raw_values = frame.loc[
                frame["treatment"].astype(str).isin(treatments),
                "clean_yield_kg_ha",
            ].dropna()
            model_limits: list[float] = []
            for sector in SECTORS:
                result = final_rcbd_models[("clean_yield_kg_ha", sector, comparison)]
                model_limits.extend(result.means["ci_low"].tolist())
                model_limits.extend(result.means["ci_high"].tolist())
            lower = min(float(raw_values.min()), min(model_limits))
            upper = max(float(raw_values.max()), max(model_limits))
            padding = 0.10 * (upper - lower)
            limits.append((max(0.0, lower - padding), upper + padding))
        return limits

    def plot_yield_treatment_points(
        ax: Any,
        *,
        positions: np.ndarray,
        treatments: Sequence[str],
        sector_data: pd.DataFrame,
        means: pd.DataFrame,
        block_offsets: dict[str, float],
    ) -> None:
        for position, treatment in zip(positions, treatments, strict=True):
            observations = sector_data.loc[
                sector_data["treatment"].astype(str).eq(treatment)
            ].sort_values("block")
            point_positions = np.asarray(
                [
                    position + block_offsets[str(block)]
                    for block in observations["block"]
                ]
            )
            ax.scatter(
                point_positions,
                observations["clean_yield_kg_ha"],
                color=TREATMENT_COLORS[treatment],
                alpha=0.34,
                s=27,
                linewidths=0,
                zorder=2,
            )
            mean_row = cast(Any, means.loc[treatment])
            is_control = treatment == "M0"
            ax.errorbar(
                position,
                mean_row["estimate"],
                yerr=[
                    [mean_row["estimate"] - mean_row["ci_low"]],
                    [mean_row["ci_high"] - mean_row["estimate"]],
                ],
                color=TREATMENT_COLORS[treatment],
                marker="o",
                markerfacecolor="white" if is_control else TREATMENT_COLORS[treatment],
                markeredgecolor=TREATMENT_COLORS[treatment],
                linestyle="none",
                markersize=MARKER_SIZE,
                elinewidth=INTERVAL_LINEWIDTH,
                capsize=ERRORBAR_CAPSIZE,
                zorder=4,
            )

    def configure_yield_panel(
        ax: Any,
        *,
        positions: np.ndarray,
        treatments: Sequence[str],
        comparison: str,
        sector: str,
        row_index: int,
        column_index: int,
        row_limit: tuple[float, float],
        result: RCBDResult,
    ) -> None:
        global_p = float(cast(Any, result.anova.loc["C(treatment)", "PR(>F)"]))
        p_text = (
            "< 0,0001" if global_p < 0.0001 else f"= {global_p:.4f}".replace(".", ",")
        )
        ax.text(
            0.02,
            1.015,
            f"ANOVA de tratamiento: p {p_text}",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=9.25,
            clip_on=False,
        )
        ax.set_xticks(positions, treatments)
        ax.set_ylim(*row_limit)
        ax.set_xlabel("Tratamiento")
        if column_index == 0:
            ax.set_ylabel(OUTCOME_LABELS["clean_yield_kg_ha"])
        if comparison == "M0–M5":
            ax.axvline(
                0.5,
                color=PLOT_PALETTE[5],
                linestyle=":",
                linewidth=REFERENCE_LINEWIDTH,
                alpha=0.7,
            )

    def plot_yield_panel(
        ax: Any,
        *,
        frame: pd.DataFrame,
        treatments: Sequence[str],
        comparison: str,
        sector: str,
        row_index: int,
        column_index: int,
        row_limit: tuple[float, float],
        block_offsets: dict[str, float],
    ) -> None:
        positions = np.arange(len(treatments), dtype=float)
        result = final_rcbd_models[("clean_yield_kg_ha", sector, comparison)]
        means = result.means.set_index("treatment")
        sector_data = frame.loc[
            frame["sector"].astype(str).eq(sector)
            & frame["treatment"].astype(str).isin(treatments)
        ]
        plot_yield_treatment_points(
            ax,
            positions=positions,
            treatments=treatments,
            sector_data=sector_data,
            means=means,
            block_offsets=block_offsets,
        )
        configure_yield_panel(
            ax,
            positions=positions,
            treatments=treatments,
            comparison=comparison,
            sector=sector,
            row_index=row_index,
            column_index=column_index,
            row_limit=row_limit,
            result=result,
        )

    def plot_yield_two_questions(frame: pd.DataFrame) -> None:
        block_offsets = dict(
            zip(BLOCKS, np.linspace(-0.12, 0.12, len(BLOCKS)), strict=True)
        )
        row_specs = [
            (TREATMENTS, "M0–M5", "Respuesta al N experimental adicional"),
            (FERTILIZED, "M1–M5", "Comparación entre calendarios"),
        ]
        fig, axes = mpl.subplots(2, 2, figsize=(12.2, 8.8))
        axes_array = np.asarray(axes)
        row_limits = yield_row_limits(frame, row_specs)

        for row_index, (treatments, comparison, _row_title) in enumerate(row_specs):
            for column_index, sector in enumerate(SECTORS):
                plot_yield_panel(
                    axes_array[row_index, column_index],
                    frame=frame,
                    treatments=treatments,
                    comparison=comparison,
                    sector=sector,
                    row_index=row_index,
                    column_index=column_index,
                    row_limit=row_limits[row_index],
                    block_offsets=block_offsets,
                )
        add_figure_header(
            fig,
            "Rendimiento de semilla limpia: dos preguntas y dos escalas",
            subtitle=(
                "Parcelas individuales y media ajustada por bloque ± IC puntual del 95 %; "
                "n = 4 por tratamiento"
            ),
        )
        add_figure_note(
            fig,
            (
                "La fila superior incluye M0; la inferior amplía M1–M5 para evitar que la gran "
                "respuesta frente a M0 comprima visualmente las diferencias entre calendarios."
            ),
        )
        fig.subplots_adjust(
            left=0.08,
            right=0.98,
            bottom=0.10,
            top=0.75,
            hspace=0.65,
            wspace=0.12,
        )
        for column_index, sector in enumerate(SECTORS):
            panel_position = axes_array[0, column_index].get_position()
            fig.text(
                (panel_position.x0 + panel_position.x1) / 2,
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
        save_figure(fig, "figura_03_rendimiento_dos_preguntas")
        mpl.show()
        mpl.close(fig)

    plot_yield_two_questions(data.harvest)
    yield "yield_overview"

    # Notebook step: yield_contrasts
    def average_fertilized_minus_control(
        result: RCBDResult,
    ) -> dict[str, float]:
        _, vectors, covariance = adjusted_treatment_means(
            result.fit,
            treatments=TREATMENTS,
        )
        fertilized_vector = np.mean(
            np.vstack([vectors[treatment] for treatment in FERTILIZED]),
            axis=0,
        )
        contrast = fertilized_vector - vectors["M0"]
        estimate = float(contrast @ result.fit.params.to_numpy())
        se = float(np.sqrt(contrast @ covariance @ contrast))
        half_width = float(cast(Any, stats.t.ppf(0.975, result.fit.df_resid))) * se
        return {
            "difference": estimate,
            "ci_low": estimate - half_width,
            "ci_high": estimate + half_width,
        }

    def build_yield_contrast_table() -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for sector in SECTORS:
            all_result = final_rcbd_models[("clean_yield_kg_ha", sector, "M0–M5")]
            aggregate = average_fertilized_minus_control(all_result)
            rows.append(
                {
                    "sector": sector,
                    "contrast": "Promedio M1–M5 − M0",
                    **aggregate,
                    "interval_type": "IC t puntual del 95 %",
                    "aggregate": True,
                }
            )

            calendar_result = final_rcbd_models[("clean_yield_kg_ha", sector, "M1–M5")]
            for raw_row in calendar_result.pairwise.itertuples(index=False):
                row = cast(Any, raw_row)
                rows.append(
                    {
                        "sector": sector,
                        "contrast": f"{row.group1} − {row.group2}",
                        "difference": row.difference,
                        "ci_low": row.ci_low,
                        "ci_high": row.ci_high,
                        "interval_type": "IC simultáneo de Tukey del 95 %",
                        "aggregate": False,
                    }
                )
        return pd.DataFrame(rows)

    yield_contrasts = build_yield_contrast_table()
    display_output(yield_contrasts.round(2))

    def plot_yield_contrast_points(
        ax: Any,
        *,
        sector: str,
        sector_table: pd.DataFrame,
        contrast_order: Sequence[str],
        y_positions: np.ndarray,
    ) -> None:
        for position, contrast_label in zip(y_positions, contrast_order, strict=True):
            row = cast(Any, sector_table.loc[contrast_label])
            aggregate = bool(row["aggregate"])
            estimate = float(row["difference"])
            plot_horizontal_interval(
                ax,
                estimate=estimate,
                lower=float(row["ci_low"]),
                upper=float(row["ci_high"]),
                y=float(position),
                color=SECTOR_COLORS[sector],
                zorder=3,
            )
            if aggregate:
                ax.annotate(
                    f"{estimate:.0f}",
                    (estimate, position),
                    xytext=(8, 0),
                    textcoords="offset points",
                    va="center",
                    fontsize=9,
                )

    def configure_yield_contrast_axis(
        ax: Any,
        *,
        sector: str,
        panel_index: int,
        contrast_order: Sequence[str],
        y_positions: np.ndarray,
        x_limits: tuple[float, float],
    ) -> None:
        ax.axvline(
            0,
            color=PLOT_PALETTE[5],
            linestyle="--",
            linewidth=REFERENCE_LINEWIDTH,
        )
        ax.axhline(
            0.5,
            color=mpl.rcParams["axes.edgecolor"],
            linewidth=REFERENCE_LINEWIDTH,
            alpha=0.65,
        )
        global_p = float(
            cast(
                Any,
                final_rcbd_models[("clean_yield_kg_ha", sector, "M1–M5")].anova.loc[
                    "C(treatment)", "PR(>F)"
                ],
            )
        )
        ax.set_title(
            f"{sector.upper()} — ANOVA M1–M5 p = {global_p:.4f}".replace(".", ",")
        )
        ax.set_xlim(*x_limits)
        ax.set_xlabel("Diferencia de rendimiento (kg ha⁻¹)")
        ax.set_yticks(y_positions, contrast_order)
        ax.tick_params(axis="y", labelleft=panel_index == 0)
        if panel_index == 0:
            ax.invert_yaxis()

    def plot_yield_contrasts() -> None:
        contrast_order = [
            "Promedio M1–M5 − M0",
            *[f"{first} − {second}" for first, second in combinations(FERTILIZED, 2)],
        ]
        y_positions = np.arange(len(contrast_order), dtype=float)
        all_limits = yield_contrasts[["ci_low", "ci_high"]].to_numpy(dtype=float)
        lower = min(0.0, float(np.nanmin(all_limits)))
        upper = max(0.0, float(np.nanmax(all_limits)))
        padding = 0.08 * (upper - lower)
        x_limits = (lower - padding, upper + padding)

        fig, axes = mpl.subplots(1, 2, figsize=(12.2, 7.3), sharex=True, sharey=True)
        axes_array = np.asarray(axes).ravel()
        for panel_index, sector in enumerate(SECTORS):
            ax = axes_array[panel_index]
            sector_table = yield_contrasts.loc[
                yield_contrasts["sector"].eq(sector)
            ].set_index("contrast")
            plot_yield_contrast_points(
                ax,
                sector=sector,
                sector_table=sector_table,
                contrast_order=contrast_order,
                y_positions=y_positions,
            )
            configure_yield_contrast_axis(
                ax,
                sector=sector,
                panel_index=panel_index,
                contrast_order=contrast_order,
                y_positions=y_positions,
                x_limits=x_limits,
            )

        add_figure_header(
            fig,
            "Contrastes de rendimiento: respuesta marginal e incertidumbre",
            subtitle=(
                "Promedio M1–M5 menos M0: IC t del 95 %. "
                "Diferencias M1–M5: IC simultáneos de Tukey del 95 %."
            ),
        )
        add_figure_note(
            fig,
            (
                "Los contrastes frente a M0 estiman la respuesta a N experimental adicional; "
                "los intervalos que cruzan cero no demuestran equivalencia agronómica."
            ),
        )
        fig.subplots_adjust(
            left=0.20,
            right=0.98,
            bottom=0.12,
            top=0.82,
            wspace=0.10,
        )
        save_figure(fig, "anexo_contrastes_rendimiento")
        mpl.show()
        mpl.close(fig)

    plot_yield_contrasts()
    yield "yield_contrasts"

    # Notebook step: yield_components
    COMPONENT_OUTCOMES = [
        "panicle_density_m2",
        "estimated_seeds_per_panicle",
        "w1000_g",
    ]

    def plot_harvest_component_points(
        ax: Any,
        *,
        raw: pd.DataFrame,
        means: pd.DataFrame,
        outcome: str,
        treatment_positions: np.ndarray,
        block_offsets: dict[str, float],
    ) -> None:
        for position, treatment in zip(treatment_positions, FERTILIZED, strict=True):
            observations = raw.loc[
                raw["treatment"].astype(str).eq(treatment)
            ].sort_values("block")
            point_positions = np.asarray(
                [
                    position + block_offsets[str(block)]
                    for block in observations["block"]
                ]
            )
            ax.scatter(
                point_positions,
                observations[outcome],
                color=TREATMENT_COLORS[treatment],
                alpha=0.32,
                s=25,
                linewidths=0,
                zorder=2,
            )
            mean_row = cast(Any, means.loc[treatment])
            ax.errorbar(
                position,
                float(mean_row["estimate"]),
                yerr=[
                    [float(mean_row["estimate"] - mean_row["ci_low"])],
                    [float(mean_row["ci_high"] - mean_row["estimate"])],
                ],
                color=TREATMENT_COLORS[treatment],
                marker=TREATMENT_MARKERS[treatment],
                markersize=MARKER_SIZE,
                linestyle="none",
                elinewidth=INTERVAL_LINEWIDTH,
                capsize=ERRORBAR_CAPSIZE,
                zorder=4,
            )

    def configure_harvest_component_axis(
        ax: Any,
        *,
        result: RCBDResult,
        outcome: str,
        sector: str,
        row_index: int,
        column_index: int,
        treatment_positions: np.ndarray,
    ) -> None:
        global_p = float(cast(Any, result.anova.loc["C(treatment)", "PR(>F)"]))
        p_text = (
            "< 0,0001" if global_p < 0.0001 else f"= {global_p:.4f}".replace(".", ",")
        )
        ax.text(
            0.02,
            1.015,
            f"ANOVA de tratamiento: p {p_text}",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=9.25,
            clip_on=False,
        )
        if row_index == 0:
            ax.set_title(sector.upper(), pad=30)
        if column_index == 0:
            ax.set_ylabel(OUTCOME_LABELS[outcome])
        if row_index == len(COMPONENT_OUTCOMES) - 1:
            ax.set_xticks(treatment_positions, FERTILIZED)
            ax.set_xlabel("Calendario")
        else:
            ax.tick_params(axis="x", labelbottom=False)

    def plot_harvest_component_panel(
        ax: Any,
        *,
        outcome: str,
        sector: str,
        row_index: int,
        column_index: int,
        treatment_positions: np.ndarray,
        block_offsets: dict[str, float],
    ) -> None:
        raw = data.harvest.loc[
            data.harvest["sector"].astype(str).eq(sector)
            & data.harvest["treatment"].astype(str).isin(FERTILIZED)
        ]
        result = final_rcbd_models[(outcome, sector, "M1–M5")]
        means = result.means.set_index("treatment")
        plot_harvest_component_points(
            ax,
            raw=raw,
            means=means,
            outcome=outcome,
            treatment_positions=treatment_positions,
            block_offsets=block_offsets,
        )
        configure_harvest_component_axis(
            ax,
            result=result,
            outcome=outcome,
            sector=sector,
            row_index=row_index,
            column_index=column_index,
            treatment_positions=treatment_positions,
        )

    def plot_harvest_component_panels() -> None:
        treatment_positions = np.arange(len(FERTILIZED), dtype=float)
        block_offsets = dict(
            zip(BLOCKS, np.linspace(-0.12, 0.12, len(BLOCKS)), strict=True)
        )
        fig, axes = mpl.subplots(
            len(COMPONENT_OUTCOMES),
            len(SECTORS),
            figsize=(12.2, 10.0),
            sharex=True,
            squeeze=False,
        )
        axes_array = np.asarray(axes)
        for row_index, outcome in enumerate(COMPONENT_OUTCOMES):
            for column_index, sector in enumerate(SECTORS):
                plot_harvest_component_panel(
                    axes_array[row_index, column_index],
                    outcome=outcome,
                    sector=sector,
                    row_index=row_index,
                    column_index=column_index,
                    treatment_positions=treatment_positions,
                    block_offsets=block_offsets,
                )

        add_figure_header(
            fig,
            "Componentes del rendimiento entre M1–M5",
            subtitle=(
                "Parcelas individuales y medias ajustadas por bloque ± IC puntual "
                "del 95 %; n = 4 por calendario."
            ),
        )
        add_figure_note(
            fig,
            (
                "Semillas por panoja se estimó a partir del rendimiento limpio, el peso "
                "de mil semillas y la cantidad de panojas; no es una medición independiente."
            ),
        )
        fig.subplots_adjust(
            left=0.10,
            right=0.98,
            bottom=0.10,
            top=0.84,
            hspace=0.31,
            wspace=0.14,
        )
        save_figure(fig, "figura_06_componentes_del_rendimiento")
        mpl.show()
        mpl.close(fig)

    plot_harvest_component_panels()
    yield "yield_components"

    # Notebook step: component_correlations
    component_means = (
        data.harvest.loc[data.harvest["treatment"].astype(str).isin(FERTILIZED)]
        .groupby(["sector", "treatment"], observed=True)[
            ["panicle_density_m2", "estimated_seeds_per_panicle"]
        ]
        .mean()
        .reset_index()
    )

    fig, ax = mpl.subplots(figsize=(8.5, 5.8))
    for sector in SECTORS:
        subset = component_means.loc[component_means["sector"].astype(str).eq(sector)]
        ax.scatter(
            subset["panicle_density_m2"],
            subset["estimated_seeds_per_panicle"],
            color=SECTOR_COLORS[sector],
            marker=SECTOR_MARKERS[sector],
            s=70,
            label=sector,
        )
        for raw_row in subset.itertuples(index=False):
            row = cast(Any, raw_row)
            ax.annotate(
                str(row.treatment),
                (row.panicle_density_m2, row.estimated_seeds_per_panicle),
                xytext=(5, 5),
                textcoords="offset points",
            )
    ax.set_xlabel("Densidad media de panojas (m⁻²)")
    ax.set_ylabel("Semillas estimadas por panoja")
    ax.legend(title="Sector")
    add_figure_header(fig, "Componentes reconstruidos entre M1–M5")
    add_figure_note(
        fig,
        "Cada punto representa la media de cuatro parcelas para un calendario.",
    )
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.16, top=0.85)
    mpl.show()
    mpl.close(fig)
    yield "component_correlations"

    # Notebook step: seed_weight_precision
    seed_repeatability = data.harvest[
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
    weights = seed_repeatability[["w100_1_g", "w100_2_g", "w100_3_g"]]
    seed_repeatability["technical_cv_pct"] = (
        100.0 * weights.std(axis=1, ddof=1) / weights.mean(axis=1)
    )
    display_output(
        seed_repeatability["technical_cv_pct"].describe().to_frame().T.round(3)
    )

    repeatability_plot = seed_repeatability.assign(
        plot_y=np.random.default_rng(RANDOM_SEED).uniform(
            -0.18,
            0.18,
            size=len(seed_repeatability),
        )
    )
    fig, ax = mpl.subplots(figsize=(10.5, 3.8))
    sns_api.scatterplot(
        data=repeatability_plot,
        x="technical_cv_pct",
        y="plot_y",
        color=PLOT_PALETTE[0],
        alpha=0.68,
        s=42,
        linewidth=0,
        ax=ax,
    )
    median_cv = float(cast(Any, seed_repeatability["technical_cv_pct"].median()))
    ax.axvline(
        median_cv,
        color=PLOT_PALETTE[3],
        linestyle="--",
        linewidth=REFERENCE_LINEWIDTH,
    )
    ax.text(
        median_cv,
        0.92,
        f"Mediana = {median_cv:.2f} %".replace(".", ","),
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=9.5,
        color=PLOT_PALETTE[3],
    )
    ax.set_xlabel("CV entre las tres submuestras de 100 semillas (%)")
    ax.set_ylabel("")
    ax.set_yticks([])
    ax.set_ylim(-0.45, 0.45)
    ax.grid(axis="x", alpha=0.25)
    add_figure_header(
        fig,
        "Repetibilidad técnica del peso de 100 semillas",
        subtitle=(
            f"Cada círculo representa una parcela; n = {len(seed_repeatability)} parcelas."
        ),
    )
    add_figure_note(
        fig,
        "El CV resume la variación entre tres submuestras técnicas de la misma parcela.",
    )
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.24, top=0.64)
    mpl.show()
    mpl.close(fig)
    yield "seed_weight_precision"

    # Notebook step: model_diagnostics
    def diagnostic_row(
        result: RCBDResult,
        *,
        sector: str,
        date: pd.Timestamp | None,
        comparison: str,
    ) -> dict[str, object]:
        residuals = np.asarray(result.fit.resid)
        shapiro_p = stats.shapiro(residuals).pvalue if len(residuals) >= 3 else np.nan
        groups = [
            group[result.outcome].dropna().to_numpy()
            for _, group in result.frame.groupby("treatment", observed=True)
        ]
        levene_p = (
            stats.levene(*groups, center="median").pvalue
            if all(len(group) >= 2 for group in groups)
            else np.nan
        )
        influence = result.fit.get_influence()
        studentized = influence.resid_studentized_external
        cooks = influence.cooks_distance[0]
        response = result.frame[result.outcome]
        q1, q3 = response.quantile([0.25, 0.75])
        iqr = q3 - q1
        iqr_flag_count = int(
            ((response < q1 - 1.5 * iqr) | (response > q3 + 1.5 * iqr)).sum()
        )
        return {
            "outcome": result.outcome,
            "label": OUTCOME_LABELS.get(result.outcome, result.outcome),
            "sector": sector,
            "date": date,
            "comparison": comparison,
            "n": len(result.frame),
            "shapiro_p": shapiro_p,
            "levene_median_p": levene_p,
            "max_abs_studentized": float(np.nanmax(np.abs(studentized))),
            "max_cooks_d": float(np.nanmax(cooks)),
            "cooks_4_over_n_count": int(np.sum(cooks > 4.0 / len(result.frame))),
            "iqr_flag_count": iqr_flag_count,
        }

    diagnostic_rows: list[dict[str, object]] = []
    for (outcome, date, sector, comparison), result in longitudinal_rcbd_models.items():
        if comparison == "M1–M5":
            diagnostic_rows.append(
                diagnostic_row(
                    result,
                    sector=sector,
                    date=date,
                    comparison=comparison,
                )
            )
    for (outcome, sector, comparison), result in final_rcbd_models.items():
        if comparison == "M1–M5" and outcome in FINAL_OUTCOMES:
            diagnostic_rows.append(
                diagnostic_row(
                    result,
                    sector=sector,
                    date=None,
                    comparison=comparison,
                )
            )

    diagnostics = pd.DataFrame(diagnostic_rows)
    diagnostics["potential_flag"] = (
        diagnostics["shapiro_p"].lt(ALPHA)
        | diagnostics["levene_median_p"].lt(ALPHA)
        | diagnostics["max_abs_studentized"].gt(3.0)
        | diagnostics["cooks_4_over_n_count"].gt(0)
        | diagnostics["iqr_flag_count"].gt(0)
    )

    display_output(
        diagnostics.loc[diagnostics["potential_flag"]]
        .sort_values(["label", "sector", "date"])
        .round(4)
    )
    yield "model_diagnostics"

    # Notebook step: primary_residual_diagnostics
    def residual_diagnostic_plots(result: RCBDResult, *, title_prefix: str) -> None:
        fitted = np.asarray(result.fit.fittedvalues)
        residuals = np.asarray(result.fit.resid)

        fig, axes = mpl.subplots(1, 2, figsize=(10.8, 4.6))
        residual_ax, qq_ax = np.asarray(axes).ravel()
        sns_api.scatterplot(
            x=fitted,
            y=residuals,
            ax=residual_ax,
            color=PLOT_PALETTE[0],
            alpha=0.8,
        )
        residual_ax.axhline(
            0,
            color=PLOT_PALETTE[5],
            linestyle="--",
            linewidth=REFERENCE_LINEWIDTH,
        )
        residual_ax.set_xlabel("Valores ajustados")
        residual_ax.set_ylabel("Residuos")
        residual_ax.set_title("Residuos frente a valores ajustados")

        (theoretical_quantiles, ordered_residuals), (slope, intercept, _) = (
            stats.probplot(residuals, dist="norm")
        )
        sns_api.scatterplot(
            x=theoretical_quantiles,
            y=ordered_residuals,
            ax=qq_ax,
            color=PLOT_PALETTE[0],
        )
        sns_api.lineplot(
            x=theoretical_quantiles,
            y=slope * theoretical_quantiles + intercept,
            ax=qq_ax,
            color=PLOT_PALETTE[5],
            estimator=None,
            sort=False,
        )
        qq_ax.set_xlabel("Cuantiles teóricos")
        qq_ax.set_ylabel("Residuos ordenados")
        qq_ax.set_title("Gráfico Q–Q normal")
        add_figure_header(fig, title_prefix)
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.14, top=0.78, wspace=0.28)
        mpl.show()
        mpl.close(fig)

    for sector in SECTORS:
        residual_diagnostic_plots(
            final_rcbd_models[("clean_yield_kg_ha", sector, "M1–M5")],
            title_prefix=f"Diagnóstico del rendimiento limpio — {sector}, M1–M5",
        )
    yield "primary_residual_diagnostics"

    # Notebook step: missing_n_sensitivity
    sep_secano = data.longitudinal.loc[
        data.longitudinal["date"].astype("datetime64[ns]").eq(DATES[0])
        & data.longitudinal["sector"].astype(str).eq("Secano")
    ].copy()

    imputed_values = {
        "n_pct": rcbd_missing_cell_estimate(
            sep_secano,
            value_column="n_pct",
            missing_treatment="M1",
            missing_block="R4",
            r_blocks=4,
            t_treatments=6,
        ),
        "adf_pct": rcbd_missing_cell_estimate(
            sep_secano,
            value_column="adf_pct",
            missing_treatment="M1",
            missing_block="R4",
            r_blocks=4,
            t_treatments=6,
        ),
        "ndf_pct": rcbd_missing_cell_estimate(
            sep_secano,
            value_column="ndf_pct",
            missing_treatment="M1",
            missing_block="R4",
            r_blocks=4,
            t_treatments=6,
        ),
    }
    display_output(pd.Series(imputed_values, name="imputación DBCA").to_frame())

    imputed_sep = sep_secano.copy()
    missing_mask = imputed_sep["treatment"].astype(str).eq("M1") & imputed_sep[
        "block"
    ].astype(str).eq("R4")
    imputed_sep.loc[missing_mask, "n_pct"] = imputed_values["n_pct"]
    imputed_sep.loc[missing_mask, "adf_pct"] = imputed_values["adf_pct"]
    imputed_sep.loc[missing_mask, "ndf_pct"] = imputed_values["ndf_pct"]
    imputed_sep.loc[missing_mask, "q_kg_n_ha"] = (
        imputed_sep.loc[missing_mask, "biomass_kg_ha_used"]
        * imputed_sep.loc[missing_mask, "n_pct"]
        / 100.0
    )
    biomass_t = imputed_sep.loc[missing_mask, "biomass_kg_ha_used"] / 1000.0
    imputed_sep.loc[missing_mask, "nni_revised"] = imputed_sep.loc[
        missing_mask, "n_pct"
    ] / (3.93 * biomass_t.pow(-0.42))

    sensitivity_rows: list[dict[str, object]] = []
    for outcome in ["n_pct", "q_kg_n_ha", "nni_revised"]:
        for frame_name, frame in [("observado", sep_secano), ("imputado", imputed_sep)]:
            result = fit_rcbd(frame, outcome=outcome, treatments=FERTILIZED)
            sensitivity_rows.append(
                {
                    "outcome": OUTCOME_LABELS[outcome],
                    "scenario": frame_name,
                    "p_M1_M5": result.anova.loc["C(treatment)", "PR(>F)"],
                }
            )
    display_output(pd.DataFrame(sensitivity_rows).round(6))
    yield "missing_n_sensitivity"

    # Notebook step: joint_sector_analysis
    def fit_joint_sector_model(
        frame: pd.DataFrame,
        *,
        outcome: str,
        treatments: Sequence[str] = FERTILIZED,
    ) -> tuple[Any, pd.DataFrame, pd.DataFrame]:
        subset = (
            frame.loc[frame["treatment"].astype(str).isin(treatments)]
            .dropna(subset=[outcome])
            .copy()
        )
        subset["treatment"] = categorical(subset["treatment"], treatments)
        subset["sector"] = categorical(subset["sector"], SECTORS)
        subset["block"] = categorical(subset["block"], BLOCKS)
        fit = smf_api.ols(
            f"{outcome} ~ C(treatment) * C(sector) + C(sector):C(block)",
            data=subset,
        ).fit()
        anova = sm_api.stats.anova_lm(fit, typ=2)
        return fit, anova, subset

    joint_rows: list[dict[str, object]] = []
    for outcome in LONGITUDINAL_OUTCOMES:
        for date in DATES:
            frame = data.longitudinal.loc[
                data.longitudinal["date"].astype("datetime64[ns]").eq(date)
            ].copy()
            _fit, anova, subset = fit_joint_sector_model(frame, outcome=outcome)
            joint_rows.append(
                {
                    "outcome": outcome,
                    "label": OUTCOME_LABELS[outcome],
                    "date": date,
                    "n": len(subset),
                    "p_treatment": anova.loc["C(treatment)", "PR(>F)"],
                    "p_sector": anova.loc["C(sector)", "PR(>F)"],
                    "p_treatment_x_sector": anova.loc[
                        "C(treatment):C(sector)", "PR(>F)"
                    ],
                }
            )

    for outcome in FINAL_OUTCOMES:
        _fit, anova, subset = fit_joint_sector_model(data.harvest, outcome=outcome)
        joint_rows.append(
            {
                "outcome": outcome,
                "label": OUTCOME_LABELS[outcome],
                "date": pd.NaT,
                "n": len(subset),
                "p_treatment": anova.loc["C(treatment)", "PR(>F)"],
                "p_sector": anova.loc["C(sector)", "PR(>F)"],
                "p_treatment_x_sector": anova.loc["C(treatment):C(sector)", "PR(>F)"],
            }
        )

    joint_results = pd.DataFrame(joint_rows)
    joint_results["date_label"] = joint_results["date"].map(DATE_LABELS)
    display_output(
        joint_results[
            [
                "label",
                "date_label",
                "n",
                "p_treatment",
                "p_treatment_x_sector",
                "p_sector",
            ]
        ].round(4)
    )

    yield "joint_sector_analysis"

    # Notebook step: correlation_audit
    final_nutrition = data.longitudinal.loc[
        data.longitudinal["date"].astype("datetime64[ns]").eq(DATES[-1]),
        [
            "plot_id",
            "biomass_kg_ha_used",
            "n_pct",
            "q_kg_n_ha",
            "nni_revised",
        ],
    ]
    final_merged = data.harvest.merge(
        final_nutrition,
        on="plot_id",
        how="left",
        validate="one_to_one",
        suffixes=("", "_nutrition"),
    )

    CORRELATION_VARIABLES = [
        "panicle_density_m2",
        "estimated_seeds_per_panicle",
        "w1000_g",
        "biomass_kg_ha_used_nutrition",
        "n_pct",
        "q_kg_n_ha",
        "harvest_index_pct",
        "cleaning_loss_pct",
    ]
    CORRELATION_LABELS = {
        "panicle_density_m2": "Panojas m⁻²",
        "estimated_seeds_per_panicle": "Semillas estimadas por panoja*",
        "w1000_g": "Peso de mil semillas",
        "biomass_kg_ha_used_nutrition": "Biomasa final",
        "n_pct": "Concentración de N",
        "q_kg_n_ha": "N presente en biomasa aérea",
        "harvest_index_pct": "Índice de cosecha*",
        "cleaning_loss_pct": "Merma de limpieza*",
    }

    def pearson_row(frame: pd.DataFrame, x: str, y: str) -> tuple[float, float, int]:
        subset = frame[[x, y]].dropna()
        result = cast(Any, stats.pearsonr(subset[x], subset[y]))
        return float(result.statistic), float(result.pvalue), len(subset)

    raw_correlation_rows: list[dict[str, object]] = []
    for variable in CORRELATION_VARIABLES:
        for sector in ["Conjunto", *SECTORS]:
            frame = (
                final_merged
                if sector == "Conjunto"
                else final_merged.loc[final_merged["sector"].astype(str).eq(sector)]
            )
            r, p, n = pearson_row(frame, variable, "clean_yield_kg_ha")
            raw_correlation_rows.append(
                {
                    "variable": CORRELATION_LABELS[variable],
                    "sector": sector,
                    "r": r,
                    "p": p,
                    "n": n,
                    "mathematically_coupled_to_yield": variable
                    in {
                        "estimated_seeds_per_panicle",
                        "harvest_index_pct",
                        "cleaning_loss_pct",
                    },
                    "inference_tier": "exploratoria",
                }
            )
    raw_correlations = pd.DataFrame(raw_correlation_rows)
    raw_correlations = add_bh_within_families(
        raw_correlations,
        p_column="p",
        family_columns=["sector"],
    )
    display_output(
        raw_correlations.pivot(index="variable", columns="sector", values="r").round(3)
    )

    def residualized_correlation(
        frame: pd.DataFrame, variable: str
    ) -> tuple[float, float, int]:
        subset = frame.dropna(subset=[variable, "clean_yield_kg_ha"]).copy()
        subset["treatment"] = categorical(subset["treatment"], TREATMENTS)
        subset["block"] = categorical(subset["block"], BLOCKS)
        x_fit = smf_api.ols(f"{variable} ~ C(treatment) + C(block)", data=subset).fit()
        y_fit = smf_api.ols(
            "clean_yield_kg_ha ~ C(treatment) + C(block)", data=subset
        ).fit()
        result = cast(Any, stats.pearsonr(x_fit.resid, y_fit.resid))
        return float(result.statistic), float(result.pvalue), len(subset)

    audit_correlation_rows: list[dict[str, object]] = []
    for variable in [
        "biomass_kg_ha_used_nutrition",
        "n_pct",
        "q_kg_n_ha",
    ]:
        for sector in SECTORS:
            sector_frame = final_merged.loc[
                final_merged["sector"].astype(str).eq(sector)
            ].copy()
            all_r, all_p, _all_n = pearson_row(
                sector_frame, variable, "clean_yield_kg_ha"
            )
            fertilized_frame = sector_frame.loc[
                sector_frame["treatment"].astype(str).isin(FERTILIZED)
            ]
            fert_r, fert_p, _fert_n = pearson_row(
                fertilized_frame, variable, "clean_yield_kg_ha"
            )
            adjusted_r, adjusted_p, _adjusted_n = residualized_correlation(
                sector_frame, variable
            )
            audit_correlation_rows.append(
                {
                    "variable": CORRELATION_LABELS[variable],
                    "sector": sector,
                    "raw_r": all_r,
                    "raw_p": all_p,
                    "M1_M5_r": fert_r,
                    "M1_M5_p": fert_p,
                    "adjusted_r": adjusted_r,
                    "adjusted_p": adjusted_p,
                }
            )
    correlation_audit = pd.DataFrame(audit_correlation_rows)
    correlation_audit["adjusted_p_bh"] = benjamini_hochberg(
        correlation_audit["adjusted_p"].astype(float).to_numpy()
    )
    correlation_audit["inference_tier"] = "exploratoria"
    display_output(correlation_audit.round(4))
    yield "correlation_audit"

    # Notebook step: mixed_models
    @dataclass
    class MixedTrajectoryResult:
        outcome: str
        sector: str
        treatments: tuple[str, ...]
        frame: pd.DataFrame
        center: float
        scale: float
        base_fit: Any
        additive_fit: Any
        full_fit: Any
        summary: dict[str, object]

    def fit_longitudinal_mixed(
        frame: pd.DataFrame,
        *,
        outcome: str,
        sector: str,
        treatments: Sequence[str],
        response_scale: Literal["original", "log"] = "original",
    ) -> MixedTrajectoryResult:
        subset = (
            frame.loc[
                frame["sector"].astype(str).eq(sector)
                & frame["treatment"].astype(str).isin(treatments)
            ]
            .dropna(subset=[outcome])
            .copy()
        )
        response = subset[outcome].astype(float)
        if response_scale == "log":
            if bool((response <= 0).any()):
                raise ValueError(f"{outcome} contiene valores no positivos.")
            response = np.log(response)
        center = float(response.mean())
        scale = float(response.std(ddof=0))
        subset["y_z"] = (response - center) / scale
        subset["treatment"] = categorical(subset["treatment"], treatments)
        subset["block"] = categorical(subset["block"], BLOCKS)
        subset["date_label"] = categorical(
            subset["date_label"], [DATE_LABELS[date] for date in DATES]
        )

        base_formula = "y_z ~ C(date_label) + C(block)"
        additive_formula = "y_z ~ C(date_label) + C(treatment) + C(block)"
        full_formula = "y_z ~ C(date_label) * C(treatment) + C(block)"
        base_fit = fit_mixedlm_best(base_formula, subset)
        additive_fit = fit_mixedlm_best(additive_formula, subset)
        full_fit = fit_mixedlm_best(full_formula, subset)

        main_lrt = likelihood_ratio(base_fit, additive_fit)
        interaction_lrt = likelihood_ratio(additive_fit, full_fit)
        global_lrt = likelihood_ratio(base_fit, full_fit)
        comparison = "M1–M5" if list(treatments) == FERTILIZED else "M0–M5"
        bootstrap_p = np.nan
        bootstrap_successful = 0
        if comparison == "M1–M5" and outcome in {"biomass_kg_ha_used", "n_pct"}:
            seed_offset = (
                1000 * ["biomass_kg_ha_used", "n_pct"].index(outcome)
                + 100 * SECTORS.index(sector)
                + (5000 if response_scale == "log" else 0)
            )
            bootstrap = parametric_bootstrap_lrt(
                subset,
                reduced_formula=additive_formula,
                full_formula=full_formula,
                reduced_fit=additive_fit,
                full_fit=full_fit,
                replicates=BOOTSTRAP_REPLICATES,
                seed=RANDOM_SEED + seed_offset,
            )
            bootstrap_p = bootstrap.p_bootstrap
            bootstrap_successful = bootstrap.successful_replicates
        random_variance = float(full_fit.cov_re.iloc[0, 0])
        residuals = subset.assign(_residual=np.asarray(full_fit.resid, dtype=float))
        residual_sd_by_date = residuals.groupby("date_label", observed=True)[
            "_residual"
        ].std()
        positive_residual_sd = residual_sd_by_date.loc[residual_sd_by_date.gt(0)]
        residual_sd_ratio = (
            float(positive_residual_sd.max() / positive_residual_sd.min())
            if len(positive_residual_sd) > 1
            else np.nan
        )
        summary: dict[str, object] = {
            "outcome": outcome,
            "label": OUTCOME_LABELS[outcome],
            "sector": sector,
            "comparison": comparison,
            "response_scale": response_scale,
            "n": len(subset),
            "plots": subset["plot_id"].nunique(),
            "p_average_treatment": main_lrt.p_asymptotic,
            "df_average_treatment": main_lrt.degrees_freedom,
            "p_treatment_x_date_asymptotic": interaction_lrt.p_asymptotic,
            "p_treatment_x_date_bootstrap": bootstrap_p,
            "p_treatment_x_date": (
                bootstrap_p
                if np.isfinite(bootstrap_p)
                else interaction_lrt.p_asymptotic
            ),
            "interaction_p_method": (
                "parametric_bootstrap"
                if np.isfinite(bootstrap_p)
                else "asymptotic_lrt_support"
            ),
            "bootstrap_successful": bootstrap_successful,
            "bootstrap_requested": (
                BOOTSTRAP_REPLICATES if np.isfinite(bootstrap_p) else 0
            ),
            "df_treatment_x_date": interaction_lrt.degrees_freedom,
            "p_global_trajectory": global_lrt.p_asymptotic,
            "df_global_trajectory": global_lrt.degrees_freedom,
            "random_intercept_variance_z": random_variance,
            "random_effect_boundary": random_variance < 1e-6,
            "residual_sd_max_min_ratio": residual_sd_ratio,
            "optimizer": getattr(full_fit, "_audit_optimizer", "unknown"),
            "optimizer_selection": getattr(full_fit, "_audit_selection", "unknown"),
            "optimizer_candidates": len(getattr(full_fit, "_audit_candidates", ())),
            "converged": bool(full_fit.converged),
        }
        return MixedTrajectoryResult(
            outcome=outcome,
            sector=sector,
            treatments=tuple(treatments),
            frame=subset,
            center=center,
            scale=scale,
            base_fit=base_fit,
            additive_fit=additive_fit,
            full_fit=full_fit,
            summary=summary,
        )

    mixed_models: dict[tuple[str, str, str], MixedTrajectoryResult] = {}
    mixed_rows: list[dict[str, object]] = []
    for outcome in LONGITUDINAL_OUTCOMES:
        for sector in SECTORS:
            for treatments in [FERTILIZED, TREATMENTS]:
                result = fit_longitudinal_mixed(
                    data.longitudinal,
                    outcome=outcome,
                    sector=sector,
                    treatments=treatments,
                )
                comparison = cast(str, result.summary["comparison"])
                mixed_models[(outcome, sector, comparison)] = result
                mixed_rows.append(result.summary)

    mixed_summary = pd.DataFrame(mixed_rows)
    mixed_summary["variable_family"] = np.where(
        mixed_summary["outcome"].isin(["biomass_kg_ha_used", "n_pct"]),
        "secundaria_primitiva",
        "apoyo_derivado",
    )
    mixed_summary["inference_tier"] = np.where(
        mixed_summary["comparison"].eq("M1–M5"),
        mixed_summary["variable_family"],
        "complementaria",
    )
    mixed_summary = add_bh_within_families(
        mixed_summary,
        p_column="p_treatment_x_date",
        family_columns=["comparison", "variable_family"],
        output_column="p_treatment_x_date_bh",
    )

    biomass_scale_rows: list[dict[str, object]] = []
    for sector in SECTORS:
        raw_result = mixed_models[("biomass_kg_ha_used", sector, "M1–M5")]
        log_result = fit_longitudinal_mixed(
            data.longitudinal,
            outcome="biomass_kg_ha_used",
            sector=sector,
            treatments=FERTILIZED,
            response_scale="log",
        )
        for scale_label, result in [
            ("original", raw_result),
            ("log", log_result),
        ]:
            biomass_scale_rows.append(
                {
                    "sector": sector,
                    "response_scale": scale_label,
                    "p_treatment_x_date_asymptotic": result.summary[
                        "p_treatment_x_date_asymptotic"
                    ],
                    "p_treatment_x_date_bootstrap": result.summary[
                        "p_treatment_x_date_bootstrap"
                    ],
                    "bootstrap_successful": result.summary["bootstrap_successful"],
                    "residual_sd_max_min_ratio": result.summary[
                        "residual_sd_max_min_ratio"
                    ],
                    "random_effect_boundary": result.summary["random_effect_boundary"],
                    "optimizer": result.summary["optimizer"],
                    "converged": result.summary["converged"],
                }
            )
    biomass_scale_sensitivity = pd.DataFrame(biomass_scale_rows)
    inference_hierarchy = pd.DataFrame(
        [
            {
                "tier": "Primaria",
                "outcomes": "Rendimiento limpio M1–M5",
                "multiplicity": "Contraste planificado; p sin ajuste",
            },
            {
                "tier": "Secundaria",
                "outcomes": "Biomasa aérea y concentración de N longitudinales",
                "multiplicity": "FDR de Benjamini-Hochberg en la familia",
            },
            {
                "tier": "Apoyo",
                "outcomes": "N presente en biomasa, INN y componentes",
                "multiplicity": "FDR por familia; no evidencia independiente",
            },
            {
                "tier": "Exploratoria/sensibilidad",
                "outcomes": "Correlaciones, EAN, productividad aparente del agua y políticas de datos",
                "multiplicity": "FDR para correlaciones; el resto descriptivo",
            },
        ]
    )
    display_output(inference_hierarchy)
    display_output(
        mixed_summary[
            [
                "label",
                "sector",
                "comparison",
                "inference_tier",
                "n",
                "plots",
                "p_average_treatment",
                "p_treatment_x_date_asymptotic",
                "p_treatment_x_date_bootstrap",
                "p_treatment_x_date",
                "p_treatment_x_date_bh",
                "interaction_p_method",
                "p_global_trajectory",
                "random_intercept_variance_z",
                "random_effect_boundary",
                "residual_sd_max_min_ratio",
                "optimizer",
                "optimizer_selection",
                "converged",
            ]
        ].round(6)
    )
    display_output(
        Markdown("**Sensibilidad de biomasa a escala original versus logarítmica:**")
    )
    display_output(biomass_scale_sensitivity.round(6))
    yield "mixed_models"

    # Notebook step: mixed_estimates
    def mixed_emmeans(result: MixedTrajectoryResult) -> pd.DataFrame:
        fit = result.full_fit
        fixed_names = list(fit.fe_params.index)
        covariance = np.asarray(
            fit.cov_params().loc[fixed_names, fixed_names].to_numpy(), dtype=float
        )
        beta = np.asarray(fit.fe_params.to_numpy(), dtype=float)
        design_info = fit.model.data.design_info
        date_levels = [DATE_LABELS[date] for date in DATES]

        rows: list[dict[str, object]] = []
        for date_label in date_levels:
            for treatment in result.treatments:
                new = pd.DataFrame(
                    {
                        "date_label": [date_label] * len(BLOCKS),
                        "treatment": [treatment] * len(BLOCKS),
                        "block": BLOCKS,
                    }
                )
                new["date_label"] = categorical(new["date_label"], date_levels)
                new["treatment"] = categorical(new["treatment"], result.treatments)
                new["block"] = categorical(new["block"], BLOCKS)
                design = np.asarray(
                    patsy_api.build_design_matrices([design_info], new)[0],
                    dtype=float,
                )
                xbar = design.mean(axis=0)
                estimate_z = float(xbar @ beta)
                se_z = float(np.sqrt(xbar @ covariance @ xbar))
                estimate = result.center + result.scale * estimate_z
                se = result.scale * se_z
                rows.append(
                    {
                        "date_label": date_label,
                        "treatment": treatment,
                        "estimate": estimate,
                        "se": se,
                        "ci_low": estimate - 1.96 * se,
                        "ci_high": estimate + 1.96 * se,
                        "design_vector": xbar,
                    }
                )
        return pd.DataFrame(rows)

    def mixed_early_late_contrasts(
        result: MixedTrajectoryResult,
    ) -> pd.DataFrame:
        if not set(FERTILIZED).issubset(result.treatments):
            raise ValueError("El contraste requiere M1–M5")
        emmeans = mixed_emmeans(result)
        fit = result.full_fit
        fixed_names = list(fit.fe_params.index)
        covariance = np.asarray(
            fit.cov_params().loc[fixed_names, fixed_names].to_numpy(), dtype=float
        )
        beta = np.asarray(fit.fe_params.to_numpy(), dtype=float)
        rows: list[dict[str, object]] = []
        for date_label in [DATE_LABELS[date] for date in DATES]:
            date_rows = emmeans.loc[emmeans["date_label"].eq(date_label)].set_index(
                "treatment"
            )
            early_vector = np.mean(
                np.vstack(
                    [
                        np.asarray(cast(Any, date_rows.at["M1", "design_vector"])),
                        np.asarray(cast(Any, date_rows.at["M2", "design_vector"])),
                    ]
                ),
                axis=0,
            )
            late_vector = np.mean(
                np.vstack(
                    [
                        np.asarray(cast(Any, date_rows.at["M4", "design_vector"])),
                        np.asarray(cast(Any, date_rows.at["M5", "design_vector"])),
                    ]
                ),
                axis=0,
            )
            contrast = early_vector - late_vector
            difference_z = float(contrast @ beta)
            se_z = float(np.sqrt(contrast @ covariance @ contrast))
            difference = result.scale * difference_z
            se = result.scale * se_z
            rows.append(
                {
                    "date_label": date_label,
                    "early_minus_late": difference,
                    "se": se,
                    "ci_low": difference - 1.96 * se,
                    "ci_high": difference + 1.96 * se,
                    "z": difference / se,
                    "p_normal": 2.0 * stats.norm.sf(abs(difference / se)),
                }
            )
        return pd.DataFrame(rows)

    def plot_mixed_treatment(
        ax: Any,
        *,
        result: MixedTrajectoryResult,
        emmeans: pd.DataFrame,
        outcome: str,
        treatment: str,
        date_positions: dict[str, float],
        treatment_offsets: dict[str, float],
        block_offsets: dict[str, float],
    ) -> None:
        observed = result.frame.loc[
            result.frame["treatment"].astype(str).eq(treatment)
        ].copy()
        observed_x = np.asarray(
            [
                date_positions[str(date_label)]
                + treatment_offsets[treatment]
                + block_offsets[str(block)]
                for date_label, block in zip(
                    observed["date_label"], observed["block"], strict=True
                )
            ]
        )
        ax.scatter(
            observed_x,
            observed[outcome],
            color=TREATMENT_COLORS[treatment],
            alpha=0.18,
            s=19,
            linewidths=0,
            zorder=1,
        )
        estimates = emmeans.loc[emmeans["treatment"].eq(treatment)].copy()
        estimate_x = np.asarray(
            [
                date_positions[str(date_label)] + treatment_offsets[treatment]
                for date_label in estimates["date_label"]
            ]
        )
        ax.errorbar(
            estimate_x,
            estimates["estimate"],
            yerr=[
                estimates["estimate"] - estimates["ci_low"],
                estimates["ci_high"] - estimates["estimate"],
            ],
            color=TREATMENT_COLORS[treatment],
            marker="o",
            linestyle="none",
            markersize=MARKER_SIZE,
            capsize=ERRORBAR_CAPSIZE,
            elinewidth=INTERVAL_LINEWIDTH,
            zorder=3,
        )

    def configure_mixed_outcome_axis(
        ax: Any,
        *,
        result: MixedTrajectoryResult,
        outcome: str,
        sector: str,
        row_index: int,
        column_index: int,
        outcome_count: int,
        date_positions: dict[str, float],
        treatment_offsets: dict[str, float],
    ) -> None:
        if outcome == "nni_revised":
            ax.axhline(
                1.0,
                color=PLOT_PALETTE[5],
                linestyle="--",
                linewidth=REFERENCE_LINEWIDTH,
                alpha=0.85,
            )
            ax.text(
                0.02,
                1.0,
                "INN = 1",
                transform=ax.get_yaxis_transform(),
                ha="left",
                va="bottom",
                fontsize=9,
                color=PLOT_PALETTE[5],
            )
        treatment_positions = [
            date_position + treatment_offsets[treatment]
            for date_position in date_positions.values()
            for treatment in FERTILIZED
        ]
        for position, treatment in zip(
            treatment_positions,
            FERTILIZED * len(date_positions),
            strict=True,
        ):
            ax.text(
                position,
                -0.035,
                treatment,
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="top",
                fontsize=mpl.rcParams["xtick.labelsize"],
                clip_on=False,
            )
        ax.set_xticks(
            list(date_positions.values()),
            [DATE_LABELS[date] for date in DATES],
        )
        ax.tick_params(axis="x", which="major", pad=25, length=0)
        ax.set_xlabel("")
        if column_index == 0:
            ax.set_ylabel(OUTCOME_LABELS[outcome])
        if row_index == 0:
            ax.set_title(sector.upper())

    def plot_mixed_outcome_panel(
        ax: Any,
        *,
        result: MixedTrajectoryResult,
        outcome: str,
        sector: str,
        row_index: int,
        column_index: int,
        outcome_count: int,
        date_positions: dict[str, float],
        treatment_offsets: dict[str, float],
        block_offsets: dict[str, float],
    ) -> None:
        emmeans = mixed_emmeans(result)
        for treatment in FERTILIZED:
            plot_mixed_treatment(
                ax,
                result=result,
                emmeans=emmeans,
                outcome=outcome,
                treatment=treatment,
                date_positions=date_positions,
                treatment_offsets=treatment_offsets,
                block_offsets=block_offsets,
            )
        configure_mixed_outcome_axis(
            ax,
            result=result,
            outcome=outcome,
            sector=sector,
            row_index=row_index,
            column_index=column_index,
            outcome_count=outcome_count,
            date_positions=date_positions,
            treatment_offsets=treatment_offsets,
        )

    def plot_mixed_outcome_grid(
        outcomes: Sequence[str],
        *,
        title: str,
        filename_stem: str,
    ) -> None:
        date_levels = [DATE_LABELS[date] for date in DATES]
        date_positions = {
            date_label: float(index) for index, date_label in enumerate(date_levels)
        }
        treatment_offsets = dict(
            zip(FERTILIZED, np.linspace(-0.28, 0.28, len(FERTILIZED)), strict=True)
        )
        block_offsets = dict(
            zip(BLOCKS, np.linspace(-0.016, 0.016, len(BLOCKS)), strict=True)
        )
        fig, axes = mpl.subplots(
            len(outcomes),
            len(SECTORS),
            figsize=(12.2, 6.2 if len(outcomes) == 1 else 9.2),
            squeeze=False,
        )
        axes_array = np.asarray(axes)
        for row_index, outcome in enumerate(outcomes):
            for column_index, sector in enumerate(SECTORS):
                result = mixed_models[(outcome, sector, "M1–M5")]
                plot_mixed_outcome_panel(
                    axes_array[row_index, column_index],
                    result=result,
                    outcome=outcome,
                    sector=sector,
                    row_index=row_index,
                    column_index=column_index,
                    outcome_count=len(outcomes),
                    date_positions=date_positions,
                    treatment_offsets=treatment_offsets,
                    block_offsets=block_offsets,
                )

        p_lines: list[str] = []
        for outcome in outcomes:
            sector_values: list[str] = []
            method_label = "LRT asintótica, apoyo"
            for sector in SECTORS:
                result = mixed_models[(outcome, sector, "M1–M5")]
                p_value = float(cast(Any, result.summary["p_treatment_x_date"]))
                adjusted_value = float(
                    mixed_summary.loc[
                        mixed_summary["outcome"].eq(outcome)
                        & mixed_summary["sector"].eq(sector)
                        & mixed_summary["comparison"].eq("M1–M5"),
                        "p_treatment_x_date_bh",
                    ].iloc[0]
                )
                method = str(result.summary["interaction_p_method"])
                method_label = (
                    "bootstrap paramétrico"
                    if method == "parametric_bootstrap"
                    else "LRT asintótica, apoyo"
                )
                sector_values.append(
                    f"{sector} p = {p_value:.4f}, q = {adjusted_value:.4f}".replace(
                        ".", ","
                    )
                )
            p_lines.append(
                f"{OUTCOME_LABELS[outcome]} — interacción calendario × fecha "
                f"({method_label}): " + "; ".join(sector_values)
            )
        add_figure_header(
            fig,
            title,
            subtitle=(
                "Puntos claros: parcelas individuales. Círculos: media marginal "
                "del modelo completo ± IC normal del 95 %."
            ),
        )
        fig.text(
            0.07,
            0.865 if len(outcomes) == 1 else 0.895,
            "\n".join(p_lines),
            ha="left",
            va="top",
            color=mpl.rcParams["axes.labelcolor"],
            fontsize=9.25,
            linespacing=1.35,
        )
        add_figure_note(
            fig,
            (
                "Fechas equidistantes en orden cronológico; M1–M5 se agrupan dentro de cada fecha "
                "y las estimaciones no se conectan. El 16 sep M5 tenía 100 kg N ha⁻¹ "
                "experimentales y M1–M4, 200 kg ha⁻¹."
            ),
        )
        fig.subplots_adjust(
            left=0.09,
            right=0.98,
            bottom=0.19 if len(outcomes) == 1 else 0.13,
            top=0.76 if len(outcomes) == 1 else 0.77,
            hspace=0.48,
            wspace=0.12,
        )
        save_figure(fig, filename_stem)
        mpl.show()
        mpl.close(fig)

    contrast_rows: list[pd.DataFrame] = []
    for outcome in LONGITUDINAL_OUTCOMES:
        for sector in SECTORS:
            result = mixed_models[(outcome, sector, "M1–M5")]
            contrasts = mixed_early_late_contrasts(result)
            contrasts.insert(0, "sector", sector)
            contrasts.insert(0, "outcome", OUTCOME_LABELS[outcome])
            contrast_rows.append(contrasts)

    early_late_contrasts = pd.concat(contrast_rows, ignore_index=True)
    display_output(early_late_contrasts.round(4))

    plot_mixed_outcome_grid(
        ["biomass_kg_ha_used"],
        title="Biomasa aérea estimada en las tres fechas (M1–M5)",
        filename_stem="figura_04_trayectorias_biomasa_aerea",
    )
    plot_mixed_outcome_grid(
        ["n_pct"],
        title="Concentración de N estimada en las tres fechas (M1–M5)",
        filename_stem="figura_05_trayectorias_concentracion_n",
    )
    plot_mixed_outcome_grid(
        ["q_kg_n_ha", "nni_revised"],
        title="Resultados derivados de apoyo: N en biomasa e INN",
        filename_stem="anexo_trayectorias_n_biomasa_e_inn",
    )
    yield "mixed_estimates"

    # Notebook step: september_sensitivity
    sep_equal_dose_rows: list[dict[str, object]] = []
    for outcome in LONGITUDINAL_OUTCOMES:
        for sector in SECTORS:
            frame = data.longitudinal.loc[
                data.longitudinal["date"].astype("datetime64[ns]").eq(DATES[0])
                & data.longitudinal["sector"].astype(str).eq(sector)
            ]
            result = fit_rcbd(
                frame,
                outcome=outcome,
                treatments=["M1", "M2", "M3", "M4"],
            )
            sep_equal_dose_rows.append(
                {
                    "outcome": OUTCOME_LABELS[outcome],
                    "sector": sector,
                    "p_M1_M4": result.anova.loc["C(treatment)", "PR(>F)"],
                    "cv_pct": result.cv_pct,
                }
            )
    display_output(pd.DataFrame(sep_equal_dose_rows).round(4))
    yield "september_sensitivity"

    # Notebook step: figure_manifest
    figure_manifest = pd.DataFrame(
        [
            {
                "archivo": "figura_01_cronograma_y_n_acumulado",
                "ubicación sugerida": "Métodos — cuerpo principal",
                "función": (
                    "Define los calendarios, el cierre del pastoreo, las aplicaciones "
                    "comunes y la dosis acumulada a cada muestreo."
                ),
                "prioridad": "Esencial",
            },
            {
                "archivo": "figura_02_aportes_mensuales_de_agua",
                "ubicación sugerida": "Sitio y manejo — cuerpo principal",
                "función": (
                    "Muestra la distribución temporal de precipitación y riego sin "
                    "confundir aportes brutos con agua disponible o consumida."
                ),
                "prioridad": "Alta",
            },
            {
                "archivo": "figura_03_rendimiento_dos_preguntas",
                "ubicación sugerida": "Resultados — cuerpo principal",
                "función": (
                    "Separa la respuesta a N adicional de la comparación M1–M5 y "
                    "muestra datos crudos, magnitud e incertidumbre."
                ),
                "prioridad": "Esencial",
            },
            {
                "archivo": "figura_04_trayectorias_biomasa_aerea",
                "ubicación sugerida": "Resultados — cuerpo principal",
                "función": (
                    "Resume la variable primitiva de biomasa con datos individuales, "
                    "medias longitudinales e interacción calendario × fecha."
                ),
                "prioridad": "Esencial",
            },
            {
                "archivo": "figura_05_trayectorias_concentracion_n",
                "ubicación sugerida": "Resultados — cuerpo principal",
                "función": (
                    "Resume la variable primitiva de concentración de N sin mezclarla "
                    "con desenlaces derivados."
                ),
                "prioridad": "Esencial",
            },
            {
                "archivo": "anexo_trayectorias_n_biomasa_e_inn",
                "ubicación sugerida": "Anexo técnico",
                "función": (
                    "Presenta N presente en biomasa e INN como resultados derivados de "
                    "apoyo, sin contarlos como evidencia primaria independiente."
                ),
                "prioridad": "Complementaria",
            },
            {
                "archivo": "figura_06_componentes_del_rendimiento",
                "ubicación sugerida": "Resultados — cuerpo principal o síntesis",
                "función": (
                    "Muestra los componentes con observaciones e intervalos sin usar la "
                    "relación algebraica como prueba de compensación fisiológica."
                ),
                "prioridad": "Alta",
            },
            {
                "archivo": "anexo_contrastes_rendimiento",
                "ubicación sugerida": "Anexo o discusión de incertidumbre",
                "función": (
                    "Cuantifica la respuesta frente a M0 y cuánto desacuerdo entre "
                    "calendarios sigue siendo compatible con la inferencia clásica."
                ),
                "prioridad": "Alta hasta disponer del anexo probabilístico",
            },
            {
                "archivo": "anexo_trayectorias_observadas_*",
                "ubicación sugerida": "Anexo",
                "función": (
                    "Conserva la comparación descriptiva M0–M5 sin confundirla con "
                    "la pregunta longitudinal principal M1–M5."
                ),
                "prioridad": "Complementaria",
            },
        ]
    )
    display_output(figure_manifest)
    yield "figure_manifest"

    # Notebook step: automatic_summary
    def format_p(value: float) -> str:
        if value < 0.0001:
            return "< 0.0001"
        return f"{value:.4f}"

    summary_lines: list[str] = []
    for sector in SECTORS:
        primary = cast(
            Any,
            final_rcbd.loc[
                final_rcbd["outcome"].eq("clean_yield_kg_ha")
                & final_rcbd["sector"].eq(sector)
                & final_rcbd["comparison"].eq("M1–M5")
            ].iloc[0],
        )
        complementary = cast(
            Any,
            final_rcbd.loc[
                final_rcbd["outcome"].eq("clean_yield_kg_ha")
                & final_rcbd["sector"].eq(sector)
                & final_rcbd["comparison"].eq("M0–M5")
            ].iloc[0],
        )
        summary_lines.append(
            f"- **{sector}:** rendimiento M1–M5 p = {format_p(primary.p_treatment)}; "
            f"M0–M5 p = {format_p(complementary.p_treatment)}; "
            f"CV M1–M5 = {primary.cv_pct:.1f} % y "
            f"CV M0–M5 = {complementary.cv_pct:.1f} %."
        )

    summary_lines.append(
        "\n**Pruebas longitudinales M1–M5 (interacción tratamiento × fecha):**"
    )
    for raw_row in mixed_summary.loc[
        mixed_summary["comparison"].eq("M1–M5")
    ].itertuples(index=False):
        row = cast(Any, raw_row)
        method_label = (
            "bootstrap paramétrico"
            if row.interaction_p_method == "parametric_bootstrap"
            else "LRT asintótica de apoyo"
        )
        summary_lines.append(
            f"- {row.label}, {row.sector}: p = {format_p(row.p_treatment_x_date)} "
            f"({method_label}; q BH = {format_p(row.p_treatment_x_date_bh)})"
            + (
                "; varianza de parcela en el límite."
                if row.random_effect_boundary
                else "."
            )
        )

    summary_lines.append("\n**Sensibilidad de escala de la biomasa:**")
    for sector in SECTORS:
        scale_rows = biomass_scale_sensitivity.loc[
            biomass_scale_sensitivity["sector"].eq(sector)
        ].set_index("response_scale")
        original_p = float(
            cast(Any, scale_rows.at["original", "p_treatment_x_date_bootstrap"])
        )
        log_p = float(cast(Any, scale_rows.at["log", "p_treatment_x_date_bootstrap"]))
        summary_lines.append(
            f"- {sector}: escala original p = {format_p(original_p)}; "
            f"escala logarítmica p = {format_p(log_p)}."
        )
    summary_lines.append(
        "La diferencia entre escalas en secano impide presentar esa interacción de "
        "biomasa como una conclusión robusta a la especificación."
    )

    summary_lines.append(
        "\n**Lectura recomendada:** los ANOVA por fecha describen momentos concretos; "
        "el modelo longitudinal evalúa directamente si las trayectorias cambian con el "
        "calendario. La ausencia de una diferencia de rendimiento entre M1–M5 no debe "
        "traducirse en equivalencia exacta, y las diferencias entre sectores siguen "
        "siendo descriptivas."
    )
    display_output(Markdown("\n".join(summary_lines)))
    yield "automatic_summary"

    # Notebook step: export_artifacts
    if EXPORT_RESULTS:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        longitudinal_rcbd.to_csv(
            RESULTS_DIR / "anova_por_fecha_y_sector.csv", index=False
        )
        final_rcbd.to_csv(RESULTS_DIR / "anova_variables_finales.csv", index=False)
        derived_descriptive.to_csv(
            RESULTS_DIR / "indicadores_derivados_descriptivos.csv", index=False
        )
        dry_matter_sensitivity.to_csv(
            RESULTS_DIR / "sensibilidad_materia_seca_150_152.csv", index=False
        )
        joint_results.to_csv(
            RESULTS_DIR / "anova_conjunto_entre_sectores.csv", index=False
        )
        diagnostics.to_csv(
            RESULTS_DIR / "diagnosticos_modelos_clasicos.csv", index=False
        )
        raw_correlations.to_csv(RESULTS_DIR / "correlaciones_tesis.csv", index=False)
        correlation_audit.to_csv(
            RESULTS_DIR / "correlaciones_extension_auditoria.csv", index=False
        )
        mixed_summary.to_csv(
            RESULTS_DIR / "modelos_longitudinales_mixtos.csv", index=False
        )
        biomass_scale_sensitivity.to_csv(
            RESULTS_DIR / "sensibilidad_escala_biomasa.csv", index=False
        )
        inference_hierarchy.to_csv(
            RESULTS_DIR / "jerarquia_inferencial.csv", index=False
        )
        early_late_contrasts.to_csv(
            RESULTS_DIR / "contrastes_temprano_menos_tardio.csv", index=False
        )
        flagged_dm.to_csv(
            RESULTS_DIR / "registros_materia_seca_a_verificar.csv", index=False
        )
        figure_manifest.to_csv(RESULTS_DIR / "seleccion_figuras_tesis.csv", index=False)
        water_inputs.to_csv(RESULTS_DIR / "aportes_mensuales_de_agua.csv", index=False)
        yield_contrasts.to_csv(
            RESULTS_DIR / "contrastes_rendimiento_clasicos.csv", index=False
        )
        print("Tablas exportadas en:", RESULTS_DIR.resolve())
        for path in sorted(RESULTS_DIR.glob("*.csv")):
            print(" -", path.name)

    if EXPORT_FIGURES:
        print("Figuras exportadas en:", FIGURES_DIR.resolve())
        for path in sorted(FIGURES_DIR.glob("*")):
            if path.suffix.lower() in {".png", ".pdf"}:
                print(" -", path.name)
    yield "export_artifacts"
