#!/usr/bin/env python3
"""
Tests for RSS feed generator
"""

import json
import os
import tempfile
from unittest.mock import patch
from xml.etree import ElementTree as ET

from generate_rss import (  # noqa: E402 # pylint: disable=wrong-import-position
    create_rss_feed,
    format_rfc822_date,
    generate_all_feeds,
    generate_individual_feed,
    generate_master_feed,
    main,
    parse_iso_timestamp,
)
from utils import (  # noqa: E402 # pylint: disable=wrong-import-position
    generate_feed_slug,
)


def test_parse_iso_timestamp():
    """Test ISO timestamp parsing"""
    dt = parse_iso_timestamp("2026-01-10T12:00:00Z")
    assert dt.year == 2026
    assert dt.month == 1
    assert dt.day == 10
    assert dt.hour == 12


def test_format_rfc822_date():
    """Test RFC 822 date formatting"""
    rfc_date = format_rfc822_date("2026-01-10T12:00:00Z")
    assert "Sat" in rfc_date  # January 10, 2026 is a Saturday
    assert "10 Jan 2026" in rfc_date
    assert "12:00:00" in rfc_date


def test_generate_feed_slug():
    """Test feed slug generation"""
    assert generate_feed_slug("Microsoft DevOps Blog") == "microsoft-devops-blog"
    assert generate_feed_slug("GitHub Blog") == "github-blog"
    assert generate_feed_slug("Test/Feed Name") == "test-feed-name"
    assert generate_feed_slug("Test--Multi---Dash") == "test-multi-dash"
    assert generate_feed_slug("  Team // Updates   Daily  ") == "team-updates-daily"


def test_create_rss_feed():
    """Test RSS feed creation"""
    articles = [
        {
            "title": "Test Article 1",
            "link": "https://example.com/article1",
            "published": "2026-01-10T12:00:00Z",
        },
        {
            "title": "Test Article 2",
            "link": "https://example.com/article2",
            "published": "2026-01-09T12:00:00Z",
        },
    ]

    rss_xml = create_rss_feed(
        title="Test Feed",
        link="https://example.com/feed.xml",
        description="Test feed description",
        articles=articles,
        last_build_date="2026-01-10T12:00:00Z",
        generator_name="DevOps Feed Hub RSS Generator",
    )

    # Parse the XML to verify structure
    root = ET.fromstring(rss_xml)

    assert root.tag == "rss"
    assert root.get("version") == "2.0"

    channel = root.find("channel")
    assert channel is not None

    # Check channel metadata
    assert channel.find("title").text == "Test Feed"
    assert channel.find("link").text == "https://example.com/feed.xml"
    assert channel.find("description").text == "Test feed description"
    assert channel.find("generator").text == "DevOps Feed Hub RSS Generator"

    # Check items
    items = channel.findall("item")
    assert len(items) == 2

    # Check first item
    assert items[0].find("title").text == "Test Article 1"
    assert items[0].find("link").text == "https://example.com/article1"
    assert items[0].find("guid").text == "https://example.com/article1"


def test_create_rss_feed_with_source():
    """Test RSS feed creation with source field"""
    articles = [
        {
            "title": "Test Article",
            "link": "https://example.com/article",
            "published": "2026-01-10T12:00:00Z",
            "source": "Test Source Feed",
        },
    ]

    rss_xml = create_rss_feed(
        title="Test Feed",
        link="https://example.com/feed.xml",
        description="Test feed description",
        articles=articles,
        last_build_date="2026-01-10T12:00:00Z",
        generator_name="DevOps Feed Hub RSS Generator",
    )

    root = ET.fromstring(rss_xml)
    channel = root.find("channel")
    items = channel.findall("item")

    # Check that source is included
    assert items[0].find("source").text == "Test Source Feed"


