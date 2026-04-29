#!/usr/bin/env python3
"""
Unit tests for generate_summary.py
Tests the summary generation functionality for RSS feed collection
"""

# pylint: disable=wrong-import-position,too-many-lines
import json
import os
import tempfile
import unittest

# pylint: disable=wrong-import-position
# flake8: noqa: E402
# Import the functions we want to test
from generate_summary import (
    generate_all_pages,
    generate_feed_articles_content,
    generate_feed_nav,
    generate_feed_slug,
    generate_html_page,
    generate_markdown_summary,
    get_static_site_dir,
    get_template_path,
    inject_website_urls,
)
from utils import DEFAULT_SITE_METADATA

TEMPLATE_PATH = get_template_path()


class TestGenerateSummary(unittest.TestCase):
    """Test cases for summary generation functions"""

    def setUp(self):
        """Set up test data"""
        self.sample_data = {
            "metadata": {
                "collected_at": "2024-01-15T10:30:00Z",
                "since": "2024-01-14T10:30:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 3,
                "successful_feeds": 2,
                "failed_feeds": 1,
                "total_articles": 5,
            },
            "feeds": {
                "Test Blog 1": {
                    "url": "https://example.com/feed1",
                    "count": 3,
                    "articles": [
                        {
                            "title": "Article 1",
                            "link": "https://example.com/article1",
                            "published": "2024-01-15T09:00:00Z",
                        },
                        {
                            "title": "Article 2",
                            "link": "https://example.com/article2",
                            "published": "2024-01-15T08:00:00Z",
                        },
                        {
                            "title": "Article 3",
                            "link": "https://example.com/article3",
                            "published": "2024-01-15T07:00:00Z",
                        },
                    ],
                },
                "Test Blog 2": {
                    "url": "https://example.com/feed2",
                    "count": 2,
                    "articles": [
                        {
                            "title": "Another Article",
                            "link": "https://example.com/article4",
                            "published": "2024-01-15T06:00:00Z",
                        },
                        {
                            "title": "Yet Another Article",
                            "link": "https://example.com/article5",
                            "published": "2024-01-15T05:00:00Z",
                        },
                    ],
                },
            },
            "failed_feeds": [
                {"name": "Failed Feed", "url": "https://example.com/failed"}
            ],
        }

        self.empty_data = {
            "metadata": {
                "collected_at": "2024-01-15T10:30:00Z",
                "since": "2024-01-14T10:30:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 1,
                "successful_feeds": 1,
                "failed_feeds": 0,
                "total_articles": 0,
            },
            "feeds": {
                "Empty Feed": {
                    "url": "https://example.com/empty",
                    "count": 0,
                    "articles": [],
                }
            },
            "failed_feeds": [],
        }
        self.site_metadata = {
            "site_name": "Platform Feed Hub",
            "site_description": "Curated platform engineering news",
            "header_title": "Platform Feed Hub",
            "rss_title": "Platform Feed Hub - All Articles",
            "rss_description": "Aggregated platform engineering news",
            "rss_generator": "Platform Feed Hub RSS Generator",
            "summary_markdown_title": "# 📰 Platform Feed Hub Summary",
            "settings_title": "Settings - Platform Feed Hub",
            "settings_description": (
                "Platform Feed Hub Settings - Configure your RSS feed preferences"
            ),
        }

    def test_generate_markdown_summary_basic(self):
        """Test basic markdown summary generation"""
        result = generate_markdown_summary(self.sample_data)

        # Check that result is a string
        self.assertIsInstance(result, str)

        # Check for key sections
        self.assertIn("# 📰 DevOps Feed Hub Summary", result)
        self.assertIn("## 📊 Summary", result)
        self.assertIn("## ✅ Successful Feeds", result)
        self.assertIn("## ❌ Failed Feeds", result)

        # Check for metadata
        self.assertIn("Collected at:", result)
        self.assertIn("Time range:** Last 24 hours", result)

        # Check for summary stats
        self.assertIn("Total feeds:** 3", result)
        self.assertIn("Successful:** 2", result)
        self.assertIn("Failed:** 1", result)
        self.assertIn("Total articles:** 5", result)

    def test_generate_markdown_summary_feed_content(self):
        """Test that feed content is included in markdown"""
        result = generate_markdown_summary(self.sample_data)

        # Check for feed names
        self.assertIn("Test Blog 1", result)
        self.assertIn("Test Blog 2", result)

        # Check for article titles
        self.assertIn("Article 1", result)
        self.assertIn("Another Article", result)

        # Check for failed feed
        self.assertIn("Failed Feed", result)

    def test_generate_markdown_summary_empty_feeds(self):
        """Test markdown generation with empty feeds"""
        result = generate_markdown_summary(self.empty_data)

        # Should still have basic structure
        self.assertIn("# 📰 DevOps Feed Hub Summary", result)
        self.assertIn("## 📊 Summary", result)

        # Should indicate no articles
        self.assertIn("Total articles:** 0", result)
        self.assertIn("*No new articles*", result)

        # Should not have failed feeds section
        self.assertNotIn("## ❌ Failed Feeds", result)

    def test_generate_html_page_basic(self):
        """Test basic HTML page generation"""
        result = generate_html_page(self.sample_data)

        # Check that result is a string
        self.assertIsInstance(result, str)

        # Check for HTML structure
        self.assertIn("<!doctype html>", result)
        self.assertIn(
            '<html lang="en"', result
        )  # Updated to allow for data-theme attribute
        self.assertIn("</html>", result)

        # Check for key sections - no emojis in new design
        self.assertIn("DevOps Feed Hub", result)
        # The new design doesn't have h1/h2 headers with emojis on the main page
        # Instead it has feed sections with h3 headers

    def test_generate_html_page_content(self):
        """Test that HTML page includes all content"""
        result = generate_html_page(self.sample_data)

        # Check for feed names
        self.assertIn("Test Blog 1", result)
        self.assertIn("Test Blog 2", result)

        # Check for article titles
        self.assertIn("Article 1", result)
        self.assertIn("Another Article", result)

        # Check for article links
        self.assertIn("https://example.com/article1", result)
        self.assertIn("https://example.com/article4", result)

        # Failed feeds are now on the summary page, not a separate failed-feeds.html page
        self.assertNotIn('href="failed-feeds.html"', result)
        # Failed feed details should NOT be in the main page
        self.assertNotIn("https://example.com/failed", result)

    def test_generate_html_page_stats(self):
        """Test that HTML page includes correct statistics on summary page"""
        result = generate_html_page(self.sample_data, current_feed="summary")

        # Check for stats values on summary page
        self.assertIn(">3</div>", result)  # total_feeds
        self.assertIn(">2</div>", result)  # successful_feeds
        self.assertIn(">1</div>", result)  # failed_feeds
        self.assertIn(">5</div>", result)  # total_articles

    def test_generate_summary_page_does_not_emit_python_comments(self):
        """Test that summary page HTML does not include stray source comments."""
        result = generate_html_page(self.sample_data, current_feed="summary")

        self.assertNotIn("# noqa", result)

    def test_generate_html_page_responsive(self):
        """Test that HTML page includes responsive design"""
        result = generate_html_page(self.sample_data)

        # Check for viewport meta tag
        self.assertIn('name="viewport"', result)
        self.assertIn("width=device-width", result)

        # CSS is now external with cache-busting version parameter
        self.assertIn('link rel="stylesheet" href="styles.css?v=', result)

    def test_generate_html_page_empty_feeds(self):
        """Test HTML generation with empty feeds"""
        result = generate_html_page(self.empty_data)

        # Should still have basic structure
        self.assertIn("<!doctype html>", result)
        self.assertIn("DevOps Feed Hub", result)

        # Should indicate no articles (shown in article count badge)
        self.assertIn("0 articles", result)
        self.assertIn("No new articles", result)

        # Should not have failed feeds section on main page (no emojis)
        self.assertNotIn("<h2>Failed Feeds</h2>", result)

    def test_generate_markdown_summary_uses_site_metadata(self):
        """Test markdown summary branding can be driven by metadata."""
        result = generate_markdown_summary(self.sample_data, self.site_metadata)

        self.assertIn("# 📰 Platform Feed Hub Summary", result)

    def test_generate_markdown_summary_merges_partial_site_metadata(self):
        """Test markdown summary derives missing branding fields from overrides."""
        result = generate_markdown_summary(
            self.sample_data, {"site_name": "Platform Feed Hub"}
        )

        self.assertIn("# 📰 Platform Feed Hub Summary", result)

    def test_generate_html_page_uses_site_metadata(self):
        """Test HTML page branding can be driven by metadata."""
        result = generate_html_page(self.sample_data, site_metadata=self.site_metadata)

        self.assertIn("<title>Platform Feed Hub</title>", result)
        self.assertIn("Curated platform engineering news", result)
        self.assertIn("Platform Feed Hub", result)
        self.assertIn(
            'title="Platform Feed Hub - All Articles"',
            result,
        )

    def test_generate_html_page_merges_partial_site_metadata(self):
        """Test HTML page branding derives missing fields from partial overrides."""
        result = generate_html_page(
            self.sample_data,
            site_metadata={"site_name": "Platform Feed Hub"},
        )

        self.assertIn("<title>Platform Feed Hub</title>", result)
        self.assertIn(
            DEFAULT_SITE_METADATA["site_description"],
            result,
        )
        self.assertIn(
            'title="DevOps Feed Hub - All Articles"',
            result,
        )

    def test_markdown_table_formatting(self):
        """Test that markdown tables are properly formatted"""
        result = generate_markdown_summary(self.sample_data)

        # Check for table headers
        self.assertIn("| Title | Published |", result)
        self.assertIn("|-------|-----------|", result)

    def test_html_escaping(self):
        """Test that special characters are properly escaped in HTML"""
        # Create data with special characters that need escaping
        special_data = self.sample_data.copy()
        special_data["feeds"] = {
            "Test Blog <script>": {
                "url": "https://example.com/feed",
                "count": 1,
                "articles": [
                    {
                        "title": 'Article with <script>alert("XSS")</script>',
                        "link": "https://example.com/article?test=1&other=2",
                        "published": "2024-01-15T09:00:00Z",
                    }
                ],
            }
        }

        result = generate_html_page(special_data)

        # The dangerous content should be escaped
        self.assertNotIn('<script>alert("XSS")</script>', result)
        self.assertIn("&lt;script&gt;", result)
        # Link special characters should be escaped
        self.assertIn("&amp;", result)
        # Feed name should be escaped
        self.assertIn("Test Blog &lt;script&gt;", result)

    def test_long_article_title_truncation(self):
        """Test that long article titles are truncated in markdown"""
        long_title_data = self.sample_data.copy()
        long_title = "A" * 100  # 100 character title
        long_title_data["feeds"]["Test Blog 1"]["articles"][0]["title"] = long_title

        result = generate_markdown_summary(long_title_data)

        # Should be truncated with ellipsis
        self.assertIn("...", result)

    def test_multiple_articles_display_limit(self):
        """Test that markdown limits article display to 10 per feed"""
        # Create data with more than 10 articles
        many_articles_data = self.sample_data.copy()
        articles = [
            {
                "title": f"Article {i}",
                "link": f"https://example.com/article{i}",
                "published": "2024-01-15T09:00:00Z",
            }
            for i in range(15)
        ]
        many_articles_data["feeds"]["Test Blog 1"]["articles"] = articles
        many_articles_data["feeds"]["Test Blog 1"]["count"] = 15

        result = generate_markdown_summary(many_articles_data)

        # Should indicate there are more articles
        self.assertIn("...and 5 more articles", result)

    def test_template_file_loading(self):
        """Test that template file is loaded correctly"""
        # This should work with default template
        result = generate_html_page(self.sample_data)

        # Check that template elements are present
        self.assertIn("<!doctype html>", result)
        self.assertIn('<html lang="en"', result)
        self.assertIn("data-theme=", result)  # Dark mode attribute

    def test_template_with_custom_path(self):
        """Test HTML generation with custom template path"""
        # Create a custom template
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".html", encoding="utf-8"
        ) as f:
            custom_template = f.name
            f.write(
                """<!doctype html>
<html>
<head><title>Custom Template</title></head>
<body>
<!-- CONTENT_PLACEHOLDER -->
<footer>Updated: <!-- TIMESTAMP_PLACEHOLDER --></footer>
</body>
</html>"""
            )

        try:
            result = generate_html_page(self.sample_data, custom_template)

            # Check custom template elements
            self.assertIn("Custom Template", result)
            self.assertIn("<footer>Updated:", result)

            # Check that content was injected
            self.assertIn("Test Blog 1", result)
        finally:
            if os.path.exists(custom_template):
                os.remove(custom_template)

    def test_template_file_not_found(self):
        """Test error handling when template file doesn't exist"""
        with self.assertRaises(FileNotFoundError) as context:
            generate_html_page(self.sample_data, "/nonexistent/path/template.html")

        # Check error message is descriptive
        self.assertIn("not found", str(context.exception).lower())
        self.assertIn("template", str(context.exception).lower())

    def test_template_utf8_encoding(self):
        """Test that template handles UTF-8 characters correctly"""
        # Create template with UTF-8 characters
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".html", encoding="utf-8"
        ) as f:
            utf8_template = f.name
            f.write(
                """<!doctype html>
<html>
<head><title>Test 🌙☀️</title></head>
<body>
<!-- CONTENT_PLACEHOLDER -->
<footer><!-- TIMESTAMP_PLACEHOLDER --></footer>
</body>
</html>"""
            )

        try:
            result = generate_html_page(self.sample_data, utf8_template)

            # Check UTF-8 characters are preserved
            self.assertIn("🌙", result)
            self.assertIn("☀️", result)
        finally:
            if os.path.exists(utf8_template):
                os.remove(utf8_template)

    def test_dark_mode_elements(self):
        """Test that dark mode toggle elements are present"""
        result = generate_html_page(self.sample_data)

        # Check for dark mode toggle button
        self.assertIn("theme-toggle", result)
        self.assertIn('aria-label="Toggle theme"', result)

        # Check for SVG icons (new design uses SVG, not emoji)
        self.assertIn("<svg", result)
        self.assertIn('id="theme-icon"', result)

        # Check for theme script (external JS file)
        self.assertIn('script src="script.js"', result)
        self.assertIn("data-theme", result)

    def test_placeholder_replacement(self):
        """Test that placeholders are correctly replaced"""
        result = generate_html_page(self.sample_data)

        # Placeholders should be replaced
        self.assertNotIn("<!-- CONTENT_PLACEHOLDER -->", result)
        self.assertNotIn("<!-- TIMESTAMP_PLACEHOLDER -->", result)

        # Content should be present
        self.assertIn("Test Blog 1", result)

        # Timestamp should be formatted correctly
        self.assertIn("January", result)
        self.assertIn("2024", result)
        self.assertIn("UTC", result)


