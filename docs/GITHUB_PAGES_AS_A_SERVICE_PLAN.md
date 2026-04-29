# GitHub Pages as a Service Plan

## Goal

Make this repository the reusable source of truth for the feed hub engine so a second site can be created in a new repository with only:

- a site metadata file (title, description, branding)
- an RSS feed list
- a tiny workflow that pins a released version of the shared engine

That keeps the site behavior, UI, tests, and deployment logic in one place and avoids copying the full repository for every new audience.

## Current Reusable Building Blocks

The repository already has most of the pieces needed for a shared platform:

- `scripts/workflows/rss-processing/generate_summary.py` generates the HTML pages.
- `scripts/workflows/rss-processing/generate_rss.py` generates the RSS output.
- `scripts/workflows/rss-processing/template.html` and `src/site/` contain the shared site shell.
- `.github/workflows/publish-pages.yml` now exposes the shared Pages pipeline as a reusable `workflow_call` workflow.
- `.github/workflows/rss-github-page.yml` now acts as a thin caller for the shared publish workflow.
- `config/rss-feeds.json` is already configuration driven for the feed sources.
- `config/site-metadata.json` now drives site branding and RSS metadata.
- `starter-sites/example-feed-hub/` now contains a copyable consumer repository starter for a generic example site.
- `.github/workflows/create-release.yml` now creates releases from the
  committed tag metadata in `config/release.json`.
- `.github/workflows/create-release.yml` now also packages and uploads the starter bundle to tagged GitHub Releases.

## Actual Status

### Phase 1 status: Parameterize branding in this repository

✅ Complete

Branding is now config driven via `config/site-metadata.json`, and the
shared generators/templates read those values instead of hardcoding the
DevOps Feed Hub identity.

### Phase 2 status: Extract a reusable workflow

✅ Complete

The shared Pages workflow now lives in:

```text
.github/workflows/publish-pages.yml
```

The repository's own publish workflow consumes it internally, which keeps
the upstream repository on the same execution path as future consumer
repositories.

### Phase 3 status: Release and document the template

✅ Implemented in the repository

- Release creation and starter bundle publishing workflow:

  ```text
  .github/workflows/create-release.yml
  ```

- Automated release creation workflow:

  ```text
  .github/workflows/create-release.yml
  ```

- Copyable starter template:

  ```text
  starter-sites/example-feed-hub/
  ```

- Consumer upgrade guidance:
  - documented in `starter-sites/example-feed-hub/README.md`
  - documented below in this plan

The remaining operational step is to run the automated release workflow for the
first stable release tag (for example `v1.0.0`). That workflow updates the
starter template pin, creates the Git tag, publishes the GitHub Release, and
uploads the starter bundle asset in the same workflow.

### Phase 4 status: Create the second site from the template

✅ Complete inside this repository

The generic example starter site now exists as a full copyable folder that
contains the exact repository structure expected for a new consumer repository:

```text
starter-sites/example-feed-hub/
├── .github/workflows/publish.yml
├── config/site-metadata.json
├── config/rss-feeds.json
└── README.md
```

Copying that folder into a new repository gives a minimal example
consumer site that only customizes config and pins the shared workflow by
release tag.

## Recommended Scalable Model

### 1. Keep this repository as the upstream "site engine"

This repository should own:

- shared HTML/CSS/JS assets
- RSS and HTML generation scripts
- Playwright/Jest/Python tests
- the reusable GitHub Actions workflow used to publish a site
- versioned releases for consumers

### 2. Add a small site metadata config

Introduce a config file such as `config/site-metadata.json` with fields like:

```json
{
  "site_name": "DevOps Feed Hub",
  "site_description": "Centralized RSS feed aggregator for DevOps and tech news",
  "header_title": "DevOps Feed Hub",
  "rss_title": "DevOps Feed Hub - All Articles",
  "rss_description": "Aggregated DevOps, cloud, and technology news from multiple sources"
}
```

Then update the generators and template to read branding from this file instead of hardcoded strings. That is the key refactor that makes the second site truly reusable.

### 3. Publish the engine as a versioned reusable workflow

Use a reusable workflow in this repository, published and consumed by tag:

- example consumer reference: `mudman1986/feed-hub-engine/.github/workflows/publish-pages.yml@v1`
- inputs: `site-metadata-path`, `feeds-config-path`, `python-version`, optional `base-path`
- secrets: only the standard `GITHUB_TOKEN`

