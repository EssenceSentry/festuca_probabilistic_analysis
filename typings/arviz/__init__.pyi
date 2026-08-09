from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd
import xarray as xr

__version__: str

class InferenceData:
    posterior: xr.Dataset
    posterior_predictive: xr.Dataset
    sample_stats: xr.Dataset
    def extend(
        self,
        other: InferenceData,
        *,
        join: str = ...,
        warn_on_custom_groups: bool = ...,
    ) -> None: ...
    def to_netcdf(self, filename: str | Path, **kwargs: Any) -> str: ...

def summary(
    data: InferenceData,
    *,
    var_names: Sequence[str] | None = ...,
    round_to: int | str | None = ...,
    **kwargs: Any,
) -> pd.DataFrame: ...