class TestSummaryIntegration(unittest.TestCase):
    """Integration tests for summary generation"""

    def test_write_markdown_to_file(self):
        """Test writing markdown summary to a file"""
        sample_data = {
            "metadata": {
                "collected_at": "2024-01-15T10:30:00Z",
                "since": "2024-01-14T10:30:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 1,
                "successful_feeds": 1,
                "failed_feeds": 0,
                "total_articles": 1,
            },
            "feeds": {
                "Test Feed": {
                    "url": "https://example.com/feed",
                    "count": 1,
                    "articles": [
                        {
                            "title": "Test Article",
                            "link": "https://example.com/article",
                            "published": "2024-01-15T09:00:00Z",
                        }
                    ],
                }
            },
            "failed_feeds": [],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".md", encoding="utf-8"
        ) as f:
            markdown_file = f.name

        try:
            markdown_content = generate_markdown_summary(sample_data)
            with open(markdown_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            # Verify file was written
            self.assertTrue(os.path.exists(markdown_file))

            # Verify content
            with open(markdown_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("Test Feed", content)
            self.assertIn("Test Article", content)
        finally:
            if os.path.exists(markdown_file):
                os.remove(markdown_file)

    def test_write_html_to_file(self):
        """Test writing HTML page to a file"""
        sample_data = {
            "metadata": {
                "collected_at": "2024-01-15T10:30:00Z",
                "since": "2024-01-14T10:30:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 1,
                "successful_feeds": 1,
                "failed_feeds": 0,
                "total_articles": 1,
            },
            "feeds": {
                "Test Feed": {
                    "url": "https://example.com/feed",
                    "count": 1,
                    "articles": [
                        {
                            "title": "Test Article",
                            "link": "https://example.com/article",
                            "published": "2024-01-15T09:00:00Z",
                        }
                    ],
                }
            },
            "failed_feeds": [],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".html", encoding="utf-8"
        ) as f:
            html_file = f.name

        try:
            html_content = generate_html_page(sample_data)
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Verify file was written
            self.assertTrue(os.path.exists(html_file))

            # Verify content
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("<!doctype html>", content)
            self.assertIn("Test Feed", content)
            self.assertIn("Test Article", content)
        finally:
            if os.path.exists(html_file):
                os.remove(html_file)


class TestMultiPageGeneration(unittest.TestCase):
    """Test cases for multi-page generation functionality"""

    def setUp(self):
        """Set up test data"""
        self.sample_data = {
            "metadata": {
                "collected_at": "2024-01-15T10:30:00Z",
                "since": "2024-01-14T10:30:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 2,
                "successful_feeds": 2,
                "failed_feeds": 0,
                "total_articles": 3,
            },
            "feeds": {
                "Test Feed 1": {
                    "url": "https://example.com/feed1",
                    "count": 2,
                    "articles": [
                        {
                            "title": "Article 1",
                            "link": "https://example.com/article1",
                            "published": "2024-01-15T09:00:00Z",
                        },
                        {
                            "title": "Article 2",
                            "link": "https://example.com/article2",
                            "published": "2024-01-15T08:00:00Z",
                        },
                    ],
                },
                "Test Feed 2": {
                    "url": "https://example.com/feed2",
                    "count": 1,
                    "articles": [
                        {
                            "title": "Article 3",
                            "link": "https://example.com/article3",
                            "published": "2024-01-15T07:00:00Z",
                        }
                    ],
                },
            },
            "failed_feeds": [],
        }
        self.site_metadata = {
            "site_name": "Platform Feed Hub",
            "site_description": "Curated platform engineering news",
            "header_title": "Platform Feed Hub",
            "rss_title": "Platform Feed Hub - All Articles",
            "rss_description": "Aggregated platform engineering news",
            "rss_generator": "Platform Feed Hub RSS Generator",
            "summary_markdown_title": "# 📰 Platform Feed Hub Summary",
            "settings_title": "Settings - Platform Feed Hub",
            "settings_description": (
                "Platform Feed Hub Settings - Configure your RSS feed preferences"
            ),
        }

    def test_generate_feed_slug(self):
        """Test feed slug generation"""
        self.assertEqual(generate_feed_slug("Test Feed 1"), "test-feed-1")
        self.assertEqual(generate_feed_slug("GitHub Blog"), "github-blog")
        self.assertEqual(
            generate_feed_slug("Microsoft/DevOps Blog"), "microsoft-devops-blog"
        )
        self.assertEqual(generate_feed_slug("Test@#$%Feed"), "testfeed")
        self.assertEqual(generate_feed_slug("Test--Feed"), "test-feed")
        self.assertEqual(generate_feed_slug("-Test Feed-"), "test-feed")

    def test_generate_feed_nav(self):
        """Test navigation generation"""
        nav_html = generate_feed_nav(self.sample_data["feeds"], None)

        # Check navigation structure
        self.assertIn('class="feed-nav"', nav_html)
        self.assertIn('aria-label="Feed navigation"', nav_html)
        self.assertIn("</nav>", nav_html)

        # Check all feeds link
        self.assertIn('href="index.html"', nav_html)
        self.assertIn("All Feeds", nav_html)

        # Check summary link
        self.assertIn('href="summary.html"', nav_html)
        self.assertIn("Summary", nav_html)

        # Check feed links
        self.assertIn('href="feed-test-feed-1.html"', nav_html)
        self.assertIn('href="feed-test-feed-2.html"', nav_html)
        self.assertIn("Test Feed 1", nav_html)
        self.assertIn("Test Feed 2", nav_html)

    def test_generate_feed_nav_with_current(self):
        """Test navigation with active feed"""
        nav_html = generate_feed_nav(self.sample_data["feeds"], "Test Feed 1")

        # Check that current feed has active class
        self.assertIn('class="nav-link active"', nav_html)

        # Verify the active link is for the current feed
        lines = nav_html.split("\n")
        for line in lines:
            # Skip the feed-list-data script tag
            if "feed-list-data" in line:
                continue
            if "Test Feed 1" in line:
                # The active class should be in the same line
                self.assertIn("active", line)
                break
        else:
            self.fail("Test Feed 1 not found in navigation")

    def test_generate_html_page_with_feed(self):
        """Test HTML page generation for a specific feed"""
        result = generate_html_page(self.sample_data, current_feed="Test Feed 1")

        # Check that only the specified feed appears in articles
        self.assertIn("Test Feed 1", result)
        self.assertIn("Article 1", result)
        self.assertIn("Article 2", result)
        # Test Feed 2's article should not appear
        self.assertIn("Test Feed 2", result)  # Will appear in navigation
        # But Article 3 should not appear in the main content area

        # Check for navigation
        self.assertIn('class="feed-nav"', result)
        self.assertIn('aria-label="Feed navigation"', result)
        self.assertIn('href="index.html"', result)
        self.assertIn('href="feed-test-feed-1.html"', result)

        # Check page title is updated
        self.assertIn("<title>Test Feed 1 - DevOps Feed Hub</title>", result)

        custom_result = generate_html_page(
            self.sample_data,
            current_feed="Test Feed 1",
            site_metadata=self.site_metadata,
        )
        self.assertIn("<title>Test Feed 1 - Platform Feed Hub</title>", custom_result)

    def test_generate_html_page_main_index(self):
        """Test HTML page generation for main index (all feeds)"""
        result = generate_html_page(self.sample_data)

        # Check that all feeds appear
        self.assertIn("Test Feed 1", result)
        self.assertIn("Test Feed 2", result)
        self.assertIn("Article 1", result)
        self.assertIn("Article 2", result)
        self.assertIn("Article 3", result)

        # Check for navigation
        self.assertIn('class="feed-nav"', result)
        self.assertIn('aria-label="Feed navigation"', result)

        # Check that main index link is active
        self.assertIn('class="nav-link active"', result)

    def test_generate_all_pages(self):
        """Test generation of all pages (index + feed pages)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_all_pages(self.sample_data, tmpdir)

            # Check that index.html was created
            index_path = os.path.join(tmpdir, "index.html")
            self.assertTrue(os.path.exists(index_path))

            # Check that feed pages were created
            feed1_path = os.path.join(tmpdir, "feed-test-feed-1.html")
            feed2_path = os.path.join(tmpdir, "feed-test-feed-2.html")
            self.assertTrue(os.path.exists(feed1_path))
            self.assertTrue(os.path.exists(feed2_path))

            # Verify index content
            with open(index_path, "r", encoding="utf-8") as f:
                index_content = f.read()
            self.assertIn("Test Feed 1", index_content)
            self.assertIn("Test Feed 2", index_content)
            self.assertIn("Article 1", index_content)
            self.assertIn("Article 3", index_content)

            # Verify feed 1 content
            with open(feed1_path, "r", encoding="utf-8") as f:
                feed1_content = f.read()
            self.assertIn("Test Feed 1", feed1_content)
            self.assertIn("Article 1", feed1_content)
            self.assertIn("Article 2", feed1_content)

            # Verify feed 2 content
            with open(feed2_path, "r", encoding="utf-8") as f:
                feed2_content = f.read()
            self.assertIn("Test Feed 2", feed2_content)
            self.assertIn("Article 3", feed2_content)

    def test_generate_all_pages_creates_directory(self):
        """Test that generate_all_pages creates output directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "nested", "output")
            # Directory doesn't exist yet
            self.assertFalse(os.path.exists(output_dir))

            generate_all_pages(self.sample_data, output_dir)

            # Directory should now exist
            self.assertTrue(os.path.exists(output_dir))
            # And contain files
            self.assertTrue(os.path.exists(os.path.join(output_dir, "index.html")))

    def test_feed_page_navigation_links(self):
        """Test that feed pages have correct navigation links"""
        result = generate_html_page(self.sample_data, current_feed="Test Feed 1")

        # Should have links to index and other feeds
        self.assertIn('href="index.html"', result)
        self.assertIn('href="feed-test-feed-1.html"', result)
        self.assertIn('href="feed-test-feed-2.html"', result)

    def test_single_feed_shows_only_its_articles(self):
        """Test that single feed page shows only articles from that feed"""
        result = generate_html_page(self.sample_data, current_feed="Test Feed 1")

        # Count article items with data-published attribute - should only have 2 for Test Feed 1
        article_count = result.count('class="article-item" data-published=')
        self.assertEqual(article_count, 2)

        # Verify correct articles are shown
        self.assertIn("Article 1", result)
        self.assertIn("Article 2", result)

    def test_feed_page_title_appears_only_once(self):
        """Test that individual feed pages show the feed title exactly once (not twice)"""
        result = generate_html_page(self.sample_data, current_feed="Test Feed 1")

        # The feed name should appear exactly once as an h2 heading in the content area
        h2_count = result.count("<h2>Test Feed 1")
        self.assertEqual(h2_count, 1, "Feed title should appear exactly once as h2")

    def test_feed_page_title_escaping(self):
        """Test that feed names with special characters are escaped in page title"""
        special_data = self.sample_data.copy()
        special_data["feeds"] = {
            "Test <script>alert('XSS')</script>": {
                "url": "https://example.com/feed",
                "count": 0,
                "articles": [],
            }
        }

        result = generate_html_page(
            special_data, current_feed="Test <script>alert('XSS')</script>"
        )

        # Title should be escaped
        self.assertIn("&lt;script&gt;", result)
        self.assertNotIn("<script>alert('XSS')</script>", result)

    def test_generate_feed_nav_with_failed_feeds(self):
        """Test navigation includes summary link (failed feeds now shown on summary page)"""
        data_with_failures = self.sample_data.copy()
        data_with_failures["failed_feeds"] = [
            {"name": "Failed Feed", "url": "https://example.com/failed"}
        ]

        nav_html = generate_feed_nav(data_with_failures["feeds"], None)

        # Check summary link appears (failed feeds are now on summary page)
        self.assertIn('href="summary.html"', nav_html)
        self.assertIn("Summary", nav_html)

    def test_generate_feed_nav_without_failed_feeds(self):
        """Test navigation includes summary link"""
        nav_html = generate_feed_nav(self.sample_data["feeds"], None)

        # Check summary link appears
        self.assertIn('href="summary.html"', nav_html)
        self.assertIn("Summary", nav_html)

    def test_generate_failed_feeds_page(self):
        """Test generation of failed feeds page (now part of summary page)"""
        data_with_failures = self.sample_data.copy()
        data_with_failures["failed_feeds"] = [
            {"name": "Failed Feed 1", "url": "https://example.com/failed1"},
            {"name": "Failed Feed 2", "url": "https://example.com/failed2"},
        ]

        # Failed feeds are now shown on the summary page, not a separate page
        result = generate_html_page(data_with_failures, current_feed="summary")

        # Check for failed feeds section (no emoji in new design)
        self.assertIn("<h2>Failed Feeds</h2>", result)
        self.assertIn("Failed Feed 1", result)
        self.assertIn("Failed Feed 2", result)
        self.assertIn("https://example.com/failed1", result)
        self.assertIn("https://example.com/failed2", result)

        # Summary page should also have stats (with new title)
        self.assertIn("<h2>Feed Collection Summary</h2>", result)
        self.assertIn("Error: Unknown", result)  # Should show error reason

    def test_generate_all_pages_with_failed_feeds(self):
        """Test that generate_all_pages includes failed feeds on summary page"""
        data_with_failures = self.sample_data.copy()
        data_with_failures["failed_feeds"] = [
            {"name": "Failed Feed", "url": "https://example.com/failed"}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            generate_all_pages(data_with_failures, tmpdir)

            # Failed feeds are now on summary.html, not failed-feeds.html
            summary_path = os.path.join(tmpdir, "summary.html")
            self.assertTrue(os.path.exists(summary_path))

            # Verify failed feeds appear on summary page
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_content = f.read()
            self.assertIn("Failed Feed", summary_content)
            self.assertIn("https://example.com/failed", summary_content)
            # Check page title
            self.assertIn("<title>Summary - DevOps Feed Hub</title>", summary_content)

            settings_path = os.path.join(tmpdir, "settings.html")
            with open(settings_path, "r", encoding="utf-8") as file:
                settings_content = file.read()

            self.assertNotIn("SETTINGS_TITLE_PLACEHOLDER", settings_content)
            self.assertIn("<title>Settings - DevOps Feed Hub</title>", settings_content)

    def test_generate_all_pages_without_failed_feeds(self):
        """Test generate_all_pages without failed feeds page"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_all_pages(self.sample_data, tmpdir)

            # Check that failed-feeds.html was NOT created
            failed_path = os.path.join(tmpdir, "failed-feeds.html")
            self.assertFalse(os.path.exists(failed_path))

    def test_alphabetical_feed_ordering(self):
        """Test that feeds are displayed in alphabetical order"""
        # Create data with feeds in non-alphabetical order
        unordered_data = self.sample_data.copy()
        unordered_data["feeds"] = {
            "Zebra Blog": {
                "url": "https://example.com/zebra",
                "count": 1,
                "articles": [
                    {
                        "title": "Zebra Article",
                        "link": "https://example.com/zebra/1",
                        "published": "2024-01-15T09:00:00Z",
                    }
                ],
            },
            "Apple Blog": {
                "url": "https://example.com/apple",
                "count": 1,
                "articles": [
                    {
                        "title": "Apple Article",
                        "link": "https://example.com/apple/1",
                        "published": "2024-01-15T09:00:00Z",
                    }
                ],
            },
            "Microsoft Blog": {
                "url": "https://example.com/microsoft",
                "count": 1,
                "articles": [
                    {
                        "title": "Microsoft Article",
                        "link": "https://example.com/microsoft/1",
                        "published": "2024-01-15T09:00:00Z",
                    }
                ],
            },
        }

        result = generate_html_page(unordered_data)

        # Find positions of feed names in the HTML
        apple_pos = result.find(">Apple Blog<")
        microsoft_pos = result.find(">Microsoft Blog<")
        zebra_pos = result.find(">Zebra Blog<")

        # All should be found
        self.assertNotEqual(apple_pos, -1)
        self.assertNotEqual(microsoft_pos, -1)
        self.assertNotEqual(zebra_pos, -1)

        # Check they appear in alphabetical order
        self.assertLess(apple_pos, microsoft_pos)
        self.assertLess(microsoft_pos, zebra_pos)

    def test_template_no_hardcoded_selected_attribute(self):
        """Test that template.html does not have hardcoded selected."""
        import re  # pylint: disable=import-outside-toplevel

        # Read the template file
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template_content = f.read()

        # Check that there's no selected attribute in any option tag
        # This prevents the timeframe selector bug where hardcoded selected
        # prevents JavaScript from setting the correct value from localStorage
        # Use regex to catch all variations
        selected_pattern = re.compile(r"<option[^>]*\sselected[\s>=]", re.IGNORECASE)
        match = selected_pattern.search(template_content)

        self.assertIsNone(
            match,
            f"Template should not have hardcoded 'selected' attribute. "
            f"Found at {match.start() if match else 'N/A'}: "
            f"{match.group() if match else 'N/A'}. "
            f"JavaScript should set timeframe from localStorage.",
        )

    def test_failed_feeds_with_error_reasons(self):
        """Test that failed feeds display error reasons"""
        data_with_errors = self.sample_data.copy()
        data_with_errors["failed_feeds"] = [
            {
                "name": "Broken Feed",
                "url": "https://example.com/broken",
                "error": "HTTP 404: Not Found",
            },
            {
                "name": "Timeout Feed",
                "url": "https://example.com/timeout",
                "error": "Connection timeout",
            },
        ]

        result = generate_html_page(data_with_errors, current_feed="summary")

        # Check that error reasons are displayed
        self.assertIn("Error: HTTP 404: Not Found", result)
        self.assertIn("Error: Connection timeout", result)
        self.assertIn("failed-feed-error", result)

    def test_failed_feeds_without_error_defaults_to_unknown(self):
        """Test that failed feeds without error field default to 'Unknown'"""
        data_without_errors = self.sample_data.copy()
        data_without_errors["failed_feeds"] = [
            {"name": "Old Feed", "url": "https://example.com/old"}
        ]


class TestFeedListJSON(unittest.TestCase):
    """Test feed list JSON generation for settings page"""

    def test_feed_list_json_embedded_in_html(self):
        """Test that feed names are embedded as JSON in generated HTML"""
        data = {
            "metadata": {
                "collected_at": "2026-01-10T00:00:00Z",
                "since": "2026-01-09T00:00:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 2,
                "successful_feeds": 2,
                "failed_feeds": 0,
                "total_articles": 2,
            },
            "feeds": {
                "Test Feed 1": {
                    "url": "https://example.com/feed1",
                    "count": 1,
                    "articles": [
                        {
                            "title": "Article 1",
                            "link": "https://example.com/1",
                            "published": "2026-01-10T00:00:00Z",
                        }
                    ],
                },
                "Test Feed 2": {
                    "url": "https://example.com/feed2",
                    "count": 1,
                    "articles": [
                        {
                            "title": "Article 2",
                            "link": "https://example.com/2",
                            "published": "2026-01-10T00:00:00Z",
                        }
                    ],
                },
            },
            "failed_feeds": [],
        }

        html = generate_html_page(data)

        # Check that feed list JSON script tag exists
        self.assertIn('id="feed-list-data"', html)
        self.assertIn('type="application/json"', html)

        # Check that feed names are in the JSON
        self.assertIn("Test Feed 1", html)
        self.assertIn("Test Feed 2", html)

    def test_feed_list_json_is_html_escaped(self):
        """Test that feed list JSON is HTML-escaped to prevent XSS"""
        data = {
            "metadata": {
                "collected_at": "2026-01-10T00:00:00Z",
                "since": "2026-01-09T00:00:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 1,
                "successful_feeds": 1,
                "failed_feeds": 0,
                "total_articles": 1,
            },
            "feeds": {
                'Test Feed <script>alert("XSS")</script>': {
                    "url": "https://example.com/feed1",
                    "count": 1,
                    "articles": [
                        {
                            "title": "Article",
                            "link": "https://example.com/1",
                            "published": "2026-01-10T00:00:00Z",
                        }
                    ],
                },
            },
            "failed_feeds": [],
        }

        html = generate_html_page(data)

        # Check that the script tag content is escaped
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;/script&gt;", html)

        # Ensure raw script tag is NOT present in feed list JSON
        # (it might be in other parts of HTML as valid script tags)
        feed_list_start = html.find('id="feed-list-data"')
        if feed_list_start != -1:
            feed_list_end = html.find("</script>", feed_list_start)
            feed_list_section = html[feed_list_start:feed_list_end]
            self.assertNotIn('alert("XSS")', feed_list_section)

    def test_feed_list_json_with_special_characters(self):
        """Test that feed names with special characters are properly escaped"""
        data = {
            "metadata": {
                "collected_at": "2026-01-10T00:00:00Z",
                "since": "2026-01-09T00:00:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 2,
                "successful_feeds": 2,
                "failed_feeds": 0,
                "total_articles": 2,
            },
            "feeds": {
                "Feed & Company": {
                    "url": "https://example.com/feed1",
                    "count": 1,
                    "articles": [
                        {
                            "title": "Article",
                            "link": "https://example.com/1",
                            "published": "2026-01-10T00:00:00Z",
                        }
                    ],
                },
                'Feed "Quotes"': {
                    "url": "https://example.com/feed2",
                    "count": 1,
                    "articles": [
                        {
                            "title": "Article",
                            "link": "https://example.com/2",
                            "published": "2026-01-10T00:00:00Z",
                        }
                    ],
                },
            },
            "failed_feeds": [],
        }

        html = generate_html_page(data)

        # Feed list JSON should contain escaped characters
        feed_list_start = html.find('id="feed-list-data"')
        self.assertNotEqual(feed_list_start, -1, "feed-list-data element should exist")

    def test_feed_list_json_empty_feeds(self):
        """Test feed list JSON with no feeds"""
        data = {
            "metadata": {
                "collected_at": "2026-01-10T00:00:00Z",
                "since": "2026-01-09T00:00:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 0,
                "successful_feeds": 0,
                "failed_feeds": 0,
                "total_articles": 0,
            },
            "feeds": {},
            "failed_feeds": [],
        }

        html = generate_html_page(data)

        # Should still have the feed-list-data element
        self.assertIn('id="feed-list-data"', html)

        # Should contain empty array
        self.assertIn("[]", html)

    def test_feed_list_json_multiple_feeds(self):
        """Test feed list JSON with multiple feeds"""
        data = {
            "metadata": {
                "collected_at": "2026-01-10T00:00:00Z",
                "since": "2026-01-09T00:00:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 4,
                "successful_feeds": 4,
                "failed_feeds": 0,
                "total_articles": 0,
            },
            "feeds": {
                "Alpha Feed": {
                    "url": "https://example.com/feed1",
                    "count": 0,
                    "articles": [],
                },
                "Beta Feed": {
                    "url": "https://example.com/feed2",
                    "count": 0,
                    "articles": [],
                },
                "Gamma Feed": {
                    "url": "https://example.com/feed3",
                    "count": 0,
                    "articles": [],
                },
                "Delta Feed": {
                    "url": "https://example.com/feed4",
                    "count": 0,
                    "articles": [],
                },
            },
            "failed_feeds": [],
        }

        html = generate_html_page(data)

        # All feed names should be present
        self.assertIn("Alpha Feed", html)
        self.assertIn("Beta Feed", html)
        self.assertIn("Gamma Feed", html)
        self.assertIn("Delta Feed", html)


class TestDeploymentScriptIssues(unittest.TestCase):
    """Test fixes for 404 issues and deployment problems"""

    def test_settings_html_exists(self):
        """Test that static settings.html is sourced and copied into site output."""
        static_settings_path = get_static_site_dir() / "settings.html"
        self.assertTrue(static_settings_path.is_file())

        with open(static_settings_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<!doctype html>", content.lower())
        self.assertIn("settings", content.lower())

        sample_data = {
            "metadata": {
                "collected_at": "2026-01-10T00:00:00Z",
                "since": "2026-01-09T00:00:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 1,
                "successful_feeds": 1,
                "failed_feeds": 0,
                "total_articles": 0,
            },
            "feeds": {
                "Test Feed": {
                    "url": "https://example.com/feed",
                    "count": 0,
                    "articles": [],
                }
            },
            "failed_feeds": [],
        }
        with tempfile.TemporaryDirectory() as output_dir:
            generate_all_pages(sample_data, output_dir)
            self.assertTrue(os.path.isfile(os.path.join(output_dir, "settings.html")))
            self.assertTrue(os.path.isfile(os.path.join(output_dir, "styles.css")))
            self.assertTrue(os.path.isfile(os.path.join(output_dir, "script.js")))

    def test_feed_pages_generation_with_new_feeds(self):
        """Test that feed pages can be generated for new DevOps feeds"""
        # Test data with feeds that were added in this PR
        data = {
            "metadata": {
                "collected_at": "2026-01-10T00:00:00Z",
                "since": "2026-01-09T00:00:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 3,
                "successful_feeds": 3,
                "failed_feeds": 0,
                "total_articles": 0,
            },
            "feeds": {
                "Docker Blog": {
                    "url": "https://www.docker.com/blog/feed/",
                    "count": 0,
                    "articles": [],
                },
                "Kubernetes Blog": {
                    "url": "https://kubernetes.io/feed.xml",
                    "count": 0,
                    "articles": [],
                },
                "AWS DevOps Blog": {
                    "url": "https://aws.amazon.com/blogs/devops/feed/",
                    "count": 0,
                    "articles": [],
                },
            },
            "failed_feeds": [],
        }

        # Should be able to generate HTML for new feeds
        html = generate_html_page(data)
        self.assertIsNotNone(html)

        # Navigation should include new feeds
        self.assertIn("Docker Blog", html)
        self.assertIn("Kubernetes Blog", html)
        self.assertIn("AWS DevOps Blog", html)

        # Should be able to generate individual feed pages
        for feed_name in ["Docker Blog", "Kubernetes Blog", "AWS DevOps Blog"]:
            feed_html = generate_html_page(data, current_feed=feed_name)
            self.assertIsNotNone(feed_html)
            self.assertIn(feed_name, feed_html)


class TestFeedTitleLinks(unittest.TestCase):
    """Test feed title hyperlink functionality"""

    def _make_feed_data(self, website_url=None):
        """Helper to create minimal feed data with optional website_url."""
        feed = {
            "url": "https://example.com/feed",
            "count": 1,
            "articles": [
                {
                    "title": "Test Article",
                    "link": "https://example.com/article1",
                    "published": "2024-01-15T09:00:00Z",
                }
            ],
        }
        if website_url is not None:
            feed["website_url"] = website_url
        return feed

    def test_feed_title_is_link_when_website_url_present(self):
        """Feed h2 title should be a hyperlink when website_url is in feed data."""
        feeds = {"My Blog": self._make_feed_data("https://myblog.example.com/")}
        html = generate_feed_articles_content(feeds)

        self.assertIn('class="feed-title-link"', html)
        self.assertIn('href="https://myblog.example.com/"', html)
        self.assertIn('target="_blank"', html)
        self.assertIn('rel="noopener noreferrer"', html)
        self.assertIn(">My Blog<", html)

    def test_feed_title_is_plain_text_when_no_website_url(self):
        """Feed h2 title should be plain text when website_url is absent."""
        feeds = {"My Blog": self._make_feed_data()}
        html = generate_feed_articles_content(feeds)

        self.assertNotIn('class="feed-title-link"', html)
        self.assertNotIn("feed-title-link", html)
        # Title text should still appear
        self.assertIn("My Blog", html)

    def test_feed_title_link_website_url_is_escaped(self):
        """website_url with special HTML characters should be properly escaped."""
        feeds = {"My Blog": self._make_feed_data("https://example.com/?a=1&b=2")}
        html = generate_feed_articles_content(feeds)

        self.assertIn("&amp;", html)
        self.assertNotIn('"https://example.com/?a=1&b=2"', html)
        # Full escaped URL should appear in the href
        self.assertIn('href="https://example.com/?a=1&amp;b=2"', html)

    def test_feed_title_link_xss_in_website_url(self):
        """Malicious website_url should be HTML-escaped so no raw attribute injection."""
        feeds = {
            "My Blog": self._make_feed_data(
                'https://example.com/" onmouseover="alert(1)'
            )
        }
        html = generate_feed_articles_content(feeds)

        # The raw unescaped injection must not appear in the HTML
        self.assertNotIn('" onmouseover="alert(1)', html)
        # The quotes should be HTML-escaped
        self.assertIn("&quot;", html)

    def test_inject_website_urls_from_config(self):
        """inject_website_urls reads website_url from a config file."""
        config = {
            "feeds": [
                {
                    "name": "Test Blog",
                    "url": "https://example.com/feed",
                    "website_url": "https://example.com/",
                }
            ]
        }
        data = {
            "feeds": {
                "Test Blog": {
                    "url": "https://example.com/feed",
                    "count": 0,
                    "articles": [],
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json", encoding="utf-8"
        ) as f:
            json_path = f.name
            json.dump(config, f)

        try:
            inject_website_urls(data, json_path)
            self.assertEqual(
                data["feeds"]["Test Blog"].get("website_url"), "https://example.com/"
            )
        finally:
            os.remove(json_path)

    def test_inject_website_urls_does_not_overwrite_existing(self):
        """inject_website_urls must not overwrite an existing website_url in feed data."""
        config = {
            "feeds": [
                {
                    "name": "Test Blog",
                    "url": "https://example.com/feed",
                    "website_url": "https://config-url.example.com/",
                }
            ]
        }
        data = {
            "feeds": {
                "Test Blog": {
                    "url": "https://example.com/feed",
                    "website_url": "https://fixture-url.example.com/",
                    "count": 0,
                    "articles": [],
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json", encoding="utf-8"
        ) as f:
            json_path = f.name
            json.dump(config, f)

        try:
            inject_website_urls(data, json_path)
            # Existing value should be preserved
            self.assertEqual(
                data["feeds"]["Test Blog"]["website_url"],
                "https://fixture-url.example.com/",
            )
        finally:
            os.remove(json_path)

    def test_inject_website_urls_missing_file(self):
        """inject_website_urls silently skips when config file is missing."""
        data = {
            "feeds": {
                "Test Blog": {
                    "url": "https://example.com/feed",
                    "count": 0,
                    "articles": [],
                }
            }
        }
        # Should not raise; feed data should be unchanged
        inject_website_urls(data, "/nonexistent/path/feeds.json")
        self.assertNotIn("website_url", data["feeds"]["Test Blog"])

    def test_inject_website_urls_skips_entries_without_name(self):
        """inject_website_urls must not raise when a config entry has no 'name' key."""
        config = {
            "feeds": [
                # Entry with no name should be silently skipped
                {
                    "url": "https://example.com/feed",
                    "website_url": "https://example.com/",
                },
                {
                    "name": "Named Blog",
                    "url": "https://named.example.com/feed",
                    "website_url": "https://named.example.com/",
                },
            ]
        }
        data = {
            "feeds": {
                "Named Blog": {
                    "url": "https://named.example.com/feed",
                    "count": 0,
                    "articles": [],
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json", encoding="utf-8"
        ) as f:
            json_path = f.name
            json.dump(config, f)

        try:
            inject_website_urls(data, json_path)
            # Named entry should get its website_url
            self.assertEqual(
                data["feeds"]["Named Blog"]["website_url"],
                "https://named.example.com/",
            )
        finally:
            os.remove(json_path)

    def test_feed_title_link_in_full_html_page(self):
        """Full HTML page should contain the feed title hyperlink."""
        sample_data = {
            "metadata": {
                "collected_at": "2024-01-15T10:30:00Z",
                "since": "2024-01-14T10:30:00Z",
                "hours": 24,
            },
            "summary": {
                "total_feeds": 1,
                "successful_feeds": 1,
                "failed_feeds": 0,
                "total_articles": 1,
            },
            "feeds": {
                "My Blog": {
                    "url": "https://example.com/feed",
                    "website_url": "https://myblog.example.com/",
                    "count": 1,
                    "articles": [
                        {
                            "title": "Test Article",
                            "link": "https://example.com/article1",
                            "published": "2024-01-15T09:00:00Z",
                        }
                    ],
                }
            },
            "failed_feeds": [],
        }

        html = generate_html_page(sample_data)

        self.assertIn('class="feed-title-link"', html)
        self.assertIn('href="https://myblog.example.com/"', html)
