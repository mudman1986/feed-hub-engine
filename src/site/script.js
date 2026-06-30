// Breakpoint constants (in pixels)
const BREAKPOINTS = {
  MOBILE: 768,
  TABLET: 1024,
  DESKTOP: 1200,
};

// Timeout constants (in milliseconds)
const TIMEOUTS = {
  SCREEN_READER_ANNOUNCEMENT: 3000,
  ERROR_MESSAGE_DISMISS: 5000,
  TOAST_DURATION: 3000,
  LOADING_MIN_DURATION: 300,
};

// Accessibility constants
const ACCESSIBILITY = {
  MIN_TOUCH_TARGET_SIZE: 48,
  MIN_FOCUS_OUTLINE_WIDTH: 2,
};

// Mark as Read constants
const READ_ARTICLES_KEY = "readArticles";
const SITE_STORAGE_PREFIX = "dfh";
const SITE_SCOPED_STORAGE_KEYS = [
  READ_ARTICLES_KEY,
  "enabledFeeds",
  "experimentalTheme",
  "experimentalViewMode",
  "theme",
  "themeMode",
  "timeframe",
  "view",
];

// List of base experimental themes (without -light/-dark suffixes)
const EXPERIMENTAL_BASE_THEMES = [
  "purple-haze",
  "ocean-deep",
  "arctic-blue",
  "high-contrast",
  "monochrome",
  "dracula",
  "minimalist",
  "terminal",
  "magazine",
  "newspaper",
  "retro",
  "futuristic",
  "compact",
];

// List of experimental view modes (layout alternatives)
const EXPERIMENTAL_VIEW_MODES = [
  "horizontal-scroll",
  "masonry-grid",
  "floating-panels",
  "center-stage",
  "top-strip",
  "list-dense",
  "timeline-vertical",
];

// All valid experimental themes including variants
const VALID_EXPERIMENTAL_THEMES = [
  ...EXPERIMENTAL_BASE_THEMES,
  ...EXPERIMENTAL_BASE_THEMES.map((t) => `${t}-light`),
  ...EXPERIMENTAL_BASE_THEMES.map((t) => `${t}-dark`),
  ...EXPERIMENTAL_VIEW_MODES,
];

function shouldScopeSiteStorageKey(key) {
  return typeof key === "string" && SITE_SCOPED_STORAGE_KEYS.includes(key);
}

function isScopedSiteStorageKey(key) {
  return typeof key === "string" && key.startsWith(`${SITE_STORAGE_PREFIX}:`);
}

function getCurrentSiteStorageScope(currentHref = window.location.href) {
  return new URL("./", currentHref).pathname;
}

function getScopedStorageKey(key, currentHref = window.location.href) {
  if (!shouldScopeSiteStorageKey(key) || isScopedSiteStorageKey(key)) {
    return key;
  }

  return `${SITE_STORAGE_PREFIX}:${getCurrentSiteStorageScope(currentHref)}:${key}`;
}

function getSiteStorageAccessKey(key, currentHref = window.location.href) {
  return shouldScopeSiteStorageKey(key)
    ? getScopedStorageKey(key, currentHref)
    : key;
}

const originalLocalStorageGetItem = window.localStorage.getItem.bind(
  window.localStorage,
);
const originalLocalStorageSetItem = window.localStorage.setItem.bind(
  window.localStorage,
);
const originalLocalStorageRemoveItem = window.localStorage.removeItem.bind(
  window.localStorage,
);

if (!window.__dfhScopedStorageProxyInstalled) {
  const nativeLocalStorage = window.localStorage;
  const scopedLocalStorage = new Proxy(nativeLocalStorage, {
    get(target, prop, receiver) {
      if (prop === "getItem") {
        return (key) =>
          originalLocalStorageGetItem(getSiteStorageAccessKey(key));
      }

      if (prop === "setItem") {
        return (key, value) =>
          originalLocalStorageSetItem(getSiteStorageAccessKey(key), value);
      }

      if (prop === "removeItem") {
        return (key) =>
          originalLocalStorageRemoveItem(getSiteStorageAccessKey(key));
      }

      const value = Reflect.get(target, prop, receiver);
      return typeof value === "function" ? value.bind(target) : value;
    },
  });

  Object.defineProperty(window, "localStorage", {
    configurable: true,
    enumerable: true,
    value: scopedLocalStorage,
  });

  window.__dfhScopedStorageProxyInstalled = true;
}

(function migrateLegacySiteStorage() {
  try {
    SITE_SCOPED_STORAGE_KEYS.forEach((key) => {
      const scopedKey = getScopedStorageKey(key);
      const scopedValue = originalLocalStorageGetItem(scopedKey);

      if (scopedValue !== null) {
        return;
      }

      const legacyValue = originalLocalStorageGetItem(key);
      if (legacyValue !== null) {
        originalLocalStorageSetItem(scopedKey, legacyValue);
      }
    });

    const scopedExperimentalThemeKey = getScopedStorageKey("experimentalTheme");
    const scopedExperimentalTheme = originalLocalStorageGetItem(
      scopedExperimentalThemeKey,
    );

    if (
      scopedExperimentalTheme &&
      EXPERIMENTAL_VIEW_MODES.includes(scopedExperimentalTheme)
    ) {
      originalLocalStorageSetItem(
        getScopedStorageKey("experimentalViewMode"),
        scopedExperimentalTheme,
      );
      originalLocalStorageRemoveItem(scopedExperimentalThemeKey);
    }
  } catch (e) {
    console.warn("Unable to migrate site-scoped localStorage:", e);
  }
})();

// ===== THEME UTILITY FUNCTIONS =====

/**
 * Get the base theme name (without -light or -dark suffix)
 * @param {string} theme - Full theme name
 * @returns {string} - Base theme name
 */
function getBaseTheme(theme) {
  if (!theme) return null;
  // Remove -light or -dark suffix
  return theme.replace(/-light$|-dark$/, "");
}

/**
 * Determine if a theme is light mode
 * @param {string} theme - Full theme name
 * @returns {boolean} - True if light mode
 */
function isLightMode(theme) {
  if (!theme) return false;
  // Arctic-blue is always light by default (no -light suffix needed)
  if (theme === "arctic-blue") return true;
  // Check for -light suffix
  return theme.endsWith("-light") || theme === "light";
}

