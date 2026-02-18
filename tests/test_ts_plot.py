"""Tests for ts_plot (regression: never call to_pandas on None)."""
from unittest.mock import MagicMock

import pytest

from ts_plot import plot_ts_data_if_present


def test_plot_ts_data_if_present_none_does_not_call_to_pandas():
    """Regression: passing None must not call .to_pandas() (fix for 'to_pandas' is not a known attribute of None)."""
    plot_ts_data_if_present(None)
    # No exception and no call to to_pandas; nothing to assert except we get here


def test_plot_ts_data_if_present_calls_to_pandas_when_not_none():
    """When dps is not None, to_pandas() and plot() are called."""
    mock_df = MagicMock()
    mock_plot = MagicMock()
    mock_dps = MagicMock()
    mock_dps.to_pandas.return_value = mock_df
    mock_df.plot.return_value = mock_plot

    plot_ts_data_if_present(mock_dps)

    mock_dps.to_pandas.assert_called_once()
    mock_df.plot.assert_called_once()
