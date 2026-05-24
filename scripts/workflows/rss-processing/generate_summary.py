#!/usr/bin/env python3
"""
Summary Generator for DevOps Feed Hub
Generates both markdown (for GitHub workflow summary) and HTML (for GitHub Pages)
"""

import argparse
import json
import os
import shutil
from html import escape as html_escape
from pathlib import Path
from typing import Any, Dict, Optional

from utils import (
    generate_feed_slug,
    load_site_metadata,
    parse_iso_timestamp,
    resolve_site_metadata,
)

STATIC_SITE_FILES = (
    "favicon-16x16.png",
    "favicon-192x192.png",
    "favicon-32x32.png",
    "favicon-48x48.png",
    "favicon.png",
    "favicon.svg",
    "script.js",
    "settings.html",
    "styles.css",
)


def get_repo_root() -> Path:
    """
    Resolve the repository root from this module location.

    Returns:
        Repository root path.

    Raises:
        FileNotFoundError: If the repository root cannot be determined.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise FileNotFoundError(
        "Could not determine repository root from generate_summary.py"
    )


def get_static_site_dir() -> Path:
    """
    Return the directory containing authored static site assets.

    Returns:
        Path to the static site asset directory.
    """
    return get_repo_root() / "src" / "site"


def get_template_path() -> Path:
    """
    Return the path to the HTML template file.

    Returns:
        Path to template.html.
    """
    return Path(__file__).resolve().with_name("template.html")


STATIC_SITE_DIR = get_static_site_dir()


def generate_markdown_summary(
    data: Dict[str, Any], site_metadata: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate markdown summary from RSS feed collection data

    Args:
        data: RSS feed collection data dictionary

    Returns:
        Markdown formatted string
    """
    metadata = resolve_site_metadata(site_metadata)
    summary = []
    summary.append(f"{metadata['summary_markdown_title']}\n")
    summary.append(f"**Collected at:** {data['metadata']['collected_at']}\n")
    hours = data["metadata"].get("hours", 24)
    summary.append(f"**Time range:** Last {hours} hours\n")
    summary.append(
        "**Note:** Web interface provides filtering for 1 day, 3 days, 7 days, 30 days, or 1 year\n"
    )
    summary.append("")

    # Overall summary
    summary.append("## 📊 Summary\n")
    summary.append(f"- **Total feeds:** {data['summary']['total_feeds']}")
    summary.append(f"- **Successful:** {data['summary']['successful_feeds']}")
    summary.append(f"- **Failed:** {data['summary']['failed_feeds']}")
    summary.append(f"- **Total articles:** {data['summary']['total_articles']}")
    summary.append("")

    # Successful feeds
    if data["feeds"]:
        summary.append("## ✅ Successful Feeds\n")
        for feed_name, feed_data in data["feeds"].items():
            summary.append(f"### {feed_name}")
            summary.append(f"- **Articles:** {feed_data['count']}")

            if feed_data["articles"]:
                summary.append("\n| Title | Published |")
                summary.append("|-------|-----------|")
                for article in feed_data["articles"][:10]:  # Limit to first 10
                    title = (
                        article["title"][:80] + "..."
                        if len(article["title"]) > 80
                        else article["title"]
                    )
                    published = article["published"]
                    summary.append(f"| [{title}]({article['link']}) | {published} |")

                if feed_data["count"] > 10:
                    summary.append(
                        f"\n*...and {feed_data['count'] - 10} more articles*"
                    )
            else:
                summary.append("*No new articles*")

            summary.append("")

    # Failed feeds
    if data["failed_feeds"]:
        summary.append("## ❌ Failed Feeds\n")
        summary.append("| Feed Name | URL | Error |")
        summary.append("|-----------|-----|-------|")
        for failed in data["failed_feeds"]:
            error_reason = failed.get("error", "Unknown")
            summary.append(f"| {failed['name']} | {failed['url']} | {error_reason} |")
        summary.append("")

    return "\n".join(summary)


