# Feed Hub Engine Documentation

This directory stores project documentation only.

## Planning Documents

- [GitHub Pages as a Service Plan](GITHUB_PAGES_AS_A_SERVICE_PLAN.md)

## Site Layout

The live site is now generated outside this directory:

```text
src/site/                         # authored site assets
scripts/workflows/rss-processing/ # site/RSS generation scripts
site/                             # generated site output for publishing/tests
config/site-metadata.json         # site branding configuration
config/rss-feeds.json             # feed configuration
```

## Site Publishing

The RSS publishing workflow generates the deployable site into `site/` and
publishes previews under `site/preview/<preview-slug>/`.

## Starter Consumer Repositories

Copy-ready consumer repository starters live outside `docs/` in:

```text
starter-sites/example-feed-hub/
```

## Live Site

```text
https://mudman1986.github.io/feed-hub-engine/
```
