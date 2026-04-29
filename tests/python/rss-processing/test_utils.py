#!/usr/bin/env python3
"""
Unit tests for utils.py.
Covers branches and paths not exercised by other test modules.
"""

# pylint: disable=missing-function-docstring

import json
import os
import tempfile
import unittest
from datetime import datetime

from utils import (
    get_article_sort_key,
    load_site_metadata,
    populate_derived_site_metadata,
    sort_articles_by_date,
)


class TestPopulateDerivedSiteMetadata(unittest.TestCase):
    """Tests for populate_derived_site_metadata."""

    def test_raises_when_site_name_is_empty(self):
        with self.assertRaises(ValueError) as ctx:
            populate_derived_site_metadata({"site_name": ""})
        self.assertIn("site_name", str(ctx.exception))

    def test_raises_when_site_name_is_whitespace(self):
        with self.assertRaises(ValueError):
            populate_derived_site_metadata({"site_name": "   "})

    def test_uses_site_name_as_header_title_fallback(self):
        result = populate_derived_site_metadata({"site_name": "My Hub"})
        self.assertEqual(result["header_title"], "My Hub")

    def test_preserves_explicit_header_title(self):
        result = populate_derived_site_metadata(
            {"site_name": "My Hub", "header_title": "Custom Header"}
        )
        self.assertEqual(result["header_title"], "Custom Header")


class TestLoadSiteMetadata(unittest.TestCase):
    """Tests for load_site_metadata error paths."""

    def test_raises_on_invalid_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "site-metadata.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("NOT VALID JSON {{{")

            with self.assertRaises(ValueError) as ctx:
                load_site_metadata(path)
        self.assertIn("Invalid JSON", str(ctx.exception))

    def test_raises_when_json_is_not_an_object(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "site-metadata.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(["not", "a", "dict"], f)

            with self.assertRaises(ValueError) as ctx:
                load_site_metadata(path)
        self.assertIn("must contain a JSON object", str(ctx.exception))

    def test_returns_defaults_when_no_file_exists(self):
        result = load_site_metadata("/nonexistent/path/site-metadata.json")
        self.assertIn("site_name", result)
        self.assertIn("summary_markdown_title", result)


class TestGetArticleSortKey(unittest.TestCase):
    """Tests for get_article_sort_key edge cases."""

    def test_returns_datetime_min_for_unknown_date(self):
        article = {"published": "Unknown"}
        result = get_article_sort_key(article)
        self.assertEqual(result, datetime.min)

    def test_returns_datetime_min_for_missing_published(self):
        article = {}
        result = get_article_sort_key(article)
        self.assertEqual(result, datetime.min)

    def test_returns_datetime_min_for_invalid_date_string(self):
        article = {"published": "not-a-date"}
        result = get_article_sort_key(article)
        self.assertEqual(result, datetime.min)

    def test_returns_parsed_date_for_valid_iso_string(self):
        article = {"published": "2024-01-15T09:00:00Z"}
        result = get_article_sort_key(article)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)


class TestSortArticlesByDate(unittest.TestCase):
    """Tests for sort_articles_by_date."""

    def test_sorts_newest_first_by_default(self):
        articles = [
            {"title": "old", "published": "2024-01-01T00:00:00Z"},
            {"title": "new", "published": "2024-06-01T00:00:00Z"},
        ]
        result = sort_articles_by_date(articles)
        self.assertEqual(result[0]["title"], "new")

    def test_sorts_oldest_first_when_reversed(self):
        articles = [
            {"title": "old", "published": "2024-01-01T00:00:00Z"},
            {"title": "new", "published": "2024-06-01T00:00:00Z"},
        ]
        result = sort_articles_by_date(articles, reverse=False)
        self.assertEqual(result[0]["title"], "old")


if __name__ == "__main__":
    unittest.main()
