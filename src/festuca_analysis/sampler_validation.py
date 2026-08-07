from __future__ import annotations

"""Independent validation utilities for the custom robust Gibbs sampler."""

# PyMC and ArviZ expose partial type information.
# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

from pathlib import Path
from typing import Any, cast

import arviz as az
import numpy as np
import pandas as pd

from festuca_analysis.annex import (
    BLOCK_PRIOR_SD,
    EXTRA_N_PRIOR_SD,
    INTERCEPT_PRIOR_SD,
    RANDOM_SEED,
    SIGMA2_PRIOR_SCALE,
    SIGMA2_PRIOR_SHAPE,
    STUDENT_T_DF,
    TREATMENTS,
    flatten,
    load_yield_data,
    make_design,
    sample_hierarchical_yield,
)


def sample_pymc_reference(
    frame: pd.DataFrame,
    *,
    timing_prior_scale: float = 0.50,
    draws: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    seed: int = RANDOM_SEED,
) -> tuple[np.ndarray, dict[str, float]]:
    """Fit the same standardized model in PyMC and return means plus diagnostics."""
    import pymc as pm

    pm_api = cast(Any, pm)
    design = make_design(frame)
    block_count = design.block_slice.stop - design.block_slice.start
    with pm_api.Model():
        intercept = pm_api.Normal("intercept", 0.0, INTERCEPT_PRIOR_SD)
        extra_n = pm_api.Normal("extra_n", 0.0, EXTRA_N_PRIOR_SD)
        tau_timing = pm_api.HalfNormal("tau_timing", timing_prior_scale)
        timing_raw = pm_api.Normal("timing_raw", 0.0, 1.0, shape=4)
        timing = pm_api.Deterministic("timing", tau_timing * timing_raw)
        if block_count:
            block = pm_api.Normal("block", 0.0, BLOCK_PRIOR_SD, shape=block_count)
            beta = pm_api.math.concatenate(
                [intercept[None], extra_n[None], timing, block]
            )
        else:
            beta = pm_api.math.concatenate([intercept[None], extra_n[None], timing])
        sigma2 = pm_api.InverseGamma(
            "sigma2",
            alpha=SIGMA2_PRIOR_SHAPE,
            beta=SIGMA2_PRIOR_SCALE,
        )
        mu = pm_api.math.dot(design.X, beta)
        pm_api.StudentT(
            "y",
            nu=STUDENT_T_DF,
            mu=mu,
            sigma=pm_api.math.sqrt(sigma2),
            observed=design.y_z,
        )
        trace = pm_api.sample(
            draws=draws,
            tune=tune,
            chains=chains,
            cores=1,
            random_seed=seed,
            target_accept=0.95,
            progressbar=False,
            compute_convergence_checks=True,
        )

    posterior = trace.posterior
    pieces = [
        np.asarray(posterior["intercept"]).reshape(-1, 1),
        np.asarray(posterior["extra_n"]).reshape(-1, 1),
        np.asarray(posterior["timing"]).reshape(-1, 4),
    ]
    if block_count:
        pieces.append(np.asarray(posterior["block"]).reshape(-1, block_count))
    beta_draws = np.column_stack(pieces)
    group_z = beta_draws @ design.X_group.T
    selected = trace.posterior[["intercept", "extra_n", "tau_timing", "timing"]]
    rhat = cast(Any, az.rhat(selected))
    ess = cast(Any, az.ess(selected))
    diagnostics = {
        "pymc_divergences": float(np.asarray(trace.sample_stats["diverging"]).sum()),
        "pymc_max_rhat": max(
            float(np.nanmax(variable.values)) for variable in rhat.data_vars.values()
        ),
        "pymc_min_ess_bulk": min(
            float(np.nanmin(variable.values)) for variable in ess.data_vars.values()
        ),
    }
    return design.center + design.scale * group_z, diagnostics


