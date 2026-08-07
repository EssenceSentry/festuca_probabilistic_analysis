from __future__ import annotations

# Pyright's strict mode remains active. These diagnostics are disabled because the
# scientific stack used here exposes partially typed NumPy-shaped APIs.
# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import arviz as az
import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.figure import Figure
from scipy.linalg import helmert
from scipy.stats import f as f_dist
from scipy.stats import geninvgauss

RANDOM_SEED = 20260807
TREATMENTS = [f"M{i}" for i in range(6)]
FERTILIZED = TREATMENTS[1:]
SECTORS = ["Secano", "Riego"]
DATES = ["Sep", "Oct", "Nov"]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = PROJECT_ROOT / "sources" / "Datos_Ema_Serrana_INN.xlsx"
RUN_DIR = PROJECT_ROOT / "festuca_probabilistic_outputs"
OUT = PROJECT_ROOT / "results"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
POSTERIORS = OUT / "posteriors"
for path in (TABLES, FIGURES, POSTERIORS):
    path.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------


def load_yield_data() -> pd.DataFrame:
    data = pd.read_excel(WORKBOOK, sheet_name="Datos_Rto", header=4)
    data = data.rename(
        columns={
            "Condición": "sector",
            "Tratamiento": "treatment",
            "Repetición": "block",
            "Peso limpio": "clean_seed_g",
        }
    )
    data = data.loc[data["treatment"].isin(TREATMENTS)].copy()
    for column in ["sector", "treatment", "block"]:
        data[column] = data[column].astype("string").str.strip()
    data["clean_yield_kg_ha"] = data["clean_seed_g"].astype(float) * 10.0 / 0.76
    data["sector"] = pd.Categorical(data["sector"], SECTORS, ordered=True)
    data["treatment"] = pd.Categorical(data["treatment"], TREATMENTS, ordered=True)
    block_levels = sorted(data["block"].dropna().unique().tolist())
    data["block"] = pd.Categorical(data["block"], block_levels, ordered=True)
    return data[["sector", "block", "treatment", "clean_yield_kg_ha"]].reset_index(
        drop=True
    )


YIELD_DATA = load_yield_data()


# -----------------------------------------------------------------------------
# Corrected Model A: robust raw-scale yield model
# -----------------------------------------------------------------------------


@dataclass
class Design:
    X: np.ndarray
    X_group: np.ndarray
    y_z: np.ndarray
    center: float
    scale: float
    frame: pd.DataFrame
    timing_slice: slice
    block_slice: slice


def make_design(frame: pd.DataFrame) -> Design:
    frame = frame.reset_index(drop=True).copy()
    y = frame["clean_yield_kg_ha"].to_numpy(float)
    center = float(y.mean())
    scale = float(y.std(ddof=1))
    y_z = (y - center) / scale

    treatment_idx = pd.Categorical(
        frame["treatment"].astype(str), categories=TREATMENTS, ordered=True
    ).codes
    present_blocks = sorted(frame["block"].astype(str).unique().tolist())
    block_idx = pd.Categorical(
        frame["block"].astype(str), categories=present_blocks, ordered=True
    ).codes

    timing_basis = helmert(5, full=False).T  # 5 x 4, orthonormal and sum-to-zero
    block_basis = (
        helmert(len(present_blocks), full=False).T
        if len(present_blocks) > 1
        else np.zeros((1, 0))
    )

    extra_n = (treatment_idx > 0).astype(float)
    timing = np.zeros((len(frame), 4))
    fertilized_mask = treatment_idx > 0
    timing[fertilized_mask] = timing_basis[treatment_idx[fertilized_mask] - 1]
    block = block_basis[block_idx]

    X = np.column_stack([np.ones(len(frame)), extra_n, timing, block])
    timing_slice = slice(2, 6)
    block_slice = slice(6, X.shape[1])

    # Expected response by treatment at the average block effect.
    X_group = np.zeros((6, X.shape[1]))
    X_group[:, 0] = 1.0
    X_group[1:, 1] = 1.0
    X_group[1:, timing_slice] = timing_basis

    return Design(
        X=X,
        X_group=X_group,
        y_z=y_z,
        center=center,
        scale=scale,
        frame=frame,
        timing_slice=timing_slice,
        block_slice=block_slice,
    )


def logp_log_tau(log_tau: float, coefficients: np.ndarray, prior_scale: float) -> float:
    """Conditional log-density of log(tau) under Normal coefficients + HalfNormal tau."""
    tau = np.exp(log_tau)
    q = len(coefficients)
    sum_squares = float(coefficients @ coefficients)
    return (
        -(q - 1) * log_tau
        - sum_squares / (2.0 * tau**2)
        - tau**2 / (2.0 * prior_scale**2)
    )


