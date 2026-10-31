# JobRadar India UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the JobRadar India single-page frontend into a clear, premium, responsive job-search workspace without changing its data or hosting architecture.

**Architecture:** Keep the existing HTML/CSS/inline JavaScript and hash router. Update layout and component styling in index.html, preserve all JavaScript-consumed IDs and behavior, then bump the service-worker shell cache version.

**Tech Stack:** HTML5, CSS, vanilla JavaScript, GitHub Pages, existing GitHub Actions checks.

**Spec:** docs/superpowers/specs/2026-10-31-jobradar-ui-redesign-design.md

## Global Constraints
- Do not change the job database schema, eligibility classifier, job sources, company mapping, or verification pipeline.
- Keep the index.html single-file app, current routes, and localStorage keys.
- Do not add runtime libraries or external asset dependencies.
- Preserve accessibility labels, keyboard focus, reduced-motion support, and light/dark theme toggle.
- Preserve the distinction between companies listed in the directory and companies with matching active JobRadar jobs.

## Review Focus
- Small mobile viewport: controls remain usable and do not overflow horizontally.
- Existing route and JS element IDs: no missing hooks after markup restructuring.
- Long employer/title/location strings: cards wrap without horizontal overflow.
- Missing/legacy data fields: card rendering has safe fallbacks.
- Reduced-motion and theme preference: animations and theme remain usable.

---

### Task 1: Simplify job discovery and job cards

**Files:** Modify index.html; create tests/test_frontend_contract.py.

**Interfaces:** Consumes existing job objects and element IDs (searchInput, searchBtn, filters, jobList, counters). Produces compact metrics, quick filters, advanced-filter disclosure, and semantic job-card classes; existing render/save/track behavior remains.

- [ ] Write a failing frontend contract test that asserts required JS hook IDs and new responsive discovery/card selectors exist.
- [ ] Run the test and verify it fails on the missing new selectors.
- [ ] Update the jobs view to show four primary metrics and compact secondary data-quality values, while retaining all existing IDs.
- [ ] Move secondary dropdown controls into an accessible details disclosure; retain region/category quick filters.
- [ ] Rework card(job) markup to avoid duplicate location fragments, reduce badge noise, preserve full description details, and retain application/save/track controls.
- [ ] Add responsive styling for the discovery layout, compact stats, filters and job cards.
- [ ] Run the new contract test, existing Python suite, and frontend GitHub Actions validation.

### Task 2: Upgrade application shell and navigation

**Files:** Modify index.html and sw.js; extend tests/test_frontend_contract.py.

**Interfaces:** Consumes existing VIEW_ROUTES, data-view links, mobile dock, theme button and localStorage theme key. Produces a consistent desktop header/mobile navigation, accessible visual states, premium hero and shared surface styles.

- [ ] Extend contract coverage for all eight route containers and theme/navigation hooks.
- [ ] Replace the remote looping hero video with a CSS-only gradient hero and a clear call to action.
- [ ] Restyle the header, desktop links, mobile menu/dock, page headings, panels, forms, tables and career-tool cards.
- [ ] Preserve the current theme toggle and user preference; define matching light/dark tokens.
- [ ] Bump CACHE_NAME in sw.js so returning visitors receive the redesigned shell.
- [ ] Run frontend contract, Python, JavaScript syntax, navigation and service-worker checks.

### Task 3: Polish Company Directory and all secondary views

**Files:** Modify index.html; extend tests/test_frontend_contract.py.

**Interfaces:** Consumes existing company master data, company matching, profile rendering and tracker functions. Produces readable company cards/profile, consistent secondary views and responsive layouts.

- [ ] Extend contract coverage for company directory search/profile hooks and vacancy caveat text.
- [ ] Improve company directory search layout, result count, cards and empty states.
- [ ] Restyle company profile, saved jobs, tracker, verification center and career tools using shared tokens.
- [ ] Run the complete Python suite and GitHub frontend validation.
- [ ] Inspect the deployed site at mobile and desktop widths; verify job search, company directory, save/track and theme interactions.
- [ ] Confirm GitHub Pages deployment succeeded before reporting it live.