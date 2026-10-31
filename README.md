# JobRadar India

Free static job discovery and application workspace.

## Architecture
- GitHub Pages hosts the HTML/CSS/JavaScript frontend.
- GitHub Actions runs `fetch_jobs.py` every six hours and on manual dispatch.
- `sources.json` lists public Greenhouse company boards.
- `jobs.json` stores normalized listings.
- `duplicate_audit.json` records possible duplicates for manual review.
- `expiry_audit.json` records source checks and availability status transitions.
- `tests/test_verification.py` tests expiry and reactivation rules.

## Verification policy
A job is marked **active** when its ID appears in the latest successful fetch of its source. A previously known job is marked **closed / not listed** only when its source fetch succeeds and the ID is absent. A failed source never closes jobs; prior availability and last successful verification time are retained. Closed records are retained and never automatically deleted. This is a source-board observation, not a guarantee about the employer's intent.

## Local browser features
Saved jobs, saved searches, applications, resume drafts and personal backup are stored locally in the browser. Export a backup before clearing browser data. These records do not sync between devices.

## Hosting limitations
GitHub Pages is static hosting. Saved searches are checked when the site is opened, not continuously in the background. Cloud login/sync, guaranteed push/email alerts, server-side AI and real-time vacancy guarantees require a backend or external service. The resume and match tools are local utilities; match scores are keyword overlap estimates, not ATS predictions.

## Development
Run tests: `python -m unittest discover -s tests -v`
Run collector: `python fetch_jobs.py`