/**
 * Get current mode (light or dark)
 * @param {string} theme - Full theme name
 * @returns {string} - "light" or "dark"
 */
function getCurrentMode(theme) {
  return isLightMode(theme) ? "light" : "dark";
}

/**
 * Apply mode to a theme (returns theme-light or theme-dark)
 * @param {string} baseTheme - Base theme name (without mode suffix)
 * @param {string} mode - "light" or "dark"
 * @returns {string} - Full theme name with mode suffix
 */
function applyModeToTheme(baseTheme, mode) {
  if (!baseTheme) return mode;

  // View modes don't have light/dark variants
  if (EXPERIMENTAL_VIEW_MODES.includes(baseTheme)) {
    return baseTheme;
  }

  // Standard themes - "light" and "dark" are already full theme names
  // (not base themes, but we handle them here for completeness)
  if (baseTheme === "light" || baseTheme === "dark") {
    return mode;
  }

  // Arctic-blue is naturally light, so no suffix for light mode
  if (baseTheme === "arctic-blue") {
    return mode === "light" ? "arctic-blue" : "arctic-blue-dark";
  }

  // For other experimental themes, append mode suffix
  if (EXPERIMENTAL_BASE_THEMES.includes(baseTheme)) {
    return mode === "light" ? `${baseTheme}-light` : baseTheme;
  }

  return baseTheme;
}

/**
 * Get the natural/default mode for a theme
 * @param {string} baseTheme - Base theme name (without mode suffix)
 * @returns {string} - "light" or "dark" (the natural default mode)
 */

// ===== SHARED UTILITY FUNCTIONS =====

/**
 * Safely get item from localStorage with error handling
 * @param {string} key - localStorage key
 * @param {*} defaultValue - default value if key not found or error occurs
 * @returns {*} - stored value or default
 */
function getLocalStorage(key, defaultValue = null) {
  try {
    const stored = localStorage.getItem(key);
    return stored !== null ? stored : defaultValue;
  } catch (e) {
    console.warn(`localStorage unavailable for key "${key}":`, e);
    return defaultValue;
  }
}

/**
 * Safely get JSON from localStorage with error handling
 * @param {string} key - localStorage key
 * @param {*} defaultValue - default value if key not found or error occurs
 * @returns {*} - parsed JSON value or default
 */
function getLocalStorageJSON(key, defaultValue = null) {
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : defaultValue;
  } catch (e) {
    console.warn(
      `localStorage unavailable or invalid JSON for key "${key}":`,
      e,
    );
    return defaultValue;
  }
}

/**
 * Safely set item in localStorage with error handling
 * @param {string} key - localStorage key
 * @param {string} value - value to store
 */
function setLocalStorage(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch (e) {
    console.warn(`Unable to save to localStorage for key "${key}":`, e);
  }
}

/**
 * Safely set JSON in localStorage with error handling
 * @param {string} key - localStorage key
 * @param {*} value - value to JSON stringify and store
 */
function setLocalStorageJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.warn(`Unable to save to localStorage for key "${key}":`, e);
  }
}

/**
 * Safely remove item from localStorage with error handling
 * @param {string} key - localStorage key
 */
function removeLocalStorage(key) {
  try {
    localStorage.removeItem(key);
  } catch (e) {
    console.warn(`Unable to remove from localStorage for key "${key}":`, e);
  }
}

/**
 * Join URL path segments into a normalized absolute path
 * @param {string[]} segments - Path segments to join
 * @param {boolean} [trailingSlash=false] - Whether to enforce a trailing slash
 * @returns {string}
 */
function joinPathSegments(segments, trailingSlash = false) {
  let normalizedPath = segments.join("/");

  if (!normalizedPath.startsWith("/")) {
    normalizedPath = `/${normalizedPath}`;
  }

  normalizedPath = normalizedPath.replace(/\/{2,}/g, "/");

  if (trailingSlash && !normalizedPath.endsWith("/")) {
    normalizedPath = `${normalizedPath}/`;
  }

  return normalizedPath || "/";
}

/**
 * Get preview deployment context for the current page, if applicable
 * @param {string} [currentHref=window.location.href] - URL to inspect
 * @returns {{slug: string, productionUrl: string, manifestUrl: string}|null}
 */
function getPreviewSiteContext(currentHref = window.location.href) {
  const currentUrl = new URL(currentHref, window.location.origin);
  const pathSegments = currentUrl.pathname.split("/");
  const previewIndex = pathSegments.findIndex(
    (segment) => segment === "preview",
  );
  const previewSlug = pathSegments[previewIndex + 1];

  if (previewIndex === -1 || !previewSlug) {
    return null;
  }

  const baseSegments = pathSegments.slice(0, previewIndex);
  const contentSegments = pathSegments.slice(previewIndex + 2);
  let productionPath = joinPathSegments(baseSegments, true);

  if (contentSegments.length > 0) {
    productionPath = joinPathSegments([...baseSegments, ...contentSegments]);
  }

  const previewBasePath = joinPathSegments([...baseSegments, "preview"]);
  const productionUrl = new URL(productionPath, currentUrl.origin);
  const manifestUrl = new URL(
    `${previewBasePath}/manifest.json`,
    currentUrl.origin,
  );

  productionUrl.search = currentUrl.search;
  productionUrl.hash = currentUrl.hash;

  return {
    slug: previewSlug,
    productionUrl: productionUrl.toString(),
    manifestUrl: manifestUrl.toString(),
  };
}

/**
 * Create an SVG element from path data
 * @param {number} width - Rendered SVG width (e.g., 16, 24)
 * @param {number} height - Rendered SVG height (e.g., 16, 24)
 * @param {string} content - SVG inner content (paths, lines, etc.) - MUST be from trusted static strings only
 * @param {number} [viewBoxWidth=24] - Internal SVG coordinate system width (defaults to 24 for icon paths)
 * @param {number} [viewBoxHeight=24] - Internal SVG coordinate system height (defaults to 24 for icon paths)
 * @returns {SVGElement} - SVG element
 * @example
 * // Render a 16x16 icon using 24x24 coordinate paths
 * const icon = createSVG(16, 16, '<path d="...24x24 coordinates..."/>');
 */