def generate_feed_nav(
    feeds: Dict[str, Any],
    current_feed: Optional[str] = None,
) -> str:
    """
    Generate navigation links for feed pages (for sidebar)

    Args:
        feeds: Dictionary of feed data
        current_feed: Name of current feed (if on a feed page), "failed" for failed feeds page,
                     or "summary" for summary page

    Returns:
        HTML navigation string
    """
    # Create a hidden element with feed names as JSON for settings page
    # Escape the JSON to prevent XSS in the script tag
    feed_names = sorted(feeds.keys())
    feed_list_json = json.dumps(feed_names)
    # HTML-escape the JSON content to prevent XSS when embedded in script tag
    escaped_feed_list_json = html_escape(feed_list_json)

    nav_html = '<nav class="feed-nav" aria-label="Feed navigation">\n'
    nav_html += '  <script type="application/json" '
    nav_html += f'id="feed-list-data">{escaped_feed_list_json}</script>\n'
    nav_html += '  <a href="index.html" class="nav-link'
    if current_feed is None:
        nav_html += " active"
    nav_html += '">All Feeds</a>\n'

    for feed_name in feed_names:
        feed_slug = generate_feed_slug(feed_name)

        nav_html += f'  <a href="feed-{feed_slug}.html" class="nav-link'
        if current_feed == feed_name:
            nav_html += " active"
        nav_html += f'">{html_escape(feed_name)}</a>\n'

    nav_html += '  <a href="summary.html" class="nav-link'
    if current_feed == "summary":
        nav_html += " active"
    nav_html += '">Summary</a>\n'

    nav_html += "</nav>\n"

    return nav_html


def generate_failed_feeds_content(failed_feeds: list) -> str:
    """
    Generate HTML content for failed feeds section

    Args:
        failed_feeds: List of failed feed dictionaries

    Returns:
        HTML content string for failed feeds
    """
    content = """
        <h2>Failed Feeds</h2>
"""
    if failed_feeds:
        content += """
        <div class="failed-feeds">
"""
        for failed in failed_feeds:
            escaped_name = html_escape(failed["name"])
            escaped_url = html_escape(failed["url"])
            # Get error reason, default to "Unknown" if not present
            error_reason = failed.get("error", "Unknown")
            escaped_error = html_escape(error_reason)
            content += f"""
            <div class="failed-feed-item">
                <div class="failed-feed-name">{escaped_name}</div>
                <div class="failed-feed-url">{escaped_url}</div>
                <div class="failed-feed-error">Error: {escaped_error}</div>
            </div>
"""
        content += """
        </div>
"""
    else:
        content += """
        <div class="no-articles">No failed feeds</div>
"""
    return content


def format_publish_date(iso_date_str: str) -> str:
    """
    Format ISO 8601 date string to human-readable format.

    Args:
        iso_date_str: ISO 8601 formatted date string

    Returns:
        Human-readable date string (e.g., "Jan 6, 2026 at 7:24 PM")
    """
    try:
        dt = parse_iso_timestamp(iso_date_str)
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except (ValueError, AttributeError):
        # If parsing fails, return the original string
        return iso_date_str


