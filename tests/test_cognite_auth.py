"""Tests for cognite_auth (require cognite_auth_config.json in utils/)."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from cognite_auth import (
    CONFIG_ENV_VAR_NAME,
    CUSTOMER_CONFIGS,
    client_with_fallback,
    load_customer_configs,
)


def test_config_env_var_name():
    """CONFIG_ENV_VAR_NAME is the env var used to override config path."""
    assert CONFIG_ENV_VAR_NAME == "COGNITE_AUTH_CONFIG_PATH"


def test_customer_configs_is_dict():
    """CUSTOMER_CONFIGS is a non-empty dict of customer configs."""
    assert isinstance(CUSTOMER_CONFIGS, dict)
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


def test_load_customer_configs_uses_env_var_when_set(tmp_path):
    """load_customer_configs uses CONFIG_ENV_VAR_NAME when set."""
    custom_config = {"env_customer": {"tenant_id": "t", "client_id": "c", "cdf_cluster": "cluster", "cognite_project": "proj"}}
    config_file = tmp_path / "custom_config.json"
    config_file.write_text(json.dumps(custom_config), encoding="utf-8")
    with patch.dict("os.environ", {CONFIG_ENV_VAR_NAME: str(config_file)}, clear=False):
        configs = load_customer_configs()
    assert configs == custom_config


def test_load_customer_configs_raises_when_missing():
    """load_customer_configs raises FileNotFoundError and message mentions CONFIG_ENV_VAR_NAME."""
    with patch.dict("os.environ", {CONFIG_ENV_VAR_NAME: "/nonexistent/auth_config.json"}, clear=False):
        with pytest.raises(FileNotFoundError) as exc_info:
            load_customer_configs()
    assert CONFIG_ENV_VAR_NAME in str(exc_info.value)


def test_client_with_fallback_never_raises_none():
    """Regression: when both auth methods fail, we never raise None (invalid)."""
    customer = next(iter(CUSTOMER_CONFIGS))
    with patch("cognite_auth.device_code_client", side_effect=RuntimeError("device failed")):
        with patch("cognite_auth.interactive_client", side_effect=ValueError("interactive failed")):
            with pytest.raises((RuntimeError, ValueError)) as exc_info:
                client_with_fallback(customer, token_cache_path=None)
    assert exc_info.value is not None
    assert isinstance(exc_info.value, BaseException)