function createSVG(
  width,
  height,
  content,
  viewBoxWidth = 24,
  viewBoxHeight = 24,
) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("width", width.toString());
  svg.setAttribute("height", height.toString());
  svg.setAttribute("viewBox", `0 0 ${viewBoxWidth} ${viewBoxHeight}`);
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "2");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");

  // Parse and create SVG elements from content string
  // WARNING: content MUST be from trusted static strings only to avoid XSS
  const temp = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  temp.innerHTML = content;
  while (temp.firstChild) {
    svg.appendChild(temp.firstChild);
  }

  return svg;
}

/**
 * Initialize a dropdown with saved value from localStorage
 * @param {string} selectId - ID of select element
 * @param {string} storageKey - localStorage key
 * @param {string} defaultValue - default value if not in storage
 * @param {function} onChange - callback when value changes
 * @returns {HTMLElement|null} - select element or null
 */
function initializeDropdown(selectId, storageKey, defaultValue, onChange) {
  const select = document.getElementById(selectId);
  if (!select) return null;

  const savedValue = getLocalStorage(storageKey, defaultValue);
  select.value = savedValue;

  select.addEventListener("change", () => {
    const value = select.value;
    setLocalStorage(storageKey, value);
    onChange(value);
  });

  return select;
}

/**
 * Sort and reorder DOM elements based on data array
 * @param {Array} dataArray - array of objects with 'element' property
 * @param {HTMLElement} parent - parent container element
 * @param {HTMLElement|null} beforeElement - insert before this element (e.g., footer)
 */
function reorderDOMElements(dataArray, parent, beforeElement = null) {
  // Detach all elements first to avoid issues with insertBefore moving elements
  const elements = dataArray.map((data) => data.element);
  elements.forEach((element) => {
    if (element.parentNode) {
      element.parentNode.removeChild(element);
    }
  });

  // Now insert them in the correct order
  if (beforeElement) {
    elements.forEach((element) => {
      parent.insertBefore(element, beforeElement);
    });
  } else {
    elements.forEach((element) => {
      parent.appendChild(element);
    });
  }
}

/**
 * Debounce function to limit how often a function can be called
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} - Debounced function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ===== LOADING STATE UTILITY =====

/**
 * Loading state utility class for visual feedback
 */
class LoadingState {
  /**
   * Show loading state on element
   * @param {HTMLElement} element - Element to show loading state on
   * @param {string} message - Optional loading message for screen readers
   * @param {boolean} overlay - Whether to use overlay style (default: false)
   */
  static show(element, message = "Loading...", overlay = false) {
    if (!element) return;

    element.setAttribute("aria-busy", "true");
    if (overlay) {
      element.classList.add("loading-overlay");
    } else {
      element.classList.add("loading");
    }

    // Announce to screen readers
    if (message) {
      announceToScreenReader(message, "polite");
    }
  }

  /**
   * Hide loading state on element
   * @param {HTMLElement} element - Element to hide loading state on
   */
  static hide(element) {
    if (!element) return;

    element.setAttribute("aria-busy", "false");
    element.classList.remove("loading", "loading-overlay");
  }

  /**
   * Execute an async function with loading state
   * @param {HTMLElement} element - Element to show loading state on
   * @param {Function} asyncFn - Async function to execute
   * @param {string} message - Loading message
   * @param {boolean} overlay - Whether to use overlay style
   * @returns {Promise} - Result of async function
   */
  static async wrap(element, asyncFn, message = "Loading...", overlay = false) {
    const startTime = Date.now();
    LoadingState.show(element, message, overlay);

    try {
      const result = await asyncFn();

      // Ensure minimum loading duration for better UX
      const elapsed = Date.now() - startTime;
      const remaining = TIMEOUTS.LOADING_MIN_DURATION - elapsed;

      if (remaining > 0) {
        await new Promise((resolve) => setTimeout(resolve, remaining));
      }

      return result;
    } finally {
      LoadingState.hide(element);
    }
  }
}

// ===== TOAST NOTIFICATION SYSTEM =====

/**
 * Show toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type: 'success', 'error', 'info' (default: 'success')
 * @param {number} duration - Duration in ms (default: 3000)
 */
function showToast(
  message,
  type = "success",
  duration = TIMEOUTS.TOAST_DURATION,
) {
  // Create toast container if it doesn't exist
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    container.setAttribute("aria-live", "polite");
    container.setAttribute("aria-atomic", "true");
    document.body.appendChild(container);
  }

  // Create toast element
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.setAttribute("role", "status");

  // Create icon
  const icon = document.createElement("div");
  icon.className = "toast-icon";
  icon.setAttribute("aria-hidden", "true");

  // Set icon SVG based on type
  let svg;
  if (type === "success") {
    svg = createSVG(24, 24, '<polyline points="20 6 9 17 4 12"></polyline>');
  } else if (type === "error") {
    svg = createSVG(
      24,
      24,
      '<circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>',
    );
  } else {
    // info
    svg = createSVG(
      24,
      24,
      '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>',
    );
  }
  icon.appendChild(svg);

  // Create content
  const content = document.createElement("div");
  content.className = "toast-content";
  content.textContent = message;

  // Assemble toast
  toast.appendChild(icon);
  toast.appendChild(content);
  container.appendChild(toast);

  // Announce to screen readers
  announceToScreenReader(message, type === "error" ? "assertive" : "polite");

  // Auto-remove after duration
  setTimeout(() => {
    toast.classList.add("toast-exit");
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      // Clean up container if empty
      if (container.children.length === 0 && container.parentNode) {
        container.parentNode.removeChild(container);
      }
    }, 300); // Match animation duration
  }, duration);
}

// ===== THEME TOGGLE FUNCTIONALITY =====

const themeToggle = document.getElementById("theme-toggle");
const htmlElement = document.documentElement;

// Load theme and mode from localStorage
let savedTheme = "dracula";
let currentMode = "dark";

const experimentalTheme = getLocalStorage("experimentalTheme");
const experimentalViewMode = getLocalStorage("experimentalViewMode");
const storedMode = getLocalStorage("themeMode", "dark"); // New: separate mode storage

