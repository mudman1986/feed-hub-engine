#!/usr/bin/env python3
"""
RSS Feed Generator for DevOps Feed Hub
Generates RSS 2.0 feeds from collected RSS feed data
"""

import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

from utils import (
    generate_feed_slug,
    parse_iso_timestamp,
    resolve_site_metadata,
    sort_articles_by_date,
)

# Default base URL - can be overridden via environment variable or CLI argument
DEFAULT_BASE_URL = os.getenv(
    "FEED_HUB_BASE_URL",
    os.getenv("GITHUB_REPOSITORY", "mudman1986/feed-hub-engine").split("/")[0]
    + ".github.io/"
    + os.getenv("GITHUB_REPOSITORY", "mudman1986/feed-hub-engine").split("/")[1],
).rstrip("/")

# Ensure it has https:// prefix
if not DEFAULT_BASE_URL.startswith("http"):
    DEFAULT_BASE_URL = f"https://{DEFAULT_BASE_URL}"


def format_rfc822_date(iso_date_str: str) -> str:
    """
    Format ISO 8601 date string to RFC 822 format required by RSS 2.0.

    Args:
            iso_date_str: ISO 8601 formatted date string

    Returns:
            RFC 822 formatted date string (e.g., "Mon, 10 Jan 2026 09:00:00 +0000")
    """
    try:
        dt = parse_iso_timestamp(iso_date_str)
        # RFC 822 format: "Day, DD Mon YYYY HH:MM:SS +0000"
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except (ValueError, AttributeError):
        # If parsing fails, return current time
        return datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")