def sample_hierarchical_yield(
    frame: pd.DataFrame,
    timing_prior_scale: float,
    *,
    chains: int = 4,
    iterations: int = 14000,
    burn: int = 3000,
    thin: int = 3,
    seed: int = RANDOM_SEED,
) -> tuple[Design, dict[str, np.ndarray], dict[str, float]]:
    """Gibbs sampler for a robust Student-t RCBD yield model.

    The response is standardized internally. Student-t(df=5) is represented as a
    Normal-Gamma scale mixture. The timing variance has a HalfNormal prior and its
    squared scale is sampled exactly from a generalized inverse-Gaussian full
    conditional. Because df > 1, the Student-t location is an arithmetic mean.
    """
    design = make_design(frame)
    n, p = design.X.shape
    X_t = design.X.T
    n_keep = len(range(burn, iterations, thin))

    beta_draws = np.empty((chains, n_keep, p))
    sigma_draws = np.empty((chains, n_keep))
    tau_draws = np.empty((chains, n_keep))

    nu = 5.0
    a0 = 1.0
    b0 = 0.1
    fixed_precision = np.zeros(p)
    fixed_precision[0] = 1.0 / 10.0**2
    fixed_precision[1] = 1.0 / 5.0**2
    if design.block_slice.stop > design.block_slice.start:
        fixed_precision[design.block_slice] = 1.0 / 1.0**2

    q_timing = design.timing_slice.stop - design.timing_slice.start
    gig_p = (1.0 - q_timing) / 2.0
    gig_a = 1.0 / timing_prior_scale**2

    for chain in range(chains):
        rng = np.random.default_rng(seed + 1000 * chain)
        beta = np.linalg.lstsq(design.X, design.y_z, rcond=None)[0]
        sigma2 = max(float(np.var(design.y_z - design.X @ beta)), 0.05)
        local_precision = np.ones(n)
        tau = 0.15
        stored = 0

        for iteration in range(iterations):
            prior_precision = fixed_precision.copy()
            prior_precision[design.timing_slice] = 1.0 / tau**2

            precision = (X_t * local_precision) @ design.X / sigma2 + np.diag(
                prior_precision
            )
            chol = np.linalg.cholesky(precision)
            rhs = (X_t * local_precision) @ design.y_z / sigma2
            posterior_mean = np.linalg.solve(chol.T, np.linalg.solve(chol, rhs))
            beta = posterior_mean + np.linalg.solve(chol.T, rng.standard_normal(p))

            # Exact update for tau^2 under Normal coefficients and HalfNormal(tau).
            sum_squares = max(
                float(beta[design.timing_slice] @ beta[design.timing_slice]), 1e-12
            )
            gig_b = sum_squares
            symmetric_parameter = np.sqrt(gig_a * gig_b)
            scale_factor = np.sqrt(gig_b / gig_a)
            tau2 = scale_factor * geninvgauss.rvs(
                gig_p,
                symmetric_parameter,
                random_state=rng,
            )
            tau = np.sqrt(max(float(tau2), 1e-12))

            residual = design.y_z - design.X @ beta
            rate = (nu + residual**2 / sigma2) / 2.0
            local_precision = rng.gamma((nu + 1.0) / 2.0, 1.0 / rate)
            posterior_shape = a0 + n / 2.0
            posterior_scale = b0 + 0.5 * np.sum(local_precision * residual**2)
            sigma2 = 1.0 / rng.gamma(posterior_shape, 1.0 / posterior_scale)

            if iteration >= burn and (iteration - burn) % thin == 0:
                beta_draws[chain, stored] = beta
                sigma_draws[chain, stored] = np.sqrt(sigma2)
                tau_draws[chain, stored] = tau
                stored += 1

    group_z = np.einsum("gp,cdp->cdg", design.X_group, beta_draws)
    mean_yield = design.center + design.scale * group_z
    mu_obs = design.center + design.scale * np.einsum(
        "np,cdp->cdn", design.X, beta_draws
    )
    sigma_yield = design.scale * sigma_draws

    samples = {
        "beta": beta_draws,
        "sigma_z": sigma_draws,
        "tau_timing": tau_draws,
        "mean_yield": mean_yield,
        "mu_obs": mu_obs,
        "sigma_yield": sigma_yield,
    }
    metadata = {"center": design.center, "scale": design.scale}
    return design, samples, metadata


def sample_fixed_yield(
    frame: pd.DataFrame,
    timing_sd: float = 3.0,
    *,
    chains: int = 4,
    iterations: int = 20000,
    burn: int = 4000,
    thin: int = 4,
    seed: int = RANDOM_SEED,
) -> tuple[Design, dict[str, np.ndarray], dict[str, float]]:
    """Nearly unpooled sensitivity model with a fixed, very wide timing prior."""
    design = make_design(frame)
    n, p = design.X.shape
    X_t = design.X.T
    n_keep = len(range(burn, iterations, thin))

    beta_draws = np.empty((chains, n_keep, p))
    sigma_draws = np.empty((chains, n_keep))

    prior_sd = np.full(p, 1.0)
    prior_sd[0] = 10.0
    prior_sd[1] = 5.0
    prior_sd[design.timing_slice] = timing_sd
    prior_precision = np.diag(1.0 / prior_sd**2)

    nu = 5.0
    a0 = 1.0
    b0 = 0.1

    for chain in range(chains):
        rng = np.random.default_rng(seed + 1000 * chain)
        beta = np.linalg.lstsq(design.X, design.y_z, rcond=None)[0]
        sigma2 = max(float(np.var(design.y_z - design.X @ beta)), 0.05)
        local_precision = np.ones(n)
        stored = 0

        for iteration in range(iterations):
            precision = (X_t * local_precision) @ design.X / sigma2 + prior_precision
            chol = np.linalg.cholesky(precision)
            rhs = (X_t * local_precision) @ design.y_z / sigma2
            posterior_mean = np.linalg.solve(chol.T, np.linalg.solve(chol, rhs))
            beta = posterior_mean + np.linalg.solve(chol.T, rng.standard_normal(p))

            residual = design.y_z - design.X @ beta
            rate = (nu + residual**2 / sigma2) / 2.0
            local_precision = rng.gamma((nu + 1.0) / 2.0, 1.0 / rate)
            posterior_shape = a0 + n / 2.0
            posterior_scale = b0 + 0.5 * np.sum(local_precision * residual**2)
            sigma2 = 1.0 / rng.gamma(posterior_shape, 1.0 / posterior_scale)

            if iteration >= burn and (iteration - burn) % thin == 0:
                beta_draws[chain, stored] = beta
                sigma_draws[chain, stored] = np.sqrt(sigma2)
                stored += 1

    group_z = np.einsum("gp,cdp->cdg", design.X_group, beta_draws)
    mean_yield = design.center + design.scale * group_z
    mu_obs = design.center + design.scale * np.einsum(
        "np,cdp->cdn", design.X, beta_draws
    )
    sigma_yield = design.scale * sigma_draws
    samples = {
        "beta": beta_draws,
        "sigma_z": sigma_draws,
        "mean_yield": mean_yield,
        "mu_obs": mu_obs,
        "sigma_yield": sigma_yield,
    }
    return design, samples, {"center": design.center, "scale": design.scale}