// Handle theme (color scheme)
if (
  experimentalTheme &&
  VALID_EXPERIMENTAL_THEMES.includes(experimentalTheme) &&
  !EXPERIMENTAL_VIEW_MODES.includes(experimentalTheme) // Make sure it's not a view mode
) {
  // Experimental theme is set
  savedTheme = experimentalTheme;
  // Detect mode from theme name or use stored mode
  const detectedMode = getCurrentMode(experimentalTheme);
  currentMode = detectedMode;
  // Update stored mode if it differs
  if (detectedMode !== storedMode) {
    setLocalStorage("themeMode", detectedMode);
  }
} else {
  if (
    experimentalTheme &&
    !EXPERIMENTAL_VIEW_MODES.includes(experimentalTheme)
  ) {
    console.warn(
      `Invalid experimental theme: ${experimentalTheme}. Using default.`,
    );
    removeLocalStorage("experimentalTheme");
  }
  savedTheme = getLocalStorage("theme", "dracula");
  currentMode = getCurrentMode(savedTheme);
  setLocalStorage("themeMode", currentMode);
}

// Handle view mode (layout)
let savedView = "list";
if (
  experimentalViewMode &&
  EXPERIMENTAL_VIEW_MODES.includes(experimentalViewMode)
) {
  savedView = experimentalViewMode;
} else {
  savedView = getLocalStorage("view", "list");
}

htmlElement.setAttribute("data-theme", savedTheme);
htmlElement.setAttribute("data-view", savedView);
updateThemeButton(currentMode);

themeToggle.addEventListener("click", async () => {
  const currentTheme = htmlElement.getAttribute("data-theme");
  const currentBaseTheme = getBaseTheme(currentTheme);
  const currentThemeMode = getCurrentMode(currentTheme);
  const newMode = currentThemeMode === "light" ? "dark" : "light";

  // Show loading state on the button
  LoadingState.show(themeToggle, `Switching to ${newMode} mode`);

  // Simulate brief delay for visual feedback
  await new Promise((resolve) =>
    setTimeout(resolve, TIMEOUTS.LOADING_MIN_DURATION),
  );

  // Apply new mode to current theme (base or experimental)
  let newTheme;
  if (currentBaseTheme && EXPERIMENTAL_BASE_THEMES.includes(currentBaseTheme)) {
    // Experimental theme: toggle between light and dark variants
    newTheme = applyModeToTheme(currentBaseTheme, newMode);
    setLocalStorage("experimentalTheme", newTheme);
  } else {
    // Standard theme: just "light" or "dark"
    newTheme = newMode;
    setLocalStorage("theme", newTheme);
    removeLocalStorage("experimentalTheme");
  }

  // Update mode storage
  setLocalStorage("themeMode", newMode);

  htmlElement.setAttribute("data-theme", newTheme);
  updateThemeButton(newMode);

  // Hide loading state
  LoadingState.hide(themeToggle);
});

function updateThemeButton(mode) {
  const iconSVG = document.getElementById("theme-icon");
  const themeText = document.getElementById("theme-text");

  // Clear existing content
  while (iconSVG.firstChild) {
    iconSVG.removeChild(iconSVG.firstChild);
  }

  if (mode === "dark") {
    // Sun icon for light mode
    const sunPath =
      '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
    const svg = createSVG(24, 24, sunPath);
    Array.from(svg.attributes).forEach((attr) => {
      iconSVG.setAttribute(attr.name, attr.value);
    });
    while (svg.firstChild) {
      iconSVG.appendChild(svg.firstChild);
    }
    if (themeText) {
      themeText.textContent = "Light Mode";
    }
  } else {
    // Moon icon for dark mode
    const moonPath =
      '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
    const svg = createSVG(24, 24, moonPath);
    Array.from(svg.attributes).forEach((attr) => {
      iconSVG.setAttribute(attr.name, attr.value);
    });
    while (svg.firstChild) {
      iconSVG.appendChild(svg.firstChild);
    }
    if (themeText) {
      themeText.textContent = "Dark Mode";
    }
  }
}

// ===== VIEW SELECTOR FUNCTIONALITY =====

// Initialize view selector - need to get value from correct storage location
const viewSelect = document.getElementById("view-select");
if (viewSelect) {
  // Set initial value from savedView (already determined above)
  viewSelect.value = savedView;

  // Listen for changes
  viewSelect.addEventListener("change", () => {
    const value = viewSelect.value;
    applyView(value);
  });
}

function applyView(view) {
  // Apply the view mode - handles both standard and experimental view modes
  if (EXPERIMENTAL_VIEW_MODES.includes(view)) {
    // Experimental view mode: store in experimentalViewMode
    setLocalStorage("experimentalViewMode", view);
    removeLocalStorage("view");
  } else {
    // Standard view mode (list/card): store in view
    setLocalStorage("view", view);
    removeLocalStorage("experimentalViewMode");
  }
  htmlElement.setAttribute("data-view", view);
}

// ===== SIDEBAR FUNCTIONALITY =====

function initializeSidebarState(sidebar) {
  // On mobile, start collapsed; on desktop, start expanded
  if (window.innerWidth <= BREAKPOINTS.MOBILE) {
    sidebar.classList.add("collapsed");
  } else {
    sidebar.classList.remove("collapsed");
  }
}

const sidebarToggle = document.getElementById("nav-toggle");
const sidebar = document.getElementById("sidebar");

if (sidebarToggle && sidebar) {
  initializeSidebarState(sidebar);
  // Debounce resize event to improve performance (150ms delay)
  window.addEventListener(
    "resize",
    debounce(() => initializeSidebarState(sidebar), 150),
  );

  sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
  });

  // Close sidebar when clicking outside (mobile only)
  document.addEventListener("click", (e) => {
    if (window.innerWidth <= BREAKPOINTS.MOBILE) {
      if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.add("collapsed");
      }
    }
  });
}

// ===== TIMEFRAME FILTERING =====

const TIMEFRAME_HOURS = {
  "1day": 24,
  "3days": 72,
  "7days": 168,
  "30days": 720,
  "1year": 8760,
};

const savedTimeframe = getLocalStorage("timeframe", "1day");
initializeDropdown(
  "timeframe-select",
  "timeframe",
  "1day",
  applyTimeframeFilter,
);
applyTimeframeFilter(savedTimeframe);

