/**
 * refreshJWTToken.js
 *
 * Finds a specific Chrome tab by URL pattern, then reads a JWT token (or any
 * value) from that tab's localStorage.
 *
 * Requires the following Chrome Extension manifest permissions:
 *   "tabs", "scripting", and the target origin in "host_permissions".
 *
 * When NOT running inside a Chrome extension (e.g. during local dev in the
 * same tab), it falls back to reading from the current page's localStorage.
 */

/**
 * Read a value from localStorage in a specific Chrome tab.
 *
 * @param {string} tabUrlPattern - URL pattern to match (e.g. "https://app.example.com/*")
 * @param {string} storageKey    - localStorage key whose value should be returned
 * @returns {Promise<string>} The stored value
 * @throws {Error} Descriptive error explaining exactly why retrieval failed
 */
async function getTokenFromTab(tabUrlPattern, storageKey) {
  // ── Chrome Extension context ──────────────────────────────────────────────
  if (typeof chrome !== 'undefined' && chrome.tabs && chrome.scripting) {
    let tabs;
    try {
      tabs = await chrome.tabs.query({ url: tabUrlPattern });
    } catch (e) {
      throw new Error(`chrome.tabs.query failed: ${e.message}. Check that "tabs" permission is declared in manifest.json.`);
    }

    if (!tabs || tabs.length === 0) {
      throw new Error(`No open tab matches the pattern "${tabUrlPattern}". Make sure the target site is open in Chrome.`);
    }

    const targetTab = tabs[0];
    console.info(`[refreshJWTToken] Found tab: [${targetTab.id}] ${targetTab.url}`);

    let results;
    try {
      results = await chrome.scripting.executeScript({
        target: { tabId: targetTab.id },
        func: (key) => localStorage.getItem(key),
        args: [storageKey],
      });
    } catch (e) {
      throw new Error(`chrome.scripting.executeScript failed: ${e.message}. Check that "scripting" permission and host_permissions are declared in manifest.json.`);
    }

    const value = results?.[0]?.result ?? null;

    if (value === null) {
      // List available keys to help diagnose the wrong key name
      let availableKeys = [];
      try {
        const keysResult = await chrome.scripting.executeScript({
          target: { tabId: targetTab.id },
          func: () => Object.keys(localStorage),
        });
        availableKeys = keysResult?.[0]?.result ?? [];
      } catch (_) { /* ignore */ }

      const hint = availableKeys.length
        ? `Available localStorage keys: [${availableKeys.join(', ')}]`
        : 'localStorage appears to be empty on that tab.';
      throw new Error(`Key "${storageKey}" not found in localStorage of tab "${targetTab.url}". ${hint}`);
    }

    return value;
  }

  // ── Fallback: same-page localStorage (non-extension context) ─────────────
  console.warn(
    '[refreshJWTToken] Chrome extension APIs not available. ' +
    'Reading from current page localStorage instead.'
  );

  const value = localStorage.getItem(storageKey);
  if (value === null) {
    const availableKeys = Object.keys(localStorage);
    const hint = availableKeys.length
      ? `Available keys on this page: [${availableKeys.join(', ')}]`
      : 'localStorage is empty on this page.';
    throw new Error(
      `Chrome extension APIs are not available — cannot read localStorage from "${tabUrlPattern}". ` +
      `Falling back to current page localStorage: key "${storageKey}" not found. ${hint}`
    );
  }

  return value;
}

/**
 * Convenience wrapper: find the target tab, read the JWT token, and return it.
 *
 * @param {string} siteURLPattern  - URL pattern of the target tab
 * @param {string} localStorageKey - localStorage key holding the JWT
 * @returns {Promise<string>} The token value
 * @throws {Error} Descriptive error if retrieval fails
 */
async function refreshJWTToken(siteURLPattern, localStorageKey) {
  const token = await getTokenFromTab(siteURLPattern, localStorageKey);
  console.info('[refreshJWTToken] Token retrieved successfully.');
  return token;
}
