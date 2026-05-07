#!/usr/bin/env python3
"""Update the preview/manifest.json with the latest preview deployment entry."""

# pylint: disable=invalid-name
# pylint: disable=too-many-arguments,too-many-positional-arguments

import json
import os
import shutil
import sys
from datetime import datetime, timezone


def update_manifest(
    manifest_json: str,
    source_branch: str,
    preview_slug: str,
    base_url: str,
    manifest_path: str,
    active_branches: set[str] | None = None,
    preview_dir: str | None = None,
) -> dict:
    """Merge a preview entry into the manifest and write it to disk.

    Args:
        manifest_json: JSON string of the existing manifest (or ``{}``)
        source_branch: Name of the source branch
        preview_slug: URL-safe slug derived from the branch name
        base_url: Base URL for the preview deployment (without trailing slash)
        manifest_path: Filesystem path where the manifest will be written
        active_branches: Active branches whose preview entries should be retained
        preview_dir: Optional preview directory to prune against the manifest

    Returns:
        The updated manifest dict.
    """
    parsed_manifest = True
    try:
        manifest = json.loads(manifest_json)
    except json.JSONDecodeError as exc:
        parsed_manifest = False
        print(
            f"Warning: could not parse existing manifest ({exc}); starting fresh",
            file=sys.stderr,
        )
        manifest = {"previews": []}

    previews = manifest.get("previews", [])
    if not isinstance(previews, list):
        previews = []
    previews = [preview for preview in previews if isinstance(preview, dict)]

    if active_branches is not None:
        previews = [p for p in previews if p.get("branch") in active_branches]

    if preview_slug:
        # Remove any stale entry for this slug then add updated one
        previews = [p for p in previews if p.get("slug") != preview_slug]
        previews.append(
            {
                "branch": source_branch,
                "slug": preview_slug,
                "url": base_url.rstrip("/") + "/",
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    previews.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    manifest["previews"] = previews

    os.makedirs(os.path.dirname(os.path.abspath(manifest_path)), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    if preview_dir and parsed_manifest:
        preview_root = os.path.abspath(preview_dir)
        if os.path.isdir(preview_root):
            active_slugs = {
                preview.get("slug") for preview in previews if preview.get("slug")
            }
            for entry_name in os.listdir(preview_root):
                entry_path = os.path.join(preview_root, entry_name)
                if os.path.isdir(entry_path) and entry_name not in active_slugs:
                    shutil.rmtree(entry_path)

    return manifest


def main() -> None:
    """Entry point: reads configuration from environment variables."""
    manifest_path = os.path.join("site", "preview", "manifest.json")
    source_branch = os.environ["SOURCE_BRANCH"]
    preview_slug = os.environ.get("PREVIEW_SLUG", "")
    base_url = os.environ["BASE_URL"]
    manifest_json = os.environ.get("MANIFEST", '{"previews":[]}')
    active_branches = {
        branch
        for branch in os.environ.get("ACTIVE_BRANCHES", "").splitlines()
        if branch
    }
    preview_dir = os.path.dirname(manifest_path)

    manifest = update_manifest(
        manifest_json,
        source_branch,
        preview_slug,
        base_url,
        manifest_path,
        active_branches or None,
        preview_dir,
    )
    print(
        f"✓ Preview manifest updated ({len(manifest['previews'])} entries)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