def test_generate_master_feed():
    """Test master feed generation"""
    data = {
        "metadata": {"collected_at": "2026-01-10T12:00:00Z"},
        "feeds": {
            "Feed A": {
                "articles": [
                    {
                        "title": "Article A1",
                        "link": "https://example.com/a1",
                        "published": "2026-01-10T10:00:00Z",
                    },
                ]
            },
            "Feed B": {
                "articles": [
                    {
                        "title": "Article B1",
                        "link": "https://example.com/b1",
                        "published": "2026-01-10T11:00:00Z",
                    },
                ]
            },
        },
    }

    rss_xml = generate_master_feed(data)

    root = ET.fromstring(rss_xml)
    channel = root.find("channel")

    # Check title
    assert "All Articles" in channel.find("title").text

    # Check items - should have all articles from all feeds
    items = channel.findall("item")
    assert len(items) == 2

    # Check that source is included in items
    sources = [item.find("source").text for item in items]
    assert "Feed A" in sources
    assert "Feed B" in sources

    # Check that articles are sorted by date (newest first)
    # B1 (11:00) should come before A1 (10:00)
    assert items[0].find("title").text == "Article B1"
    assert items[1].find("title").text == "Article A1"


def test_generate_master_feed_uses_site_metadata():
    """Test master feed generation uses configurable metadata."""
    data = {
        "metadata": {"collected_at": "2026-01-10T12:00:00Z"},
        "feeds": {"Feed A": {"articles": []}},
    }

    rss_xml = generate_master_feed(
        data,
        base_url="https://example.com/custom",
        site_metadata={
            "site_name": "Platform Feed Hub",
            "rss_title": "Platform Feed Hub - All Articles",
            "rss_description": "Platform engineering articles",
            "rss_generator": "Platform Feed Hub RSS Generator",
        },
    )

    channel = ET.fromstring(rss_xml).find("channel")
    assert channel.find("title").text == "Platform Feed Hub - All Articles"
    assert channel.find("description").text == "Platform engineering articles"
    assert channel.find("generator").text == "Platform Feed Hub RSS Generator"
    assert channel.find("link").text == "https://example.com/custom/feed.xml"


def test_generate_master_feed_merges_partial_site_metadata():
    """Test master feed generation merges partial metadata overrides."""
    data = {
        "metadata": {"collected_at": "2026-01-10T12:00:00Z"},
        "feeds": {"Feed A": {"articles": []}},
    }

    rss_xml = generate_master_feed(
        data,
        site_metadata={"rss_description": "Platform engineering articles"},
    )

    channel = ET.fromstring(rss_xml).find("channel")
    assert channel.find("title").text == "DevOps Feed Hub - All Articles"
    assert channel.find("description").text == "Platform engineering articles"
    assert channel.find("generator").text == "DevOps Feed Hub RSS Generator"


def test_generate_individual_feed():
    """Test individual feed generation"""
    feed_data = {
        "articles": [
            {
                "title": "Article 1",
                "link": "https://example.com/1",
                "published": "2026-01-10T10:00:00Z",
            },
            {
                "title": "Article 2",
                "link": "https://example.com/2",
                "published": "2026-01-10T11:00:00Z",
            },
        ]
    }

    rss_xml = generate_individual_feed(
        feed_name="Test Feed",
        feed_data=feed_data,
        collected_at="2026-01-10T12:00:00Z",
    )

    root = ET.fromstring(rss_xml)
    channel = root.find("channel")

    # Check title includes feed name
    assert "Test Feed" in channel.find("title").text

    # Check items are sorted (newest first)
    items = channel.findall("item")
    assert len(items) == 2
    assert items[0].find("title").text == "Article 2"  # 11:00 is newer
    assert items[1].find("title").text == "Article 1"  # 10:00 is older


def test_generate_individual_feed_uses_site_metadata():
    """Test individual feed titles use configurable site metadata."""
    feed_data = {"articles": []}

    rss_xml = generate_individual_feed(
        feed_name="Test Feed",
        feed_data=feed_data,
        collected_at="2026-01-10T12:00:00Z",
        base_url="https://example.com/custom",
        site_metadata={
            "site_name": "Platform Feed Hub",
            "rss_generator": "Platform Feed Hub RSS Generator",
        },
    )

    channel = ET.fromstring(rss_xml).find("channel")
    assert channel.find("title").text == "Platform Feed Hub - Test Feed"
    assert channel.find("generator").text == "Platform Feed Hub RSS Generator"
    assert channel.find("link").text == "https://example.com/custom/feed-test-feed.xml"


