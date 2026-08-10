"""Canonical CSV loading, reconstruction, validation, and provenance."""

from __future__ import annotations

# pandas exposes partially typed dataframe boundaries.
# pyright: reportArgumentType=false, reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
import argparse
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, cast

import numpy as np
import pandas as pd

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR: Final = PROJECT_ROOT / "data"
CANONICAL_JSON_FILES: Final = ("manifest.json", "formulas.json")
REQUIRED_FORMULA_TARGETS: Final = frozenset(
    {
        ("dry_matter_calculated.csv", "dry_matter_pct_from_weights"),
        ("dry_matter_calculated.csv", "dry_matter_abs_difference_pp"),
        ("dry_matter_calculated.csv", "dry_matter_relative_difference"),
        ("dry_matter_calculated.csv", "dry_matter_issue"),
        ("dry_matter_calculated.csv", "biomass_recorded_dm_kg_ha"),
        ("dry_matter_calculated.csv", "biomass_ratio_dm_kg_ha"),
        (
            "dry_matter_calculated.csv",
            "biomass_recalculation_difference_kg_ha",
        ),
        ("dry_matter_calculated.csv", "tiller_density_m2"),
        ("harvest_calculated.csv", "w1000_g"),
        ("harvest_calculated.csv", "panicle_density_m2"),
        ("harvest_calculated.csv", "dirty_yield_kg_ha"),
        ("harvest_calculated.csv", "clean_yield_kg_ha"),
        ("harvest_calculated.csv", "clean_recovery"),
        ("harvest_calculated.csv", "cleaning_loss_pct"),
        ("harvest_calculated.csv", "estimated_seed_count"),
        ("harvest_calculated.csv", "estimated_seeds_per_panicle"),
        ("harvest_calculated.csv", "harvest_index_pct"),
        ("quality_calculated.csv", "estimated_n_pct"),
        ("quality_calculated.csv", "estimated_adf_pct"),
        ("quality_calculated.csv", "estimated_ndf_pct"),
        ("quality_calculated.csv", "n_accumulated_kg_ha"),
        ("quality_calculated.csv", "critical_n_pct"),
        ("quality_calculated.csv", "nni"),
        ("missing_quality_estimate.csv", "n_pct_estimated"),
        ("missing_quality_estimate.csv", "adf_pct_estimated"),
        ("missing_quality_estimate.csv", "ndf_pct_estimated"),
        ("missing_quality_estimate.csv", "n_accumulated_kg_ha"),
        ("missing_quality_estimate.csv", "critical_n_pct"),
        ("missing_quality_estimate.csv", "nni"),
    }
)

DataStatus = Literal[
    "recorded",
    "recorded_method_not_encoded",
    "calculated_materialization",
    "estimated",
    "missing",
    "analysis_derived",
    "metadata",
]
DryMatterPolicy = Literal["recorded", "ratio", "exclude"]


@dataclass(frozen=True)
class ExperimentSpec:
    """Design and management information loaded from the canonical data bundle."""

    data_dir: Path
    source_sha256: str
    experiment_year: int
    treatments: tuple[str, ...]
    sectors: tuple[str, ...]
    blocks: tuple[str, ...]
    repetitions: int
    plot_area_m2: float
    row_spacing_m: float
    biomass_sample_area_m2: float
    harvest_sample_area_m2: float
    experimental_n_total_kg_ha: float
    applications_per_treatment: int
    dose_per_application_kg_ha: float
    schedule: pd.DataFrame
    management: pd.DataFrame
    water_monthly: pd.DataFrame
    water_period_totals: pd.DataFrame
    source_audit: pd.DataFrame


