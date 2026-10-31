# JobRadar India UI Redesign — Design Spec

**Date:** 2026-10-31

## Intent
Make JobRadar India feel like a focused, trustworthy job-search product rather than a crowded generic dashboard. The primary audience is job seekers using phones; desktop must remain first-class.

## Goals
- Make the job search action visually dominant and immediately understandable.
- Show the four most useful top-level metrics without turning each metric into a large dashboard tile.
- Reduce mobile filter clutter by keeping region/category quick filters visible and moving secondary filters into a compact advanced-filter disclosure.
- Make job cards scannable: role, employer, location, work mode/category, availability and India eligibility should be clear without repeated location fragments or excessive badges.
- Improve spacing, typography, contrast, touch targets, and responsive behavior across all current views.
- Give Company Directory a clear search-first layout and distinguish a company profile from actual JobRadar vacancy records.
- Keep the existing theme toggle and user theme preference.
- Preserve all existing functionality and the current static-site deployment model.

## Non-goals
- No backend, schema, source integration, job verification, company mapping, or eligibility-classifier redesign.
- No migration to React/Vue or addition of runtime dependencies.
- No new account system, paid APIs, or hosted services.
- No changes to the truth conditions behind job eligibility or active status.

## Constraints
- Keep the existing single-page index.html, hash routes, element IDs consumed by JavaScript, localStorage saved jobs/application tracker, JSON feed contract, and GitHub Pages deployment.
- Keep sw.js shell cache behavior and bump its cache version when the shell changes.
- Use semantic HTML, accessible labels/focus states, reduced-motion support, and mobile-first CSS.
- Never imply an employer is hiring from a company-directory entry alone.

## Approaches
1. **Recommended — focused workspace refresh:** retain the current single-file architecture and functions; rebuild presentation, compact filters, and card information hierarchy. Lowest risk and keeps every current feature.
2. Split the frontend into a component framework: cleaner long-term code structure, but adds build tooling and a deployment migration that this project does not need for a visual redesign.
3. Cosmetic color-only pass: lowest effort, but leaves the underlying clutter, repeated data, and weak hierarchy unchanged.

## Selected direction
Approach 1. Use a premium dark-first visual language with an upgraded light theme; deep ink/navy surfaces, restrained indigo/blue accents, mint for confirmed India eligibility, amber for unclear states, and neutral treatment for restrictions. Keep the current theme preference mechanism. Remove the remote looping hero video in favor of a lightweight CSS gradient. Use compact metric cards, horizontally scrollable quick-filter chips, a collapsed advanced-filter section, readable job cards, and clear desktop/mobile navigation.

## Implementation decisions left to the builder
- Keep all routes and features but visually group them into a consistent responsive workspace.
- Preserve current behavior for job search, region/category filtering, company links, save/track, resume/career tools, and tracker data.
- Test JavaScript syntax, all route IDs, critical DOM hooks, and the existing Python suite before claiming completion.