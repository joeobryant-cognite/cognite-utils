"""Tests for cognite_auth (require cognite_auth_config.json in utils/)."""
from unittest.mock import patch

import pytest

from cognite_auth import (
    CUSTOMER_CONFIGS,
    client_with_fallback,
    load_customer_configs,
)


def test_customer_configs_is_dict():
    """CUSTOMER_CONFIGS is a non-empty dict of customer configs."""
    assert isinstance(CUSTOMER_CONFIGS, dict)
    # Config file in repo has at least one customer
    assert len(CUSTOMER_CONFIGS) >= 1


def test_load_customer_configs_returns_dict():
    """load_customer_configs returns a dict with expected keys per customer."""
    configs = load_customer_configs()
    assert isinstance(configs, dict)
    for customer, config in configs.items():
        assert isinstance(config, dict)
        assert "tenant_id" in config
        assert "client_id" in config
        assert "cdf_cluster" in config
        assert "cognite_project" in config


def test_client_with_fallback_never_raises_none():
    """Regression: when both auth methods fail, we never raise None (invalid)."""
    customer = next(iter(CUSTOMER_CONFIGS))
    with patch("cognite_auth.device_code_client", side_effect=RuntimeError("device failed")):
        with patch("cognite_auth.interactive_client", side_effect=ValueError("interactive failed")):
            with pytest.raises((RuntimeError, ValueError)) as exc_info:
                client_with_fallback(customer, token_cache_path=None)
    # Must be a real exception, not None (BaseException is the base of all raise-ables)
    assert exc_info.value is not None
    assert isinstance(exc_info.value, BaseException)
