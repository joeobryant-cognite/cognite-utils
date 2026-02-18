"""Helpers for plotting time series data from Cognite (handles optional retrieve results)."""

from typing import Optional, Protocol


class _HasToPandas(Protocol):
    """Protocol for objects that can be converted to pandas (e.g. Cognite time series data)."""

    def to_pandas(self): ...


def plot_ts_data_if_present(dps: Optional[_HasToPandas]) -> None:
    """Plot time series data if present; no-op if dps is None (e.g. retrieve returned None)."""
    if dps is not None:
        dps.to_pandas().plot()
