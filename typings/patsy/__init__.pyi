from collections.abc import Iterable, Sequence
from typing import Any, Literal, overload

import pandas as pd

class DesignInfo: ...

class DesignMatrixFrame(pd.DataFrame):
    design_info: DesignInfo

@overload
def dmatrix(
    formula_like: str,
    data: object = ...,
    eval_env: object = ...,
    NA_action: object = ...,
    return_type: Literal["dataframe"] = ...,
) -> DesignMatrixFrame: ...
@overload
def dmatrix(
    formula_like: str,
    data: object = ...,
    eval_env: object = ...,
    NA_action: object = ...,
    return_type: Literal["matrix"] = ...,
) -> Any: ...
def build_design_matrices(
    design_infos: Sequence[DesignInfo] | Iterable[object],
    data: object,
    NA_action: object = ...,
    return_type: Literal["matrix", "dataframe"] = ...,
    dtype: object = ...,
) -> list[DesignMatrixFrame]: ...
