import { test } from "@playwright/test";

/**
 * Screenshot Generator for Themes
 * Generates screenshots of different themes for documentation
 */

const themes = [
  { name: "classic", category: "theme" },
  // Color variations (Beta themes)
  { name: "purple-haze", category: "theme" },
  { name: "ocean-deep", category: "theme" },
  { name: "monochrome", category: "theme" },

  // Themed styles (Beta themes)
  { name: "minimalist", category: "theme" },
  { name: "terminal", category: "theme" },
  { name: "magazine", category: "theme" },
  { name: "newspaper", category: "theme" },
  { name: "retro", category: "theme" },
  { name: "futuristic", category: "theme" },
  { name: "compact", category: "theme" },

  // Alternative layouts (Beta viewmodes)
  { name: "horizontal-scroll", category: "viewmode" },
  { name: "masonry-grid", category: "viewmode" },
  { name: "center-stage", category: "viewmode" },
];

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.waitForLoadState("load");
  await page.evaluate(() => localStorage.clear());
});

for (const theme of themes) {
  test(`screenshot: ${theme.name} (${theme.category})`, async ({ page }) => {
    // Navigate to settings page
    await page.goto("/settings.html");
    await page.waitForLoadState("load");

    // Use appropriate selector based on category
    if (theme.category === "viewmode") {
      // Set beta view mode
      await page.locator("#view-setting").selectOption(theme.name);
    } else {
      // Set beta theme
      await page.locator("#theme-setting").selectOption(theme.name);
    }

    // Go to index page for screenshot
    await page.goto("/");
    await page.waitForLoadState("load");
    await page.waitForTimeout(500); // Let theme apply

    // Take screenshot
    await page.screenshot({
      path: `/tmp/theme-${theme.name}.png`,
      fullPage: false,
    });
  });
}
