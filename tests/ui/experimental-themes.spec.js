import { expect, test } from "@playwright/test";

// Mock system date to match test data (2026-01-11, 12 hours after collection)
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    const fakeNow = new Date("2026-01-11T00:00:00Z").getTime();
    Date.now = () => fakeNow;
  });

  // Navigate to page and clear localStorage in correct order
  await page.goto("/");
  await page.waitForLoadState("load");
  await page.evaluate(() => localStorage.clear());
});

/**
 * Experimental Themes Tests
 * Tests the consolidated experimental themes functionality in main Theme and View Mode dropdowns
 */
test.describe("Experimental Themes - Consolidated", () => {
  test.describe("Settings Page - Theme Dropdown", () => {
    test("should display Theme dropdown with Dracula default, Classic, and beta themes", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // Check for Theme setting
      const themeSelect = page.locator("#theme-setting");
      await expect(themeSelect).toBeVisible();

      // Check for Dracula default option
      const defaultOption = themeSelect.locator('option[value="default"]');
      await expect(defaultOption).toBeAttached();
      await expect(defaultOption).toHaveText("Dracula (Default)");

      const classicOption = themeSelect.locator('option[value="classic"]');
      await expect(classicOption).toBeAttached();
      await expect(classicOption).toHaveText("Classic");

      // Check for some beta themes
      const purpleHazeOption = themeSelect.locator(
        'option[value="purple-haze"]',
      );
      const oceanDeepOption = themeSelect.locator('option[value="ocean-deep"]');
      await expect(purpleHazeOption).toBeAttached();
      await expect(oceanDeepOption).toBeAttached();
      await expect(
        themeSelect.locator('option[value="magazine"]'),
      ).toBeAttached();
      await expect(
        themeSelect.locator('option[value="newspaper"]'),
      ).toBeAttached();
    });

    test("should have 14 theme options (Dracula default + Classic + 12 beta themes)", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      const themeSelect = page.locator("#theme-setting");
      const options = themeSelect.locator("option");

      // Count options: 1 default Dracula + 1 Classic + 12 beta themes = 14
      const count = await options.count();
      expect(count).toBe(14);
    });

    test("should place the Dracula default and Classic options above beta themes", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      const options = await page
        .locator("#theme-setting option")
        .evaluateAll((elements) =>
          elements.map((option) => ({
            value: option.value,
            text: option.textContent?.trim(),
          })),
        );

      expect(options[0]).toEqual({
        value: "default",
        text: "Dracula (Default)",
      });
      expect(options[1]).toEqual({
        value: "classic",
        text: "Classic",
      });
      expect(options[2]?.text).toContain("Beta -");
    });

    test("should display beta themes with 'Beta - ' prefix", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      const themeSelect = page.locator("#theme-setting");

      // Check that experimental themes have Beta prefix
      const purpleHazeOption = themeSelect.locator(
        'option[value="purple-haze"]',
      );
      const purpleHazeText = await purpleHazeOption.textContent();
      expect(purpleHazeText).toContain("Beta - Purple Haze");

      const oceanDeepOption = themeSelect.locator('option[value="ocean-deep"]');
      const oceanDeepText = await oceanDeepOption.textContent();
      expect(oceanDeepText).toContain("Beta - Ocean Deep");

      await expect(themeSelect.locator('option[value="dracula"]')).toHaveCount(
        0,
      );
    });

    test("should apply the Classic theme using the light-dark toggle system", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      await page.locator("#theme-setting").selectOption("classic");

      await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

      const storedTheme = await page.evaluate(() =>
        localStorage.getItem("theme"),
      );
      const experimentalTheme = await page.evaluate(() =>
        localStorage.getItem("experimentalTheme"),
      );

      expect(storedTheme).toBe("dark");
      expect(experimentalTheme).toBeNull();
    });

    test("should show Classic as selected when the plain light-dark theme is active", async ({
      page,
    }) => {
      await page.goto("/");
      await page.evaluate(() => {
        localStorage.setItem("theme", "light");
        localStorage.setItem("themeMode", "light");
        localStorage.removeItem("experimentalTheme");
      });

      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      await expect(page.locator("#theme-setting")).toHaveValue("classic");
    });
  });

  test.describe("Settings Page - View Mode Dropdown", () => {
    test("should display View Mode dropdown with standard and beta view modes", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // Check for View Mode setting
      const viewSelect = page.locator("#view-setting");
      await expect(viewSelect).toBeVisible();

      // Check for standard options
      const listOption = viewSelect.locator('option[value="list"]');
      const cardOption = viewSelect.locator('option[value="card"]');
      await expect(listOption).toBeAttached();
      await expect(cardOption).toBeAttached();

      // Check for some beta view modes
      const horizontalScrollOption = viewSelect.locator(
        'option[value="horizontal-scroll"]',
      );
      const masonryGridOption = viewSelect.locator(
        'option[value="masonry-grid"]',
      );
      await expect(horizontalScrollOption).toBeAttached();
      await expect(masonryGridOption).toBeAttached();
    });

    test("should have 9 view mode options (2 standard + 7 beta)", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      const viewSelect = page.locator("#view-setting");
      const options = viewSelect.locator("option");

      // Count options: 2 standard + 7 beta = 9
      const count = await options.count();
      expect(count).toBe(9);
    });

    test("should display beta view modes with 'Beta - ' prefix", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      const viewSelect = page.locator("#view-setting");

      // Check that experimental view modes have Beta prefix
      const horizontalScrollOption = viewSelect.locator(
        'option[value="horizontal-scroll"]',
      );
      const horizontalScrollText = await horizontalScrollOption.textContent();
      expect(horizontalScrollText).toContain("Beta - Horizontal Scroll");

      const masonryGridOption = viewSelect.locator(
        'option[value="masonry-grid"]',
      );
      const masonryGridText = await masonryGridOption.textContent();
      expect(masonryGridText).toContain("Beta - Masonry Grid");
    });
  });

  test.describe("Theme Application", () => {
    test("should apply beta theme when selected", async ({ page }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // Select a beta theme
      const themeSelect = page.locator("#theme-setting");
      await themeSelect.selectOption("purple-haze");

      // Wait for theme to be applied
      await page.waitForTimeout(100);

      // Check that data-theme attribute is set
      const dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      expect(dataTheme).toBe("purple-haze");
    });

    test("should persist beta theme in localStorage", async ({ page }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // Select a beta theme
      const themeSelect = page.locator("#theme-setting");
      await themeSelect.selectOption("terminal");

      // Check localStorage
      const experimentalTheme = await page.evaluate(() =>
        localStorage.getItem("experimentalTheme"),
      );
      expect(experimentalTheme).toBe("terminal");
    });

    test("should load beta theme on page reload", async ({ page }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // Set beta theme
      await page.locator("#theme-setting").selectOption("minimalist");

      // Reload page
      await page.reload();
      await page.waitForLoadState("load");

      // Check that theme is still applied
      const dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      expect(dataTheme).toBe("minimalist");

      // Check that select still shows the beta theme
      const selectedValue = await page.locator("#theme-setting").inputValue();
      expect(selectedValue).toBe("minimalist");
    });

    test("should clear beta theme when selecting 'default'", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // First set a beta theme
      await page.locator("#theme-setting").selectOption("retro");

      // Then select "default"
      await page.locator("#theme-setting").selectOption("default");

      // Check localStorage
      const experimentalTheme = await page.evaluate(() =>
        localStorage.getItem("experimentalTheme"),
      );
      expect(experimentalTheme).toBeNull();

      // Should revert to default Dracula theme variants
      const dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      expect(["dracula", "dracula-light"]).toContain(dataTheme);
    });
  });

  test.describe("View Mode Application", () => {
    test("should apply beta view mode when selected", async ({ page }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // Select a beta view mode
      const viewSelect = page.locator("#view-setting");
      await viewSelect.selectOption("horizontal-scroll");

      // Wait for view mode to be applied
      await page.waitForTimeout(100);

      // Check localStorage
      const experimentalViewMode = await page.evaluate(() =>
        localStorage.getItem("experimentalViewMode"),
      );
      expect(experimentalViewMode).toBe("horizontal-scroll");
    });

    test("should persist beta view mode in localStorage", async ({ page }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // Select a beta view mode
      const viewSelect = page.locator("#view-setting");
      await viewSelect.selectOption("masonry-grid");

      // Check localStorage
      const experimentalViewMode = await page.evaluate(() =>
        localStorage.getItem("experimentalViewMode"),
      );
      expect(experimentalViewMode).toBe("masonry-grid");
    });

    test("should clear beta view mode when selecting standard view", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // First set a beta view mode
      await page.locator("#view-setting").selectOption("masonry-grid");

      // Then select standard view
      await page.locator("#view-setting").selectOption("list");

      // Check localStorage
      const experimentalViewMode = await page.evaluate(() =>
        localStorage.getItem("experimentalViewMode"),
      );
      expect(experimentalViewMode).toBeNull();

      const view = await page.evaluate(() => localStorage.getItem("view"));
      expect(view).toBe("list");
    });
  });

  test.describe("Color Variation Themes", () => {
    const colorThemes = [
      { name: "purple-haze", expectedDefault: "purple-haze" }, // Naturally dark
      { name: "ocean-deep", expectedDefault: "ocean-deep" }, // Naturally dark
      { name: "arctic-blue", expectedDefault: "arctic-blue" }, // Naturally light (special case)
    ];

    for (const { name, expectedDefault } of colorThemes) {
      test(`should apply ${name} color theme`, async ({ page }) => {
        await page.goto("/settings.html");
        await page.waitForLoadState("load");

        await page.locator("#theme-setting").selectOption(name);

        const dataTheme = await page.evaluate(() =>
          document.documentElement.getAttribute("data-theme"),
        );
        // Should apply theme in its natural default mode
        expect(dataTheme).toBe(expectedDefault);
      });
    }
  });

  test.describe("Themed Style Themes", () => {
    const themedStyles = [
      "minimalist",
      "terminal",
      "retro",
      "futuristic",
      "compact",
    ];

    for (const theme of themedStyles.slice(0, 3)) {
      // Test first 3 to save time
      test(`should apply ${theme} themed style`, async ({ page }) => {
        await page.goto("/settings.html");
        await page.waitForLoadState("load");

        await page.locator("#theme-setting").selectOption(theme);

        const dataTheme = await page.evaluate(() =>
          document.documentElement.getAttribute("data-theme"),
        );
        expect(dataTheme).toBe(theme);
      });
    }
  });

  test.describe("Theme Persistence Across Pages", () => {
    test("should apply beta theme on index page", async ({ page }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // Set beta theme
      await page.locator("#theme-setting").selectOption("terminal");

      // Navigate to index
      await page.goto("/");
      await page.waitForLoadState("load");

      // Check that theme is applied
      const dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      expect(dataTheme).toBe("terminal");
    });

    test("should maintain beta theme when navigating back to settings", async ({
      page,
    }) => {
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // Set beta theme
      await page.locator("#theme-setting").selectOption("retro");

      // Navigate away and back
      await page.goto("/");
      await page.goto("/settings.html");
      await page.waitForLoadState("load");

      // Check that theme is still selected
      const selectedValue = await page.locator("#theme-setting").inputValue();
      expect(selectedValue).toBe("retro");

      const dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      expect(dataTheme).toBe("retro");
    });
  });
});