function applyTimeframeFilter(timeframe) {
  const hours = TIMEFRAME_HOURS[timeframe] || 24;
  const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000);

  // Filter articles by timeframe
  const allArticles = document.querySelectorAll(".article-item");

  allArticles.forEach((article) => {
    const publishedISO = article.getAttribute("data-published");
    if (publishedISO) {
      try {
        const publishDate = new Date(publishedISO);
        if (!Number.isNaN(publishDate.getTime())) {
          if (publishDate >= cutoffTime) {
            article.removeAttribute("data-hidden-by-timeframe");
            article.style.display = "";
          } else {
            article.setAttribute("data-hidden-by-timeframe", "true");
            article.style.display = "none";
          }
        } else {
          article.removeAttribute("data-hidden-by-timeframe");
          article.style.display = "";
        }
      } catch {
        article.removeAttribute("data-hidden-by-timeframe");
        article.style.display = "";
      }
    } else {
      article.removeAttribute("data-hidden-by-timeframe");
      article.style.display = "";
    }
  });

  // Update feed counts and reorder
  updateFeedCounts();
  updateStats();
}

/**
 * Update feed counts and reorder feeds
 */
// Helper to cache section elements
function getSectionElements(section) {
  // Use a WeakMap to cache elements per section
  if (!getSectionElements.cache) {
    getSectionElements.cache = new WeakMap();
  }

  if (!getSectionElements.cache.has(section)) {
    getSectionElements.cache.set(section, {
      heading: section.querySelector("h2"),
      countBadge: section.querySelector(".feed-count"),
      articleList: section.querySelector(".article-list"),
      // noArticlesMsg is dynamic, query each time
    });
  }

  return getSectionElements.cache.get(section);
}

// Helper function to extract feed name from section heading
function extractFeedName(section) {
  const cached = getSectionElements(section);
  const heading = cached.heading;
  if (!heading) {
    return "";
  }

  const titleLink = heading.querySelector(".feed-title-link");
  if (titleLink) {
    return titleLink.textContent.trim();
  }

  const headingClone = heading.cloneNode(true);
  const countBadge = headingClone.querySelector(".feed-count");
  if (countBadge) {
    countBadge.remove();
  }

  return headingClone.textContent.trim();
}

// Helper function to update count badge
function updateCountBadge(section, count) {
  const cached = getSectionElements(section);
  const countBadge = cached.countBadge;
  if (countBadge) {
    const plural = count !== 1 ? "s" : "";
    countBadge.textContent = `${count} article${plural}`;
  }
}

// Helper function to update "no articles" message
function updateNoArticlesMessage(
  section,
  count,
  messageText = "No new articles in this time period",
) {
  const cached = getSectionElements(section);
  const noArticlesMsg = section.querySelector(".no-articles"); // Query fresh as it's dynamic
  const articleList = cached.articleList;

  if (count === 0) {
    if (articleList) articleList.style.display = "none";
    if (!noArticlesMsg) {
      const msg = document.createElement("div");
      msg.className = "no-articles";
      msg.textContent = messageText;
      section.appendChild(msg);
    } else {
      noArticlesMsg.style.display = "";
    }
  } else {
    if (articleList) articleList.style.display = "";
    if (noArticlesMsg) {
      noArticlesMsg.remove();
    }
  }
}

// Helper function to order feeds by unread status
function orderFeedsByUnreadStatus(feedsData) {
  const feedsWithUnread = feedsData
    .filter((f) => f.unreadCount > 0)
    .sort((a, b) => a.name.localeCompare(b.name));
  const feedsAllRead = feedsData
    .filter((f) => f.unreadCount === 0 && (f.count || 0) > 0)
    .sort((a, b) => a.name.localeCompare(b.name));
  const emptyFeeds = feedsData
    .filter((f) => (f.count || 0) === 0)
    .sort((a, b) => a.name.localeCompare(b.name));

  return [...feedsWithUnread, ...feedsAllRead, ...emptyFeeds];
}

function updateFeedCounts() {
  const feedSections = document.querySelectorAll(".feed-section");
  const feedsData = [];

  feedSections.forEach((section) => {
    // Skip feeds that are hidden by the feed filter
    if (section.hasAttribute("data-hidden-by-filter")) {
      return;
    }

    const articles = section.querySelectorAll(".article-item");
    const visibleArticles = Array.from(articles).filter(
      (a) => a.style.display !== "none",
    );
    const count = visibleArticles.length;

    // Calculate unread count (articles that are visible and not marked as read)
    const unreadArticles = Array.from(articles).filter((article) => {
      const link = article.querySelector(".article-title");
      if (!link) return false;
      const articleUrl = link.getAttribute("href");
      return (
        !isArticleRead(articleUrl) &&
        !article.hasAttribute("data-hidden-by-timeframe")
      );
    });
    const unreadCount = unreadArticles.length;

    updateCountBadge(section, count);
    updateNoArticlesMessage(section, count);

    feedsData.push({
      element: section,
      count,
      unreadCount,
      name: extractFeedName(section),
    });
  });

  // Reorder feeds by unread status
  if (feedSections.length > 0 && feedSections[0].parentNode) {
    const parent = feedSections[0].parentNode;
    const footer = parent.querySelector(".footer");
    const orderedFeeds = orderFeedsByUnreadStatus(feedsData);
    reorderDOMElements(orderedFeeds, parent, footer);
  }
}

function updateStats() {
  const statCards = document.querySelectorAll(".stat-card");
  if (statCards.length === 0) return;

  const allArticles = document.querySelectorAll(".article-item");
  if (allArticles.length === 0) return;

  const visibleArticles = Array.from(allArticles).filter(
    (a) => a.style.display !== "none",
  );

  statCards.forEach((card) => {
    const label = card.querySelector(".stat-label");
    if (label && label.textContent === "Total Articles") {
      const value = card.querySelector(".stat-value");
      if (value) {
        value.textContent = visibleArticles.length;
      }
    }
  });
}

// ===== MARK AS READ FUNCTIONALITY =====

function getReadArticles() {
  return getLocalStorageJSON(READ_ARTICLES_KEY, []);
}

