import json
import os
from pathlib import Path

from cognite.client import ClientConfig, CogniteClient
from cognite.client.credentials import OAuthDeviceCode, OAuthInteractive

CONFIG_ENV_VAR_NAME = "COGNITE_AUTH_CONFIG_PATH"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "cognite_auth_config.json"

_CLIENT_NAME = "Cognite Academy course taker"


def load_customer_configs() -> dict:
    config_path = Path(os.environ.get(CONFIG_ENV_VAR_NAME, str(DEFAULT_CONFIG_PATH)))
    if not config_path.exists():
        raise FileNotFoundError(
            f"Cognite auth config file not found. "
            f"Create {DEFAULT_CONFIG_PATH} or set {CONFIG_ENV_VAR_NAME}."
        )
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


CUSTOMER_CONFIGS = load_customer_configs()


def _base_url(config: dict) -> str:
    """Build CDF base URL from customer config."""
    return f"https://{config['cdf_cluster']}.cognitedata.com"


def _create_client(config: dict, credentials) -> CogniteClient:
    """Build CogniteClient from config and credentials (SRP: single place for ClientConfig)."""
    return CogniteClient(
        ClientConfig(
            client_name=_CLIENT_NAME,
            project=config["cognite_project"],
            base_url=_base_url(config),
            credentials=credentials,
        )
    )


def _get_config_and_cache(customer, token_cache_path):
    """Validate customer and return (config, cache_path)."""
    if customer not in CUSTOMER_CONFIGS:
        raise ValueError(
            f"Customer '{customer}' not found. Available customers: {list(CUSTOMER_CONFIGS.keys())}"
        )
    config = CUSTOMER_CONFIGS[customer]
    cache_path = token_cache_path or None
    if cache_path:
        if not isinstance(cache_path, Path):
            cache_path = Path(cache_path)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
    return config, cache_path


def interactive_client(customer, token_cache_path=None, redirect_port=53000):
    """
    Instantiate CogniteClient using the interactive (browser) OAuth flow.
    Requires a free local redirect port (default 53000). On WSL, port 53000
    is often taken by wslrelay.exe; use device_code_client() instead if you
    cannot change the app registration redirect URIs.
    """
    config, cache_path = _get_config_and_cache(customer, token_cache_path)
    base_url = _base_url(config)
    credentials = OAuthInteractive(
        authority_url=f"https://login.microsoftonline.com/{config['tenant_id']}",
        client_id=config["client_id"],
        scopes=[f"{base_url}/.default"],
        redirect_port=redirect_port,
        token_cache_path=cache_path,
    )
    return _create_client(config, credentials)


def device_code_client(customer, token_cache_path=None):
    """
    Instantiate CogniteClient using the device-code OAuth flow. No local port
    is used: you get a code and URL, open the URL in a browser, enter the code,
    then the client continues. Use this when the interactive redirect port
    (53000) is in use (e.g. by wslrelay.exe) and you cannot add other redirect
    URIs to the app registration.
    """
    config, cache_path = _get_config_and_cache(customer, token_cache_path)
    credentials = OAuthDeviceCode.default_for_azure_ad(
        tenant_id=config["tenant_id"],
        client_id=config["client_id"],
        cdf_cluster=config["cdf_cluster"],
        token_cache_path=cache_path,
    )
    return _create_client(config, credentials)


def client_with_fallback(customer, token_cache_path=None, *, verbose=False):
    """
    Try device-code auth first, then interactive. Returns a CogniteClient.
    Never raises None: if both methods fail, raises the last exception or
    RuntimeError("Authentication failed"). Use in notebooks to avoid
    invalid "raise last_exc" when last_exc can be None.
    """
    last_exc = None
    for use_device_code in (True, False):
        try:
            if use_device_code:
                return device_code_client(customer, token_cache_path)
            return interactive_client(customer, token_cache_path)
        except Exception as e:
            last_exc = e
            if verbose and use_device_code:
                print(f"Device-code failed ({e}), trying interactive...")
            continue
    raise last_exc if last_exc is not None else RuntimeError("Authentication failed")