def inject_website_urls(data: Dict[str, Any], feeds_config_path: str) -> None:
    """
    Inject website_url from a feeds config JSON file into feed data.

    Reads the feeds config (e.g. rss-feeds.json) and adds the ``website_url``
    field to each matching feed entry in ``data["feeds"]``.  Feeds that
    already carry a ``website_url`` value are left unchanged so that embedded
    test fixtures take precedence.

    Args:
        data: RSS feed collection data dictionary (modified in place)
        feeds_config_path: Path to the feeds configuration JSON file
    """
    try:
        with open(feeds_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return

    url_map = {
        feed_name: website_url
        for feed in config.get("feeds", [])
        for feed_name, website_url in [(feed.get("name"), feed.get("website_url"))]
        if feed_name and website_url
    }

    for feed_name, feed_data in data.get("feeds", {}).items():
        if "website_url" not in feed_data and feed_name in url_map:
            feed_data["website_url"] = url_map[feed_name]


def render_site_metadata_placeholders(
    content: str,
    site_metadata: Dict[str, str],
    *,
    page_title: Optional[str] = None,
    page_description: Optional[str] = None,
) -> str:
    """
    Replace branding placeholders in generated HTML assets.

    Args:
        content: Raw file content with placeholders.
        site_metadata: Site metadata dictionary.
        page_title: Optional keyword-only page title override.
        page_description: Optional keyword-only page description override.

    Returns:
        Content with branding placeholders replaced.
    """
    replacements = {
        "__PAGE_TITLE__": html_escape(page_title or site_metadata["site_name"]),
        "<!-- PAGE_DESCRIPTION_PLACEHOLDER -->": html_escape(
            page_description or site_metadata["site_description"]
        ),
        "<!-- SITE_RSS_TITLE_PLACEHOLDER -->": html_escape(site_metadata["rss_title"]),
        "<!-- HEADER_TITLE_PLACEHOLDER -->": html_escape(site_metadata["header_title"]),
        "__SETTINGS_TITLE__": html_escape(site_metadata["settings_title"]),
        "<!-- SETTINGS_DESCRIPTION_PLACEHOLDER -->": html_escape(
            site_metadata["settings_description"]
        ),
    }

    rendered = content
    for placeholder, replacement in replacements.items():
        rendered = rendered.replace(placeholder, replacement)

    return rendered


def copy_static_site_assets(
    output_dir: str, site_metadata: Optional[Dict[str, str]] = None
) -> None:
    """
    Copy authored static site assets into the generated output directory.

    Args:
        output_dir: Directory that will contain the generated site.

    Raises:
        FileNotFoundError: If any required source asset is missing.
    """
    missing_assets = [
        asset_name
        for asset_name in STATIC_SITE_FILES
        if not (STATIC_SITE_DIR / asset_name).is_file()
    ]
    if missing_assets:
        missing_list = ", ".join(sorted(missing_assets))
        raise FileNotFoundError(
            f"Static site assets not found in '{STATIC_SITE_DIR}': {missing_list}"
        )

    metadata = resolve_site_metadata(site_metadata)

    for asset_name in STATIC_SITE_FILES:
        source_path = STATIC_SITE_DIR / asset_name
        target_path = os.path.join(output_dir, asset_name)
        if asset_name == "settings.html":
            settings_content = source_path.read_text(encoding="utf-8")
            rendered_settings = render_site_metadata_placeholders(
                settings_content,
                metadata,
                page_title=metadata["settings_title"],
                page_description=metadata["settings_description"],
            )
            Path(target_path).write_text(rendered_settings, encoding="utf-8")
            continue

        shutil.copy2(source_path, target_path)


def generate_feed_articles_content(feeds_to_display: Dict[str, Any]) -> str:
    """
    Generate HTML content for feed articles section

    Args:
        feeds_to_display: Dictionary of feeds to display

    Returns:
        HTML content string for feed articles
    """
    if not feeds_to_display:
        return ""

    content = ""
    for feed_name, feed_data in feeds_to_display.items():
        article_count = feed_data["count"]
        escaped_feed_name = html_escape(feed_name)
        article_plural = "s" if article_count != 1 else ""
        website_url = feed_data.get("website_url")
        if website_url:
            escaped_website_url = html_escape(website_url)
            title_html = (
                f'<a href="{escaped_website_url}" class="feed-title-link"'
                f' target="_blank" rel="noopener noreferrer">{escaped_feed_name}</a>'
            )
        else:
            title_html = escaped_feed_name
        content += f"""
        <div class="feed-section">
            <h2>{title_html}
                <span class="feed-count">
                    {article_count} article{article_plural}
                </span>
            </h2>
"""
        if feed_data["articles"]:
            content += """
            <ul class="article-list">
"""
            for index, article in enumerate(feed_data["articles"]):
                escaped_title = html_escape(article["title"])
                escaped_link = html_escape(article["link"])
                formatted_date = format_publish_date(article["published"])
                iso_timestamp = html_escape(article["published"])
                if index == 0:
                    article_rank = "lead"
                elif index < 3:
                    article_rank = "feature"
                else:
                    article_rank = "compact"
                content += f"""
                <li
                    class="article-item article-item--{article_rank}"
                    data-article-rank="{article_rank}"
                    data-published="{iso_timestamp}"
                >
                    <a href="{escaped_link}" class="article-title"
                       target="_blank" rel="noopener noreferrer">
                        {escaped_title}
                    </a>
                    <div class="article-meta">{html_escape(formatted_date)}</div>
                </li>
"""
            content += """
            </ul>
"""
        else:
            content += """
            <div class="no-articles">No new articles in this time period</div>
"""
        content += """
        </div>
"""
    return content


def generate_html_content(
    data: Dict[str, Any], current_feed: Optional[str] = None
) -> str:
    """
    Generate HTML content (without template wrapper) from RSS feed collection data

    Args:
        data: RSS feed collection data dictionary
        current_feed: If specified, generate content for only this feed,
                      or "failed" for failed feeds page, or "summary" for summary page

    Returns:
        HTML content string to be injected into template
    """
    content = ""

    # If showing summary page
    if current_feed == "summary":
        failed_icon_path = (
            "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3"
            "L13.71 3.86a2 2 0 0 0-3.42 0z"
        )
        content += """
        <h2>Feed Collection Summary</h2>
        <div class="summary-intro">
            Overview of RSS feed collection status and statistics.
        </div>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-icon">
                    <svg
                        width="32"
                        height="32"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >
                        <path d="M4 11a9 9 0 0 1 9 9"></path>
                        <path d="M4 4a16 16 0 0 1 16 16"></path>
                        <circle cx="5" cy="19" r="1"></circle>
                    </svg>
                </div>
                <div class="stat-label">Total Feeds</div>
                <div class="stat-value">"""
        content += f"{data['summary']['total_feeds']}"
        content += """</div>
            </div>
            <div class="stat-card success">
                <div class="stat-icon">
                    <svg
                        width="32"
                        height="32"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                        <polyline points="9 12 11 14 15 10"></polyline>
                    </svg>
                </div>
                <div class="stat-label">Successful</div>
                <div class="stat-value">"""
        content += f"{data['summary']['successful_feeds']}"
        content += f"""</div>
            </div>
            <div class="stat-card error">
                <div class="stat-icon">
                    <svg
                        width="32"
                        height="32"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >
                        <path d="{failed_icon_path}"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                </div>
                <div class="stat-label">Failed</div>
                <div class="stat-value">"""
        content += f"{data['summary']['failed_feeds']}"
        content += """</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <svg
                        width="32"
                        height="32"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >
                        <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                        <polyline points="2 17 12 22 22 17"></polyline>
                        <polyline points="2 12 12 17 22 12"></polyline>
                    </svg>
                </div>
                <div class="stat-label">Total Articles</div>
                <div class="stat-value">"""
        content += f"{data['summary']['total_articles']}"
        content += """</div>
            </div>
        </div>
"""
        # Add failed feeds section to summary page
        if data.get("failed_feeds"):
            content += generate_failed_feeds_content(data.get("failed_feeds", []))

        # Add feed breakdown section
        if data.get("feeds"):
            content += """
        <h2>Feed Breakdown</h2>
        <div class="feed-breakdown">
"""
            # Sort feeds by article count (descending)
            sorted_feeds = sorted(
                data["feeds"].items(), key=lambda x: x[1]["count"], reverse=True
            )

            for feed_name, feed_data in sorted_feeds:
                escaped_name = html_escape(feed_name)
                article_count = feed_data["count"]
                total_articles = data["summary"]["total_articles"]
                percentage = (
                    (article_count / total_articles * 100) if total_articles > 0 else 0
                )
                feed_slug = generate_feed_slug(feed_name)

                content += f"""
            <div class="feed-breakdown-item">
                <div class="feed-breakdown-header">
                    <a href="feed-{feed_slug}.html" class="feed-breakdown-name">
                        {escaped_name}
                    </a>
                    <div class="feed-breakdown-count">{article_count} articles</div>
                </div>
                <div class="feed-breakdown-bar">
                    <div class="feed-breakdown-fill" style="width: {percentage:.1f}%"></div>
                </div>
            </div>
"""
            content += """
        </div>
"""

        return content

    # If showing failed feeds page (deprecated - now part of summary)
    if current_feed == "failed":
        content += generate_failed_feeds_content(data.get("failed_feeds", []))
        return content

    # Determine which feeds to display
    feeds_to_display = {}
    if current_feed:
        # Single feed view
        if current_feed in data["feeds"]:
            feeds_to_display = {current_feed: data["feeds"][current_feed]}
    else:
        # All feeds view - sort with feeds having articles first, then empty feeds
        # Within each group, sort alphabetically
        feeds_with_articles = {}
        empty_feeds = {}

        for feed_name, feed_data in data["feeds"].items():
            if feed_data["count"] > 0:
                feeds_with_articles[feed_name] = feed_data
            else:
                empty_feeds[feed_name] = feed_data

        # Combine: feeds with articles (sorted), then empty feeds (sorted)
        feeds_to_display = dict(sorted(feeds_with_articles.items()))
        feeds_to_display.update(dict(sorted(empty_feeds.items())))

    # Display feeds
    content += generate_feed_articles_content(feeds_to_display)

    return content


def generate_html_page(
    data: Dict[str, Any],
    template_path: Optional[str] = None,
    current_feed: Optional[str] = None,
    site_metadata: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate complete HTML page from RSS feed collection data using template.

    Args:
        data: RSS feed collection data dictionary.
        template_path: Path to HTML template file (optional).
        current_feed: If specified, generate page for only this feed.

    Returns:
        Complete HTML page string.

    Raises:
        FileNotFoundError: If the specified template file does not exist.
        IOError: If an I/O error occurs while reading the template file.
        OSError: If a path-related or other OS-level error occurs when
            accessing the template file.
    """
    # Get template path
    if template_path is None:
        template_path = str(get_template_path())

    # Read template with error handling and explicit UTF-8 encoding
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"HTML template file not found at '{template_path}'. "
            "Ensure the template file exists and the path is correct."
        ) from exc
    except OSError as exc:
        raise OSError(
            f"Error reading HTML template file at '{template_path}': {exc}"
        ) from exc

    metadata = resolve_site_metadata(site_metadata)

    # Generate content
    content = generate_html_content(data, current_feed)

    # Generate sidebar navigation
    sidebar_content = generate_feed_nav(data["feeds"], current_feed)

    # Get formatted timestamp
    collected_time = parse_iso_timestamp(data["metadata"]["collected_at"])
    formatted_time = collected_time.strftime("%B %d, %Y at %I:%M %p UTC")
    # Create a version string for cache busting (epoch timestamp)
    cache_version = str(int(collected_time.timestamp()))

    # Update title if this is a feed-specific page
    page_title = metadata["site_name"]
    if current_feed == "summary":
        page_title = f"Summary - {metadata['site_name']}"
    elif current_feed == "failed":
        page_title = f"Failed Feeds - {metadata['site_name']}"
    elif current_feed:
        page_title = f"{current_feed} - {metadata['site_name']}"

    # Replace placeholders
    html = render_site_metadata_placeholders(
        template,
        metadata,
        page_title=page_title,
        page_description=metadata["site_description"],
    )
    html = html.replace("<!-- CONTENT_PLACEHOLDER -->", content)
    html = html.replace("<!-- SIDEBAR_PLACEHOLDER -->", sidebar_content)
    html = html.replace("<!-- TIMESTAMP_PLACEHOLDER -->", formatted_time)
    # Replace timestamp in CSS link for cache busting
    html = html.replace(
        'href="styles.css?v=<!-- TIMESTAMP_PLACEHOLDER -->"',
        f'href="styles.css?v={cache_version}"',
    )
    return html


def generate_all_pages(
    data: Dict[str, Any],
    output_dir: str,
    site_metadata: Optional[Dict[str, str]] = None,
) -> None:
    """
    Generate all HTML pages (main index + individual feed pages + failed feeds page)

    Args:
        data: RSS feed collection data dictionary
        output_dir: Directory to write HTML files

    Returns:
        None
    """
    # Ensure output directory exists
    metadata = resolve_site_metadata(site_metadata)
    os.makedirs(output_dir, exist_ok=True)
    copy_static_site_assets(output_dir, metadata)

    # Generate main index page (all feeds)
    index_path = os.path.join(output_dir, "index.html")
    index_html = generate_html_page(data, site_metadata=metadata)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"✓ Main index page written to {index_path}")

    # Generate summary page
    summary_path = os.path.join(output_dir, "summary.html")
    summary_html = generate_html_page(
        data, current_feed="summary", site_metadata=metadata
    )
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_html)
    print(f"✓ Summary page written to {summary_path}")

    # Generate individual feed pages (sorted alphabetically)
    for feed_name in sorted(data["feeds"].keys()):
        feed_slug = generate_feed_slug(feed_name)
        feed_path = os.path.join(output_dir, f"feed-{feed_slug}.html")
        feed_html = generate_html_page(
            data, current_feed=feed_name, site_metadata=metadata
        )
        with open(feed_path, "w", encoding="utf-8") as f:
            f.write(feed_html)
        print(f"✓ Feed page for '{feed_name}' written to {feed_path}")


def main():
    """
    Main entry point for the summary generator script.

    Parses command line arguments and generates markdown and/or HTML summaries
    from RSS feed collection data.

    Returns:
        int: 0 on success, 1 on error.
    """
    parser = argparse.ArgumentParser(
        description="Generate summary from RSS feed collection data"
    )
    parser.add_argument(
        "--input", required=True, help="Input JSON file from RSS feed collection"
    )
    parser.add_argument("--markdown", help="Output markdown file path")
    parser.add_argument(
        "--output-dir",
        help="Output directory for multi-page HTML (generates index + feed pages)",
    )
    parser.add_argument(
        "--feeds-config",
        help="Path to the feeds config JSON (e.g. config/rss-feeds.json) used to "
        "inject website_url into feed data for feed-title hyperlinks",
    )
    parser.add_argument(
        "--site-metadata",
        help="Path to the site metadata JSON used for site branding",
    )

    args = parser.parse_args()

    # Read input JSON
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file {args.input} not found")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input}: {e}")
        return 1

    try:
        site_metadata = load_site_metadata(args.site_metadata)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    # Inject website URLs from feeds config if provided
    if args.feeds_config:
        inject_website_urls(data, args.feeds_config)

    # Generate markdown if requested
    if args.markdown:
        markdown_content = generate_markdown_summary(data, site_metadata)
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✓ Markdown summary written to {args.markdown}")

    # Generate multi-page HTML if output directory is specified
    if args.output_dir:
        generate_all_pages(data, args.output_dir, site_metadata)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
