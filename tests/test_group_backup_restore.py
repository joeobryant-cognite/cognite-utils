"""Tests for group_backup_restore (no CDF client required)."""
import json
import re
from pathlib import Path

import pytest

from group_backup_restore import (
    DEFAULT_ARCHIVE_DIR,
    _timestamp,
    list_backups,
    load_backup_json,
)


def test_timestamp_format():
    """_timestamp() returns YYYY-MM-DD_HH-MM-SS."""
    ts = _timestamp()
    assert re.match(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$", ts), ts


def test_list_backups_empty_or_missing(tmp_path):
    """list_backups on empty or missing dir returns []."""
    assert list_backups(tmp_path) == []
    assert list_backups(tmp_path / "nonexistent") == []


def test_list_backups_finds_pairs(tmp_path):
    """list_backups finds matching .json/.xlsx pairs, newest first."""
    (tmp_path / "groups_backup_2026-01-01_12-00-00.json").write_text("{}")
    (tmp_path / "groups_backup_2026-01-01_12-00-00.xlsx").write_bytes(b"")
    (tmp_path / "groups_backup_2026-01-02_10-00-00.json").write_text("{}")
    (tmp_path / "groups_backup_2026-01-02_10-00-00.xlsx").write_bytes(b"")
    pairs = list_backups(tmp_path)
    assert len(pairs) == 2
    excel1, json1, ts1 = pairs[0]
    excel2, json2, ts2 = pairs[1]
    # Newest first
    assert "2026-01-02" in ts1
    assert "2026-01-01" in ts2
    assert json1.suffix == ".json" and excel1.suffix == ".xlsx"


def test_load_backup_json(tmp_path):
    """load_backup_json returns parsed JSON."""
    data = {"customer-a": [{"id": 1, "name": "G1", "capabilities": []}]}
    path = tmp_path / "backup.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load_backup_json(path) == data


def test_default_archive_dir_is_under_project():
    """DEFAULT_ARCHIVE_DIR is groups/archive under project root."""
    assert DEFAULT_ARCHIVE_DIR.name == "archive"
    assert DEFAULT_ARCHIVE_DIR.parent.name == "groups"
