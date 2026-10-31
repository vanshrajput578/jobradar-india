# JobRadar India — UI/UX Pro Max Design System

**Source:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill  
**License:** MIT (upstream project)  
**Project stack:** Static HTML, CSS and JavaScript; GitHub Pages  
**Product type:** Job discovery and application-tracking dashboard  
**Primary context:** Mobile-first use in India, including low-bandwidth devices

## Design direction

**Selected direction: Minimalism & Swiss Style adapted to a modern recruitment SaaS dashboard.** Prioritize scannability, trust, fast job discovery and compact information density. Use a disciplined grid, strong typographic hierarchy, calm surfaces, restrained shadows and one blue primary action color. Keep semantic status colors distinct and never communicate status by color alone. Avoid glassmorphism, excessive gradients, decorative 3D and visual clutter.

## Tokens

- Background: `#f5f7fb`
- Surface: `#ffffff`
- Secondary surface: `#f8faff`
- Text: `#172033`
- Muted text: `#68758b`
- Border: `#e5eaf2`
- Primary action: `#3659e3`
- Positive status: `#14845b`
- Warning status: `#9a6500`
- Error status: `#b93838`
- Card radius: `18px`
- Body typography: system sans-serif, 15px base, 1.55 line-height
- Motion: subtle; honor `prefers-reduced-motion`

## UX rules

1. Job title, employer, location, work mode and verification state must be easy to scan.
2. Never imply a job is verified unless its source check supports that status.
3. Filters and actions must work with touch, keyboard and pointer.
4. Maintain visible focus indicators and a skip link to the main job results.
5. Keep tap targets around 44px minimum where practical.
6. Do not rely on color alone for job status; retain textual labels.
7. Forms need persistent labels or accessible names; placeholders alone are not labels.
8. Support narrow screens without horizontal page scrolling or clipped chips.
9. Preserve browser zoom and reduced-motion preferences.
10. Avoid decorative animation, emoji used as structural icons, and unnecessary third-party assets.

## Implementation scope

The current page remains plain HTML/CSS/JS. No framework, package, backend, paid service or tracking script is added. Existing job collection, search/filter logic, local saved jobs, application tracker, company directory, verification semantics and PWA files must remain intact.

## Applied in this pass

- Added a keyboard-accessible skip link to job listings and an accessible name to the main search input.
- Added visible `:focus-visible` styling and larger touch targets.
- Rethemed the header, hero, search bar, stats, filters, job cards, company cards, workspace tools, tables and mobile dock with a consistent dashboard visual system.
- Tightened typography, spacing, border radii, shadows and interaction feedback.
- Improved narrow-screen layouts while preserving the existing HTML IDs and JavaScript interactions.
- Preserved the dark theme and reduced-motion support.

## Verification still required

- Run the repository's GitHub Actions tests after the UI commit.
- Inspect the deployed GitHub Pages site on 360px, 390px, 768px, 1024px and desktop widths.
- Verify contrast ratios and all interactive states in both light and dark themes.
- Regression-test search, filters, save/unsave, application tracker, company directory and career tools.

## Upstream skill note

The upstream project contains a CLI, searchable datasets and stack-specific guidance. This repository records the project-specific design decisions and applies selected guidance; it does **not** vendor the complete upstream CLI/data bundle or install a global assistant skill.