def create_rss_feed(
    # pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments
    title: str,
    link: str,
    description: str,
    articles: List[Dict[str, Any]],
    last_build_date: str,
    generator_name: str,
) -> str:
    """
    Create an RSS 2.0 feed from articles.

    Args:
            title: Feed title
            link: Feed link URL
            description: Feed description
            articles: List of article dictionaries with title, link, published
            last_build_date: ISO 8601 timestamp of when feed was built

    Returns:
            RSS 2.0 XML string
    """
    # Create RSS root element
    rss = ET.Element("rss")
    rss.set("version", "2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

    # Create channel element
    channel = ET.SubElement(rss, "channel")

    # Add channel metadata
    title_elem = ET.SubElement(channel, "title")
    title_elem.text = title

    link_elem = ET.SubElement(channel, "link")
    link_elem.text = link

    description_elem = ET.SubElement(channel, "description")
    description_elem.text = description

    # Add atom:link for self-reference
    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", link)
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    # Add lastBuildDate
    last_build_elem = ET.SubElement(channel, "lastBuildDate")
    last_build_elem.text = format_rfc822_date(last_build_date)

    # Add generator
    generator = ET.SubElement(channel, "generator")
    generator.text = generator_name

    # Add items (articles)
    for article in articles:
        item = ET.SubElement(channel, "item")

        item_title = ET.SubElement(item, "title")
        item_title.text = article.get("title", "No title")

        item_link = ET.SubElement(item, "link")
        item_link.text = article.get("link", "")

        # Add GUID (using link as identifier)
        guid = ET.SubElement(item, "guid")
        guid.set("isPermaLink", "true")
        guid.text = article.get("link", "")

        # Add publication date if available
        pub_date = article.get("published")
        if pub_date and pub_date != "Unknown":
            pub_date_elem = ET.SubElement(item, "pubDate")
            pub_date_elem.text = format_rfc822_date(pub_date)

        # Add source feed name if available
        if "source" in article:
            source = ET.SubElement(item, "source")
            source.text = article["source"]

    # Convert to string with XML declaration
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    xml_str = ET.tostring(rss, encoding="unicode")

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str


def generate_master_feed(
    data: Dict[str, Any],
    base_url: Optional[str] = None,
    site_metadata: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate master RSS feed with all articles from all feeds.

    Args:
            data: RSS feed collection data dictionary
            base_url: Base URL for the feed hub (defaults to DEFAULT_BASE_URL)

    Returns:
            RSS 2.0 XML string
    """
    if base_url is None:
        base_url = DEFAULT_BASE_URL
    metadata = resolve_site_metadata(site_metadata)

    # Collect all articles from all feeds
    all_articles = []
    for feed_name, feed_data in data["feeds"].items():
        for article in feed_data["articles"]:
            # Add source feed name to article
            article_with_source = article.copy()
            article_with_source["source"] = feed_name
            all_articles.append(article_with_source)

    # Sort by publication date (newest first)
    all_articles = sort_articles_by_date(all_articles)

    # Generate RSS feed
    return create_rss_feed(
        title=metadata["rss_title"],
        link=f"{base_url}/feed.xml",
        description=metadata["rss_description"],
        articles=all_articles,
        last_build_date=data["metadata"]["collected_at"],
        generator_name=metadata["rss_generator"],
    )


def generate_individual_feed(
    feed_name: str,
    feed_data: Dict[str, Any],
    collected_at: str,
    base_url: Optional[str] = None,
    site_metadata: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate RSS feed for a single source feed.

    Args:
            feed_name: Name of the feed
            feed_data: Feed data dictionary with articles
            collected_at: ISO 8601 timestamp of when feed was collected
            base_url: Base URL for the feed hub (defaults to DEFAULT_BASE_URL)

    Returns:
            RSS 2.0 XML string
    """
    if base_url is None:
        base_url = DEFAULT_BASE_URL
    metadata = resolve_site_metadata(site_metadata)

    feed_slug = generate_feed_slug(feed_name)

    # Sort articles by publication date (newest first)
    sorted_articles = sort_articles_by_date(feed_data["articles"])

    return create_rss_feed(
        title=f"{metadata['site_name']} - {feed_name}",
        link=f"{base_url}/feed-{feed_slug}.xml",
        description=f"Articles from {feed_name}",
        articles=sorted_articles,
        last_build_date=collected_at,
        generator_name=metadata["rss_generator"],
    )


def generate_all_feeds(
    data: Dict[str, Any],
    output_dir: str,
    base_url: Optional[str] = None,
    site_metadata: Optional[Dict[str, str]] = None,
) -> None:
    """
    Generate all RSS feeds (master feed + individual feed files).

    Args:
            data: RSS feed collection data dictionary
            output_dir: Directory to write RSS files

    Returns:
            None
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate master feed (all articles)
    master_feed_path = os.path.join(output_dir, "feed.xml")
    metadata = resolve_site_metadata(site_metadata)
    master_feed_xml = generate_master_feed(data, base_url, metadata)
    with open(master_feed_path, "w", encoding="utf-8") as f:
        f.write(master_feed_xml)
    print(f"✓ Master RSS feed written to {master_feed_path}")

    # Generate individual feeds
    for feed_name in sorted(data["feeds"].keys()):
        feed_data = data["feeds"][feed_name]
        feed_slug = generate_feed_slug(feed_name)
        feed_path = os.path.join(output_dir, f"feed-{feed_slug}.xml")
        feed_xml = generate_individual_feed(
            feed_name,
            feed_data,
            data["metadata"]["collected_at"],
            base_url,
            metadata,
        )
        with open(feed_path, "w", encoding="utf-8") as f:
            f.write(feed_xml)
        print(f"✓ RSS feed for '{feed_name}' written to {feed_path}")


def main():
    """
    Main entry point for the RSS feed generator script.

    Parses command line arguments and generates RSS feeds
    from collected feed data.

    Returns:
            int: 0 on success, 1 on error.
    """
    parser = argparse.ArgumentParser(
        description="Generate RSS feeds from collected feed data"
    )
    parser.add_argument(
        "--input", required=True, help="Input JSON file from RSS feed collection"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for RSS feed files",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL for the feed hub (default: {DEFAULT_BASE_URL})",
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
        site_metadata = resolve_site_metadata(site_metadata_path=args.site_metadata)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    # Generate RSS feeds
    generate_all_feeds(data, args.output_dir, args.base_url, site_metadata)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