function saveReadArticles(readArticles) {
  setLocalStorageJSON(READ_ARTICLES_KEY, readArticles);
}

function isArticleRead(articleUrl) {
  const readArticles = getReadArticles();
  return readArticles.includes(articleUrl);
}

function toggleArticleRead(articleUrl) {
  let readArticles = getReadArticles();

  if (readArticles.includes(articleUrl)) {
    readArticles = readArticles.filter((url) => url !== articleUrl);
  } else {
    readArticles.push(articleUrl);
  }

  saveReadArticles(readArticles);
  return readArticles.includes(articleUrl);
}

function markArticleAsRead(articleUrl) {
  const readArticles = getReadArticles();
  if (!readArticles.includes(articleUrl)) {
    readArticles.push(articleUrl);
    saveReadArticles(readArticles);
  }
  return true;
}

function resetAllReadArticles() {
  try {
    removeLocalStorage(READ_ARTICLES_KEY);
    initializeReadStatus();
    updateFeedCountsAfterReadFilter();
    // Show success toast
    showToast("All read articles cleared successfully", "success");
  } catch (e) {
    console.warn("Unable to reset read articles:", e);
    // Show error toast
    showToast("Failed to clear read articles", "error");
  }
}

function initializeReadStatus() {
  const articles = document.querySelectorAll(".article-item");

  articles.forEach((article) => {
    const link = article.querySelector(".article-title");
    if (!link) return;

    const articleUrl = link.getAttribute("href");
    if (!articleUrl) return;

    const existingIndicator = article.querySelector(".read-indicator");
    if (existingIndicator) {
      existingIndicator.remove();
    }

    const indicator = document.createElement("button");
    indicator.className = "read-indicator";
    indicator.setAttribute("aria-label", "Mark as read/unread");
    const svg = createSVG(
      16,
      16,
      '<polyline points="20 6 9 17 4 12"></polyline>',
    );
    indicator.appendChild(svg);

    indicator.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      toggleArticleRead(articleUrl);
      updateArticleReadState(article, articleUrl);
      updateFeedCountsAfterReadFilter();
    });

    article.insertBefore(indicator, article.firstChild);
    updateArticleReadState(article, articleUrl);
  });
}

function updateArticleReadState(article, articleUrl) {
  const indicator = article.querySelector(".read-indicator");
  const isRead = isArticleRead(articleUrl);

  if (isRead) {
    article.classList.add("read");
    if (indicator) indicator.classList.add("active");
  } else {
    article.classList.remove("read");
    if (indicator) indicator.classList.remove("active");
  }
}

function updateFeedCountsAfterReadFilter() {
  const feedSections = document.querySelectorAll(".feed-section");
  const feedsData = [];

  feedSections.forEach((section) => {
    // Skip feeds that are hidden by the feed filter
    if (section.hasAttribute("data-hidden-by-filter")) {
      return;
    }

    const cached = getSectionElements(section);
    const articleList = cached.articleList;

    // Handle feeds with no article list (empty feeds with 0 articles across all timeframes)
    if (!articleList) {
      // Empty feed with no articles at all
      feedsData.push({
        element: section,
        count: 0,
        unreadCount: 0,
        name: extractFeedName(section),
      });
      return;
    }

    const articles = section.querySelectorAll(".article-item");
    const visibleArticles = Array.from(articles).filter(
      (a) => a.style.display !== "none",
    );

    const unreadArticles = Array.from(articles).filter((article) => {
      const link = article.querySelector(".article-title");
      if (!link) return false;
      const articleUrl = link.getAttribute("href");
      return (
        !isArticleRead(articleUrl) &&
        !article.hasAttribute("data-hidden-by-timeframe")
      );
    });

    const count = visibleArticles.length;
    const unreadCount = unreadArticles.length;

    reorderArticlesInFeed(articleList, articles);
    updateCountBadge(section, count);

    // Use different message text for this context
    const noArticlesMsg = section.querySelector(".no-articles");

    if (count === 0) {
      if (articleList) articleList.style.display = "none";
      if (!noArticlesMsg) {
        const msg = document.createElement("div");
        msg.className = "no-articles";
        msg.textContent = "No articles to display";
        section.appendChild(msg);
      } else {
        noArticlesMsg.style.display = "";
      }
    } else {
      if (articleList) articleList.style.display = "";
      if (noArticlesMsg) noArticlesMsg.style.display = "none";
    }

    feedsData.push({
      element: section,
      count,
      unreadCount,
      name: extractFeedName(section),
    });
  });

  reorderFeedsByUnreadStatus(feedsData);
  updateStats();
}

function reorderArticlesInFeed(articleList, articles) {
  if (!articleList || articles.length === 0) return;

  const articleData = Array.from(articles).map((article) => {
    const link = article.querySelector(".article-title");
    const articleUrl = link ? link.getAttribute("href") : null;
    const isRead = articleUrl ? isArticleRead(articleUrl) : false;
    const publishedISO = article.getAttribute("data-published");
    const publishDate = publishedISO ? new Date(publishedISO) : new Date(0);

    return {
      element: article,
      isRead,
      articleUrl,
      publishDate,
    };
  });

  const unreadArticles = articleData
    .filter((a) => !a.isRead)
    .sort((a, b) => b.publishDate - a.publishDate);
  const readArticles = articleData
    .filter((a) => a.isRead)
    .sort((a, b) => b.publishDate - a.publishDate);

  const orderedArticles = [...unreadArticles, ...readArticles];
  orderedArticles.forEach((articleData) => {
    articleList.appendChild(articleData.element);
  });
}

function reorderFeedsByUnreadStatus(feedsData) {
  if (feedsData.length === 0) return;

  const feedSections = document.querySelectorAll(".feed-section");
  if (feedSections.length === 0) return;

  const parent = feedSections[0].parentNode;
  if (!parent) return;

  const footer = parent.querySelector(".footer");
  const orderedFeeds = orderFeedsByUnreadStatus(feedsData);
  reorderDOMElements(orderedFeeds, parent, footer);
}

