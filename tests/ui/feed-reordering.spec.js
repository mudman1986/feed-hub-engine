import { expect, test } from "@playwright/test";

async function clearSiteStorage(page) {
  await page.goto("/");
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.waitForSelector(".feed-section", { timeout: 10000 });
}

async function openSidebarIfNeeded(page) {
  const sidebar = page.locator("#sidebar");
  const navToggle = page.locator("#nav-toggle");
  const isCollapsed = await sidebar
    .evaluate((element) => element.classList.contains("collapsed"))
    .catch(() => false);

  if (isCollapsed && (await navToggle.isVisible().catch(() => false))) {
    await navToggle.click();
    await expect(sidebar).not.toHaveClass(/collapsed/);
  }
}

async function openFeedSelection(page) {
  await page.goto("/settings.html");
  await page.locator('.settings-menu-item:has-text("Feed Selection")').click();
  await page.waitForSelector("#feed-checkboxes", { timeout: 15000 });
}

async function getNavFeedOrder(page) {
  return page.evaluate(() => {
    return Array.from(document.querySelectorAll(".feed-nav .nav-link"))
      .map((link) => link.textContent.trim())
      .filter((name) => name !== "All Feeds" && name !== "Summary");
  });
}

async function getMainFeedOrder(page) {
  return page.evaluate(() => {
    return Array.from(document.querySelectorAll(".feed-section")).map(
      (section) => {
        const titleLink = section.querySelector(".feed-title-link");
        return titleLink ? titleLink.textContent.trim() : "";
      },
    );
  });
}

async function getSettingsFeedOrder(page) {
  return page.evaluate(() => {
    return Array.from(
      document.querySelectorAll("#feed-checkboxes .feed-checkbox-item"),
    ).map((item) => item.getAttribute("data-feed-name"));
  });
}

function isTouchProject(projectName) {
  return projectName.includes("Tablet") || projectName.includes("Mobile");
}

test.describe("Feed reordering", () => {
  test("nav drag-and-drop persists and updates settings automatically", async ({
    page,
  }) => {
    const projectName = test.info().project.name;
    const expectedOrder = [
      "Test Feed C",
      "AWS DevOps Blog",
      "Atlassian DevOps",
      "Docker Blog",
      "GitHub Blog",
      "Opensource.com",
      "Terraform weekly",
      "Test Feed A",
      "Test Feed B",
    ];

    await clearSiteStorage(page);

    const settingsPage = await page.context().newPage();
    await openFeedSelection(settingsPage);
    await openSidebarIfNeeded(page);

    if (isTouchProject(projectName)) {
      await page.evaluate((feedOrder) => {
        window.saveFeedOrder(feedOrder);
      }, expectedOrder);
      await page.reload();
      await openSidebarIfNeeded(page);
    } else {
      await page
        .locator('.feed-nav .nav-link:has-text("Test Feed C")')
        .dragTo(
          page.locator('.feed-nav .nav-link:has-text("AWS DevOps Blog")'),
          {
            targetPosition: { x: 16, y: 4 },
          },
        );
    }

    await expect.poll(() => getNavFeedOrder(page)).toEqual(expectedOrder);
    await expect.poll(() => getMainFeedOrder(page)).toEqual(expectedOrder);
    await expect
      .poll(() => getSettingsFeedOrder(settingsPage))
      .toEqual(expectedOrder);

    await page.reload();
    await openSidebarIfNeeded(page);
    await expect.poll(() => getNavFeedOrder(page)).toEqual(expectedOrder);

    await settingsPage.close();
  });

  test("settings drag-and-drop updates main navigation automatically", async ({
    page,
  }) => {
    const projectName = test.info().project.name;
    const expectedOrder = [
      "Test Feed B",
      "AWS DevOps Blog",
      "Atlassian DevOps",
      "Docker Blog",
      "GitHub Blog",
      "Opensource.com",
      "Terraform weekly",
      "Test Feed A",
      "Test Feed C",
    ];

    await clearSiteStorage(page);
    await openSidebarIfNeeded(page);

    const settingsPage = await page.context().newPage();
    await openFeedSelection(settingsPage);

    if (projectName === "Desktop Chrome 1920x1080") {
      await settingsPage
        .locator('#feed-checkboxes .feed-checkbox-item:has-text("Test Feed B")')
        .dragTo(
          settingsPage.locator(
            '#feed-checkboxes .feed-checkbox-item:has-text("AWS DevOps Blog")',
          ),
          {
            targetPosition: { x: 16, y: 4 },
          },
        );
    } else {
      await settingsPage.evaluate((feedOrder) => {
        window.saveFeedOrder(feedOrder);
      }, expectedOrder);
      await settingsPage.reload();
      await openFeedSelection(settingsPage);
    }

    await expect
      .poll(() => getSettingsFeedOrder(settingsPage))
      .toEqual(expectedOrder);
    await expect.poll(() => getNavFeedOrder(page)).toEqual(expectedOrder);
    await expect.poll(() => getMainFeedOrder(page)).toEqual(expectedOrder);

    await settingsPage.close();
  });
});