@dataclass(frozen=True)
class ExperimentData:
    """Analysis-ready tables plus source and lineage metadata."""

    spec: ExperimentSpec
    longitudinal: pd.DataFrame
    harvest: pd.DataFrame
    seed_weight_long: pd.DataFrame
    baseline_biomass: pd.DataFrame
    baseline_tillers: pd.DataFrame
    variable_lineage: pd.DataFrame
    qa: pd.DataFrame


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_data_dir(
    data_dir: Path | str | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Resolve the canonical directory and reject workbook paths explicitly."""

    if data_dir is not None:
        explicit = Path(data_dir).expanduser().resolve()
        if explicit.is_file():
            if explicit.suffix.casefold() == ".xlsx":
                raise ValueError(
                    "El XLSX es evidencia histórica de migración y no puede usarse "
                    "como fuente analítica; indique el directorio data/."
                )
            raise NotADirectoryError(
                f"La fuente canónica debe ser un directorio: {explicit}"
            )
        if not explicit.is_dir():
            raise FileNotFoundError(f"No existe el directorio de datos: {explicit}")
        return explicit

    root = (project_root or PROJECT_ROOT).resolve()
    candidates = [root / "data", Path("/mnt/data") / "data"]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    attempted = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        f"No se encontró el directorio canónico data/. Se probó: {attempted}"
    )


def sha256_data_bundle(data_dir: Path) -> str:
    """Hash all analytical CSV and JSON inputs in deterministic path order."""

    digest = hashlib.sha256()
    files = sorted(
        path
        for path in data_dir.iterdir()
        if path.is_file() and path.suffix.casefold() in {".csv", ".json"}
    )
    for path in files:
        relative = path.relative_to(data_dir).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, object]:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"Expected a JSON object: {path}")
    return cast(dict[str, object], raw)


def _manifest_datasets(manifest: Mapping[str, object]) -> dict[str, dict[str, object]]:
    raw = manifest.get("datasets")
    if not isinstance(raw, dict):
        raise TypeError("manifest.json must contain an object named datasets")
    result: dict[str, dict[str, object]] = {}
    for filename, spec in raw.items():
        if not isinstance(filename, str) or not isinstance(spec, dict):
            raise TypeError("Each manifest dataset must map a filename to an object")
        result[filename] = cast(dict[str, object], spec)
    return result


def _parse_boolean(series: pd.Series) -> pd.Series:
    mapping: dict[object, object] = {
        "true": True,
        "false": False,
        "": pd.NA,
        None: pd.NA,
    }
    normalized = series.fillna("").astype(str).str.casefold().map(mapping)
    invalid = normalized.isna() & series.notna() & series.astype(str).ne("")
    if invalid.any():
        values = sorted(set(series.loc[invalid].astype(str)))
        raise ValueError(f"Invalid boolean values: {values}")
    return normalized.astype("boolean")


def _read_typed_csv(
    data_dir: Path, filename: str, spec: Mapping[str, object]
) -> pd.DataFrame:
    path = data_dir / filename
    if not path.is_file():
        raise FileNotFoundError(f"Falta el archivo canónico: {path}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    raw_columns = spec.get("columns")
    if not isinstance(raw_columns, dict):
        raise TypeError(f"Manifest columns must be an object for {filename}")
    columns = cast(dict[str, dict[str, object]], raw_columns)
    expected = list(columns)
    if frame.columns.tolist() != expected:
        raise ValueError(
            f"Columnas inesperadas en {filename}: {frame.columns.tolist()}; "
            f"se esperaba {expected}."
        )
    for column, column_spec in columns.items():
        data_type = column_spec.get("type")
        nullable = bool(column_spec.get("nullable", False))
        empty = frame[column].eq("")
        if not nullable and empty.any():
            rows = (frame.index[empty] + 2).tolist()[:5]
            raise ValueError(
                f"Valores vacíos no permitidos en {filename}:{column}, filas {rows}"
            )
        if data_type == "integer":
            numeric = pd.to_numeric(frame[column].replace("", pd.NA), errors="raise")
            non_integer = numeric.dropna().mod(1).ne(0)
            if non_integer.any():
                raise ValueError(f"Expected integer values in {filename}:{column}")
            frame[column] = numeric.astype("Int64")
        elif data_type == "number":
            frame[column] = pd.to_numeric(
                frame[column].replace("", pd.NA), errors="raise"
            ).astype(float)
        elif data_type == "date":
            parsed = pd.to_datetime(frame[column].replace("", pd.NA), errors="raise")
            frame[column] = parsed
        elif data_type == "boolean":
            frame[column] = _parse_boolean(frame[column])
        elif data_type == "string":
            frame[column] = frame[column].replace("", pd.NA).astype("string")
        else:
            raise ValueError(f"Unsupported manifest type {data_type!r} in {filename}")

    raw_primary_key = spec.get("primary_key")
    if not isinstance(raw_primary_key, list) or not all(
        isinstance(value, str) for value in raw_primary_key
    ):
        raise TypeError(f"Invalid primary key in manifest for {filename}")
    primary_key = cast(list[str], raw_primary_key)
    if frame[primary_key].isna().any(axis=None):
        raise ValueError(f"Null primary key in {filename}: {primary_key}")
    if frame.duplicated(primary_key).any():
        raise ValueError(f"Duplicate primary key in {filename}: {primary_key}")
    return frame


def _assert_close(
    observed: pd.Series,
    expected: pd.Series,
    *,
    label: str,
    atol: float = 1e-9,
) -> None:
    np.testing.assert_allclose(
        pd.to_numeric(observed, errors="coerce").to_numpy(float),
        pd.to_numeric(expected, errors="coerce").to_numpy(float),
        rtol=1e-12,
        atol=atol,
        equal_nan=True,
        err_msg=label,
    )


def _metadata_values(frame: pd.DataFrame) -> dict[str, object]:
    values: dict[str, object] = {}
    for record in frame.itertuples(index=False):
        parameter = str(record.parameter)
        if record.value_type == "integer":
            values[parameter] = int(record.value)
        elif record.value_type == "number":
            values[parameter] = float(record.value)
        else:
            values[parameter] = str(record.value)
    return values


def _validate_formula_metadata(
    formulas: Mapping[str, object], frames: Mapping[str, pd.DataFrame]
) -> None:
    raw_formulas = formulas.get("formulas")
    if not isinstance(raw_formulas, list) or not raw_formulas:
        raise TypeError("formulas.json must contain a non-empty formulas array")
    identifiers: set[str] = set()
    targets: set[tuple[str, str]] = set()
    for raw in raw_formulas:
        if not isinstance(raw, dict):
            raise TypeError("Each formula definition must be an object")
        formula = cast(dict[str, object], raw)
        identifier = formula.get("id")
        output_file = formula.get("output_file")
        output_column = formula.get("output_column")
        if not all(
            isinstance(value, str) for value in (identifier, output_file, output_column)
        ):
            raise TypeError("Formula id, output_file and output_column must be strings")
        identifier_text = cast(str, identifier)
        if identifier_text in identifiers:
            raise ValueError(f"Duplicate formula id: {identifier_text}")
        identifiers.add(identifier_text)
        output_file_text = cast(str, output_file)
        output_column_text = cast(str, output_column)
        if output_file_text not in frames:
            raise ValueError(f"Formula targets unknown dataset: {output_file_text}")
        if output_column_text not in frames[output_file_text].columns:
            raise ValueError(
                f"Formula {identifier_text} targets unknown column "
                f"{output_file_text}:{output_column_text}"
            )
        target = (output_file_text, output_column_text)
        if target in targets:
            raise ValueError(f"Duplicate formula target: {target}")
        targets.add(target)
        inputs = formula.get("inputs")
        if (
            not isinstance(inputs, list)
            or not inputs
            or not all(isinstance(value, str) and value for value in inputs)
        ):
            raise TypeError(f"Formula {identifier_text} has invalid inputs")
        for field in ("expression", "excel_formula_template"):
            value = formula.get(field)
            if not isinstance(value, str) or not value:
                raise TypeError(f"Formula {identifier_text} has invalid {field}")
        if "unit" not in formula:
            raise TypeError(f"Formula {identifier_text} is missing unit")
    required_targets = set(REQUIRED_FORMULA_TARGETS)
    if targets != required_targets:
        missing = sorted(required_targets - targets)
        unexpected = sorted(targets - required_targets)
        raise ValueError(
            "Formula targets do not cover the canonical materializations; "
            f"missing={missing}, unexpected={unexpected}"
        )


def _validate_relations(
    dataset_specs: Mapping[str, Mapping[str, object]],
    frames: Mapping[str, pd.DataFrame],
) -> None:
    for filename, spec in dataset_specs.items():
        raw_foreign_keys = spec.get("foreign_keys", [])
        if not isinstance(raw_foreign_keys, list):
            raise TypeError(f"foreign_keys must be a list for {filename}")
        for raw in raw_foreign_keys:
            if not isinstance(raw, dict):
                raise TypeError(f"Invalid foreign key definition for {filename}")
            foreign_key = cast(dict[str, object], raw)
            columns = cast(list[str], foreign_key["columns"])
            reference_file = cast(str, foreign_key["references"])
            reference_columns = cast(
                list[str], foreign_key.get("reference_columns", columns)
            )
            left = frames[filename][columns].dropna().drop_duplicates()
            right = frames[reference_file][reference_columns].dropna().drop_duplicates()
            right.columns = columns
            unmatched = left.merge(right, on=columns, how="left", indicator=True)
            if unmatched["_merge"].ne("both").any():
                raise ValueError(
                    f"Foreign key violation: {filename}{columns} -> "
                    f"{reference_file}{reference_columns}"
                )


def _rcbd_estimate(
    frame: pd.DataFrame,
    value_column: str,
    *,
    treatment: str,
    block: str,
    treatment_count: int,
    block_count: int,
) -> tuple[float, float, float, float]:
    observed = frame.dropna(subset=[value_column])
    block_total = float(observed.loc[observed["block"].eq(block), value_column].sum())
    treatment_total = float(
        observed.loc[observed["treatment"].eq(treatment), value_column].sum()
    )
    grand_total = float(observed[value_column].sum())
    estimate = (
        treatment_count * block_total + block_count * treatment_total - grand_total
    ) / ((treatment_count - 1) * (block_count - 1))
    return block_total, treatment_total, grand_total, estimate


def _validate_scientific_identities(
    frames: Mapping[str, pd.DataFrame], metadata: Mapping[str, object]
) -> None:
    design = frames["experimental_design.csv"]
    if len(design) != 24:
        raise ValueError(
            f"Expected 24 experimental design positions, found {len(design)}"
        )
    expected_treatments = {f"M{index}" for index in range(6)}
    for block, block_frame in design.groupby("block", observed=True):
        observed = set(block_frame["treatment"].astype(str))
        if observed != expected_treatments:
            raise ValueError(
                f"Block {block} does not contain M0-M5 exactly once: {observed}"
            )

    experiment_year = int(metadata["experiment_year"])
    for filename, frame in frames.items():
        for column in frame.columns:
            if column != "date":
                continue
            years = set(frame[column].dropna().dt.year.astype(int))
            if years and years != {experiment_year}:
                raise ValueError(
                    f"Experimental dates in {filename}:{column} do not match "
                    f"experiment year {experiment_year}: {years}"
                )

    timeline = frames["field_timeline.csv"]
    years = set(pd.to_datetime(timeline["date"]).dt.year)
    if years != {experiment_year}:
        raise ValueError(f"Timeline years do not match experiment year: {years}")
    applications = timeline.loc[timeline["event_type"].eq("nitrogen_application")]
    if len(applications) != 10:
        raise ValueError(
            f"Expected 10 treatment applications, found {len(applications)}"
        )
    counts = applications.groupby("treatment", observed=True)[
        "application_number"
    ].nunique()
    if counts.to_dict() != {f"M{index}": 2 for index in range(1, 6)}:
        raise ValueError(
            f"Each M1-M5 treatment must have two applications: {counts.to_dict()}"
        )
    m3_second = applications.loc[
        applications["treatment"].eq("M3") & applications["application_number"].eq(2),
        "date",
    ]
    if len(m3_second) != 1 or pd.Timestamp(m3_second.iloc[0]) != pd.Timestamp(
        "2025-08-21"
    ):
        raise ValueError("M3 application 2 must be 2025-08-21")
    if timeline["date"].isin([pd.Timestamp("2025-07-31")]).any():
        raise ValueError("The obsolete 2025-07-31 date is not permitted")

    water = frames["water_inputs.csv"]
    expected_months = list(range(1, 12))
    if water["month"].astype(int).tolist() != expected_months:
        raise ValueError("Water inputs must contain January-November exactly once")
    if not np.isclose(float(water["irrigation_mm"].sum()), 165.0):
        raise ValueError("Monthly irrigation must sum to 165 mm")
    if not np.isclose(float(water["rainfall_mm"].sum()), 1176.0):
        raise ValueError("Monthly rainfall must sum to 1176 mm")

    dry_raw = frames["dry_matter_recorded.csv"]
    dry_calc = frames["dry_matter_calculated.csv"]
    if len(dry_raw) != 154 or len(dry_calc) != 154:
        raise ValueError("Dry-matter datasets must each contain 154 rows")
    dry = dry_raw.merge(dry_calc, on="observation_id", validate="one_to_one")
    ratio = 100.0 * dry["dry_weight_g"] / dry["green_weight_sample_g"]
    _assert_close(dry["dry_matter_pct_from_weights"], ratio, label="dry matter ratio")
    absolute = (dry["dry_matter_pct"] - ratio).abs()
    relative = absolute / dry["dry_matter_pct"].abs().replace(0.0, np.nan)
    _assert_close(
        dry["dry_matter_abs_difference_pp"],
        absolute,
        label="dry matter absolute difference",
    )
    _assert_close(
        dry["dry_matter_relative_difference"],
        relative,
        label="dry matter relative difference",
    )
    issue = (absolute.ge(5.0) & relative.ge(0.20)).fillna(False)
    pd.testing.assert_series_equal(
        dry["dry_matter_issue"].fillna(False).astype(bool).reset_index(drop=True),
        issue.astype(bool).reset_index(drop=True),
        check_names=False,
        obj="dry matter issue",
    )
    area = float(metadata["biomass_sample_area_m2"])
    biomass = dry["green_weight_1m_g"] * (dry["dry_matter_pct"] / 100.0) * 10.0 / area
    biomass_ratio = dry["green_weight_1m_g"] * (ratio / 100.0) * 10.0 / area
    _assert_close(
        dry["biomass_recorded_dm_kg_ha"],
        biomass,
        label="biomass using recorded dry matter",
    )
    _assert_close(
        dry["biomass_ratio_dm_kg_ha"],
        biomass_ratio,
        label="biomass using reconstructed dry matter",
    )
    _assert_close(
        dry["biomass_recalculation_difference_kg_ha"],
        biomass - dry["biomass_reported_kg_ha"],
        label="biomass reconciliation",
    )
    tillers = (
        dry["tillers_30_cm"]
        * (100.0 / 30.0)
        * (100.0 / float(metadata["row_spacing_cm"]))
    )
    _assert_close(dry["tiller_density_m2"], tillers, label="tiller density")

    harvest_raw = frames["harvest_recorded.csv"]
    harvest_calc = frames["harvest_calculated.csv"]
    if len(harvest_raw) != 48 or len(harvest_calc) != 48:
        raise ValueError("Harvest datasets must each contain 48 rows")
    harvest = harvest_raw.merge(
        harvest_calc, on="observation_id", validate="one_to_one"
    )
    harvest_area = float(metadata["harvest_sample_area_m2"])
    w1000 = harvest[["w100_rep1_g", "w100_rep2_g", "w100_rep3_g"]].mean(axis=1) * 10.0
    _assert_close(harvest["w1000_g"], w1000, label="thousand seed weight")
    _assert_close(
        harvest["panicle_density_m2"],
        harvest["panicle_count"] / harvest_area,
        label="panicle density",
    )
    _assert_close(
        harvest["dirty_yield_kg_ha"],
        harvest["dirty_seed_mass_g"] * 10.0 / harvest_area,
        label="dirty yield",
    )
    _assert_close(
        harvest["clean_yield_kg_ha"],
        harvest["clean_seed_mass_g"] * 10.0 / harvest_area,
        label="clean yield",
    )
    recovery = harvest["clean_seed_mass_g"] / harvest["dirty_seed_mass_g"]
    _assert_close(harvest["clean_recovery"], recovery, label="clean recovery")
    _assert_close(
        harvest["cleaning_loss_pct"], 100.0 * (1.0 - recovery), label="cleaning loss"
    )
    seed_count = 1000.0 * harvest["clean_seed_mass_g"] / w1000
    _assert_close(
        harvest["estimated_seed_count"], seed_count, label="estimated seed count"
    )
    _assert_close(
        harvest["estimated_seeds_per_panicle"],
        seed_count / harvest["panicle_count"],
        label="estimated seeds per panicle",
    )
    final_biomass = dry.loc[
        dry["date"].eq(dry["date"].max())
        & dry["treatment"].astype(str).str.fullmatch(r"M[0-5]", na=False),
        ["sector", "treatment", "block", "biomass_recorded_dm_kg_ha"],
    ]
    harvest_with_biomass = harvest.merge(
        final_biomass,
        on=["sector", "treatment", "block"],
        how="left",
        validate="one_to_one",
    )
    _assert_close(
        harvest_with_biomass["harvest_index_pct"],
        100.0
        * harvest_with_biomass["clean_yield_kg_ha"]
        / harvest_with_biomass["biomass_recorded_dm_kg_ha"],
        label="harvest index",
    )

    quality_raw = frames["quality_recorded.csv"]
    quality_calc = frames["quality_calculated.csv"]
    estimate = frames["missing_quality_estimate.csv"]
    if len(quality_raw) != 152 or len(quality_calc) != 152 or len(estimate) != 1:
        raise ValueError("Quality datasets must contain 152, 152, and 1 rows")
    estimated_rows = quality_raw.loc[quality_raw["measurement_status"].eq("estimated")]
    if len(estimated_rows) != 1:
        raise ValueError("Exactly one quality row must be marked estimated")
    missing = estimated_rows.iloc[0]
    subset = quality_raw.loc[
        quality_raw["date"].eq(missing["date"])
        & quality_raw["sector"].eq(missing["sector"])
    ]
    estimate_row = estimate.iloc[0]
    for variable, prefix in (("n_pct", "n"), ("adf_pct", "adf"), ("ndf_pct", "ndf")):
        block_total, treatment_total, grand_total, value = _rcbd_estimate(
            subset,
            variable,
            treatment=str(missing["treatment"]),
            block=str(missing["block"]),
            treatment_count=6,
            block_count=4,
        )
        expected = pd.Series([block_total, treatment_total, grand_total, value])
        observed = estimate_row[
            [
                f"{prefix}_block_total",
                f"{prefix}_treatment_total",
                f"{prefix}_grand_total",
                f"{prefix}_pct_estimated",
            ]
        ]
        _assert_close(observed, expected, label=f"{prefix} DBCA estimate")
    if not np.isclose(float(estimate_row["n_pct_estimated"]), 2.8688484862162937):
        raise ValueError("The canonical missing N estimate is incorrect")
    if not np.isclose(float(estimate_row["adf_pct_estimated"]), 40.77623836505554):
        raise ValueError("The canonical missing ADF estimate is incorrect")
    if not np.isclose(float(estimate_row["ndf_pct_estimated"]), 69.57708690222144):
        raise ValueError("The canonical missing NDF estimate is incorrect")
    if not np.isclose(float(estimate_row["n_accumulated_kg_ha"]), 201.8808679750406):
        raise ValueError("The canonical missing accumulated N is incorrect")
    if not np.isclose(float(estimate_row["nni"]), 1.1159131393270323):
        raise ValueError("The canonical missing NNI is incorrect")

    estimate_biomass = float(estimate_row["biomass_kg_ha"])
    estimate_n = float(estimate_row["n_pct_estimated"])
    estimate_critical = 4.8 * (estimate_biomass / 1000.0) ** -0.32
    _assert_close(
        estimate["n_accumulated_kg_ha"],
        pd.Series([estimate_biomass * estimate_n / 100.0]),
        label="missing accumulated N",
    )
    _assert_close(
        estimate["critical_n_pct"],
        pd.Series([estimate_critical]),
        label="missing critical N",
    )
    _assert_close(
        estimate["nni"],
        pd.Series([estimate_n / estimate_critical]),
        label="missing NNI",
    )

    quality = quality_raw.merge(
        quality_calc,
        on="sample_id",
        validate="one_to_one",
        suffixes=("_recorded", "_calculated"),
    ).merge(
        dry[["sample_id", "biomass_reported_kg_ha"]].dropna(subset=["sample_id"]),
        on="sample_id",
        validate="one_to_one",
    )
    estimated_mask = quality["measurement_status"].eq("estimated")
    expected_n_estimate = pd.Series(np.nan, index=quality.index)
    expected_adf_estimate = pd.Series(np.nan, index=quality.index)
    expected_ndf_estimate = pd.Series(np.nan, index=quality.index)
    expected_n_estimate.loc[estimated_mask] = float(estimate_row["n_pct_estimated"])
    expected_adf_estimate.loc[estimated_mask] = float(estimate_row["adf_pct_estimated"])
    expected_ndf_estimate.loc[estimated_mask] = float(estimate_row["ndf_pct_estimated"])
    _assert_close(
        quality["estimated_n_pct"],
        expected_n_estimate,
        label="identified N estimate",
    )
    _assert_close(
        quality["estimated_adf_pct"],
        expected_adf_estimate,
        label="identified ADF estimate",
    )
    _assert_close(
        quality["estimated_ndf_pct"],
        expected_ndf_estimate,
        label="identified NDF estimate",
    )
    effective_n = quality["n_pct"].fillna(quality["estimated_n_pct"])
    materialized_biomass = quality["biomass_reported_kg_ha"]
    critical_n = 4.8 * (materialized_biomass / 1000.0) ** -0.32
    _assert_close(
        quality["n_accumulated_kg_ha"],
        materialized_biomass * effective_n / 100.0,
        label="quality accumulated N",
    )
    _assert_close(
        quality["critical_n_pct"],
        critical_n,
        label="quality critical N",
    )
    _assert_close(quality["nni"], effective_n / critical_n, label="quality NNI")


def validate_data_bundle(
    data_dir: Path | str | None = None,
    *,
    project_root: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Validate schemas, relationships, chronology, and calculated identities."""

    path = locate_data_dir(data_dir, project_root=project_root)
    manifest = _read_json(path / "manifest.json")
    formulas = _read_json(path / "formulas.json")
    if manifest.get("schema_version") != 1 or formulas.get("schema_version") != 1:
        raise ValueError("Unsupported canonical data schema version")
    if manifest.get("authority") != "canonical_csv_bundle":
        raise ValueError("manifest.json does not declare the CSV bundle as canonical")
    dataset_specs = _manifest_datasets(manifest)
    frames = {
        filename: _read_typed_csv(path, filename, spec)
        for filename, spec in dataset_specs.items()
    }
    _validate_relations(dataset_specs, frames)
    _validate_formula_metadata(formulas, frames)
    metadata = _metadata_values(frames["experiment_metadata.csv"])
    _validate_scientific_identities(frames, metadata)
    return frames


def _schedule_from_timeline(
    timeline: pd.DataFrame, treatments: tuple[str, ...], experiment_year: int
) -> pd.DataFrame:
    applications = timeline.loc[
        timeline["event_type"].eq("nitrogen_application"),
        ["treatment", "application_number", "date"],
    ].copy()
    if (
        not applications.empty
        and not applications["date"].dt.year.eq(experiment_year).all()
    ):
        wrong = applications.loc[
            ~applications["date"].dt.year.eq(experiment_year)
        ].iloc[0]
        raise ValueError(
            f"Application {wrong['treatment']} belongs to {wrong['date'].year}; "
            f"expected experiment year {experiment_year}."
        )
    rows: list[dict[str, object]] = []
    for treatment in treatments:
        subset = applications.loc[applications["treatment"].eq(treatment)].set_index(
            "application_number"
        )
        rows.append(
            {
                "treatment": treatment,
                "first_application": (
                    subset.loc[1, "date"] if 1 in subset.index else pd.NaT
                ),
                "second_application": (
                    subset.loc[2, "date"] if 2 in subset.index else pd.NaT
                ),
                "source_dataset": "field_timeline.csv",
                "source_range": "field_timeline.csv",
            }
        )
    return pd.DataFrame(rows)


def _management_and_water(
    frames: Mapping[str, pd.DataFrame],
    *,
    study_start: pd.Timestamp,
    study_end: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    management = (
        frames["field_management.csv"].rename(columns={"activity": "management"}).copy()
    )
    management["source_dataset"] = "field_management.csv"
    water = (
        frames["water_inputs.csv"]
        .rename(columns={"irrigation_mm": "supplemental_irrigation_mm"})
        .copy()
    )
    water["month_start"] = pd.to_datetime(
        {"year": water["year"], "month": water["month"], "day": 1}
    )
    water["included_in_study_months"] = water["month_start"].between(
        study_start.to_period("M").to_timestamp(),
        study_end.to_period("M").to_timestamp(),
        inclusive="both",
    )
    water["irrigated_sector_input_mm"] = (
        water["rainfall_mm"] + water["supplemental_irrigation_mm"]
    )
    water["source_dataset"] = "water_inputs.csv"
    period = water.loc[water["included_in_study_months"]]
    rainfall = float(period["rainfall_mm"].sum())
    irrigation = float(period["supplemental_irrigation_mm"].sum())
    totals = pd.DataFrame(
        [
            {
                "sector": "Secano",
                "rainfall_mm": rainfall,
                "supplemental_irrigation_mm": 0.0,
                "gross_input_mm": rainfall,
                "aggregation": "meses calendario que intersectan el ensayo",
                "study_start": study_start,
                "study_end": study_end,
            },
            {
                "sector": "Riego",
                "rainfall_mm": rainfall,
                "supplemental_irrigation_mm": irrigation,
                "gross_input_mm": rainfall + irrigation,
                "aggregation": "meses calendario que intersectan el ensayo",
                "study_start": study_start,
                "study_end": study_end,
            },
        ]
    )
    return management, water, totals


def _source_audit(
    *,
    schedule: pd.DataFrame,
    sample_dates: tuple[pd.Timestamp, ...],
    management: pd.DataFrame,
    quality: pd.DataFrame,
    dry_matter: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    sample_set = set(sample_dates)
    for record in schedule.itertuples(index=False):
        for application_number, application_date in enumerate(
            [record.first_application, record.second_application], start=1
        ):
            if (
                pd.notna(application_date)
                and pd.Timestamp(application_date) in sample_set
            ):
                rows.append(
                    {
                        "severity": "warning",
                        "issue": "application_and_sampling_same_date",
                        "location": "field_timeline.csv",
                        "detail": (
                            "Aplicación y muestreo comparten fecha; el orden intradía no "
                            "está documentado y no se interpreta el muestreo como respuesta "
                            "posterior a esa aplicación."
                        ),
                        "observed": (
                            f"{record.treatment}, aplicación {application_number}, "
                            f"{pd.Timestamp(application_date).date()}"
                        ),
                    }
                )
    april = management.loc[management["month"].eq(4), "management"].dropna()
    if not april.empty:
        rows.append(
            {
                "severity": "warning",
                "issue": "common_n_active_dose_unresolved",
                "location": "field_management.csv:2025-04",
                "detail": (
                    "El registro conserva la masa de producto, pero no codifica su "
                    "fracción de N; no se transforma a kg N/ha ni se suma al N experimental."
                ),
                "observed": str(april.iloc[0]),
            }
        )
    estimated = quality.loc[quality["measurement_status"].eq("estimated"), "sample_id"]
    if not estimated.empty:
        rows.append(
            {
                "severity": "warning",
                "issue": "estimated_quality_values_present",
                "location": "quality_recorded.csv:measurement_status",
                "detail": (
                    "La muestra estimada se conserva para auditoría, pero se excluye "
                    "del análisis primario de mediciones."
                ),
                "observed": ", ".join(str(value) for value in estimated),
            }
        )
    difference = dry_matter["biomass_recalculation_difference_kg_ha"].abs().dropna()
    rows.append(
        {
            "severity": "info",
            "issue": "biomass_materialization_reconciled",
            "location": "dry_matter_calculated.csv",
            "detail": (
                "La biomasa se recalcula uniformemente desde peso verde, porcentaje "
                "de materia seca y geometría; la materialización histórica se conserva "
                "solo para conciliación."
            ),
            "observed": float(difference.max()) if not difference.empty else np.nan,
        }
    )
    return pd.DataFrame(rows)


def _variable_lineage() -> pd.DataFrame:
    rows = [
        (
            "Fecha, sector, tratamiento, bloque y muestra",
            "metadata",
            "CSV canónicos",
            "Identificadores normalizados.",
        ),
        (
            "Pesos y conteos de campo",
            "recorded",
            "dry_matter_recorded.csv y harvest_recorded.csv",
            "Mediciones primitivas.",
        ),
        (
            "Materia seca registrada",
            "recorded_method_not_encoded",
            "dry_matter_recorded.csv",
            "El valor está registrado; el procedimiento exacto no está codificado.",
        ),
        (
            "Biomasa materializada",
            "calculated_materialization",
            "dry_matter_calculated.csv",
            "Se conserva para conciliación con la migración.",
        ),
        (
            "Biomasa usada",
            "analysis_derived",
            "Mediciones primitivas y geometría",
            "Se recalcula uniformemente para todas las filas.",
        ),
        (
            "N, FDA y FDN",
            "recorded / estimated",
            "quality_recorded.csv y missing_quality_estimate.csv",
            "La medición y la estimación DBCA permanecen separadas.",
        ),
        (
            "N acumulado e INN materializados",
            "calculated_materialization",
            "quality_calculated.csv",
            "Resultados verificables de formulas.json.",
        ),
        (
            "N acumulado e INN usados",
            "analysis_derived",
            "Biomasa recalculada, N primario y curva crítica",
            "La muestra estimada no entra al análisis primario.",
        ),
        (
            "Peso de mil semillas",
            "calculated_materialization / analysis_derived",
            "harvest_calculated.csv",
            "Promedio de tres réplicas por diez.",
        ),
        (
            "Rendimientos y componentes",
            "analysis_derived",
            "Mediciones de cosecha y geometría",
            "Transformaciones deterministas.",
        ),
        (
            "Semillas estimadas por panoja",
            "analysis_derived",
            "Peso limpio, PMS y panojas",
            "Reconstrucción, no conteo independiente.",
        ),
        (
            "EAN y productividad aparente del agua",
            "analysis_derived",
            "Rendimiento, M0 y aportes mensuales",
            "Indicadores descriptivos.",
        ),
    ]
    return pd.DataFrame(
        rows, columns=["variable", "status", "source", "interpretation"]
    )


def _apply_dry_matter_policy(frame: pd.DataFrame, policy: DryMatterPolicy) -> pd.Series:
    used = frame["dry_matter_pct"].copy()
    if policy == "ratio":
        used.loc[frame["dry_matter_issue"]] = frame.loc[
            frame["dry_matter_issue"], "dry_matter_pct_from_weights"
        ]
    elif policy == "exclude":
        used.loc[frame["dry_matter_issue"]] = np.nan
    return used


def _build_qa(
    *,
    spec: ExperimentSpec,
    longitudinal: pd.DataFrame,
    harvest: pd.DataFrame,
    sample_dates: tuple[pd.Timestamp, ...],
) -> pd.DataFrame:
    expected_plots = len(spec.treatments) * spec.repetitions * len(spec.sectors)
    expected_longitudinal = expected_plots * len(sample_dates)
    rows: list[dict[str, object]] = []

    def add(
        check: str,
        observed: object,
        expected: object,
        passed: bool,
        severity: str = "error",
    ) -> None:
        rows.append(
            {
                "check": check,
                "observed": observed,
                "expected": expected,
                "passes": bool(passed),
                "severity": severity,
            }
        )

    add(
        "treatments in schedule",
        len(spec.schedule),
        len(spec.treatments),
        len(spec.schedule) == len(spec.treatments),
    )
    add("harvest rows", len(harvest), expected_plots, len(harvest) == expected_plots)
    add(
        "longitudinal rows",
        len(longitudinal),
        expected_longitudinal,
        len(longitudinal) == expected_longitudinal,
    )
    add(
        "unique harvest plots",
        harvest["plot_id"].nunique(),
        expected_plots,
        harvest["plot_id"].nunique() == expected_plots,
    )
    add(
        "duplicate harvest plots",
        int(harvest["plot_id"].duplicated().sum()),
        0,
        not harvest["plot_id"].duplicated().any(),
    )
    add(
        "duplicate plot-date rows",
        int(longitudinal.duplicated(["plot_id", "date"]).sum()),
        0,
        not longitudinal.duplicated(["plot_id", "date"]).any(),
    )
    date_counts = longitudinal.groupby("plot_id", observed=True)["date"].nunique()
    add(
        "dates per plot (minimum)",
        int(date_counts.min()) if not date_counts.empty else 0,
        len(sample_dates),
        bool(not date_counts.empty and date_counts.min() == len(sample_dates)),
    )
    max_w1000_difference = float(
        (harvest["w1000_g"] - harvest["w1000_materialized_g"]).abs().max()
    )
    add(
        "max |PMS recomputed - materialized|",
        max_w1000_difference,
        "<= 1e-10 g",
        bool(max_w1000_difference <= 1e-10),
    )
    add(
        "missing measured N values",
        int(longitudinal["n_pct"].isna().sum()),
        "reported, not imputed in primary analysis",
        True,
        severity="info",
    )
    add(
        "dry-matter records flagged by dynamic rule",
        int(longitudinal["dm_issue"].sum()),
        "reported for verification",
        True,
        severity="info",
    )
    measured_q = longitudinal.loc[
        longitudinal["quality_status"].eq("measured"),
        "q_materialized_recompute_difference",
    ].dropna()
    add(
        "max |N accumulated recomputed - materialized| for measured rows",
        float(measured_q.abs().max()) if not measured_q.empty else np.nan,
        "reported as reconciliation diagnostic",
        True,
        severity="info",
    )
    measured_nni = longitudinal.loc[
        longitudinal["quality_status"].eq("measured"),
        "nni_sensitivity_materialized_difference",
    ].dropna()
    add(
        "max |sensitivity NNI recomputed - materialized| for measured rows",
        float(measured_nni.abs().max()) if not measured_nni.empty else np.nan,
        "reported as reconciliation diagnostic",
        True,
        severity="info",
    )
    return pd.DataFrame(rows)


def load_experiment_data(
    data_dir: Path | str | None = None,
    *,
    project_root: Path | None = None,
    dry_matter_policy: DryMatterPolicy = "recorded",
    include_estimated_quality: bool = False,
    nni_primary_coefficient: float = 3.93,
    nni_primary_exponent: float = -0.42,
    nni_sensitivity_coefficient: float = 4.8,
    nni_sensitivity_exponent: float = -0.32,
    dm_absolute_difference_threshold: float = 5.0,
    dm_relative_difference_threshold: float = 0.20,
) -> ExperimentData:
    """Load, validate, and reconstruct the experiment from canonical CSV data."""

    if dry_matter_policy not in {"recorded", "ratio", "exclude"}:
        raise ValueError("dry_matter_policy debe ser recorded, ratio o exclude")
    path = locate_data_dir(data_dir, project_root=project_root)
    frames = validate_data_bundle(path)
    metadata = _metadata_values(frames["experiment_metadata.csv"])
    design = frames["experimental_design.csv"]
    treatments = tuple(sorted(design["treatment"].astype(str).unique()))
    blocks = tuple(sorted(design["block"].astype(str).unique()))
    experiment_year = int(metadata["experiment_year"])
    schedule = _schedule_from_timeline(
        frames["field_timeline.csv"], treatments, experiment_year
    )

    dry = frames["dry_matter_recorded.csv"].merge(
        frames["dry_matter_calculated.csv"],
        on="observation_id",
        validate="one_to_one",
    )
    dry["dry_matter_issue"] = (
        dry["dry_matter_abs_difference_pp"].ge(dm_absolute_difference_threshold)
        & dry["dry_matter_relative_difference"].ge(dm_relative_difference_threshold)
    ).fillna(False)
    dry["dm_pct_used"] = _apply_dry_matter_policy(dry, dry_matter_policy)
    area = float(metadata["biomass_sample_area_m2"])
    dry["biomass_kg_ha"] = (
        dry["green_weight_1m_g"] * (dry["dm_pct_used"] / 100.0) * 10.0 / area
    )
    dry["biomass_recompute_difference"] = (
        dry["biomass_kg_ha"] - dry["biomass_reported_kg_ha"]
    )
    dry["biomass_calculation_status"] = "calculated_materialization"
    dry["dm_pct_status"] = "recorded_method_not_encoded"
    baseline = dry.loc[
        ~dry["treatment"].astype(str).str.fullmatch(r"M[0-5]", na=False)
    ].copy()
    experimental = dry.loc[
        dry["treatment"].astype(str).str.fullmatch(r"M[0-5]", na=False)
    ].copy()

    quality = frames["quality_recorded.csv"].merge(
        frames["quality_calculated.csv"], on="sample_id", validate="one_to_one"
    )
    quality["n_pct_recorded"] = quality["n_pct"]
    quality["n_pct_primary"] = quality["n_pct"]
    quality["adf_primary"] = quality["adf_pct"]
    quality["ndf_primary"] = quality["ndf_pct"]
    if include_estimated_quality:
        estimated = quality["measurement_status"].eq("estimated")
        quality.loc[estimated, "n_pct_primary"] = quality.loc[
            estimated, "estimated_n_pct"
        ]
        quality.loc[estimated, "adf_primary"] = quality.loc[
            estimated, "estimated_adf_pct"
        ]
        quality.loc[estimated, "ndf_primary"] = quality.loc[
            estimated, "estimated_ndf_pct"
        ]
    else:
        quality.loc[quality["measurement_status"].ne("measured"), "n_pct_primary"] = (
            np.nan
        )

    key = ["date", "sample_id", "sector", "treatment", "block"]
    longitudinal = experimental[
        key
        + [
            "dry_matter_pct",
            "dry_matter_pct_from_weights",
            "dry_matter_abs_difference_pp",
            "dry_matter_relative_difference",
            "dry_matter_issue",
            "dm_pct_used",
            "biomass_reported_kg_ha",
            "biomass_kg_ha",
            "biomass_recompute_difference",
            "biomass_calculation_status",
            "dm_pct_status",
        ]
    ].merge(
        quality[
            key
            + [
                "lab_registration",
                "n_pct_recorded",
                "n_pct_primary",
                "adf_primary",
                "ndf_primary",
                "n_accumulated_kg_ha",
                "nni",
                "data_origin",
                "measurement_status",
            ]
        ],
        on=key,
        how="left",
        validate="one_to_one",
    )
    longitudinal = longitudinal.rename(
        columns={
            "dry_matter_pct": "dm_pct_recorded",
            "dry_matter_pct_from_weights": "dm_ratio_pct",
            "dry_matter_abs_difference_pp": "dm_abs_difference_pp",
            "dry_matter_relative_difference": "dm_relative_difference",
            "dry_matter_issue": "dm_issue",
            "biomass_reported_kg_ha": "biomass_kg_ha_materialized",
            "biomass_calculation_status": "kgms_materialized_status",
            "lab_registration": "lab_id",
            "n_pct_primary": "n_pct",
            "adf_primary": "adf_pct",
            "ndf_primary": "ndf_pct",
            "n_accumulated_kg_ha": "q_kg_n_ha_materialized",
            "nni": "nni_materialized",
            "measurement_status": "quality_status",
        }
    )
    longitudinal["n_pct_cell_status"] = np.where(
        longitudinal["quality_status"].eq("estimated"), "estimated", "recorded"
    )
    longitudinal["adf_cell_status"] = longitudinal["n_pct_cell_status"]
    longitudinal["ndf_cell_status"] = longitudinal["n_pct_cell_status"]
    longitudinal["q_materialized_status"] = np.where(
        longitudinal["quality_status"].eq("estimated"),
        "estimated",
        "calculated_materialization",
    )
    longitudinal["nni_materialized_status"] = longitudinal["q_materialized_status"]
    longitudinal["q_kg_n_ha"] = (
        longitudinal["biomass_kg_ha"] * longitudinal["n_pct"] / 100.0
    )
    biomass_t_ha = longitudinal["biomass_kg_ha"] / 1000.0
    valid_biomass = biomass_t_ha.where(biomass_t_ha.gt(0.0))
    critical_primary = nni_primary_coefficient * valid_biomass.pow(nni_primary_exponent)
    critical_sensitivity = nni_sensitivity_coefficient * valid_biomass.pow(
        nni_sensitivity_exponent
    )
    longitudinal["nni_primary"] = longitudinal["n_pct"] / critical_primary
    longitudinal["nni_sensitivity"] = longitudinal["n_pct"] / critical_sensitivity
    longitudinal["q_materialized_recompute_difference"] = (
        longitudinal["q_kg_n_ha"] - longitudinal["q_kg_n_ha_materialized"]
    )
    longitudinal["nni_sensitivity_materialized_difference"] = (
        longitudinal["nni_sensitivity"] - longitudinal["nni_materialized"]
    )
    longitudinal["plot_id"] = (
        longitudinal["sector"].astype(str)
        + "_"
        + longitudinal["block"].astype(str)
        + "_"
        + longitudinal["treatment"].astype(str)
    )
    sample_dates = tuple(
        pd.Timestamp(value) for value in sorted(longitudinal["date"].dropna().unique())
    )
    if not sample_dates:
        raise ValueError(
            "No se encontraron fechas experimentales en los CSV canónicos."
        )
    date_labels = {
        value: pd.Timestamp(value).strftime("%d %b").lower() for value in sample_dates
    }
    longitudinal["date_label"] = longitudinal["date"].map(date_labels)

    harvest = (
        frames["harvest_recorded.csv"]
        .merge(
            frames["harvest_calculated.csv"], on="observation_id", validate="one_to_one"
        )
        .rename(
            columns={
                "dirty_seed_mass_g": "dirty_mass_g",
                "clean_seed_mass_g": "clean_mass_g",
                "w100_rep1_g": "w100_1_g",
                "w100_rep2_g": "w100_2_g",
                "w100_rep3_g": "w100_3_g",
                "w1000_g": "w1000_materialized_g",
                "panicle_count": "panicle_count",
            }
        )
    )
    harvest_area = float(metadata["harvest_sample_area_m2"])
    harvest["w1000_g"] = (
        harvest[["w100_1_g", "w100_2_g", "w100_3_g"]].mean(axis=1) * 10.0
    )
    harvest["panicle_density_m2"] = harvest["panicle_count"] / harvest_area
    harvest["dirty_yield_kg_ha"] = harvest["dirty_mass_g"] * 10.0 / harvest_area
    harvest["clean_yield_kg_ha"] = harvest["clean_mass_g"] * 10.0 / harvest_area
    harvest["clean_recovery"] = harvest["clean_mass_g"] / harvest["dirty_mass_g"]
    harvest["cleaning_loss_pct"] = 100.0 * (1.0 - harvest["clean_recovery"])
    harvest["estimated_seed_count"] = (
        1000.0 * harvest["clean_mass_g"] / harvest["w1000_g"]
    )
    harvest["estimated_seeds_per_panicle"] = (
        harvest["estimated_seed_count"] / harvest["panicle_count"]
    )
    harvest["w1000_materialized_status"] = "calculated_materialization"
    harvest["plot_id"] = (
        harvest["sector"].astype(str)
        + "_"
        + harvest["block"].astype(str)
        + "_"
        + harvest["treatment"].astype(str)
    )
    final_date = max(sample_dates)
    final_biomass = longitudinal.loc[
        longitudinal["date"].eq(final_date), ["plot_id", "biomass_kg_ha", "dm_issue"]
    ]
    harvest = harvest.drop(columns=["harvest_index_pct"]).merge(
        final_biomass, on="plot_id", how="left", validate="one_to_one"
    )
    harvest["harvest_index_pct"] = (
        100.0 * harvest["clean_yield_kg_ha"] / harvest["biomass_kg_ha"]
    )

    application_dates = [
        pd.Timestamp(value)
        for value in schedule[["first_application", "second_application"]]
        .stack()
        .dropna()
    ]
    study_start = min([*application_dates, *sample_dates])
    study_end = max(max(sample_dates), pd.Timestamp(harvest["date"].max()))
    management, water_monthly, water_period_totals = _management_and_water(
        frames, study_start=study_start, study_end=study_end
    )
    water_map = water_period_totals.set_index("sector")["gross_input_mm"]
    harvest["gross_water_input_mm"] = harvest["sector"].map(water_map)
    harvest["apparent_water_productivity"] = (
        harvest["clean_yield_kg_ha"] / harvest["gross_water_input_mm"]
    )
    m0_reference = harvest.loc[
        harvest["treatment"].eq("M0"), ["sector", "block", "clean_yield_kg_ha"]
    ].rename(columns={"clean_yield_kg_ha": "m0_yield_same_block"})
    harvest = harvest.merge(
        m0_reference, on=["sector", "block"], how="left", validate="many_to_one"
    )
    experimental_n_total = float(metadata["experimental_n_total_kg_ha"])
    harvest["agronomic_efficiency"] = np.where(
        harvest["treatment"].eq("M0"),
        np.nan,
        (harvest["clean_yield_kg_ha"] - harvest["m0_yield_same_block"])
        / experimental_n_total,
    )

    sectors = tuple(
        sorted(
            longitudinal["sector"].dropna().astype(str).unique(),
            key=lambda value: (value != "Secano", value),
        )
    )
    audit = _source_audit(
        schedule=schedule,
        sample_dates=sample_dates,
        management=management,
        quality=quality,
        dry_matter=dry,
    )
    spec = ExperimentSpec(
        data_dir=path,
        source_sha256=sha256_data_bundle(path),
        experiment_year=experiment_year,
        treatments=treatments,
        sectors=sectors,
        blocks=blocks,
        repetitions=int(metadata["repetitions"]),
        plot_area_m2=float(metadata["plot_area_m2"]),
        row_spacing_m=float(metadata["row_spacing_cm"]) / 100.0,
        biomass_sample_area_m2=area,
        harvest_sample_area_m2=harvest_area,
        experimental_n_total_kg_ha=experimental_n_total,
        applications_per_treatment=int(metadata["applications_per_treatment"]),
        dose_per_application_kg_ha=float(metadata["dose_per_application_kg_ha"]),
        schedule=schedule.reset_index(drop=True),
        management=management.reset_index(drop=True),
        water_monthly=water_monthly.reset_index(drop=True),
        water_period_totals=water_period_totals.reset_index(drop=True),
        source_audit=audit.reset_index(drop=True),
    )
    for frame in (longitudinal, harvest):
        frame["sector"] = pd.Categorical(
            frame["sector"], categories=list(sectors), ordered=True
        )
        frame["block"] = pd.Categorical(
            frame["block"], categories=list(blocks), ordered=True
        )
        frame["treatment"] = pd.Categorical(
            frame["treatment"], categories=list(treatments), ordered=True
        )
    longitudinal["date"] = pd.Categorical(
        longitudinal["date"], categories=list(sample_dates), ordered=True
    )

    seed_weight_long = harvest.melt(
        id_vars=["plot_id", "sector", "block", "treatment", "sample_id"],
        value_vars=["w100_1_g", "w100_2_g", "w100_3_g"],
        var_name="technical_replicate",
        value_name="w100_g",
    )
    baseline_biomass = baseline.loc[
        baseline["biomass_recorded_dm_kg_ha"].notna(),
        ["date", "sample_id", "sector", "block", "biomass_recorded_dm_kg_ha"],
    ].rename(columns={"biomass_recorded_dm_kg_ha": "biomass_kg_ha"})
    baseline_tillers = baseline.loc[
        baseline["tiller_density_m2"].notna(),
        ["date", "sample_id", "sector", "block", "tiller_density_m2"],
    ].rename(columns={"block": "replicate_label", "tiller_density_m2": "tillers_m2"})
    longitudinal = longitudinal.sort_values(
        ["sector", "block", "treatment", "date"]
    ).reset_index(drop=True)
    harvest = harvest.sort_values(["sector", "block", "treatment"]).reset_index(
        drop=True
    )
    qa = _build_qa(
        spec=spec, longitudinal=longitudinal, harvest=harvest, sample_dates=sample_dates
    )
    failed = qa.loc[qa["severity"].eq("error") & ~qa["passes"]]
    if not failed.empty:
        raise AssertionError(failed.to_string(index=False))
    return ExperimentData(
        spec=spec,
        longitudinal=longitudinal,
        harvest=harvest,
        seed_weight_long=seed_weight_long.reset_index(drop=True),
        baseline_biomass=baseline_biomass.reset_index(drop=True),
        baseline_tillers=baseline_tillers.reset_index(drop=True),
        variable_lineage=_variable_lineage(),
        qa=qa,
    )


def source_provenance_table(data: ExperimentData) -> pd.DataFrame:
    """Compact canonical-bundle provenance for notebook display."""

    spec = data.spec
    csv_count = len(list(spec.data_dir.glob("*.csv")))
    return pd.DataFrame(
        [
            {
                "source_kind": "canonical_csv_bundle",
                "source_path": str(spec.data_dir),
                "sha256": spec.source_sha256,
                "csv_files": csv_count,
                "experiment_year": spec.experiment_year,
                "dry_matter_rows": len(data.longitudinal),
                "harvest_rows": len(data.harvest),
            }
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the canonical Festuca CSV bundle."
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    arguments = parser.parse_args()
    frames = validate_data_bundle(cast(Path, arguments.data_dir))
    print(
        f"Validated {len(frames)} canonical datasets in "
        f"{cast(Path, arguments.data_dir).resolve()}"
    )


if __name__ == "__main__":
    main()
