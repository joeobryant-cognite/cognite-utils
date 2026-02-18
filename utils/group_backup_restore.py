"""
Backup and restore CDF group permissions (capabilities).
Backups are stored as Excel (same format as groups_by_customer.xlsx) plus JSON (full capability data for restore).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from cognite_groups_export import (
    build_customer_dataframe,
    collect_all_capabilities,
    write_groups_to_excel,
)

# Default archive directory: project repo root / groups / archive
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ARCHIVE_DIR = _PROJECT_ROOT / "groups" / "archive"


def _timestamp() -> str:
    """Return timestamp for filenames: YYYY-MM-DD_HH-MM-SS."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def backup_groups_to_archive(
    groups_by_customer: dict[str, list],
    archive_dir: Path | str | None = None,
) -> tuple[Path, Path]:
    """
    Save current groups to the archive: one Excel (same format as groups_by_customer.xlsx) and one JSON (for restore).
    groups_by_customer: {customer_name: list of Group objects}
    archive_dir: where to write files (default: DEFAULT_ARCHIVE_DIR).
    Returns (excel_path, json_path).
    """
    archive_path = Path(archive_dir) if archive_dir else DEFAULT_ARCHIVE_DIR
    archive_path.mkdir(parents=True, exist_ok=True)
    ts = _timestamp()
    excel_path = archive_path / f"groups_backup_{ts}.xlsx"
    json_path = archive_path / f"groups_backup_{ts}.json"

    all_capabilities = collect_all_capabilities(groups_by_customer)
    dataframes_by_customer = {}
    backup_data = {}
    for customer_name, groups in groups_by_customer.items():
        if groups is None:
            dataframes_by_customer[customer_name] = None
            backup_data[customer_name] = []
            continue
        dataframes_by_customer[customer_name] = build_customer_dataframe(groups, all_capabilities)
        backup_data[customer_name] = [
            {
                "id": g.id,
                "name": getattr(g, "name", ""),
                "capabilities": [c.dump(camel_case=True) for c in (getattr(g, "capabilities") or [])],
            }
            for g in groups
        ]
    write_groups_to_excel(dataframes_by_customer, excel_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2)

    print(f"✅ Backup saved: {excel_path.name} and {json_path.name}")
    return excel_path, json_path


def list_backups(archive_dir: Path | str | None = None) -> list[tuple[Path, Path, str]]:
    """
    List backup pairs (excel_path, json_path, timestamp) in archive_dir, newest first.
    """
    archive_path = Path(archive_dir) if archive_dir else DEFAULT_ARCHIVE_DIR
    if not archive_path.exists():
        return []
    pairs = []
    for json_path in sorted(archive_path.glob("groups_backup_*.json"), reverse=True):
        # groups_backup_2026-02-18_14-30-00.json
        stem = json_path.stem  # groups_backup_2026-02-18_14-30-00
        ts = stem.replace("groups_backup_", "") if stem.startswith("groups_backup_") else ""
        excel_path = json_path.with_suffix(".xlsx")
        if excel_path.exists():
            pairs.append((excel_path, json_path, ts))
    return pairs


def load_backup_json(json_path: Path | str) -> dict:
    """
    Load a backup JSON file. Returns {customer_name: [{"id", "name", "capabilities": [dict, ...]}, ...]}.
    """
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def restore_groups_from_backup(client, backup_data: dict, dry_run: bool = True):
    """
    Restore each group's capabilities from backup_data (as returned by load_backup_json).
    Uses Capability.load() to reconstruct capability objects, then update_group_capabilities.
    client: CogniteClient
    dry_run: if True, only print what would be restored.
    """
    from cognite.client.data_classes.capabilities import Capability
    from remove_capabilities import update_group_capabilities

    for customer_name, groups_data in backup_data.items():
        for gd in groups_data:
            gid = gd["id"]
            name = gd.get("name", "")
            cap_dicts = gd.get("capabilities", [])
            try:
                caps = [Capability.load(c, allow_unknown=True) for c in cap_dicts]
            except Exception as e:
                print(f"  Skip group {name!r} (id={gid}): failed to load capabilities: {e}")
                continue
            if dry_run:
                print(f"  [dry run] Would restore {len(caps)} capabilities to group {name!r} (id={gid})")
                continue
            group_placeholder = SimpleNamespace(id=gid)
            try:
                update_group_capabilities(client, group_placeholder, caps)
                print(f"  Restored {len(caps)} capabilities to group {name!r} (id={gid})")
            except Exception as e:
                print(f"  Error restoring group {name!r} (id={gid}): {e}")