This should be the primary distribution mechanism because it avoids duplicating the current Pages workflow in every new repository.

Current repository status:

- The reusable workflow exists at `.github/workflows/publish-pages.yml`.
- The committed release source of truth lives in `config/release.json`.
- The starter consumer workflow is updated in the feature branch so it already
  pins the upstream workflow to the tag that will be released after merge.
- `.github/workflows/create-release.yml` validates the committed release
  metadata, creates a Git tag from the pushed `main` commit, and publishes the
  GitHub Release without making commits on `main`.
- The release workflow also uploads the starter bundle from the tagged release
  contents.

### 4. Use GitHub Releases for bootstrap assets, not as the primary runtime

Each release should attach a small starter bundle that contains:

- sample `config/site-metadata.json`
- sample `config/rss-feeds.json`
- a minimal consumer workflow
- setup instructions

Releases are a good fit for versioned templates and examples. They are less useful than a reusable workflow for the ongoing build itself, because consumers would otherwise need to reimplement the workflow logic locally.

Current repository status:

- The starter bundle lives in `starter-sites/example-feed-hub/`.
- The release workflow validates that `starter-sites/example-feed-hub/` already
  matches the committed release tag before creating the release.
- The release workflow `.github/workflows/create-release.yml` packages that
  tagged folder as a `.tar.gz` archive and uploads it to the GitHub Release.

### 5. Treat GitHub Packages as optional

GitHub Packages only helps if the shared engine is split into an installable package. For this repository, the deployment workflow is the most valuable reusable unit, so Packages should be optional rather than the first step.

If packaging is desired later, the best candidate is a small Python package for the generators. That can happen after the reusable workflow is working.

## What a Consumer Repository Should Contain

A second site repository should stay very small:

```text
.github/workflows/publish.yml        # calls the reusable workflow by release tag
config/site-metadata.json            # title, description, branding
config/rss-feeds.json                # audience-specific feeds
README.md                            # repo-specific documentation
```

That exact structure is now available in:

```text
starter-sites/example-feed-hub/
```

That repository should not copy:

- `src/site/`
- `scripts/workflows/rss-processing/`
- Playwright/Jest/Python test suites
- Pages deployment logic

## Rollout Plan

### Phase 1: Parameterize branding in this repository

Update the shared engine so these values come from config instead of being hardcoded:

- page title and meta description in `template.html`
- header title in `template.html`
- Markdown summary title in `generate_summary.py`
- RSS feed titles and descriptions in `generate_rss.py`

### Phase 2: Extract a reusable workflow

Create a `workflow_call` workflow that:

- checks out the consumer repository
- reads the consumer config files
- runs the feed collector
- builds HTML and RSS with the shared scripts
- publishes to GitHub Pages

The existing `.github/workflows/rss-github-page.yml` can then call the same reusable workflow internally so the upstream repository uses the same path as consumers.

### Phase 3: Release and document the template

For each tagged release:

- publish the reusable workflow under a stable tag (`v1`, `v1.1`, etc.)
- attach the starter bundle to the GitHub Release
- document the upgrade path for consumer repos

Repository status:

- ✅ automated release creation workflow added
- ✅ starter template tag sync is automated during release creation
- ✅ starter bundle upload merged into the release workflow
- ✅ starter bundle documentation added
- ⏳ first automated stable release still needs to be run operationally

### Phase 4: Create the second site from the template

The second repository should prove the model by changing only:

- `config/site-metadata.json`
- `config/rss-feeds.json`
- the repository name / Pages URL

If more files are required, the shared layer is still too coupled.

Repository status:

- ✅ generic starter repository created in `starter-sites/example-feed-hub/`
- ✅ starter repository changes only config and workflow reference
- ✅ no shared engine code is duplicated into the consumer template

## Why This Scales to 5+ Sites

This approach scales because:

- UI, tests, and deployment logic stay centralized.
- Each site repository is mostly configuration.
- Fixes ship once in the upstream repository and are adopted by bumping a version tag.
- New sites avoid forks and large copy/paste drift.
- Release tags provide stable, auditable upgrades.

## Recommendation

Use this repository as a versioned upstream platform, with a reusable workflow as the main distribution mechanism and GitHub Releases as the bootstrap/template channel.

That gives the least duplication for a second site now and stays manageable if another five sites are added later.
