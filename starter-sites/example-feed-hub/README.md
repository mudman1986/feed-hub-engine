# Example Feed Hub Starter

Copy the contents of this folder into a new repository to bootstrap a
generic feed hub site that uses the shared Pages workflow from:

```text
mudman1986/feed-hub-engine/.github/workflows/publish-pages.yml@v2.0.0
```

## Included Files

```text
.github/workflows/publish.yml
config/site-metadata.json
config/rss-feeds.json
README.md
```

## Setup

1. Create a new GitHub repository for your feed hub site.
2. Copy the full contents of this folder into the new repository root.
3. Review and update:
   - `config/site-metadata.json`
   - `config/rss-feeds.json`
4. Enable GitHub Pages for the repository.
5. Push to the default branch or run the workflow manually.

The pinned workflow tag in this starter is updated in the repository before a
new upstream release is published, so the committed starter contents match the
tagged release. The workflow `uses:` reference and `engine-ref` input stay
aligned to that same release tag.

## What To Customize

### Site branding

Update `config/site-metadata.json` to change:

- site name
- header title
- page description
- RSS title and description

### Feed sources

Update `config/rss-feeds.json` to add, remove, or replace feeds for your topic.

Each entry supports:

```json
{
  "name": "Feed name",
  "url": "https://example.com/rss.xml",
  "website_url": "https://example.com/"
}
```

## Upgrade Path

This starter pins the shared workflow to the release reference shown in
`.github/workflows/publish.yml`.

When a newer release is available:

1. Review the upstream release notes.
2. Update `.github/workflows/publish.yml` so both the `uses:` reference and the
   `engine-ref` input point to the new stable tag (for example `v2.0.1`).
3. Commit and push the workflow change.

## Notes

- The shared engine repository owns the HTML, CSS, JavaScript, tests, and
  deployment logic.
- Consumer repositories should stay configuration-only whenever possible.
