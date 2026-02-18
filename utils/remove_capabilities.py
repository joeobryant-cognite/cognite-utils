"""
Helpers for removing capabilities from CDF IAM groups.
Used by the Remove_Capabilities.ipynb playbook.
"""
from __future__ import annotations

# Legacy entity resource names: capabilities for these resources can be removed in bulk.
LEGACY_RESOURCE_NAMES = [
    "assets",
    "timeseries",
    "events",
    "files",
    "sequences",
    "raw",
    "data_sets",
    "spaces",
    "containers",
    "datapoints",
    "three_d",
    "three_d_models",
    "documents",
]


def capability_keys_to_remove(
    *,
    legacy_resources: bool = False,
    specific_keys: list[str] | None = None,
    legacy_list: list[str] | None = None,
) -> set[str]:
    """
    Build the set of capability keys that should be removed.
    A capability key is in resource:action or resource:action:scope format.
    """
    to_remove = set()
    if specific_keys:
        to_remove.update(k.strip() for k in specific_keys if k.strip())
    if legacy_resources:
        legacy = legacy_list or LEGACY_RESOURCE_NAMES
        # We'll match any key that starts with one of these resources (e.g. "assets:read", "timeseries:write:...")
        for res in legacy:
            res_lower = res.lower().strip()
            to_remove.add(res_lower)  # so we can match "resource:" prefix
    return to_remove


def should_remove_capability_key(key: str, to_remove: set[str], legacy_resources: bool) -> bool:
    """Return True if this capability key should be removed."""
    key_lower = key.lower()
    # Exact match (e.g. specific key "assets:write")
    if key_lower in to_remove:
        return True
    # Legacy: to_remove contains resource names without ":" (e.g. "assets"); match "resource:action"
    if legacy_resources:
        for r in to_remove:
            if ":" not in r and key_lower.startswith(r + ":"):
                return True
    return False


def filter_capabilities_for_removal(group, to_remove: set[str], legacy_resources: bool, extract_key_fn):
    """
    Return a new list of capability objects for the group, excluding any whose key(s) are in to_remove
    or (if legacy_resources) whose resource is in the legacy set.
    extract_key_fn(cap) returns str | list[str] | None (same as cognite_groups_export.extract_capability_key).
    """
    if not getattr(group, "capabilities", None):
        return []
    keep = []
    for cap in group.capabilities:
        keys = extract_key_fn(cap)
        if keys is None:
            keep.append(cap)
            continue
        key_list = [keys] if isinstance(keys, str) else keys
        if not any(should_remove_capability_key(k, to_remove, legacy_resources) for k in key_list):
            keep.append(cap)
    return keep


def update_group_capabilities(client, group, new_capabilities: list) -> dict:
    """
    Call CDF API to update a group's capabilities.
    client: CogniteClient
    group: Group with .id
    new_capabilities: list of Capability objects (will be dumped to API format).
    Returns the API response (or raises).
    """
    payload = [
        {
            "id": group.id,
            "update": {
                "capabilities": {
                    "set": [c.dump(camel_case=True) for c in new_capabilities],
                }
            },
        }
    ]
    res = client.iam.groups._post(url_path=client.iam.groups._RESOURCE_PATH + "/update", json={"items": payload})
    res.raise_for_status()
    return res.json()
