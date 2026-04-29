#!/usr/bin/env python3
"""Tests for merge-pages-content.py."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "workflows"
    / "merge-pages-content.py"
)
spec = importlib.util.spec_from_file_location("merge_pages_content", str(SCRIPT_PATH))
if spec is None or spec.loader is None:
    raise ImportError(f"Unable to load module spec for {SCRIPT_PATH}")
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)
merge_pages_content = _module.merge_pages_content
validate_deploy_subdir = _module.validate_deploy_subdir
remove_directory_contents = _module.remove_directory_contents
main = _module.main


def write_file(path: Path, content: str) -> None:
    """Write a file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_validate_deploy_subdir_rejects_parent_segments() -> None:
    """Reject deploy subdirectories that traverse upward."""
    with pytest.raises(ValueError, match="parent path segments"):
        validate_deploy_subdir("../preview")


def test_validate_deploy_subdir_rejects_absolute_path() -> None:
    """Reject absolute deploy subdirectory paths."""
    with pytest.raises(ValueError, match="must be relative"):
        validate_deploy_subdir("/absolute/path")


def test_validate_deploy_subdir_accepts_empty_string() -> None:
    """Empty string resolves to an empty Path."""
    assert validate_deploy_subdir("") == Path()


def test_validate_deploy_subdir_accepts_dot() -> None:
    """Dot resolves to an empty Path."""
    assert validate_deploy_subdir(".") == Path()


def test_remove_directory_contents_noop_when_directory_missing(tmp_path: Path) -> None:
    """Should silently return when directory does not exist."""
    missing = tmp_path / "nonexistent"
    remove_directory_contents(missing)  # must not raise


def test_remove_directory_contents_removes_subdirectories(tmp_path: Path) -> None:
    """Should remove nested subdirectories from the target directory."""
    subdir = tmp_path / "nested" / "deep"
    subdir.mkdir(parents=True)
    (tmp_path / "file.txt").write_text("data", encoding="utf-8")

    remove_directory_contents(tmp_path)

    assert not (tmp_path / "nested").exists()
    assert not (tmp_path / "file.txt").exists()


def test_remove_directory_contents_preserves_named_entries(tmp_path: Path) -> None:
    """Should preserve entries whose names appear in preserve_names."""
    keep_dir = tmp_path / "keep"
    keep_dir.mkdir()
    (keep_dir / "index.html").write_text("keep", encoding="utf-8")
    (tmp_path / "remove.html").write_text("remove", encoding="utf-8")

    remove_directory_contents(tmp_path, preserve_names={"keep"})

    assert keep_dir.exists()
    assert not (tmp_path / "remove.html").exists()


def test_merge_pages_content_raises_when_build_dir_missing(tmp_path: Path) -> None:
    """Raise ValueError when the build directory does not exist."""
    build_dir = tmp_path / "nonexistent_build"
    output_dir = tmp_path / "site"

    with pytest.raises(ValueError, match="does not exist"):
        merge_pages_content(str(build_dir), str(output_dir))


def test_main_merges_build_into_output(tmp_path: Path) -> None:
    """main() should copy build files into the output directory."""
    build_dir = tmp_path / "build"
    output_dir = tmp_path / "site"
    build_dir.mkdir()
    (build_dir / "index.html").write_text("built", encoding="utf-8")

    cli_args = [
        "merge-pages-content.py",
        "--build-dir",
        str(build_dir),
        "--output-dir",
        str(output_dir),
    ]
    with patch.object(sys, "argv", cli_args):
        main()

    assert (output_dir / "index.html").read_text(encoding="utf-8") == "built"


def test_merge_root_build_preserves_existing_previews(tmp_path: Path) -> None:
    """Keep existing previews while replacing production files."""
    existing_dir = tmp_path / "existing"
    build_dir = tmp_path / "build"
    output_dir = tmp_path / "site"

    write_file(existing_dir / "index.html", "production v1")
    write_file(existing_dir / "old.html", "remove me")
    write_file(existing_dir / "preview" / "feature-a" / "index.html", "preview")
    write_file(
        existing_dir / "preview" / "manifest.json",
        '{"previews":[{"slug":"feature-a"}]}\n',
    )
    write_file(build_dir / "index.html", "production v2")
    write_file(build_dir / "summary.html", "summary")

    merge_pages_content(str(build_dir), str(output_dir), existing_dir=str(existing_dir))

    assert (output_dir / "index.html").read_text(encoding="utf-8") == "production v2"
    assert (output_dir / "summary.html").read_text(encoding="utf-8") == "summary"
    assert not (output_dir / "old.html").exists()
    assert (output_dir / "preview" / "feature-a" / "index.html").read_text(
        encoding="utf-8"
    ) == "preview"


def test_merge_preview_build_preserves_production_site(tmp_path: Path) -> None:
    """Keep production content when updating one preview directory."""
    existing_dir = tmp_path / "existing"
    build_dir = tmp_path / "build"
    output_dir = tmp_path / "site"

    write_file(existing_dir / "index.html", "production")
    write_file(existing_dir / "summary.html", "summary")
    write_file(existing_dir / "preview" / "feature-a" / "old.html", "stale")
    write_file(build_dir / "index.html", "preview")

    merge_pages_content(
        str(build_dir),
        str(output_dir),
        deploy_subdir="preview/feature-a",
        existing_dir=str(existing_dir),
    )

    assert (output_dir / "index.html").read_text(encoding="utf-8") == "production"
    assert (output_dir / "summary.html").read_text(encoding="utf-8") == "summary"
    assert (output_dir / "preview" / "feature-a" / "index.html").read_text(
        encoding="utf-8"
    ) == "preview"
    assert not (output_dir / "preview" / "feature-a" / "old.html").exists()


def test_merge_preview_build_creates_nested_directory(tmp_path: Path) -> None:
    """Create nested preview directories when no prior state exists."""
    build_dir = tmp_path / "build"
    output_dir = tmp_path / "site"

    write_file(build_dir / "index.html", "preview")

    merge_pages_content(
        str(build_dir),
        str(output_dir),
        deploy_subdir="preview/feature-branch",
    )

    assert (output_dir / "preview" / "feature-branch" / "index.html").read_text(
        encoding="utf-8"
    ) == "preview"


def test_merge_pages_content_replaces_existing_output_dir(tmp_path: Path) -> None:
    """Remove and recreate the output directory if it already exists."""
    build_dir = tmp_path / "build"
    output_dir = tmp_path / "site"

    write_file(build_dir / "new.html", "new content")
    write_file(output_dir / "old.html", "stale content")  # pre-existing output

    merge_pages_content(str(build_dir), str(output_dir))

    assert (output_dir / "new.html").read_text(encoding="utf-8") == "new content"
    assert not (output_dir / "old.html").exists()
