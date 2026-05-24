const { test, expect } = require("@playwright/test");

test.describe("Redesign theme layouts", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      const fakeNow = new Date("2026-01-11T00:00:00Z").getTime();
      Date.now = () => fakeNow;
    });
    await page.goto("/");
    await page.waitForLoadState("load");
    await page.evaluate(() => localStorage.clear());
  });

  test("magazine theme creates a strong editorial hierarchy in card view", async ({
    page,
  }) => {
    await page.goto("/settings.html");
    await page.locator("#theme-setting").selectOption("magazine");
    await page.locator("#view-setting").selectOption("card");

    await page.goto("/");
    await page.waitForSelector('.article-item[data-article-rank="lead"]');

    const articleList = page.locator(".article-list").first();
    await expect(articleList).toBeVisible();

    const leadArticle = page
      .locator('.article-item[data-article-rank="lead"]')
      .first();
    const featureArticle = page
      .locator('.article-item[data-article-rank="feature"]')
      .first();

    const leadBox = await leadArticle.boundingBox();
    const featureBox = await featureArticle.boundingBox();

    expect(leadBox).not.toBeNull();
    expect(featureBox).not.toBeNull();

    const viewport = page.viewportSize();
    if (viewport && viewport.width > 1024) {
      expect(leadBox.width).toBeGreaterThan(featureBox.width * 1.5);
    } else {
      expect(leadBox.width).toBeGreaterThanOrEqual(featureBox.width);
    }

    const leadTitleSize = await leadArticle
      .locator(".article-title")
      .evaluate((element) => parseFloat(getComputedStyle(element).fontSize));
    const featureTitleSize = await featureArticle
      .locator(".article-title")
      .evaluate((element) => parseFloat(getComputedStyle(element).fontSize));

    expect(leadTitleSize).toBeGreaterThan(featureTitleSize);
  });

  test("newspaper theme uses a distinct blank-slate desktop layout", async ({
    page,
  }) => {
    await page.goto("/settings.html");
    await page.locator("#theme-setting").selectOption("newspaper");
    await page.locator("#view-setting").selectOption("card");

    await page.goto("/");
    await page.waitForSelector(".feed-section");

    const viewport = page.viewportSize();
    if (viewport && viewport.width <= 768) {
      return;
    }

    await expect(page.locator("html")).toHaveAttribute("data-theme", /newspaper/);

    const sidebarBox = await page.locator("#sidebar").boundingBox();
    const mainBox = await page.locator("#main-content").boundingBox();

    expect(sidebarBox).not.toBeNull();
    expect(mainBox).not.toBeNull();
    expect(sidebarBox.x).toBeLessThan(mainBox.x);

    const firstSection = page.locator(".feed-section").first();
    const headingBox = await firstSection.locator("h2").boundingBox();
    const articleListBox = await firstSection.locator(".article-list").boundingBox();

    expect(headingBox).not.toBeNull();
    expect(articleListBox).not.toBeNull();
    expect(headingBox.x).toBeLessThan(articleListBox.x);
    expect(articleListBox.x - headingBox.x).toBeGreaterThan(120);
  });
});