def reference_comparison(
    frame: pd.DataFrame,
    *,
    timing_prior_scale: float = 0.50,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Compare posterior treatment means from the custom and PyMC samplers."""
    _, custom, _ = sample_hierarchical_yield(
        frame,
        timing_prior_scale=timing_prior_scale,
        chains=2,
        iterations=6000,
        burn=1500,
        thin=3,
        seed=seed,
    )
    custom_means = flatten(custom, "mean_yield")
    reference_means, reference_diagnostics = sample_pymc_reference(
        frame,
        timing_prior_scale=timing_prior_scale,
        draws=1000,
        tune=1000,
        chains=4,
        seed=seed + 1,
    )
    rows: list[dict[str, object]] = []
    for index, treatment in enumerate(TREATMENTS):
        custom_mean = float(custom_means[:, index].mean())
        reference_mean = float(reference_means[:, index].mean())
        rows.append(
            {
                "treatment": treatment,
                "custom_posterior_mean": custom_mean,
                "pymc_posterior_mean": reference_mean,
                "difference_custom_minus_pymc": custom_mean - reference_mean,
                **reference_diagnostics,
            }
        )
    return pd.DataFrame(rows)


def simulated_dataset(seed: int = RANDOM_SEED) -> tuple[pd.DataFrame, dict[str, float]]:
    """Generate a known RCBD signal for end-to-end recovery checks."""
    rng = np.random.default_rng(seed)
    true_means = {
        "M0": 700.0,
        "M1": 1300.0,
        "M2": 1340.0,
        "M3": 1260.0,
        "M4": 1380.0,
        "M5": 1220.0,
    }
    block_effects = {"R1": -45.0, "R2": -10.0, "R3": 15.0, "R4": 40.0}
    rows: list[dict[str, object]] = []
    for block, block_effect in block_effects.items():
        for treatment in TREATMENTS:
            rows.append(
                {
                    "sector": "Simulado",
                    "block": block,
                    "treatment": treatment,
                    "clean_yield_kg_ha": (
                        true_means[treatment]
                        + block_effect
                        + 65.0 * rng.standard_t(STUDENT_T_DF)
                    ),
                }
            )
    frame = pd.DataFrame(rows)
    frame["treatment"] = pd.Categorical(frame["treatment"], TREATMENTS, ordered=True)
    frame["block"] = pd.Categorical(frame["block"], list(block_effects), ordered=True)
    return frame, true_means


def simulation_recovery(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Check recovery of known treatment means from a simulated experiment."""
    frame, truth = simulated_dataset(seed)
    _, samples, _ = sample_hierarchical_yield(
        frame,
        timing_prior_scale=0.50,
        chains=3,
        iterations=7000,
        burn=1500,
        thin=3,
        seed=seed + 100,
    )
    means = flatten(samples, "mean_yield")
    rows: list[dict[str, object]] = []
    for index, treatment in enumerate(TREATMENTS):
        values = means[:, index]
        lower = float(np.quantile(values, 0.025))
        upper = float(np.quantile(values, 0.975))
        true_value = truth[treatment]
        rows.append(
            {
                "treatment": treatment,
                "true_mean": true_value,
                "posterior_mean": float(values.mean()),
                "lower_95": lower,
                "upper_95": upper,
                "covered_by_95_interval": lower <= true_value <= upper,
            }
        )
    return pd.DataFrame(rows)


def run_validation() -> None:
    """Run reference and recovery checks and save compact audit tables."""
    output = Path(__file__).resolve().parents[2] / "results" / "validation"
    output.mkdir(parents=True, exist_ok=True)
    yield_data = load_yield_data()
    comparison_tables: list[pd.DataFrame] = []
    for sector_index, sector in enumerate(["Secano", "Riego"]):
        frame = yield_data.loc[yield_data["sector"].astype(str).eq(sector)].copy()
        comparison = reference_comparison(
            frame,
            seed=RANDOM_SEED + sector_index * 10000,
        )
        comparison.insert(0, "sector", sector)
        comparison_tables.append(comparison)
    reference = pd.concat(comparison_tables, ignore_index=True)
    recovery = simulation_recovery()
    reference.to_csv(output / "custom_vs_pymc.csv", index=False)
    recovery.to_csv(output / "simulation_recovery.csv", index=False)

    max_difference = float(reference["difference_custom_minus_pymc"].abs().max())
    coverage = float(recovery["covered_by_95_interval"].mean())
    divergences = int(reference["pymc_divergences"].max())
    max_rhat = float(reference["pymc_max_rhat"].max())
    if max_difference > 100.0:
        raise AssertionError(
            f"La diferencia máxima frente a PyMC fue {max_difference:.1f} kg/ha."
        )
    if coverage < 5.0 / 6.0:
        raise AssertionError(f"Cobertura insuficiente en recuperación: {coverage:.1%}.")
    if divergences:
        raise AssertionError(f"La referencia PyMC tuvo {divergences} divergencias.")
    if max_rhat > 1.01:
        raise AssertionError(f"R-hat máximo de la referencia PyMC: {max_rhat:.4f}.")


if __name__ == "__main__":
    run_validation()