function setupMarkAsReadControls() {
  const resetButton = document.getElementById("reset-read-button");
  if (resetButton) {
    const newButton = resetButton.cloneNode(true);
    resetButton.parentNode.replaceChild(newButton, resetButton);

    newButton.addEventListener(
      "click",
      async function handleResetClick(e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        try {
          const confirmed = window.confirm(
            "Are you sure you want to clear all read articles? This will mark all articles as unread and restore the original feed order.",
          );

          if (confirmed === true) {
            // Show loading state
            LoadingState.show(newButton, "Clearing read articles");

            // Add slight delay for visual feedback
            await new Promise((resolve) =>
              setTimeout(resolve, TIMEOUTS.LOADING_MIN_DURATION),
            );

            resetAllReadArticles();

            // Hide loading state
            LoadingState.hide(newButton);
          }
        } catch (error) {
          console.error("Error in reset button handler:", error);
          LoadingState.hide(newButton);
          resetAllReadArticles();
        }

        return false;
      },
      { passive: false, capture: true },
    );
  }
}

function initializeMarkAsReadFeature() {
  initializeReadStatus();
  updateFeedCountsAfterReadFilter();
  setupMarkAsReadControls();
}

document.addEventListener("DOMContentLoaded", initializeMarkAsReadFeature);

if (
  document.readyState === "complete" ||
  document.readyState === "interactive"
) {
  setTimeout(initializeMarkAsReadFeature, 0);
}

// ===== FEED FILTERING =====

function getEnabledFeeds() {
  return getLocalStorageJSON("enabledFeeds", null);
}

function applyFeedFilter() {
  const enabledFeeds = getEnabledFeeds();

  if (!enabledFeeds || enabledFeeds.length === 0) {
    return;
  }

  const navLinks = document.querySelectorAll(".nav-link");
  navLinks.forEach((link) => {
    const linkText = link.textContent.trim();
    if (linkText === "All Feeds" || linkText === "Summary") {
      return;
    }

    if (!enabledFeeds.includes(linkText)) {
      link.style.display = "none";
    } else {
      link.style.display = "";
    }
  });

  const feedSections = document.querySelectorAll(".feed-section");
  feedSections.forEach((section) => {
    const feedName = extractFeedName(section);

    if (!enabledFeeds.includes(feedName)) {
      section.style.display = "none";
      section.setAttribute("data-hidden-by-filter", "true");
    } else {
      section.style.display = "";
      section.removeAttribute("data-hidden-by-filter");
    }
  });

  updateStats();
}

function initializeFeedFilter() {
  applyFeedFilter();
}

document.addEventListener("DOMContentLoaded", initializeFeedFilter);

if (
  document.readyState === "complete" ||
  document.readyState === "interactive"
) {
  setTimeout(initializeFeedFilter, 0);
}

window.addEventListener("storage", (e) => {
  if (e.key === getScopedStorageKey("enabledFeeds")) {
    applyFeedFilter();
  }
});

// ===== ACCESSIBILITY ENHANCEMENTS =====

/**
 * Initialize accessibility features across the application
 */
function initAccessibility() {
  // Add keyboard navigation for settings menu items
  const settingsMenuItems = document.querySelectorAll(".settings-menu-item");
  settingsMenuItems.forEach((item) => {
    item.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        this.click();
      }
    });
  });

  // Add keyboard support for article items to mark as read
  const articleItems = document.querySelectorAll(".article-item");
  articleItems.forEach((item) => {
    const link = item.querySelector(".article-title");
    if (link) {
      // Add keyboard event for marking as read (Ctrl+M or Cmd+M)
      item.addEventListener("keydown", function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === "m") {
          e.preventDefault();
          // Toggle read status
          this.classList.toggle("read");
          const articleUrl = link.href;
          markArticleAsRead(articleUrl);
          announceToScreenReader(
            "Article marked as " +
              (this.classList.contains("read") ? "read" : "unread"),
          );
        }
      });
    }
  });

  // Ensure proper focus management
  enhanceFocusManagement();

  // Add ARIA live region if not exists
  addAriaLiveRegion();

  // Prevent flash of transitions on page load
  preventInitialTransitions();
}

/**
 * Announce messages to screen readers
 * @param {string} message - Message to announce
 * @param {string} priority - 'polite' or 'assertive'
 */
function announceToScreenReader(message, priority = "polite") {
  const liveRegion = document.getElementById("aria-live-region");
  if (liveRegion) {
    liveRegion.setAttribute("aria-live", priority);
    liveRegion.textContent = message;
    // Clear after announcement (3 seconds to allow for slower screen readers)
    setTimeout(() => {
      liveRegion.textContent = "";
    }, TIMEOUTS.SCREEN_READER_ANNOUNCEMENT);
  }
}

/**
 * Add ARIA live region for dynamic announcements
 */
function addAriaLiveRegion() {
  if (!document.getElementById("aria-live-region")) {
    const liveRegion = document.createElement("div");
    liveRegion.id = "aria-live-region";
    liveRegion.className = "sr-only";
    liveRegion.setAttribute("aria-live", "polite");
    liveRegion.setAttribute("aria-atomic", "true");
    document.body.appendChild(liveRegion);
  }
}

/**
 * Enhance focus management for better keyboard navigation
 */
function enhanceFocusManagement() {
  // Trap focus in modal-like elements (if any)
  const modals = document.querySelectorAll('[role="dialog"]');
  modals.forEach((modal) => {
    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    );

    if (focusableElements.length > 0) {
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      modal.addEventListener("keydown", function (e) {
        if (e.key === "Tab") {
          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      });
    }
  });
}

/**
 * Prevent flash of transitions on initial page load
 */
function preventInitialTransitions() {
  document.body.classList.add("preload");
  setTimeout(() => {
    document.body.classList.remove("preload");
  }, 100);
}

/**
 * Update article count with screen reader announcement
 * @param {number} count - Number of visible articles
 * @param {string} filterName - Name of current filter
 */
// eslint-disable-next-line no-unused-vars
function updateArticleCountAccessible(count, filterName) {
  announceToScreenReader(
    `Showing ${count} articles for ${filterName}`,
    "polite",
  );
}

/**
 * Enhance timeframe selector with announcements
 */
function enhanceTimeframeSelector() {
  const timeframeSelect = document.getElementById("timeframe-select");
  if (timeframeSelect) {
    timeframeSelect.addEventListener("change", function () {
      const selectedOption = this.options[this.selectedIndex].text;
      announceToScreenReader(`Filter changed to ${selectedOption}`, "polite");
    });
  }
}

