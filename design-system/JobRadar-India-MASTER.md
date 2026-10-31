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

- Added a homepage search form with a live location selector populated only from current job records.
- Added category shortcuts based on observed job-feed categories and counts.
- Simplified primary navigation; moved lower-frequency personal/workspace links into an accessible More menu.
- Added an internship discovery shortcut that filters job titles only; the current feed has no explicit internship-titled listings, so the empty state states that limitation.
- Added a Government Recruiters shortcut to the actual public-sector recruiter category in the company master list. The directory explains that it is not a live vacancy feed.
- Added job-type and experience selectors that populate from actual feed values and stay disabled while every source record says Not specified.
- Job cards prefer the source-provided posted_at timestamp; first_detected_at is labelled First seen when posted_at is unavailable.
- Added labels, focus states, responsive layout rules, and a restrained blue/ink design system across light/dark themes.
- Preserved existing job collection, Greenhouse source connections, canonical company matching, eligibility classification, saved jobs, tracker, verification, career tools, and PWA behavior.
- Kept the static HTML/CSS/JavaScript architecture and added no runtime dependencies.

## Verification results

- Frontend GitHub Actions contract and regression suite: 29 tests passed on commit 253e716a.
- Jobs database and compact public feed validation passed.
- Company/source mapping tests passed.
- Inline JavaScript syntax validation passed.
- All nine existing page views and hash routing validation passed.
- Latest Pages deployment and live-browser checks are being completed against the post-refresh commit.

## Known data limitations

- Current connected source feeds provide no populated job_type or experience fields; those controls remain unavailable until source data contains values.
- Current job feed has no explicit internship-titled roles, so the internship route currently shows a truthful empty state.
- Government employers and recruiting bodies exist in the company master directory, but no live government vacancy sources are connected. The navigation shortcut therefore opens recruiter profiles, not fabricated government job postings.


## Upstream skill note

The upstream project contains a CLI, searchable datasets and stack-specific guidance. This repository records the project-specific design decisions and applies selected guidance; it does **not** vendor the complete upstream CLI/data bundle or install a global assistant skill.
