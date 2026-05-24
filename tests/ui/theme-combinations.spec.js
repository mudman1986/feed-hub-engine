/**
 * Theme Combinations Tests
 * Validates all combinations of themes, view modes, and dark/light modes work correctly
 */

const { test, expect } = require("@playwright/test");

test.describe("Theme Combinations - All Settings", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => localStorage.clear());
  });

  // All themes to test
  const themes = [
    "default",
    "classic",
    "purple-haze",
    "ocean-deep",
    "arctic-blue",
    "high-contrast",
    "monochrome",
    "minimalist",
    "terminal",
    "magazine",
    "newspaper",
    "retro",
    "futuristic",
    "compact",
  ];

  test.describe("Theme Selection and Dark/Light Toggle", () => {
    for (const theme of themes) {
      test(`should persist ${theme} theme when toggling dark/light mode`, async ({
        page,
      }) => {
        // Go to settings
        await page.goto("/settings.html");

        // Select the theme
        const themeSelect = page.locator("#theme-setting");
        await themeSelect.selectOption(theme);
        await page.waitForTimeout(500);

        // Check theme is applied
        let dataTheme = await page.evaluate(() =>
          document.documentElement.getAttribute("data-theme"),
        );
        // Default theme is Dracula initially
        if (theme === "default") {
          expect(dataTheme).toBe("dracula");
        } else if (theme === "classic") {
          expect(dataTheme).toBe("dark");
        } else {
          // For experimental themes, should have theme name (might have -light or no suffix for dark)
          expect(dataTheme).toContain(theme.split("-")[0]); // Check base theme name is present
        }

        // Click the theme toggle button to switch modes
        const themeToggle = page.locator("#theme-toggle");
        await themeToggle.click();
        await page.waitForTimeout(500);

        // Verify theme is still present after toggle
        dataTheme = await page.evaluate(() =>
          document.documentElement.getAttribute("data-theme"),
        );

        if (theme === "default") {
          // Default theme should switch to Dracula Light after toggle
          expect(dataTheme).toBe("dracula-light");
        } else if (theme === "classic") {
          expect(dataTheme).toBe("light");
        } else {
          // Experimental theme should still contain the base theme name
          expect(dataTheme).toContain(theme.split("-")[0]);
        }

        // Navigate to home page and verify persistence
        await page.goto("/");
        await page.waitForTimeout(500);

        dataTheme = await page.evaluate(() =>
          document.documentElement.getAttribute("data-theme"),
        );

        if (theme === "default") {
          expect(dataTheme).toBe("dracula-light");
        } else if (theme === "classic") {
          expect(dataTheme).toBe("light");
        } else {
          expect(dataTheme).toContain(theme.split("-")[0]);
        }
      });
    }
  });

  test.describe("View Mode with Theme Combinations", () => {
    const sampleThemes = ["default", "classic", "magazine", "newspaper"]; // Test subset
    const sampleViewModes = ["card", "center-stage", "masonry-grid"]; // Test subset

    for (const theme of sampleThemes) {
      for (const viewMode of sampleViewModes) {
        test(`should persist ${theme} theme + ${viewMode} view mode when navigating`, async ({
          page,
        }) => {
          // Go to settings
          await page.goto("/settings.html");

          // Select theme
          const themeSelect = page.locator("#theme-setting");
          await themeSelect.selectOption(theme);
          await page.waitForTimeout(300);

          // Select view mode
          const viewSelect = page.locator("#view-setting");
          await viewSelect.selectOption(viewMode);
          await page.waitForTimeout(300);

          // Navigate to home page
          await page.goto("/");
          await page.waitForTimeout(500);

          // Verify theme persisted
          const dataTheme = await page.evaluate(() =>
            document.documentElement.getAttribute("data-theme"),
          );
          if (theme === "default") {
            expect(["dracula", "dracula-light"]).toContain(dataTheme);
          } else if (theme === "classic") {
            expect(["dark", "light"]).toContain(dataTheme);
          } else {
            expect(dataTheme).toContain(theme.split("-")[0]);
          }

          // Verify view mode persisted
          const dataView = await page.evaluate(() =>
            document.documentElement.getAttribute("data-view"),
          );
          expect(dataView).toBe(viewMode);

          // Go back to settings and verify both are still selected
          await page.goto("/settings.html");
          await page.waitForTimeout(500);

          const selectedTheme = await page
            .locator("#theme-setting")
            .inputValue();
          const selectedView = await page.locator("#view-setting").inputValue();

          expect(selectedTheme).toBe(theme);
          expect(selectedView).toBe(viewMode);
        });
      }
    }
  });

  test.describe("Theme + View Mode + Dark/Light Toggle Combinations", () => {
    test("should handle purple-haze + card mode + dark/light toggle", async ({
      page,
    }) => {
      // Go to settings
      await page.goto("/settings.html");

      // Select purple-haze theme
      await page.locator("#theme-setting").selectOption("purple-haze");
      await page.waitForTimeout(300);

      // Select card view
      await page.locator("#view-setting").selectOption("card");
      await page.waitForTimeout(300);

      // Navigate to home
      await page.goto("/");
      await page.waitForTimeout(500);

      // Verify both are applied
      let dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      let dataView = await page.evaluate(() =>
        document.documentElement.getAttribute("data-view"),
      );

      expect(dataTheme).toContain("purple-haze");
      expect(dataView).toBe("card");

      // Toggle dark/light mode
      await page.locator("#theme-toggle").click();
      await page.waitForTimeout(500);

      // Verify theme is still purple-haze and view is still card
      dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      dataView = await page.evaluate(() =>
        document.documentElement.getAttribute("data-view"),
      );

      expect(dataTheme).toContain("purple-haze");
      expect(dataView).toBe("card");

      // Go back to settings
      await page.goto("/settings.html");
      await page.waitForTimeout(500);

      // Verify selections are still correct
      const selectedTheme = await page.locator("#theme-setting").inputValue();
      const selectedView = await page.locator("#view-setting").inputValue();

      expect(selectedTheme).toBe("purple-haze");
      expect(selectedView).toBe("card");
    });

    test("should handle center-stage + theme selection", async ({ page }) => {
      // Go to settings
      await page.goto("/settings.html");

      // Select center-stage view mode first
      await page.locator("#view-setting").selectOption("center-stage");
      await page.waitForTimeout(300);

      // Select a theme
      await page.locator("#theme-setting").selectOption("retro");
      await page.waitForTimeout(300);

      // Navigate to home
      await page.goto("/");
      await page.waitForTimeout(500);

      // Verify both are applied
      const dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      const dataView = await page.evaluate(() =>
        document.documentElement.getAttribute("data-view"),
      );

      expect(dataTheme).toContain("retro");
      expect(dataView).toBe("center-stage");

      // View mode layout should be preserved via data-view attribute
      expect(dataView).toBe("center-stage");
    });

    test("should preserve view mode when toggling theme dark/light mode", async ({
      page,
    }) => {
      // Go to settings
      await page.goto("/settings.html");

      // Select center-stage view mode
      await page.locator("#view-setting").selectOption("center-stage");
      await page.waitForTimeout(300);

      // Select a theme
      await page.locator("#theme-setting").selectOption("default");
      await page.waitForTimeout(300);

      // Navigate to home
      await page.goto("/");
      await page.waitForTimeout(500);

      // Toggle dark/light mode
      await page.locator("#theme-toggle").click();
      await page.waitForTimeout(500);

      // Verify view mode is still center-stage
      const dataView = await page.evaluate(() =>
        document.documentElement.getAttribute("data-view"),
      );
      expect(dataView).toBe("center-stage");

      // Verify theme is still Dracula (with mode suffix)
      const dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      expect(dataTheme).toContain("dracula");
    });
  });

  test.describe("Bug Reproduction Tests", () => {
    test("BUG: Theme disappears when clicking dark/light button - fresh state", async ({
      page,
    }) => {
      // Start completely fresh - no localStorage
      await page.goto("/");
      await page.evaluate(() => localStorage.clear());
      await page.reload();
      await page.waitForTimeout(500);

      // Go to settings and choose a theme
      await page.goto("/settings.html");
      await page.locator("#theme-setting").selectOption("purple-haze");
      await page.waitForTimeout(500);

      // Verify theme is applied (should be purple-haze in dark mode initially)
      let dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      console.log("Theme after selection:", dataTheme);
      expect(dataTheme).toContain("purple-haze");

      // Click the dark/light toggle button
      await page.locator("#theme-toggle").click();
      await page.waitForTimeout(500);

      // Check what happened
      dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      console.log("Theme after toggle:", dataTheme);

      const storedTheme = await page.evaluate(() =>
        localStorage.getItem("experimentalTheme"),
      );
      const storedMode = await page.evaluate(() =>
        localStorage.getItem("themeMode"),
      );
      console.log("Stored theme:", storedTheme);
      console.log("Stored mode:", storedMode);

      // BUG: Theme should NOT disappear - it should still be purple-haze
      expect(dataTheme).toContain("purple-haze");
      expect(storedTheme).toContain("purple-haze");
    });

    test("BUG: Theme disappears on home page after settings selection", async ({
      page,
    }) => {
      // Fresh start
      await page.goto("/");
      await page.evaluate(() => localStorage.clear());

      // Go to settings
      await page.goto("/settings.html");

      // Select theme
      await page.locator("#theme-setting").selectOption("default");
      await page.waitForTimeout(500);

      let dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      console.log("Theme in settings after selection:", dataTheme);

      // Navigate to home page
      await page.goto("/");
      await page.waitForTimeout(500);

      dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      console.log("Theme on home page:", dataTheme);
      expect(dataTheme).toContain("dracula");

      // Now click toggle on home page
      await page.locator("#theme-toggle").click();
      await page.waitForTimeout(500);

      dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      console.log("Theme after toggle on home:", dataTheme);

      const storedTheme = await page.evaluate(() =>
        localStorage.getItem("experimentalTheme"),
      );
      console.log("Stored theme after toggle:", storedTheme);

      // Theme should still be Dracula
      expect(dataTheme).toContain("dracula");
    });
  });
});