def test_generate_individual_feed_merges_partial_site_metadata():
    """Test individual feed generation merges partial metadata overrides."""
    feed_data = {"articles": []}

    rss_xml = generate_individual_feed(
        feed_name="Test Feed",
        feed_data=feed_data,
        collected_at="2026-01-10T12:00:00Z",
        site_metadata={"site_name": "Platform Feed Hub"},
    )

    channel = ET.fromstring(rss_xml).find("channel")
    assert channel.find("title").text == "Platform Feed Hub - Test Feed"
    assert channel.find("description").text == "Articles from Test Feed"
    assert channel.find("generator").text == "DevOps Feed Hub RSS Generator"


def test_generate_all_feeds():
    """Test generation of all feeds to files"""
    data = {
        "metadata": {"collected_at": "2026-01-10T12:00:00Z"},
        "feeds": {
            "Test Feed A": {
                "articles": [
                    {
                        "title": "Article A1",
                        "link": "https://example.com/a1",
                        "published": "2026-01-10T10:00:00Z",
                    },
                ]
            },
            "Test Feed B": {
                "articles": [
                    {
                        "title": "Article B1",
                        "link": "https://example.com/b1",
                        "published": "2026-01-10T11:00:00Z",
                    },
                ]
            },
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        generate_all_feeds(data, tmpdir)

        # Check master feed exists
        master_feed_path = os.path.join(tmpdir, "feed.xml")
        assert os.path.exists(master_feed_path)

        # Check individual feeds exist
        feed_a_path = os.path.join(tmpdir, "feed-test-feed-a.xml")
        assert os.path.exists(feed_a_path)

        feed_b_path = os.path.join(tmpdir, "feed-test-feed-b.xml")
        assert os.path.exists(feed_b_path)

        # Verify master feed content
        with open(master_feed_path, "r", encoding="utf-8") as f:
            master_content = f.read()
            assert "Article A1" in master_content
            assert "Article B1" in master_content

        # Verify individual feed content
        with open(feed_a_path, "r", encoding="utf-8") as f:
            feed_a_content = f.read()
            assert "Article A1" in feed_a_content
            assert "Article B1" not in feed_a_content


def test_rss_feed_handles_unknown_dates():
    """Test that RSS feed handles articles with unknown dates"""
    articles = [
        {
            "title": "Article with date",
            "link": "https://example.com/1",
            "published": "2026-01-10T12:00:00Z",
        },
        {
            "title": "Article without date",
            "link": "https://example.com/2",
            "published": "Unknown",
        },
    ]

    rss_xml = create_rss_feed(
        title="Test Feed",
        link="https://example.com/feed.xml",
        description="Test feed",
        articles=articles,
        last_build_date="2026-01-10T12:00:00Z",
        generator_name="DevOps Feed Hub RSS Generator",
    )

    root = ET.fromstring(rss_xml)
    channel = root.find("channel")
    items = channel.findall("item")

    # Both articles should be included
    assert len(items) == 2

    # First item should have pubDate
    assert items[0].find("pubDate") is not None

    # Second item should not have pubDate (because it's "Unknown")
    assert items[1].find("pubDate") is None


def test_rss_feed_xml_declaration():
    """Test that RSS feed has proper XML declaration"""
    articles = [
        {
            "title": "Test Article",
            "link": "https://example.com/1",
            "published": "2026-01-10T12:00:00Z",
        },
    ]

    rss_xml = create_rss_feed(
        title="Test Feed",
        link="https://example.com/feed.xml",
        description="Test feed",
        articles=articles,
        last_build_date="2026-01-10T12:00:00Z",
        generator_name="DevOps Feed Hub RSS Generator",
    )

    # Check XML declaration
    assert rss_xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_rss_feed_atom_namespace():
    """Test that RSS feed includes atom namespace for self-reference"""
    articles = []

    rss_xml = create_rss_feed(
        title="Test Feed",
        link="https://example.com/feed.xml",
        description="Test feed",
        articles=articles,
        last_build_date="2026-01-10T12:00:00Z",
        generator_name="DevOps Feed Hub RSS Generator",
    )

    # Check that xmlns:atom is in the XML string
    assert 'xmlns:atom="http://www.w3.org/2005/Atom"' in rss_xml

    root = ET.fromstring(rss_xml)

    # Check atom:link element
    channel = root.find("channel")
    atom_link = channel.find("{http://www.w3.org/2005/Atom}link")
    assert atom_link is not None
    assert atom_link.get("rel") == "self"
    assert atom_link.get("type") == "application/rss+xml"


def test_main_generates_feeds_with_site_metadata_file():
    """Test CLI entry point supports the site metadata file option."""
    data = {
        "metadata": {"collected_at": "2026-01-10T12:00:00Z"},
        "feeds": {
            "Test Feed": {
                "articles": [
                    {
                        "title": "Article 1",
                        "link": "https://example.com/1",
                        "published": "2026-01-10T10:00:00Z",
                    }
                ]
            }
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.json")
        metadata_path = os.path.join(tmpdir, "site-metadata.json")
        output_dir = os.path.join(tmpdir, "feeds")

        with open(input_path, "w", encoding="utf-8") as file:
            json.dump(data, file)
        with open(metadata_path, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "site_name": "Platform Feed Hub",
                    "rss_title": "Platform Feed Hub - All Articles",
                },
                file,
            )

        with patch(
            "sys.argv",
            [
                "generate_rss.py",
                "--input",
                input_path,
                "--output-dir",
                output_dir,
                "--base-url",
                "https://example.com/custom",
                "--site-metadata",
                metadata_path,
            ],
        ):
            assert main() == 0

        master_feed_path = os.path.join(output_dir, "feed.xml")
        individual_feed_path = os.path.join(output_dir, "feed-test-feed.xml")
        assert os.path.exists(master_feed_path)
        assert os.path.exists(individual_feed_path)

        with open(master_feed_path, "r", encoding="utf-8") as file:
            master_feed = file.read()
        with open(individual_feed_path, "r", encoding="utf-8") as file:
            individual_feed = file.read()

        assert "Platform Feed Hub - All Articles" in master_feed
        assert "Platform Feed Hub - Test Feed" in individual_feed


def test_format_rfc822_date_invalid_input_returns_fallback():
    """Test that invalid ISO strings fall back to current time."""
    result = format_rfc822_date("not-a-valid-date")
    # Should return a non-empty RFC 822 date string (current time)
    assert result
    assert len(result) > 10


def test_main_returns_1_when_input_file_missing():
    """main() should return 1 when the input file does not exist."""
    with patch(
        "sys.argv",
        [
            "generate_rss.py",
            "--input",
            "/nonexistent/path/input.json",
            "--output-dir",
            "/tmp/out",
        ],
    ):
        result = main()
    assert result == 1


def test_main_returns_1_when_input_file_has_invalid_json():
    """main() should return 1 when the input file contains invalid JSON."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        f.write("NOT VALID JSON {{{")
        path = f.name

    try:
        with patch(
            "sys.argv",
            [
                "generate_rss.py",
                "--input",
                path,
                "--output-dir",
                "/tmp/out",
            ],
        ):
            result = main()
    finally:
        os.unlink(path)

    assert result == 1


def test_main_returns_1_when_site_metadata_is_invalid():
    """main() should return 1 when the site metadata file is invalid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.json")
        metadata_path = os.path.join(tmpdir, "site-metadata.json")

        with open(input_path, "w", encoding="utf-8") as f:
            json.dump({"metadata": {}, "feeds": {}}, f)
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write("INVALID JSON")

        with patch(
            "sys.argv",
            [
                "generate_rss.py",
                "--input",
                input_path,
                "--output-dir",
                tmpdir,
                "--site-metadata",
                metadata_path,
            ],
        ):
            result = main()

    assert result == 1