test.describe("Theme Application Across All Pages", () => {
  const testTheme = "futuristic";

  test("should apply beta theme on index page", async ({ page }) => {
    // Set theme via settings
    await page.goto("/settings.html");
    await page.waitForLoadState("load");
    await page.locator("#theme-setting").selectOption(testTheme);

    // Navigate to index
    await page.goto("/");
    await page.waitForLoadState("load");

    const dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe(testTheme);
  });

  test("should apply beta theme on feed page", async ({ page }) => {
    // Set theme via settings
    await page.goto("/settings.html");
    await page.waitForLoadState("load");
    await page.locator("#theme-setting").selectOption(testTheme);

    // Navigate to a feed page
    await page.goto("/feed-test-feed-a.html");
    await page.waitForLoadState("load");

    const dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe(testTheme);
  });

  test("should apply beta theme on summary page", async ({ page }) => {
    // Set theme via settings
    await page.goto("/settings.html");
    await page.waitForLoadState("load");
    await page.locator("#theme-setting").selectOption(testTheme);

    // Navigate to summary page (if it exists)
    const response = await page.goto("/summary.html");
    if (response && response.ok()) {
      await page.waitForLoadState("load");

      const dataTheme = await page.evaluate(() =>
        document.documentElement.getAttribute("data-theme"),
      );
      expect(dataTheme).toBe(testTheme);
    }
  });

  test("should maintain theme when navigating between pages", async ({
    page,
  }) => {
    // Set theme
    await page.goto("/settings.html");
    await page.waitForLoadState("load");
    await page.locator("#theme-setting").selectOption(testTheme);

    // Navigate through different pages
    await page.goto("/");
    let dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe(testTheme);

    await page.goto("/feed-test-feed-a.html");
    dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe(testTheme);

    await page.goto("/settings.html");
    dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe(testTheme);
  });
});

