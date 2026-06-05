---
name: testing-landing-page
description: Test the Build Flow Action landing page end-to-end. Use when verifying UI changes to site/index.html, site/styles.css, or site/script.js.
---

# Testing the Landing Page

## Prerequisites

- The `site/` directory contains `index.html`, `styles.css`, and `script.js`
- Python 3 available for local HTTP server
- Chrome browser for visual testing

## Setup

1. Start a local HTTP server from the `site/` directory:
   ```bash
   cd /path/to/build-flow-action/site && python3 -m http.server 8080 &
   ```
2. Open `http://localhost:8080` in Chrome

## Test 1: Page Structure & Content (Desktop)

Verify all 8 sections render at full desktop width:

| Section | What to check |
|---------|---------------|
| Hero (#hero) | Badge "Open Source · MIT", h1 with train emoji, tagline, 2 CTA buttons, philosophy text |
| Why Build Flow (#why) | 6 feature cards in 3-column grid |
| How It Works (#how) | Pipeline: steps 1, 2, 3a/3b (parallel), 4 + CodeQL aside |
| Supported Ecosystems (#ecosystems) | 8 cards in 4-column grid (Node+Bun through Custom) |
| Available Workflows (#workflows) | 4 cards, app.yml has "Recommended" badge |
| Getting Started (#setup) | 3 numbered steps with YAML code block |
| Branch Strategy (#strategy) | 4 strategy cards |
| Footer | Dynamic year via JS (`new Date().getFullYear()`), project and org links |

## Test 2: Navigation Scroll & Shrink

1. At page top: verify nav height is 64px (no `.scrolled` class)
2. Click a nav link (e.g., "How It Works")
3. Verify page scrolls to correct `#section` and URL updates
4. Verify nav shrinks to 52px with `.scrolled` class (triggers at scrollY > 20)
5. Click the logo to return to hero
6. Verify nav restores to 64px

You can check nav state programmatically:
```javascript
JSON.stringify({
  scrollY: window.scrollY,
  navHasScrolled: document.getElementById('nav').classList.contains('scrolled'),
  navHeight: getComputedStyle(document.getElementById('nav')).height
})
```

## Test 3: Mobile Responsive (375px)

1. Open Chrome DevTools (F12) and toggle device toolbar (Ctrl+Shift+M)
2. Set viewport to ~375px width
3. Verify hamburger button (3 lines) is visible, desktop nav links hidden
4. Click hamburger — dropdown should show all 6 nav links, `aria-expanded="true"`
5. Click a nav link — dropdown should auto-close, page scrolls to section
6. Verify cards use single-column layout at mobile width

**Tip:** The mobile breakpoint is at 768px (hamburger appears). Single-column cards kick in at 480px.

## Test 4: Deploy Workflow Validation

Validate `.github/workflows/deploy.yml` via shell:

```bash
# Check YAML parses
cat .github/workflows/deploy.yml

# Verify site/ directory has all files
ls -la site/

# Check triggers and permissions
grep -A3 "on:" .github/workflows/deploy.yml
grep -A3 "permissions:" .github/workflows/deploy.yml
grep "path:" .github/workflows/deploy.yml
```

Expected: triggers on push to main (paths: `site/**`) + workflow_dispatch, permissions include pages write + id-token write, upload path is `site`.

## Notes

- The page uses a dark theme with primary color `#016EEA`
- CSS variables are defined in `:root` in styles.css
- The `.js` class on `<html>` gates mobile nav visibility (progressive enhancement)
- Footer year is set dynamically by `script.js` using `getElementById('year')`
- If the hamburger menu doesn't appear in DevTools device mode, make sure the page has reloaded after enabling the device toolbar — the `.js` class needs to be present on `<html>`
- No secrets are needed for local testing
