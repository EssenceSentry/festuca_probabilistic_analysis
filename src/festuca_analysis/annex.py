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
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.figure import Figure
from scipy.linalg import helmert
from scipy.stats import f as f_dist
from scipy.stats import geninvgauss

from festuca_analysis.plotting import (
    DATA_LINEWIDTH,
    EMPHASIS_LINEWIDTH,
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

RANDOM_SEED = 20260807
TREATMENTS = [f"M{i}" for i in range(6)]
FERTILIZED = TREATMENTS[1:]
SECTORS = ["Secano", "Riego"]
DATES = ["Sep", "Oct", "Nov"]

STUDENT_T_DF = 5.0
INTERCEPT_PRIOR_SD = 1.5
EXTRA_N_PRIOR_SD = 2.0
BLOCK_PRIOR_SD = 0.75
SIGMA2_PRIOR_SHAPE = 2.0
SIGMA2_PRIOR_SCALE = 0.5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKBOOK = PROJECT_ROOT / "sources" / "Datos_Ema_Serrana_INN.xlsx"
REFERENCE_TABLES = PROJECT_ROOT / "reference_outputs" / "legacy_probabilistic_run"
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


def prior_specification_table() -> pd.DataFrame:
    """Return the complete numerical prior specification on the z scale."""
    return pd.DataFrame(
        [
            {
                "parameter": "Intercepto",
                "prior": f"Normal(0, {INTERCEPT_PRIOR_SD})",
                "scale": "respuesta estandarizada",
                "role": "media general",
            },
            {
                "parameter": "N adicional (M1–M5 vs M0)",
                "prior": f"Normal(0, {EXTRA_N_PRIOR_SD})",
                "scale": "respuesta estandarizada",
                "role": "contraste planificado",
            },
            {
                "parameter": "Contrastes M1–M5",
                "prior": "Normal(0, tau_timing)",
                "scale": "respuesta estandarizada",
                "role": "regularización jerárquica",
            },
            {
                "parameter": "tau_timing",
                "prior": "HalfNormal(0.25 / 0.50 / 1.00)",
                "scale": "respuesta estandarizada",
                "role": "sensibilidad de regularización",
            },
            {
                "parameter": "Bloques",
                "prior": f"Normal(0, {BLOCK_PRIOR_SD})",
                "scale": "respuesta estandarizada",
                "role": "contrastes ortonormales",
            },
            {
                "parameter": "sigma^2",
                "prior": (f"InverseGamma({SIGMA2_PRIOR_SHAPE}, {SIGMA2_PRIOR_SCALE})"),
                "scale": "respuesta estandarizada",
                "role": "varianza residual",
            },
            {
                "parameter": "y",
                "prior": f"Student-t(nu={int(STUDENT_T_DF)}, mu, sigma)",
                "scale": "kg ha^-1 tras desestandarizar",
                "role": "verosimilitud robusta",
            },
        ]
    )


def prior_predictive_summary(
    frame: pd.DataFrame,
    *,
    timing_prior_scale: float,
    draws: int = 20000,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Simulate prior predictions and summarize their agronomic plausibility."""
    design = make_design(frame)
    rng = np.random.default_rng(seed)
    coefficient_draws = np.zeros((draws, design.X.shape[1]))
    coefficient_draws[:, 0] = rng.normal(0.0, INTERCEPT_PRIOR_SD, draws)
    coefficient_draws[:, 1] = rng.normal(0.0, EXTRA_N_PRIOR_SD, draws)
    tau = np.abs(rng.normal(0.0, timing_prior_scale, draws))
    coefficient_draws[:, design.timing_slice] = rng.normal(
        0.0,
        tau[:, None],
        (draws, design.timing_slice.stop - design.timing_slice.start),
    )
    if design.block_slice.stop > design.block_slice.start:
        coefficient_draws[:, design.block_slice] = rng.normal(
            0.0,
            BLOCK_PRIOR_SD,
            (draws, design.block_slice.stop - design.block_slice.start),
        )
    group_z = coefficient_draws @ design.X_group.T
    group_means = design.center + design.scale * group_z
    sigma2 = 1.0 / rng.gamma(
        SIGMA2_PRIOR_SHAPE,
        1.0 / SIGMA2_PRIOR_SCALE,
        draws,
    )
    replicated = group_means + design.scale * np.sqrt(sigma2)[:, None] * rng.standard_t(
        STUDENT_T_DF,
        size=group_means.shape,
    )
    fertilized_range = np.ptp(group_means[:, 1:], axis=1)
    return pd.DataFrame(
        [
            {
                "timing_prior_scale": timing_prior_scale,
                "draws": draws,
                "mean_lower_95": float(np.quantile(group_means, 0.025)),
                "mean_upper_95": float(np.quantile(group_means, 0.975)),
                "p_any_treatment_mean_below_zero": float(
                    np.mean(np.any(group_means < 0.0, axis=1))
                ),
                "p_replicated_yield_below_zero": float(np.mean(replicated < 0.0)),
                "p_replicated_yield_above_3000": float(np.mean(replicated > 3000.0)),
                "median_prior_range_m1_m5": float(np.median(fertilized_range)),
                "range_upper_95_m1_m5": float(np.quantile(fertilized_range, 0.95)),
            }
        ]
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

    nu = STUDENT_T_DF
    a0 = SIGMA2_PRIOR_SHAPE
    b0 = SIGMA2_PRIOR_SCALE
    fixed_precision = np.zeros(p)
    fixed_precision[0] = 1.0 / INTERCEPT_PRIOR_SD**2
    fixed_precision[1] = 1.0 / EXTRA_N_PRIOR_SD**2
    if design.block_slice.stop > design.block_slice.start:
        fixed_precision[design.block_slice] = 1.0 / BLOCK_PRIOR_SD**2

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
    prior_sd[0] = INTERCEPT_PRIOR_SD
    prior_sd[1] = EXTRA_N_PRIOR_SD
    prior_sd[design.timing_slice] = timing_sd
    prior_sd[design.block_slice] = BLOCK_PRIOR_SD
    prior_precision = np.diag(1.0 / prior_sd**2)

    nu = STUDENT_T_DF
    a0 = SIGMA2_PRIOR_SHAPE
    b0 = SIGMA2_PRIOR_SCALE

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
# Accepted summaries from the original probabilistic run
# -----------------------------------------------------------------------------


def load_legacy_table(filename: str) -> pd.DataFrame:
    """Load a compact accepted summary from the preserved probabilistic run."""
    path = REFERENCE_TABLES / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"No se encontró el insumo de referencia {path}. "
            "Consulte reference_outputs/legacy_probabilistic_run/README.md."
        )
    return pd.read_csv(path)


def summarize_longitudinal_model_a() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the accepted Model A summaries without shipping 49 MB of chains."""
    return (
        load_legacy_table("model_a_longitudinal_trajectories.csv"),
        load_legacy_table("model_a_longitudinal_contrasts.csv"),
    )


# -----------------------------------------------------------------------------
# Execution
# -----------------------------------------------------------------------------


def run_all() -> None:
    yield_data = load_yield_data()
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

    prior_table = prior_specification_table()
    prior_predictive_rows: list[pd.DataFrame] = []
    for sector_index, sector in enumerate(SECTORS):
        sector_frame = yield_data.loc[
            yield_data["sector"].astype(str).eq(sector)
        ].copy()
        for prior_index, timing_scale in enumerate([0.25, 0.50, 1.00]):
            prior_summary = prior_predictive_summary(
                sector_frame,
                timing_prior_scale=timing_scale,
                seed=RANDOM_SEED + 50000 + sector_index * 1000 + prior_index * 100,
            )
            prior_summary.insert(0, "sector", sector)
            prior_predictive_rows.append(prior_summary)
    prior_predictive = pd.concat(prior_predictive_rows, ignore_index=True)

    for sector_index, sector in enumerate(SECTORS):
        sector_frame = yield_data.loc[
            yield_data["sector"].astype(str).eq(sector)
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
        sector_frame = yield_data.loc[
            yield_data["sector"].astype(str).eq(sector)
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
    model_b_states = load_legacy_table("model_b_state_trajectories.csv")
    model_b_nni = load_legacy_table("model_b_final_nni_probabilities.csv")
    reconstruction_null = load_legacy_table("reconstruction_null_percentiles.csv")
    original_diagnostics = load_legacy_table("original_run_diagnostics.csv")

    # Save all tables.
    yield_data.to_csv(TABLES / "yield_data.csv", index=False)
    prior_table.to_csv(TABLES / "prior_specification.csv", index=False)
    prior_predictive.to_csv(TABLES / "prior_predictive_summary.csv", index=False)
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
        yield_data=yield_data,
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


def run_all_cli() -> None:
    """Regenerate the annex with a non-interactive plotting backend."""
    plt.switch_backend("Agg")
    run_all()


def save_figure(fig: Figure, name: str) -> None:
    fig.savefig(FIGURES / f"{name}.png", dpi=180, bbox_inches="tight")
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def plot_observed_yield_panels(
    axes: Any,
    *,
    yield_data: pd.DataFrame,
    treatment_means: pd.DataFrame,
    treatment_colors: dict[str, str],
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
        for index, treatment in enumerate(TREATMENTS):
            values = observed.loc[
                observed["treatment"].astype(str).eq(treatment),
                "clean_yield_kg_ha",
            ].to_numpy()
            jitter = rng.normal(0.0, 0.035, size=len(values))
            axis.scatter(
                np.full(len(values), index) + jitter,
                values,
                color=treatment_colors[treatment],
                alpha=0.45,
                s=26,
                linewidths=0,
            )
            row = posterior.loc[treatment]
            axis.errorbar(
                index,
                row["posterior_mean"],
                yerr=np.array(
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
                label="Media posterior e IC 95 %" if index == 0 else None,
            )
        axis.set_xticks(np.arange(len(TREATMENTS)), TREATMENTS)
        axis.set_title(sector.upper())
        axis.set_xlabel("Tratamiento")
        axis.grid(axis="y", alpha=0.25)


def plot_margin_panels(
    axes: Any,
    margins: pd.DataFrame,
    *,
    principal_color: str,
) -> None:
    for axis, sector in zip(axes, SECTORS):
        subset = margins.loc[margins["sector"].eq(sector)]
        principal = subset.loc[subset["specification"].eq("Principal")]
        axis.plot(
            principal["margin_kg_ha"],
            principal["p_range_gt_margin"],
            color=principal_color,
            linewidth=EMPHASIS_LINEWIDTH,
            zorder=3,
        )
        alternatives = subset.loc[subset["specification"].ne("Principal")]
        for _, group in alternatives.groupby("specification", sort=False):
            axis.plot(
                group["margin_kg_ha"],
                group["p_range_gt_margin"],
                color="0.48",
                alpha=0.52,
                linewidth=SECONDARY_LINEWIDTH,
                zorder=2,
            )
        axis.axvline(100.0, linestyle="--", linewidth=REFERENCE_LINEWIDTH)
        axis.axhline(0.5, linestyle=":", linewidth=REFERENCE_LINEWIDTH)
        axis.set_title(sector.upper())
        axis.set_xlabel("Margen práctico δ (kg/ha)")
        axis.set_ylim(-0.02, 1.02)
        axis.grid(alpha=0.22)


def plot_near_optimal_panels(
    axes: Any,
    primary_ranks: pd.DataFrame,
    *,
    treatment_colors: dict[str, str],
) -> None:
    for axis, sector in zip(axes, SECTORS):
        group = (
            primary_ranks.loc[primary_ranks["sector"].eq(sector)]
            .set_index("treatment")
            .reindex(FERTILIZED)
        )
        axis.bar(
            FERTILIZED,
            group["p_within_100_best"],
            color=[treatment_colors[treatment] for treatment in FERTILIZED],
        )
        axis.set_title(sector.upper())
        axis.set_xlabel("Calendario")
        axis.set_ylim(0.0, 1.0)
        axis.grid(axis="y", alpha=0.22)
        for index, value in enumerate(group["p_within_100_best"]):
            axis.text(
                index,
                value + 0.025,
                f"{100 * value:.0f}%",
                ha="center",
                fontsize=9.5,
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
        axis.axhline(
            full_value,
            linestyle="--",
            linewidth=REFERENCE_LINEWIDTH,
            label="Todos los bloques",
        )
        axis.set_title(sector.upper())
        axis.set_xlabel("Bloque omitido")
        axis.set_ylim(0.0, 1.0)
        axis.grid(axis="y", alpha=0.22)


def plot_ppc_panels(axes: Any, ppc_draws: pd.DataFrame) -> None:
    observed_p = {"Secano": 0.428718, "Riego": 0.175851}
    for axis, sector in zip(axes, SECTORS):
        values = ppc_draws.loc[ppc_draws["sector"].eq(sector), "p_value_m1_m5"]
        axis.hist(values, bins=np.linspace(0, 1, 31), density=True, alpha=0.75)
        axis.axvline(
            0.05,
            linestyle="--",
            linewidth=REFERENCE_LINEWIDTH,
            label="0,05",
        )
        axis.axvline(
            observed_p[sector],
            linestyle=":",
            linewidth=DATA_LINEWIDTH,
            label="p observado",
        )
        axis.set_title(sector.upper())
        axis.set_xlabel("p del ANOVA M1–M5 en un ensayo replicado")
        axis.grid(axis="y", alpha=0.18)


def plot_trajectory_panels(
    axes: Any,
    frame: pd.DataFrame,
    *,
    value_column: str,
    y_label: str,
    treatment_colors: dict[str, str],
    reference: float | None = None,
) -> None:
    date_x = np.arange(3)
    treatment_offsets = dict(
        zip(TREATMENTS, np.linspace(-0.31, 0.31, len(TREATMENTS)), strict=True)
    )
    for axis, sector in zip(axes, SECTORS):
        subset = frame.loc[frame["sector"].eq(sector)]
        for treatment in TREATMENTS:
            group = (
                subset.loc[subset["treatment"].eq(treatment)]
                .set_index("date")
                .reindex(DATES)
            )
            estimate_x = date_x + treatment_offsets[treatment]
            axis.errorbar(
                estimate_x,
                group[value_column],
                yerr=np.vstack(
                    [
                        group[value_column] - group["lower_95"],
                        group["upper_95"] - group[value_column],
                    ]
                ),
                marker="o",
                linestyle="none",
                color=treatment_colors[treatment],
                markerfacecolor=(
                    "white" if treatment == "M0" else treatment_colors[treatment]
                ),
                markeredgecolor=treatment_colors[treatment],
                capsize=ERRORBAR_CAPSIZE,
                elinewidth=INTERVAL_LINEWIDTH,
                markersize=MARKER_SIZE,
                label=treatment,
            )
        if reference is not None:
            axis.axhline(
                reference,
                linestyle="--",
                linewidth=REFERENCE_LINEWIDTH,
            )
        for date_position in date_x:
            for treatment in TREATMENTS:
                axis.text(
                    date_position + treatment_offsets[treatment],
                    -0.035,
                    treatment,
                    transform=axis.get_xaxis_transform(),
                    ha="center",
                    va="top",
                    fontsize=8.5,
                    color="0.38",
                    clip_on=False,
                )
        axis.set_xticks(date_x, ["16 sep", "20 oct", "12 nov"])
        axis.tick_params(axis="x", which="major", pad=25, length=0)
        axis.set_title(sector.upper())
        axis.set_xlabel("")
        axis.grid(alpha=0.22)
    axes[0].set_ylabel(y_label)


def plot_targeted_contrast_panels(
    axes: Any,
    display_contrasts: pd.DataFrame,
    *,
    color: str,
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
        for estimate, lower, upper, y_position in zip(med, low, high, y, strict=True):
            plot_horizontal_interval(
                axis,
                estimate=float(estimate),
                lower=float(lower),
                upper=float(upper),
                y=float(y_position),
                color=color,
            )
        axis.axvline(0, linewidth=REFERENCE_LINEWIDTH)
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
    palette = apply_plot_theme()
    treatment_colors = dict(zip(TREATMENTS, palette[: len(TREATMENTS)], strict=True))

    # 1. Observed yield + corrected posterior means.
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.2), sharey=True)
    plot_observed_yield_panels(
        axes,
        yield_data=yield_data,
        treatment_means=treatment_means,
        treatment_colors=treatment_colors,
    )
    axes[0].set_ylabel("Rendimiento de semilla limpia (kg/ha)")
    handles, labels = axes[1].get_legend_handles_labels()
    add_figure_header(
        fig,
        "Rendimiento observado y estimación posterior corregida",
        subtitle=(
            "Puntos claros: parcelas observadas. Círculos y barras: media posterior "
            "e intervalo creíble del 95 %."
        ),
    )
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.83))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.15, top=0.70, wspace=0.12)
    save_figure(fig, "01_yield_observed_posterior")

    # 2. Practical-margin sensitivity by prior.
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.2), sharey=True)
    plot_margin_panels(
        axes,
        margins,
        principal_color=palette[3],
    )
    axes[0].set_ylabel("P(rango M1–M5 > δ | datos)")
    add_figure_header(
        fig,
        "La conclusión depende del margen práctico y de la regularización",
        subtitle=(
            "Curva principal destacada; las tres curvas grises son sensibilidades "
            "alternativas. La línea vertical marca 100 kg ha⁻¹."
        ),
    )
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.15, top=0.76, wspace=0.12)
    save_figure(fig, "02_margin_prior_sensitivity")

    # 3. Near-optimal probabilities under the primary prior.
    primary_ranks = ranks.loc[ranks["specification"].eq("Principal")].copy()
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.0), sharey=True)
    plot_near_optimal_panels(
        axes,
        primary_ranks,
        treatment_colors=treatment_colors,
    )
    axes[0].set_ylabel("P(a ≤100 kg/ha del mejor | datos)")
    add_figure_header(
        fig,
        "Probabilidad de rendimiento prácticamente cercano al mejor",
        subtitle=(
            "Probabilidad posterior de quedar a no más de 100 kg ha⁻¹ del mejor "
            "calendario fertilizado."
        ),
    )
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.15, top=0.76, wspace=0.12)
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
    fig, axis = plt.subplots(figsize=(8.8, 4.8))
    y = np.arange(len(labels))
    med = np.array([item[0] for item in values])
    low = np.array([item[1] for item in values])
    high = np.array([item[2] for item in values])
    for estimate, lower, upper, y_position in zip(med, low, high, y, strict=True):
        plot_horizontal_interval(
            axis,
            estimate=float(estimate),
            lower=float(lower),
            upper=float(upper),
            y=float(y_position),
            color=palette[1],
        )
    axis.axvline(0.0, linewidth=REFERENCE_LINEWIDTH)
    axis.axvline(100.0, linestyle="--", linewidth=REFERENCE_LINEWIDTH)
    axis.axvline(-100.0, linestyle="--", linewidth=REFERENCE_LINEWIDTH)
    axis.set_yticks(y, labels)
    axis.set_xlabel("Contraste de rendimiento (kg/ha)")
    axis.grid(axis="x", alpha=0.22)
    add_figure_header(
        fig,
        "Tempranos M1–M2 versus tardíos M4–M5",
        subtitle=(
            "Mediana posterior e intervalo creíble del 95 %; las líneas punteadas "
            "marcan ±100 kg ha⁻¹."
        ),
    )
    fig.subplots_adjust(left=0.19, right=0.98, bottom=0.17, top=0.75)
    save_figure(fig, "04_early_late_sector_contrast")

    # 5. Leave-one-block-out sensitivity.
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.0), sharey=True)
    plot_leave_one_out_panels(
        axes,
        leave_one_out=leave_one_out,
        margins=margins,
    )
    axes[0].set_ylabel("P(rango M1–M5 >100 kg/ha)")
    axes[1].legend(loc="best")
    add_figure_header(
        fig,
        "Sensibilidad al dejar afuera un bloque",
        subtitle=(
            "Cada punto omite un bloque; la línea punteada muestra el ajuste con "
            "todos los bloques."
        ),
    )
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.15, top=0.76, wspace=0.12)
    save_figure(fig, "05_leave_one_block_out")

    # 6. Posterior predictive classical p-values.
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.2), sharey=True)
    plot_ppc_panels(axes, ppc_draws)
    axes[0].set_ylabel("Densidad")
    handles, labels = axes[1].get_legend_handles_labels()
    add_figure_header(
        fig,
        "Qué produciría nuevamente el análisis convencional",
        subtitle=(
            "Distribución posterior predictiva del p del ANOVA M1–M5; se muestran "
            "el umbral 0,05 y el p observado."
        ),
    )
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.83),
        ncol=2,
    )
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.17, top=0.69, wspace=0.12)
    save_figure(fig, "06_posterior_predictive_anova")

    # 7. Longitudinal biomass trajectories.
    biomass = trajectories.loc[trajectories["variable"].eq("Biomasa aérea")]
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.7), sharey=True)
    plot_trajectory_panels(
        axes,
        biomass,
        value_column="median",
        y_label="Biomasa típica posterior (kg MS/ha)",
        treatment_colors=treatment_colors,
    )
    add_figure_header(
        fig,
        "Biomasa posterior en las tres fechas de muestreo",
        subtitle="Mediana posterior e intervalo creíble del 95 % para cada calendario.",
    )
    add_figure_note(
        fig,
        "Las fechas se muestran como categorías equidistantes; los puntos no se conectan.",
    )
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.23, top=0.76, wspace=0.12)
    save_figure(fig, "07_longitudinal_biomass")

    # 8. Longitudinal N concentration trajectories.
    n_conc = trajectories.loc[trajectories["variable"].eq("Concentración de N")]
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.7), sharey=True)
    plot_trajectory_panels(
        axes,
        n_conc,
        value_column="median",
        y_label="Concentración típica posterior de N (%)",
        treatment_colors=treatment_colors,
    )
    add_figure_header(
        fig,
        "Concentración de N posterior en las tres fechas de muestreo",
        subtitle="Mediana posterior e intervalo creíble del 95 % para cada calendario.",
    )
    add_figure_note(
        fig,
        "Las fechas se muestran como categorías equidistantes; los puntos no se conectan.",
    )
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.23, top=0.76, wspace=0.12)
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
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.7))
    plot_targeted_contrast_panels(
        axes,
        display_contrasts,
        color=palette[1],
    )
    add_figure_header(
        fig,
        "Contrastes temporales dirigidos por hipótesis",
        subtitle=(
            "Mediana posterior e intervalo creíble del 95 %; la línea vertical "
            "marca una diferencia nula."
        ),
    )
    fig.subplots_adjust(left=0.13, right=0.98, bottom=0.17, top=0.76, wspace=0.42)
    save_figure(fig, "09_targeted_longitudinal_contrasts")

    # 10. Model B NNI trajectories (exploratory support).
    nni = model_b_states.loc[model_b_states["variable"].eq("nni_revised")]
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.7), sharey=True)
    plot_trajectory_panels(
        axes,
        nni,
        value_column="posterior_median",
        y_label="INN revisado latente",
        treatment_colors=treatment_colors,
        reference=1.0,
    )
    add_figure_header(
        fig,
        "Modelo B: INN latente en las tres fechas de muestreo",
        subtitle=(
            "Mediana posterior e intervalo creíble del 95 %; la línea horizontal "
            "marca INN = 1."
        ),
    )
    add_figure_note(
        fig,
        "Resultado de apoyo. Las fechas son categorías equidistantes y los puntos no se conectan.",
    )
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.23, top=0.76, wspace=0.12)
    save_figure(fig, "10_model_b_nni")

    # 11. Reconstruction-null observed vs null interval.
    table = reconstruction_null.copy().iloc[::-1].reset_index(drop=True)
    fig, axis = plt.subplots(figsize=(10.4, 5.2))
    y = np.arange(len(table))
    null_median = table["null_median"].to_numpy()
    null_low = table["null_lower_95"].to_numpy()
    null_high = table["null_upper_95"].to_numpy()
    observed = table["observed_correlation"].to_numpy()
    null_y = y + 0.09
    observed_y = y - 0.09
    for index, (estimate, lower, upper, y_position) in enumerate(
        zip(null_median, null_low, null_high, null_y, strict=True)
    ):
        plot_horizontal_interval(
            axis,
            estimate=float(estimate),
            lower=float(lower),
            upper=float(upper),
            y=float(y_position),
            color=palette[1],
            label=("Nulo de reconstrucción: mediana e IC 95 %" if index == 0 else None),
        )
    axis.scatter(
        observed,
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
    axis.set_yticks(y, table["pattern"])
    axis.set_xlabel("Correlación panojas–semillas estimadas por panoja")
    axis.grid(axis="x", alpha=0.22)
    axis.legend(
        loc="lower right",
        bbox_to_anchor=(1.0, 1.02),
        ncol=2,
    )
    add_figure_header(
        fig,
        "Asociación observada frente al nulo de reconstrucción",
        subtitle=(
            "Círculos llenos y barras: mediana e intervalo nulo del 95 %. "
            "Círculos vacíos: correlación observada."
        ),
    )
    fig.subplots_adjust(left=0.28, right=0.98, bottom=0.17, top=0.76)
    save_figure(fig, "11_reconstruction_null")


if __name__ == "__main__":
    run_all_cli()