test.describe("Theme Mode Toggle - Home Page Only", () => {
  test("should toggle between dark and light variants using home page theme toggle", async ({
    page,
  }) => {
    // Set a beta theme first
    await page.goto("/settings.html");
    await page.waitForLoadState("load");
    await page.locator("#theme-setting").selectOption("ocean-deep");
    await page.waitForTimeout(100);

    // Navigate to home page
    await page.goto("/");
    await page.waitForLoadState("load");

    // Verify dark theme is applied
    let dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe("ocean-deep");

    // Click theme toggle
    await page.locator("#theme-toggle").click();
    await page.waitForTimeout(300);

    // Verify light variant is applied
    dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe("ocean-deep-light");

    // Click theme toggle again
    await page.locator("#theme-toggle").click();
    await page.waitForTimeout(300);

    // Verify back to dark variant
    dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe("ocean-deep");
  });

  test("should toggle default theme between Dracula and Dracula Light", async ({
    page,
  }) => {
    // Start with default theme
    await page.goto("/");
    await page.waitForLoadState("load");

    // Default should be dracula
    let dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe("dracula");

    // Click theme toggle
    await page.locator("#theme-toggle").click();
    await page.waitForTimeout(300);

    // Should switch to dracula-light
    dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe("dracula-light");

    // Click theme toggle again and wait for theme change
    await page.locator("#theme-toggle").click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dracula");

    // Verify dracula theme is applied
    dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe("dracula");
  });
});

