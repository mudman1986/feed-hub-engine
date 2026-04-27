#!/usr/bin/env python3
"""Tests for update-preview-manifest.py"""

import importlib.util
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

# pylint: disable=missing-function-docstring,too-few-public-methods
# pylint: disable=too-many-arguments,too-many-positional-arguments

MANIFEST_FILENAME = "manifest.json"

# Load the script as a module without executing its __main__ block
SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "workflows"
    / "update-preview-manifest.py"
)
spec = importlib.util.spec_from_file_location(
    "update_preview_manifest", str(SCRIPT_PATH)
)
if spec is None or spec.loader is None:
    raise ImportError(f"Unable to load module spec for {SCRIPT_PATH}")
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)
update_manifest = _module.update_manifest
main = _module.main


def _run(
    manifest_json: str,
    branch: str,
    slug: str,
    url: str,
    tmp_path: str,
    active_branches: set[str] | None = None,
    preview_dir: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Helper: call update_manifest and return (returned dict, written dict)."""
    manifest_file = str(Path(tmp_path) / MANIFEST_FILENAME)
    result = update_manifest(
        manifest_json,
        branch,
        slug,
        url,
        manifest_file,
        active_branches,
        preview_dir,
    )
    with open(manifest_file, encoding="utf-8") as f:
        written = json.load(f)
    return result, written


class TestUpdateManifestFreshStart:
    """Tests for creating a preview manifest from empty or invalid input."""

    def test_creates_entry_from_empty_manifest(self, tmp_path):
        _, written = _run(
            '{"previews":[]}',
            "feature/foo",
            "feature--foo",
            "https://example.com/preview/feature--foo",
            str(tmp_path),
        )
        assert len(written["previews"]) == 1
        entry = written["previews"][0]
        assert entry["branch"] == "feature/foo"
        assert entry["slug"] == "feature--foo"
        assert entry["url"] == "https://example.com/preview/feature--foo/"

    def test_creates_entry_when_manifest_key_missing(self, tmp_path):
        _, written = _run(
            "{}",
            "main-preview",
            "main-preview",
            "https://example.com/preview/main-preview",
            str(tmp_path),
        )
        assert len(written["previews"]) == 1

    def test_invalid_json_falls_back_to_fresh(self, tmp_path):
        _, written = _run(
            "NOT VALID JSON",
            "branch",
            "branch",
            "https://example.com/preview/branch",
            str(tmp_path),
        )
        assert len(written["previews"]) == 1


class TestUpdateManifestUpdate:
    """Tests for updating and deduplicating preview entries."""

    def test_updates_existing_slug(self, tmp_path):
        existing = json.dumps(
            {
                "previews": [
                    {
                        "branch": "feature/foo",
                        "slug": "feature--foo",
                        "url": "https://example.com/preview/feature--foo/",
                        "updated_at": "2026-01-01T00:00:00Z",
                    }
                ]
            }
        )
        _, written = _run(
            existing,
            "feature/foo",
            "feature--foo",
            "https://example.com/preview/feature--foo",
            str(tmp_path),
        )
        # Still only one entry for this slug
        assert len(written["previews"]) == 1
        # URL stays correct
        assert (
            written["previews"][0]["url"] == "https://example.com/preview/feature--foo/"
        )

    def test_adds_new_slug_without_removing_others(self, tmp_path):
        existing = json.dumps(
            {
                "previews": [
                    {
                        "branch": "feature/bar",
                        "slug": "feature--bar",
                        "url": "https://example.com/preview/feature--bar/",
                        "updated_at": "2026-01-01T00:00:00Z",
                    }
                ]
            }
        )
        _, written = _run(
            existing,
            "feature/foo",
            "feature--foo",
            "https://example.com/preview/feature--foo",
            str(tmp_path),
        )
        slugs = {p["slug"] for p in written["previews"]}
        assert "feature--bar" in slugs
        assert "feature--foo" in slugs

    def test_only_one_entry_per_slug_after_update(self, tmp_path):
        existing = json.dumps(
            {
                "previews": [
                    {
                        "branch": "feature/foo",
                        "slug": "feature--foo",
                        "url": "old/",
                        "updated_at": "2026-01-01T00:00:00Z",
                    },
                    {
                        "branch": "feature/foo",
                        "slug": "feature--foo",
                        "url": "duplicate/",
                        "updated_at": "2026-01-02T00:00:00Z",
                    },
                ]
            }
        )
        _, written = _run(
            existing,
            "feature/foo",
            "feature--foo",
            "https://example.com/preview/feature--foo",
            str(tmp_path),
        )
        foo_entries = [p for p in written["previews"] if p["slug"] == "feature--foo"]
        assert len(foo_entries) == 1


class TestUpdateManifestSorting:
    """Tests for preview ordering by newest update timestamp."""

    def test_most_recently_updated_is_first(self, tmp_path):
        existing = json.dumps(
            {
                "previews": [
                    {
                        "branch": "old-branch",
                        "slug": "old-branch",
                        "url": "https://example.com/preview/old-branch/",
                        "updated_at": "2026-01-01T00:00:00Z",
                    }
                ]
            }
        )
        _, written = _run(
            existing,
            "new-branch",
            "new-branch",
            "https://example.com/preview/new-branch",
            str(tmp_path),
        )
        # The freshly added entry has a newer timestamp so should be first
        assert written["previews"][0]["slug"] == "new-branch"


class TestUpdateManifestPruning:
    """Tests for pruning previews that no longer map to active branches."""

    def test_prunes_previews_for_removed_branches(self, tmp_path):
        existing = json.dumps(
            {
                "previews": [
                    {
                        "branch": "feature/stale",
                        "slug": "feature--stale",
                        "url": "https://example.com/preview/feature--stale/",
                        "updated_at": "2026-01-01T00:00:00Z",
                    },
                    {
                        "branch": "feature/live",
                        "slug": "feature--live",
                        "url": "https://example.com/preview/feature--live/",
                        "updated_at": "2026-01-02T00:00:00Z",
                    },
                ]
            }
        )
        _, written = _run(
            existing,
            "feature/live",
            "",
            "https://example.com",
            str(tmp_path),
            {"feature/live", "main"},
        )
        assert [preview["slug"] for preview in written["previews"]] == ["feature--live"]

    def test_main_build_prunes_without_adding_new_preview(self, tmp_path):
        existing = json.dumps(
            {
                "previews": [
                    {
                        "branch": "feature/live",
                        "slug": "feature--live",
                        "url": "https://example.com/preview/feature--live/",
                        "updated_at": "2026-01-02T00:00:00Z",
                    }
                ]
            }
        )
        _, written = _run(
            existing,
            "main",
            "",
            "https://example.com",
            str(tmp_path),
            {"main"},
        )
        assert written["previews"] == []

    def test_prunes_preview_directories_missing_from_manifest(self, tmp_path):
        preview_dir = Path(tmp_path) / "preview"
        (preview_dir / "active").mkdir(parents=True)
        (preview_dir / "stale").mkdir(parents=True)

        _, written = _run(
            json.dumps(
                {
                    "previews": [
                        {
                            "branch": "feature/active",
                            "slug": "active",
                            "url": "https://example.com/preview/active/",
                            "updated_at": "2026-01-02T00:00:00Z",
                        }
                    ]
                }
            ),
            "main",
            "",
            "https://example.com",
            str(tmp_path),
            {"feature/active", "main"},
            str(preview_dir),
        )

        assert [preview["slug"] for preview in written["previews"]] == ["active"]
        assert (preview_dir / "active").exists()
        assert not (preview_dir / "stale").exists()

    def test_invalid_manifest_does_not_prune_preview_directories(self, tmp_path):
        preview_dir = Path(tmp_path) / "preview"
        (preview_dir / "feature--live").mkdir(parents=True)
        (preview_dir / "feature--stale").mkdir(parents=True)

        _, written = _run(
            "NOT VALID JSON",
            "feature/live",
            "feature--live",
            "https://example.com/preview/feature--live",
            str(tmp_path),
            {"feature/live", "main"},
            str(preview_dir),
        )

        assert [preview["slug"] for preview in written["previews"]] == ["feature--live"]
        assert (preview_dir / "feature--live").exists()
        assert (preview_dir / "feature--stale").exists()


class TestUpdateManifestFileOutput:
    """Tests for manifest file creation and serialized output."""

    def test_written_file_ends_with_newline(self, tmp_path):
        manifest_file = os.path.join(str(tmp_path), MANIFEST_FILENAME)
        update_manifest(
            '{"previews":[]}',
            "branch",
            "branch",
            "https://example.com/preview/branch",
            manifest_file,
        )
        with open(manifest_file, encoding="utf-8") as f:
            content = f.read()
        assert content.endswith("\n")

    def test_written_file_is_valid_json(self, tmp_path):
        manifest_file = os.path.join(str(tmp_path), MANIFEST_FILENAME)
        update_manifest(
            '{"previews":[]}',
            "branch",
            "branch",
            "https://example.com/preview/branch",
            manifest_file,
        )
        with open(manifest_file, encoding="utf-8") as f:
            parsed = json.load(f)
        assert "previews" in parsed

    def test_creates_parent_directories(self, tmp_path):
        deep_path = os.path.join(str(tmp_path), "a", "b", "c", MANIFEST_FILENAME)
        update_manifest(
            '{"previews":[]}',
            "branch",
            "branch",
            "https://example.com/preview/branch",
            deep_path,
        )
        assert os.path.exists(deep_path)


class TestUpdateManifestMainEntryPoint:
    """Tests for the main() entry point function."""

    def test_main_creates_manifest_from_environment(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        env = {
            "SOURCE_BRANCH": "feature/test",
            "PREVIEW_SLUG": "feature--test",
            "BASE_URL": "https://example.com/preview/feature--test",
            "MANIFEST": '{"previews":[]}',
            "ACTIVE_BRANCHES": "feature/test\nmain",
        }
        with patch.dict(os.environ, env, clear=False):
            main()

        manifest_file = tmp_path / "site" / "preview" / MANIFEST_FILENAME
        assert manifest_file.exists()
        written = json.loads(manifest_file.read_text(encoding="utf-8"))
        assert any(p["slug"] == "feature--test" for p in written["previews"])

    def test_main_prints_entry_count(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        env = {
            "SOURCE_BRANCH": "main",
            "PREVIEW_SLUG": "",
            "BASE_URL": "https://example.com",
            "MANIFEST": '{"previews":[]}',
            "ACTIVE_BRANCHES": "main",
        }
        with patch.dict(os.environ, env, clear=False):
            main()

        captured = capsys.readouterr()
        assert "Preview manifest updated" in captured.err