def convergence_diagnostics(samples: dict[str, np.ndarray]) -> dict[str, float]:
    selected = {
        key: value
        for key, value in samples.items()
        if key in {"beta", "sigma_z", "tau_timing", "mean_yield"}
    }
    data_vars: dict[str, Any] = {}
    for key, value in selected.items():
        dimensions = ["chain", "draw"] + [
            f"{key}_dim_{index}" for index in range(value.ndim - 2)
        ]
        data_vars[key] = (dimensions, value)
    dataset = xr.Dataset(data_vars)
    rhat = cast(Any, az.rhat(dataset))
    ess = cast(Any, az.ess(dataset))
    return {
        "max_rhat": max(
            float(np.nanmax(variable.values)) for variable in rhat.data_vars.values()
        ),
        "min_ess_bulk": min(
            float(np.nanmin(variable.values)) for variable in ess.data_vars.values()
        ),
    }


def flatten(samples: dict[str, np.ndarray], variable: str) -> np.ndarray:
    value = samples[variable]
    return value.reshape((-1,) + value.shape[2:])


def summarize_yield_draws(
    sector: str,
    specification: str,
    samples: dict[str, np.ndarray],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    means = flatten(samples, "mean_yield")
    fertilized = means[:, 1:]
    spread = np.ptp(fertilized, axis=1)
    early_late = fertilized[:, :2].mean(axis=1) - fertilized[:, 3:5].mean(axis=1)
    m5_vs_others = fertilized[:, 4] - fertilized[:, :4].mean(axis=1)
    extra_n = fertilized.mean(axis=1) - means[:, 0]
    best = np.argmax(fertilized, axis=1)
    worst = np.argmin(fertilized, axis=1)

    treatment_rows = []
    for index, treatment in enumerate(TREATMENTS):
        values = means[:, index]
        treatment_rows.append(
            {
                "sector": sector,
                "specification": specification,
                "treatment": treatment,
                "posterior_mean": float(values.mean()),
                "median": float(np.median(values)),
                "lower_95": float(np.quantile(values, 0.025)),
                "upper_95": float(np.quantile(values, 0.975)),
            }
        )

    estimand_rows = []
    estimands = {
        "Promedio M1–M5 menos M0": extra_n,
        "M1–M2 menos M4–M5": early_late,
        "M5 menos promedio M1–M4": m5_vs_others,
        "Rango máximo M1–M5": spread,
    }
    for name, values in estimands.items():
        estimand_rows.append(
            {
                "sector": sector,
                "specification": specification,
                "estimand": name,
                "posterior_mean": float(values.mean()),
                "median": float(np.median(values)),
                "lower_95": float(np.quantile(values, 0.025)),
                "upper_95": float(np.quantile(values, 0.975)),
                "p_gt_0": float(np.mean(values > 0.0)),
                "p_abs_gt_100": float(np.mean(np.abs(values) > 100.0)),
            }
        )

    rank_rows = []
    for index, treatment in enumerate(FERTILIZED):
        rank_rows.append(
            {
                "sector": sector,
                "specification": specification,
                "treatment": treatment,
                "p_best": float(np.mean(best == index)),
                "p_worst": float(np.mean(worst == index)),
                "p_within_50_best": float(
                    np.mean(fertilized[:, index] >= fertilized.max(axis=1) - 50.0)
                ),
                "p_within_100_best": float(
                    np.mean(fertilized[:, index] >= fertilized.max(axis=1) - 100.0)
                ),
                "p_within_150_best": float(
                    np.mean(fertilized[:, index] >= fertilized.max(axis=1) - 150.0)
                ),
            }
        )

    margin_rows = []
    for margin in np.arange(0.0, 301.0, 5.0):
        margin_rows.append(
            {
                "sector": sector,
                "specification": specification,
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


def rcbd_anova_p_values(
    y_rep: np.ndarray, treatment: np.ndarray, block: np.ndarray
) -> np.ndarray:
    """Vectorized treatment F-test for M1-M5 RCBD replicated datasets."""
    mask = np.isin(treatment, FERTILIZED)
    treatment_sub = treatment[mask]
    block_sub = block[mask]
    y_sub = y_rep[:, mask]

    treatment_levels = FERTILIZED
    block_levels = sorted(np.unique(block_sub).tolist())
    treatment_dummy = np.column_stack(
        [(treatment_sub == level).astype(float) for level in treatment_levels[1:]]
    )
    block_dummy = np.column_stack(
        [(block_sub == level).astype(float) for level in block_levels[1:]]
    )
    intercept = np.ones((len(treatment_sub), 1))
    x_full = np.column_stack([intercept, treatment_dummy, block_dummy])
    x_reduced = np.column_stack([intercept, block_dummy])

    h_full = x_full @ np.linalg.pinv(x_full)
    h_reduced = x_reduced @ np.linalg.pinv(x_reduced)
    residual_full = y_sub @ (np.eye(len(treatment_sub)) - h_full)
    residual_reduced = y_sub @ (np.eye(len(treatment_sub)) - h_reduced)
    sse_full = np.sum(residual_full**2, axis=1)
    sse_reduced = np.sum(residual_reduced**2, axis=1)

    df_num = x_full.shape[1] - x_reduced.shape[1]
    df_den = len(treatment_sub) - x_full.shape[1]
    f_values = ((sse_reduced - sse_full) / df_num) / (sse_full / df_den)
    f_values = np.maximum(f_values, 0.0)
    return f_dist.sf(f_values, df_num, df_den)


def posterior_predictive_summary(
    sector: str,
    design: Design,
    samples: dict[str, np.ndarray],
    observed_p: float,
    n_replications: int = 5000,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(RANDOM_SEED + (0 if sector == "Secano" else 1000))
    means = flatten(samples, "mean_yield")
    mu_obs = flatten(samples, "mu_obs")
    sigma = flatten(samples, "sigma_yield")
    n_posterior = len(means)
    selected = rng.choice(
        n_posterior, size=min(n_replications, n_posterior), replace=False
    )
    residuals = rng.standard_t(df=5, size=(len(selected), len(design.frame)))
    y_rep = mu_obs[selected] + sigma[selected, None] * residuals

    p_values = rcbd_anova_p_values(
        y_rep,
        design.frame["treatment"].astype(str).to_numpy(),
        design.frame["block"].astype(str).to_numpy(),
    )
    latent_spread = np.ptp(means[selected, 1:], axis=1)
    treatment_idx = pd.Categorical(
        design.frame["treatment"].astype(str), TREATMENTS, ordered=True
    ).codes
    replicated_means = np.column_stack(
        [y_rep[:, treatment_idx == index].mean(axis=1) for index in range(6)]
    )

    summary = pd.DataFrame(
        [
            {
                "sector": sector,
                "observed_p_m1_m5": observed_p,
                "p_rep_anova_non_significant": float(np.mean(p_values > 0.05)),
                "p_rep_anova_p_le_observed": float(np.mean(p_values <= observed_p)),
                "p_latent_range_gt_100": float(np.mean(latent_spread > 100.0)),
                "p_non_significant_given_range_gt_100": float(
                    np.mean(p_values[latent_spread > 100.0] > 0.05)
                    if np.any(latent_spread > 100.0)
                    else np.nan
                ),
                "p_m5_last_in_replication": float(
                    np.mean(np.argmin(replicated_means[:, 1:], axis=1) == 4)
                ),
                "n_replications": len(selected),
            }
        ]
    )
    draws = pd.DataFrame(
        {
            "sector": sector,
            "p_value_m1_m5": p_values,
            "latent_range_m1_m5": latent_spread,
        }
    )
    return summary, draws


# -----------------------------------------------------------------------------
# Original Model A longitudinal posterior extraction
# -----------------------------------------------------------------------------


def load_netcdf_array(path: Path, dataset: str) -> np.ndarray:
    with h5py.File(path, "r") as file:
        return np.asarray(file[dataset])


def posterior_interval(values: np.ndarray) -> dict[str, float]:
    return {
        "median": float(np.median(values)),
        "lower_95": float(np.quantile(values, 0.025)),
        "upper_95": float(np.quantile(values, 0.975)),
    }


def longitudinal_trajectory_rows(
    draws: np.ndarray,
    *,
    sector: str,
    variable_label: str,
    units: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for treatment_index, treatment in enumerate(TREATMENTS):
        for date_index, date in enumerate(DATES):
            rows.append(
                {
                    "sector": sector,
                    "variable": variable_label,
                    "units": units,
                    "treatment": treatment,
                    "date": date,
                    **posterior_interval(draws[:, treatment_index, date_index]),
                }
            )
    return rows


def longitudinal_contrast_row(
    values: np.ndarray,
    *,
    sector: str,
    variable_label: str,
    date: str,
    contrast: str,
    direction: str,
) -> dict[str, Any]:
    return {
        "sector": sector,
        "variable": variable_label,
        "date": date,
        "contrast": contrast,
        "direction": direction,
        **posterior_interval(values),
        "probability_direction": float(np.mean(values > 0.0)),
    }


def longitudinal_contrast_rows(
    draws: np.ndarray,
    *,
    sector: str,
    variable_key: str,
    variable_label: str,
) -> list[dict[str, Any]]:
    if variable_key != "biomass":
        return [
            longitudinal_contrast_row(
                draws[:, 4:6, date_index].mean(axis=1)
                - draws[:, 1:3, date_index].mean(axis=1),
                sector=sector,
                variable_label=variable_label,
                date=date,
                contrast="Tardíos M4–M5 menos tempranos M1–M2",
                direction="Mayor en tardíos",
            )
            for date_index, date in enumerate(DATES)
        ]

    clean_september = draws[:, 1:3, 0].mean(axis=1) - draws[:, 3:5, 0].mean(axis=1)
    rows = [
        longitudinal_contrast_row(
            clean_september,
            sector=sector,
            variable_label=variable_label,
            date="Sep",
            contrast="Tempranos M1–M2 menos intermedios M3–M4",
            direction="Mayor en tempranos",
        )
    ]
    for date_index, date in enumerate(DATES[1:], start=1):
        early_late = draws[:, 1:3, date_index].mean(axis=1) - draws[
            :, 4:6, date_index
        ].mean(axis=1)
        rows.append(
            longitudinal_contrast_row(
                early_late,
                sector=sector,
                variable_label=variable_label,
                date=date,
                contrast="Tempranos M1–M2 menos tardíos M4–M5",
                direction="Mayor en tempranos",
            )
        )
    return rows


def summarize_longitudinal_model_a() -> tuple[pd.DataFrame, pd.DataFrame]:
    trajectory_rows: list[dict[str, Any]] = []
    contrast_rows: list[dict[str, Any]] = []

    for sector_key, sector in [("secano", "Secano"), ("riego", "Riego")]:
        for variable_key, variable_label, units in [
            ("biomass", "Biomasa aérea", "kg MS/ha"),
            ("n", "Concentración de N", "% N"),
        ]:
            path = RUN_DIR / "posteriors" / f"model_a_{sector_key}_{variable_key}.nc"
            draws = load_netcdf_array(path, "posterior/median_outcome")
            draws = draws.reshape((-1, 6, 3))
            trajectory_rows.extend(
                longitudinal_trajectory_rows(
                    draws,
                    sector=sector,
                    variable_label=variable_label,
                    units=units,
                )
            )
            contrast_rows.extend(
                longitudinal_contrast_rows(
                    draws,
                    sector=sector,
                    variable_key=variable_key,
                    variable_label=variable_label,
                )
            )

    return pd.DataFrame(trajectory_rows), pd.DataFrame(contrast_rows)


# -----------------------------------------------------------------------------
# Execution
# -----------------------------------------------------------------------------


def run_all() -> None:
    specifications = {
        "Regularización fuerte": ("hierarchical", 0.25),
        "Principal": ("hierarchical", 0.50),
        "Regularización débil": ("hierarchical", 1.00),
        "Casi no agrupado": ("fixed", 3.00),
    }

    treatment_tables = []
    estimand_tables = []
    rank_tables = []
    margin_tables = []
    diagnostic_rows = []
    primary: dict[str, tuple[Design, dict[str, np.ndarray]]] = {}

    for sector_index, sector in enumerate(SECTORS):
        sector_frame = YIELD_DATA.loc[
            YIELD_DATA["sector"].astype(str).eq(sector)
        ].copy()
        for specification_index, (specification, (kind, scale)) in enumerate(
            specifications.items()
        ):
            seed = RANDOM_SEED + sector_index * 10000 + specification_index * 100
            if kind == "hierarchical":
                design, samples, metadata = sample_hierarchical_yield(
                    sector_frame,
                    timing_prior_scale=scale,
                    seed=seed,
                )
            else:
                design, samples, metadata = sample_fixed_yield(
                    sector_frame,
                    timing_sd=scale,
                    seed=seed,
                )
            diagnostics: dict[str, object] = {**convergence_diagnostics(samples)}
            diagnostics.update(
                {
                    "sector": sector,
                    "specification": specification,
                    "kind": kind,
                    "timing_prior_scale": scale,
                    **metadata,
                }
            )
            diagnostic_rows.append(diagnostics)
            treatment, estimand, rank, margin = summarize_yield_draws(
                sector, specification, samples
            )
            treatment_tables.append(treatment)
            estimand_tables.append(estimand)
            rank_tables.append(rank)
            margin_tables.append(margin)
            if specification == "Principal":
                primary[sector] = (design, samples)
                np.savez_compressed(
                    POSTERIORS / f"model_a_corrected_{sector.lower()}.npz",
                    mean_yield=samples["mean_yield"],
                    mu_obs=samples["mu_obs"],
                    sigma_yield=samples["sigma_yield"],
                    beta=samples["beta"],
                    tau_timing=samples.get("tau_timing", np.array([])),
                )

    treatment_means = pd.concat(treatment_tables, ignore_index=True)
    estimands = pd.concat(estimand_tables, ignore_index=True)
    ranks = pd.concat(rank_tables, ignore_index=True)
    margins = pd.concat(margin_tables, ignore_index=True)
    diagnostics = pd.DataFrame(diagnostic_rows)

    # Cross-sector comparisons under the primary prior.
    secano_means = flatten(primary["Secano"][1], "mean_yield")
    riego_means = flatten(primary["Riego"][1], "mean_yield")
    n_pair = min(len(secano_means), len(riego_means))
    secano_means = secano_means[:n_pair]
    riego_means = riego_means[:n_pair]
    secano_early_late = secano_means[:, 1:3].mean(axis=1) - secano_means[:, 4:6].mean(
        axis=1
    )
    riego_early_late = riego_means[:, 1:3].mean(axis=1) - riego_means[:, 4:6].mean(
        axis=1
    )
    sector_difference = riego_early_late - secano_early_late
    centered_secano = secano_means[:, 1:] - secano_means[:, 1:].mean(
        axis=1, keepdims=True
    )
    centered_riego = riego_means[:, 1:] - riego_means[:, 1:].mean(axis=1, keepdims=True)
    pattern_difference = centered_riego - centered_secano
    max_abs_pattern_difference = np.max(np.abs(pattern_difference), axis=1)
    rms_pattern_difference = np.sqrt(np.mean(pattern_difference**2, axis=1))

    sector_rows = []
    for name, values in {
        "Diferencia sectorial del contraste temprano–tardío": sector_difference,
        "Máxima diferencia absoluta del patrón relativo M1–M5": max_abs_pattern_difference,
        "Diferencia RMS del patrón relativo M1–M5": rms_pattern_difference,
    }.items():
        sector_rows.append(
            {
                "estimand": name,
                "median": float(np.median(values)),
                "lower_95": float(np.quantile(values, 0.025)),
                "upper_95": float(np.quantile(values, 0.975)),
                "p_abs_gt_50": float(np.mean(np.abs(values) > 50.0)),
                "p_abs_gt_100": float(np.mean(np.abs(values) > 100.0)),
                "p_gt_0": float(np.mean(values > 0.0)),
            }
        )
    sector_comparison = pd.DataFrame(sector_rows)

    # Leave-one-block-out sensitivity for primary prior.
    loo_rows = []
    for sector_index, sector in enumerate(SECTORS):
        sector_frame = YIELD_DATA.loc[
            YIELD_DATA["sector"].astype(str).eq(sector)
        ].copy()
        present_blocks = sorted(sector_frame["block"].astype(str).unique().tolist())
        for block_index, omitted in enumerate(present_blocks):
            subset = sector_frame.loc[
                sector_frame["block"].astype(str).ne(omitted)
            ].copy()
            _, samples, _ = sample_hierarchical_yield(
                subset,
                timing_prior_scale=0.50,
                iterations=10000,
                burn=2000,
                thin=4,
                seed=RANDOM_SEED + 20000 + sector_index * 1000 + block_index * 50,
            )
            means = flatten(samples, "mean_yield")
            fertilized = means[:, 1:]
            spread = np.ptp(fertilized, axis=1)
            early_late = fertilized[:, :2].mean(axis=1) - fertilized[:, 3:5].mean(
                axis=1
            )
            extra_n = fertilized.mean(axis=1) - means[:, 0]
            diagnostics_loo = convergence_diagnostics(samples)
            loo_rows.append(
                {
                    "sector": sector,
                    "omitted_block": omitted,
                    "median_range": float(np.median(spread)),
                    "p_range_gt_100": float(np.mean(spread > 100.0)),
                    "median_early_late": float(np.median(early_late)),
                    "p_early_gt_late": float(np.mean(early_late > 0.0)),
                    "median_extra_n": float(np.median(extra_n)),
                    **diagnostics_loo,
                }
            )
    leave_one_out = pd.DataFrame(loo_rows)

    # Posterior predictive replication of the thesis ANOVA.
    ppc_summaries = []
    ppc_draws = []
    observed_p = {"Secano": 0.428718, "Riego": 0.175851}
    for sector in SECTORS:
        summary, draws = posterior_predictive_summary(
            sector,
            primary[sector][0],
            primary[sector][1],
            observed_p[sector],
        )
        ppc_summaries.append(summary)
        ppc_draws.append(draws)
    ppc_summary = pd.concat(ppc_summaries, ignore_index=True)
    ppc_draws_table = pd.concat(ppc_draws, ignore_index=True)

    # Longitudinal Model A, Model B, and reconstruction-null summaries from supplied run.
    trajectories, longitudinal_contrasts = summarize_longitudinal_model_a()
    model_b_states = pd.read_csv(RUN_DIR / "tables" / "model_b_state_trajectories.csv")
    model_b_nni = pd.read_csv(
        RUN_DIR / "tables" / "model_b_final_nni_probabilities.csv"
    )
    reconstruction_null = pd.read_csv(
        RUN_DIR / "tables" / "reconstruction_null_percentiles.csv"
    )
    original_diagnostics = pd.read_csv(RUN_DIR / "tables" / "diagnostics_overview.csv")

    # Save all tables.
    YIELD_DATA.to_csv(TABLES / "yield_data.csv", index=False)
    treatment_means.to_csv(
        TABLES / "model_a_corrected_treatment_means.csv", index=False
    )
    estimands.to_csv(TABLES / "model_a_corrected_estimands.csv", index=False)
    ranks.to_csv(TABLES / "model_a_corrected_rank_probabilities.csv", index=False)
    margins.to_csv(TABLES / "model_a_corrected_margin_curves.csv", index=False)
    diagnostics.to_csv(TABLES / "model_a_corrected_diagnostics.csv", index=False)
    sector_comparison.to_csv(
        TABLES / "model_a_corrected_sector_comparison.csv", index=False
    )
    leave_one_out.to_csv(
        TABLES / "model_a_corrected_leave_one_block_out.csv", index=False
    )
    ppc_summary.to_csv(TABLES / "model_a_corrected_ppc_summary.csv", index=False)
    ppc_draws_table.to_csv(TABLES / "model_a_corrected_ppc_draws.csv", index=False)
    trajectories.to_csv(TABLES / "model_a_longitudinal_trajectories.csv", index=False)
    longitudinal_contrasts.to_csv(
        TABLES / "model_a_longitudinal_contrasts.csv", index=False
    )
    model_b_states.to_csv(TABLES / "model_b_state_trajectories.csv", index=False)
    model_b_nni.to_csv(TABLES / "model_b_final_nni_probabilities.csv", index=False)
    reconstruction_null.to_csv(
        TABLES / "reconstruction_null_percentiles.csv", index=False
    )
    original_diagnostics.to_csv(TABLES / "original_run_diagnostics.csv", index=False)

    make_figures(
        yield_data=YIELD_DATA,
        treatment_means=treatment_means,
        margins=margins,
        ranks=ranks,
        estimands=estimands,
        sector_comparison=sector_comparison,
        leave_one_out=leave_one_out,
        ppc_draws=ppc_draws_table,
        trajectories=trajectories,
        longitudinal_contrasts=longitudinal_contrasts,
        model_b_states=model_b_states,
        reconstruction_null=reconstruction_null,
    )


def save_figure(fig: Figure, name: str) -> None:
    fig.savefig(FIGURES / f"{name}.png", dpi=180, bbox_inches="tight")
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def plot_observed_yield_panels(
    axes: Any,
    *,
    yield_data: pd.DataFrame,
    treatment_means: pd.DataFrame,
) -> None:
    rng = np.random.default_rng(RANDOM_SEED)
    for axis, sector in zip(axes, SECTORS):
        observed = yield_data.loc[yield_data["sector"].astype(str).eq(sector)]
        posterior = (
            treatment_means.loc[
                treatment_means["sector"].eq(sector)
                & treatment_means["specification"].eq("Principal")
            ]
            .set_index("treatment")
            .reindex(TREATMENTS)
        )
        x = np.arange(6)
        for index, treatment in enumerate(TREATMENTS):
            values = observed.loc[
                observed["treatment"].astype(str).eq(treatment),
                "clean_yield_kg_ha",
            ].to_numpy()
            jitter = rng.normal(0.0, 0.035, size=len(values))
            axis.scatter(np.full(len(values), index) + jitter, values, alpha=0.55, s=26)
        axis.errorbar(
            x,
            posterior["posterior_mean"],
            yerr=np.vstack(
                [
                    posterior["posterior_mean"] - posterior["lower_95"],
                    posterior["upper_95"] - posterior["posterior_mean"],
                ]
            ),
            fmt="o",
            capsize=4,
            linewidth=1.6,
            label="Media posterior e IC 95 %",
        )
        axis.set_xticks(x, TREATMENTS)
        axis.set_title(sector)
        axis.set_xlabel("Tratamiento")
        axis.grid(axis="y", alpha=0.25)


def plot_margin_panels(axes: Any, margins: pd.DataFrame) -> None:
    for axis, sector in zip(axes, SECTORS):
        subset = margins.loc[margins["sector"].eq(sector)]
        for specification, group in subset.groupby("specification", sort=False):
            linewidth = 2.6 if specification == "Principal" else 1.4
            axis.plot(
                group["margin_kg_ha"],
                group["p_range_gt_margin"],
                label=specification,
                linewidth=linewidth,
            )
        axis.axvline(100.0, linestyle="--", linewidth=1.0)
        axis.axhline(0.5, linestyle=":", linewidth=1.0)
        axis.set_title(sector)
        axis.set_xlabel("Margen práctico δ (kg/ha)")
        axis.set_ylim(-0.02, 1.02)
        axis.grid(alpha=0.22)


def plot_near_optimal_panels(axes: Any, primary_ranks: pd.DataFrame) -> None:
    for axis, sector in zip(axes, SECTORS):
        group = (
            primary_ranks.loc[primary_ranks["sector"].eq(sector)]
            .set_index("treatment")
            .reindex(FERTILIZED)
        )
        axis.bar(FERTILIZED, group["p_within_100_best"])
        axis.set_title(sector)
        axis.set_xlabel("Calendario")
        axis.set_ylim(0.0, 1.0)
        axis.grid(axis="y", alpha=0.22)
        for index, value in enumerate(group["p_within_100_best"]):
            axis.text(
                index, value + 0.025, f"{100*value:.0f}%", ha="center", fontsize=9
            )


def yield_contrast_plot_data(
    primary_estimands: pd.DataFrame,
    sector_comparison: pd.DataFrame,
) -> tuple[list[str], list[tuple[float, float, float]]]:
    labels: list[str] = []
    values: list[tuple[float, float, float]] = []
    for sector in SECTORS:
        row = primary_estimands.loc[primary_estimands["sector"].eq(sector)].iloc[0]
        labels.append(sector)
        values.append(
            (float(row["median"]), float(row["lower_95"]), float(row["upper_95"]))
        )
    row = sector_comparison.loc[
        sector_comparison["estimand"].eq(
            "Diferencia sectorial del contraste temprano–tardío"
        )
    ].iloc[0]
    labels.append("Riego − Secano")
    values.append(
        (float(row["median"]), float(row["lower_95"]), float(row["upper_95"]))
    )
    return labels, values


def plot_leave_one_out_panels(
    axes: Any,
    *,
    leave_one_out: pd.DataFrame,
    margins: pd.DataFrame,
) -> None:
    for axis, sector in zip(axes, SECTORS):
        group = leave_one_out.loc[leave_one_out["sector"].eq(sector)].copy()
        axis.scatter(group["omitted_block"], group["p_range_gt_100"], s=52)
        full_value = margins.loc[
            margins["sector"].eq(sector)
            & margins["specification"].eq("Principal")
            & margins["margin_kg_ha"].eq(100.0),
            "p_range_gt_margin",
        ].iloc[0]
        axis.axhline(full_value, linestyle="--", label="Todos los bloques")
        axis.set_title(sector)
        axis.set_xlabel("Bloque omitido")
        axis.set_ylim(0.0, 1.0)
        axis.grid(axis="y", alpha=0.22)


def plot_ppc_panels(axes: Any, ppc_draws: pd.DataFrame) -> None:
    observed_p = {"Secano": 0.428718, "Riego": 0.175851}
    for axis, sector in zip(axes, SECTORS):
        values = ppc_draws.loc[ppc_draws["sector"].eq(sector), "p_value_m1_m5"]
        axis.hist(values, bins=np.linspace(0, 1, 31), density=True, alpha=0.75)
        axis.axvline(0.05, linestyle="--", linewidth=1.2, label="0,05")
        axis.axvline(
            observed_p[sector], linestyle=":", linewidth=1.8, label="p observado"
        )
        axis.set_title(sector)
        axis.set_xlabel("p del ANOVA M1–M5 en un ensayo replicado")
        axis.grid(axis="y", alpha=0.18)


def plot_trajectory_panels(
    axes: Any,
    frame: pd.DataFrame,
    *,
    value_column: str,
    y_label: str,
    legend_location: str,
    reference: float | None = None,
) -> None:
    date_x = np.arange(3)
    for axis, sector in zip(axes, SECTORS):
        subset = frame.loc[frame["sector"].eq(sector)]
        for treatment in TREATMENTS:
            group = (
                subset.loc[subset["treatment"].eq(treatment)]
                .set_index("date")
                .reindex(DATES)
            )
            axis.plot(date_x, group[value_column], marker="o", label=treatment)
            axis.fill_between(date_x, group["lower_95"], group["upper_95"], alpha=0.09)
        if reference is not None:
            axis.axhline(reference, linestyle="--", linewidth=1.0)
        axis.set_xticks(date_x, ["16 sep.", "20 oct.", "12 nov."])
        axis.set_title(sector)
        axis.set_xlabel("Fecha")
        axis.grid(alpha=0.22)
    axes[0].set_ylabel(y_label)
    axes[1].legend(ncol=2, loc=legend_location)


def plot_targeted_contrast_panels(
    axes: Any,
    display_contrasts: pd.DataFrame,
) -> None:
    for axis, variable in zip(axes, ["Biomasa aérea", "Concentración de N"]):
        group = display_contrasts.loc[
            display_contrasts["variable"].eq(variable)
        ].reset_index(drop=True)
        y = np.arange(len(group))
        med = group["median"].to_numpy()
        low = group["lower_95"].to_numpy()
        high = group["upper_95"].to_numpy()
        labels = [f"{s} — {d}" for s, d in zip(group["sector"], group["date"])]
        axis.errorbar(
            med, y, xerr=np.vstack([med - low, high - med]), fmt="o", capsize=4
        )
        axis.axvline(0, linewidth=1.0)
        axis.set_yticks(y, labels)
        axis.grid(axis="x", alpha=0.22)
        axis.set_title(variable)
        axis.set_xlabel(
            "Diferencia de biomasa (kg MS/ha)"
            if variable == "Biomasa aérea"
            else "Diferencia de concentración de N (puntos porcentuales)"
        )


def make_figures(
    *,
    yield_data: pd.DataFrame,
    treatment_means: pd.DataFrame,
    margins: pd.DataFrame,
    ranks: pd.DataFrame,
    estimands: pd.DataFrame,
    sector_comparison: pd.DataFrame,
    leave_one_out: pd.DataFrame,
    ppc_draws: pd.DataFrame,
    trajectories: pd.DataFrame,
    longitudinal_contrasts: pd.DataFrame,
    model_b_states: pd.DataFrame,
    reconstruction_null: pd.DataFrame,
) -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
        }
    )

    # 1. Observed yield + corrected posterior means.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    plot_observed_yield_panels(
        axes,
        yield_data=yield_data,
        treatment_means=treatment_means,
    )
    axes[0].set_ylabel("Rendimiento de semilla limpia (kg/ha)")
    axes[1].legend(loc="lower left")
    fig.suptitle("Rendimiento observado y estimación posterior corregida")
    fig.tight_layout()
    save_figure(fig, "01_yield_observed_posterior")

    # 2. Practical-margin sensitivity by prior.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    plot_margin_panels(axes, margins)
    axes[0].set_ylabel("P(rango M1–M5 > δ | datos)")
    axes[1].legend(loc="upper right")
    fig.suptitle("La conclusión depende del margen práctico y de la regularización")
    fig.tight_layout()
    save_figure(fig, "02_margin_prior_sensitivity")

    # 3. Near-optimal probabilities under the primary prior.
    primary_ranks = ranks.loc[ranks["specification"].eq("Principal")].copy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    plot_near_optimal_panels(axes, primary_ranks)
    axes[0].set_ylabel("P(a ≤100 kg/ha del mejor | datos)")
    fig.suptitle("Probabilidad de rendimiento prácticamente cercano al mejor")
    fig.tight_layout()
    save_figure(fig, "03_near_optimal_probabilities")

    # 4. Early-late yield contrasts and sector difference.
    primary_estimands = estimands.loc[
        estimands["specification"].eq("Principal")
        & estimands["estimand"].eq("M1–M2 menos M4–M5")
    ].copy()
    labels, values = yield_contrast_plot_data(
        primary_estimands,
        sector_comparison,
    )
    fig, axis = plt.subplots(figsize=(8.5, 4.2))
    y = np.arange(len(labels))
    med = np.array([item[0] for item in values])
    low = np.array([item[1] for item in values])
    high = np.array([item[2] for item in values])
    axis.errorbar(med, y, xerr=np.vstack([med - low, high - med]), fmt="o", capsize=4)
    axis.axvline(0.0, linewidth=1.0)
    axis.axvline(100.0, linestyle="--", linewidth=0.9)
    axis.axvline(-100.0, linestyle="--", linewidth=0.9)
    axis.set_yticks(y, labels)
    axis.set_xlabel("Contraste de rendimiento (kg/ha)")
    axis.set_title("Tempranos M1–M2 versus tardíos M4–M5")
    axis.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    save_figure(fig, "04_early_late_sector_contrast")

    # 5. Leave-one-block-out sensitivity.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
    plot_leave_one_out_panels(
        axes,
        leave_one_out=leave_one_out,
        margins=margins,
    )
    axes[0].set_ylabel("P(rango M1–M5 >100 kg/ha)")
    axes[1].legend(loc="best")
    fig.suptitle("Sensibilidad al dejar afuera un bloque")
    fig.tight_layout()
    save_figure(fig, "05_leave_one_block_out")

    # 6. Posterior predictive classical p-values.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
    plot_ppc_panels(axes, ppc_draws)
    axes[0].set_ylabel("Densidad")
    axes[1].legend(loc="upper right")
    fig.suptitle("Qué produciría nuevamente el análisis convencional")
    fig.tight_layout()
    save_figure(fig, "06_posterior_predictive_anova")

    # 7. Longitudinal biomass trajectories.
    biomass = trajectories.loc[trajectories["variable"].eq("Biomasa aérea")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.0), sharey=True)
    plot_trajectory_panels(
        axes,
        biomass,
        value_column="median",
        y_label="Biomasa típica posterior (kg MS/ha)",
        legend_location="upper left",
    )
    fig.suptitle(
        "Trayectorias posteriores de biomasa: separación temprana y convergencia parcial"
    )
    fig.tight_layout()
    save_figure(fig, "07_longitudinal_biomass")

    # 8. Longitudinal N concentration trajectories.
    n_conc = trajectories.loc[trajectories["variable"].eq("Concentración de N")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.0), sharey=True)
    plot_trajectory_panels(
        axes,
        n_conc,
        value_column="median",
        y_label="Concentración típica posterior de N (%)",
        legend_location="upper right",
    )
    fig.suptitle("El mayor estado nitrogenado se desplaza hacia calendarios tardíos")
    fig.tight_layout()
    save_figure(fig, "08_longitudinal_n_concentration")

    # 9. Targeted longitudinal contrasts.
    display_contrasts = longitudinal_contrasts.loc[
        (
            (longitudinal_contrasts["variable"].eq("Biomasa aérea"))
            & longitudinal_contrasts["date"].eq("Sep")
        )
        | (
            (longitudinal_contrasts["variable"].eq("Concentración de N"))
            & longitudinal_contrasts["date"].isin(["Oct", "Nov"])
        )
    ].copy()
    display_contrasts["label"] = (
        display_contrasts["sector"]
        + " — "
        + display_contrasts["variable"]
        + " — "
        + display_contrasts["date"]
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    plot_targeted_contrast_panels(axes, display_contrasts)
    fig.suptitle("Contrastes temporales preespecificados")
    fig.tight_layout()
    save_figure(fig, "09_targeted_longitudinal_contrasts")

    # 10. Model B NNI trajectories (exploratory support).
    nni = model_b_states.loc[model_b_states["variable"].eq("nni_revised")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.0), sharey=True)
    plot_trajectory_panels(
        axes,
        nni,
        value_column="posterior_median",
        y_label="INN revisado latente",
        legend_location="upper right",
        reference=1.0,
    )
    fig.suptitle("Modelo B: trayectorias latentes del INN (resultado de apoyo)")
    fig.tight_layout()
    save_figure(fig, "10_model_b_nni")

    # 11. Reconstruction-null observed vs null interval.
    table = reconstruction_null.copy().iloc[::-1].reset_index(drop=True)
    fig, axis = plt.subplots(figsize=(10.2, 4.6))
    y = np.arange(len(table))
    null_median = table["null_median"].to_numpy()
    null_low = table["null_lower_95"].to_numpy()
    null_high = table["null_upper_95"].to_numpy()
    observed = table["observed_correlation"].to_numpy()
    axis.errorbar(
        null_median,
        y,
        xerr=np.vstack([null_median - null_low, null_high - null_median]),
        fmt="o",
        capsize=4,
        label="Nulo de reconstrucción: mediana e IC 95 %",
    )
    axis.scatter(
        observed, y, marker="x", s=80, linewidths=2.0, label="Correlación observada"
    )
    axis.axvline(0.0, linewidth=0.8)
    axis.set_yticks(y, table["pattern"])
    axis.set_xlabel("Correlación panojas–semillas estimadas por panoja")
    axis.set_title(
        "La asociación inversa observada es ordinaria bajo la reconstrucción matemática"
    )
    axis.grid(axis="x", alpha=0.22)
    axis.legend(loc="upper right")
    fig.tight_layout()
    save_figure(fig, "11_reconstruction_null")


if __name__ == "__main__":
    run_all()