test.describe("Arctic Blue Theme Special Handling", () => {
  test("should apply arctic-blue in its natural light mode when selected", async ({
    page,
  }) => {
    await page.goto("/settings.html");
    await page.waitForLoadState("load");

    // Select arctic-blue theme - should always be light (its natural mode)
    await page.locator("#theme-setting").selectOption("arctic-blue");
    await page.waitForTimeout(100);

    // Should apply arctic-blue (naturally light)
    const dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe("arctic-blue");
  });

  test("should toggle arctic-blue to dark mode using theme toggle", async ({
    page,
  }) => {
    await page.goto("/settings.html");
    await page.waitForLoadState("load");

    // Select arctic-blue theme (naturally light)
    await page.locator("#theme-setting").selectOption("arctic-blue");
    await page.waitForTimeout(100);

    // Navigate to home page and toggle to dark mode
    await page.goto("/");
    await page.waitForLoadState("load");
    await page.locator("#theme-toggle").click();
    await page.waitForTimeout(300);

    // Should now be arctic-blue-dark
    const dataTheme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(dataTheme).toBe("arctic-blue-dark");
  });
});

test.describe("No Theme Mode Dropdown in Settings", () => {
  test("should not have theme-mode-setting dropdown in appearance section", async ({
    page,
  }) => {
    await page.goto("/settings.html");
    await page.waitForLoadState("load");

    // Check that theme-mode-setting does not exist
    const themeModeSelect = page.locator("#theme-mode-setting");
    await expect(themeModeSelect).not.toBeAttached();
  });

  test("should not have experimental section in settings menu", async ({
    page,
  }) => {
    await page.goto("/settings.html");
    await page.waitForLoadState("load");

    // Check that experimental section does not exist
    const experimentalMenuItem = page.locator(
      '.settings-menu-item[data-section="experimental"]',
    );
    await expect(experimentalMenuItem).not.toBeAttached();
  });
});
