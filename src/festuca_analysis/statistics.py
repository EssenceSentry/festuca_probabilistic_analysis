from __future__ import annotations

"""Statistical utilities shared by the executable thesis analyses."""

# The scientific Python stack exposes only partial type information for MixedLM.
# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import chi2


@dataclass(frozen=True)
class LikelihoodRatioResult:
    statistic: float
    degrees_freedom: int
    p_asymptotic: float


@dataclass(frozen=True)
class BootstrapLikelihoodRatioResult:
    observed: float
    p_bootstrap: float
    successful_replicates: int
    requested_replicates: int


def likelihood_ratio(reduced: Any, full: Any) -> LikelihoodRatioResult:
    """Compare nested maximum-likelihood fits with an asymptotic LRT."""
    statistic = max(0.0, 2.0 * (float(full.llf) - float(reduced.llf)))
    degrees_freedom = round(float(full.df_modelwc - reduced.df_modelwc))
    if degrees_freedom <= 0:
        raise ValueError(
            "El modelo completo debe tener más parámetros que el reducido."
        )
    return LikelihoodRatioResult(
        statistic=statistic,
        degrees_freedom=degrees_freedom,
        p_asymptotic=float(chi2.sf(statistic, degrees_freedom)),
    )


def fit_mixedlm_best(
    formula: str,
    frame: pd.DataFrame,
    *,
    group_column: str = "plot_id",
    methods: Sequence[str] = ("lbfgs", "bfgs", "powell", "nm", "cg"),
    stop_at_first_converged: bool = False,
    maxiter: int = 5000,
) -> Any:
    """Fit every requested optimizer and retain the best converged solution.

    A finite likelihood is not sufficient evidence of convergence.  The main
    analysis therefore evaluates all optimizers and selects the converged fit
    with the largest log-likelihood.  Bootstrap refits may opt into an early
    exit after the first converged fit to keep the resampling cost tractable.
    """
    candidates: list[tuple[Any, str, tuple[str, ...]]] = []
    errors: list[str] = []
    smf_api = cast(Any, smf)

    for method in dict.fromkeys(methods):
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                fit = smf_api.mixedlm(
                    formula,
                    frame,
                    groups=frame[group_column],
                ).fit(
                    reml=False,
                    method=method,
                    maxiter=maxiter,
                    disp=False,
                )
            warning_messages = tuple(str(item.message) for item in caught)
            if np.isfinite(float(fit.llf)):
                candidates.append((fit, method, warning_messages))
                if stop_at_first_converged and bool(fit.converged):
                    break
        except Exception as exc:  # noqa: BLE001 - the audit records every failure
            errors.append(f"{method}: {type(exc).__name__}: {exc}")

    if not candidates:
        detail = " | ".join(errors) if errors else "ningún ajuste finito"
        raise RuntimeError(f"No se pudo ajustar MixedLM. {detail}")

    converged = [candidate for candidate in candidates if bool(candidate[0].converged)]
    eligible = converged or candidates
    best_fit, best_method, best_warnings = max(
        eligible,
        key=lambda candidate: float(candidate[0].llf),
    )
    audit = tuple(
        {
            "optimizer": method,
            "llf": float(fit.llf),
            "converged": bool(fit.converged),
            "warnings": warning_messages,
        }
        for fit, method, warning_messages in candidates
    )
    best_fit._audit_optimizer = best_method
    best_fit._audit_warnings = best_warnings
    best_fit._audit_candidates = audit
    best_fit._audit_selection = (
        "best_converged" if converged else "best_finite_nonconverged"
    )
    return best_fit


def parametric_bootstrap_lrt(
    frame: pd.DataFrame,
    *,
    reduced_formula: str,
    full_formula: str,
    reduced_fit: Any,
    full_fit: Any,
    group_column: str = "plot_id",
    response_column: str = "y_z",
    replicates: int = 199,
    seed: int = 20260807,
) -> BootstrapLikelihoodRatioResult:
    """Calibrate a nested MixedLM LRT by simulation under the reduced model."""
    if replicates < 1:
        raise ValueError("replicates debe ser al menos 1")

    observed = likelihood_ratio(reduced_fit, full_fit).statistic
    fixed_mean = np.asarray(reduced_fit.model.exog, dtype=float) @ np.asarray(
        reduced_fit.fe_params,
        dtype=float,
    )
    group_codes, _ = pd.factorize(frame[group_column], sort=True)
    group_count = int(group_codes.max()) + 1
    random_variance = max(float(reduced_fit.cov_re.iloc[0, 0]), 0.0)
    residual_variance = max(float(reduced_fit.scale), np.finfo(float).eps)
    preferred = str(getattr(reduced_fit, "_audit_optimizer", "lbfgs"))
    methods = tuple(dict.fromkeys((preferred, "lbfgs", "powell", "nm")))
    rng = np.random.default_rng(seed)
    simulated_statistics: list[float] = []

    for _ in range(replicates):
        random_intercepts = rng.normal(0.0, np.sqrt(random_variance), group_count)
        simulated = (
            fixed_mean
            + random_intercepts[group_codes]
            + rng.normal(0.0, np.sqrt(residual_variance), len(frame))
        )
        bootstrap_frame = frame.copy()
        bootstrap_frame[response_column] = simulated
        try:
            reduced_bootstrap = fit_mixedlm_best(
                reduced_formula,
                bootstrap_frame,
                group_column=group_column,
                methods=methods,
                stop_at_first_converged=True,
                maxiter=2000,
            )
            full_bootstrap = fit_mixedlm_best(
                full_formula,
                bootstrap_frame,
                group_column=group_column,
                methods=methods,
                stop_at_first_converged=True,
                maxiter=2000,
            )
        except (RuntimeError, ValueError, np.linalg.LinAlgError):
            continue
        if bool(reduced_bootstrap.converged) and bool(full_bootstrap.converged):
            simulated_statistics.append(
                likelihood_ratio(reduced_bootstrap, full_bootstrap).statistic
            )

    successful = len(simulated_statistics)
    minimum_successful = min(
        replicates,
        max(20, int(np.ceil(0.80 * replicates))),
    )
    if successful < minimum_successful:
        raise RuntimeError(
            "Bootstrap LRT inestable: "
            f"solo convergieron {successful} de {replicates} réplicas."
        )
    exceedances = int(np.sum(np.asarray(simulated_statistics) >= observed))
    p_bootstrap = (1.0 + exceedances) / (1.0 + successful)
    return BootstrapLikelihoodRatioResult(
        observed=observed,
        p_bootstrap=float(p_bootstrap),
        successful_replicates=successful,
        requested_replicates=replicates,
    )


def benjamini_hochberg(values: Sequence[float] | np.ndarray) -> np.ndarray:
    """Return Benjamini-Hochberg adjusted p-values in the original order."""
    p_values = np.asarray(values, dtype=float)
    if p_values.ndim != 1 or np.any(~np.isfinite(p_values)):
        raise ValueError("Los valores p deben ser finitos y unidimensionales.")
    if np.any((p_values < 0.0) | (p_values > 1.0)):
        raise ValueError("Los valores p deben estar entre 0 y 1.")
    count = len(p_values)
    if count == 0:
        return np.asarray([], dtype=float)
    order = np.argsort(p_values)
    ranked = p_values[order]
    adjusted_ranked = np.minimum.accumulate(
        (ranked * count / np.arange(1, count + 1))[::-1]
    )[::-1]
    adjusted = np.empty(count, dtype=float)
    adjusted[order] = np.minimum(adjusted_ranked, 1.0)
    return adjusted