/**
 * Enhance view mode selector with announcements
 */
function enhanceViewModeSelector() {
  const viewSelect = document.getElementById("view-select");
  if (viewSelect) {
    viewSelect.addEventListener("change", function () {
      const selectedOption = this.options[this.selectedIndex].text;
      announceToScreenReader(
        `View mode changed to ${selectedOption}`,
        "polite",
      );
    });
  }
}

/**
 * Show a prominent return-to-production banner on preview deployments
 */
function initializePreviewReturnBanner() {
  const previewContext = getPreviewSiteContext();
  const header = document.querySelector(".header");

  if (
    !previewContext ||
    !header ||
    document.getElementById("preview-site-banner")
  ) {
    return;
  }

  const banner = document.createElement("div");
  banner.className = "preview-site-banner";
  banner.id = "preview-site-banner";
  banner.setAttribute("role", "region");
  banner.setAttribute("aria-label", "Preview deployment notice");
  banner.setAttribute("aria-live", "polite");

  const content = document.createElement("div");
  content.className = "preview-site-banner-content";

  const label = document.createElement("span");
  label.className = "preview-site-banner-label";
  label.textContent = "Preview site";

  const message = document.createElement("p");
  message.className = "preview-site-banner-text";
  message.textContent = "You are viewing a preview deployment, not production.";

  const link = document.createElement("a");
  link.className = "preview-return-button";
  link.id = "return-to-production-link";
  link.href = previewContext.productionUrl;
  link.textContent = "Return to Production";

  content.appendChild(label);
  content.appendChild(message);
  banner.appendChild(content);
  banner.appendChild(link);
  header.parentNode.insertBefore(banner, header);
}

// Initialize accessibility features when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", function () {
    initializePreviewReturnBanner();
    initAccessibility();
    enhanceTimeframeSelector();
    enhanceViewModeSelector();
  });
} else {
  initializePreviewReturnBanner();
  initAccessibility();
  enhanceTimeframeSelector();
  enhanceViewModeSelector();
}

// ===== TOUCH TARGET ENHANCEMENTS =====

/**
 * Ensure all interactive elements meet minimum touch target size
 */
function ensureTouchTargets() {
  // Cache touch device detection
  const isTouchDevice =
    "ontouchstart" in window || navigator.maxTouchPoints > 0;

  // Only run on touch devices and only once
  if (!isTouchDevice || document.body.dataset.touchTargetsEnhanced === "true") {
    return;
  }

  // Mark as enhanced to prevent re-running
  document.body.dataset.touchTargetsEnhanced = "true";

  const interactiveElements = document.querySelectorAll(
    'button, a, input, select, [role="button"], .article-item',
  );

  interactiveElements.forEach((element) => {
    const rect = element.getBoundingClientRect();
    const minSize = ACCESSIBILITY.MIN_TOUCH_TARGET_SIZE;

    // Add padding if element is too small
    if (rect.height < minSize || rect.width < minSize) {
      const currentPadding = window.getComputedStyle(element).padding;
      if (currentPadding === "0px" || currentPadding === "") {
        element.style.padding = "0.75rem";
      }
    }
  });
}

// Run touch target check after page load
window.addEventListener("load", ensureTouchTargets);

// ===== IMPROVED ERROR HANDLING WITH ACCESSIBILITY =====

/**
 * Display accessible error messages
 * @param {string} message - Error message to display
 * @param {string} severity - 'error', 'warning', or 'info'
 */
// eslint-disable-next-line no-unused-vars
function displayAccessibleError(message, severity = "error") {
  const errorContainer = document.getElementById("error-container");
  if (errorContainer) {
    errorContainer.setAttribute(
      "role",
      severity === "error" ? "alert" : "status",
    );
    errorContainer.setAttribute(
      "aria-live",
      severity === "error" ? "assertive" : "polite",
    );
    errorContainer.textContent = message;

    // Auto-dismiss after 5 seconds for non-critical messages
    if (severity !== "error") {
      setTimeout(() => {
        errorContainer.textContent = "";
      }, TIMEOUTS.ERROR_MESSAGE_DISMISS);
    }
  }

  // Also announce to screen readers
  announceToScreenReader(
    message,
    severity === "error" ? "assertive" : "polite",
  );
}

// ===== EXTERNAL LINK INDICATORS =====

/**
 * Add external link indicators to all article links
 */
function initializeExternalLinkIndicators() {
  const articleLinks = document.querySelectorAll(".article-title");

  articleLinks.forEach((link) => {
    // Skip if already has indicator
    if (link.querySelector(".external-link-icon")) {
      return;
    }

    // Add screen reader text
    const srText = document.createElement("span");
    srText.className = "sr-only";
    srText.textContent = " (opens in new tab)";

    // Add visual icon
    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("class", "external-link-icon");
    icon.setAttribute("aria-hidden", "true");
    icon.setAttribute("width", "12");
    icon.setAttribute("height", "12");
    icon.setAttribute("viewBox", "0 0 24 24");
    icon.setAttribute("fill", "none");
    icon.setAttribute("stroke", "currentColor");
    icon.setAttribute("stroke-width", "2");
    icon.setAttribute("stroke-linecap", "round");
    icon.setAttribute("stroke-linejoin", "round");

    // External link icon path
    const path1 = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "path",
    );
    path1.setAttribute(
      "d",
      "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6",
    );

    const path2 = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "polyline",
    );
    path2.setAttribute("points", "15 3 21 3 21 9");

    const path3 = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "line",
    );
    path3.setAttribute("x1", "10");
    path3.setAttribute("y1", "14");
    path3.setAttribute("x2", "21");
    path3.setAttribute("y2", "3");

    icon.appendChild(path1);
    icon.appendChild(path2);
    icon.appendChild(path3);

    // Append to link
    link.appendChild(srText);
    link.appendChild(icon);
  });
}

// Initialize external link indicators on page load
if (document.readyState === "loading") {
  document.addEventListener(
    "DOMContentLoaded",
    initializeExternalLinkIndicators,
  );
} else {
  initializeExternalLinkIndicators();
}
