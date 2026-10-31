#!/usr/bin/env python3
"""Build a lightweight public job feed for the GitHub Pages frontend."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "jobs.json"
TARGET = ROOT / "jobs_public.json"
DESCRIPTION_LIMIT = 2200

PUBLIC_FIELDS = (
    "id", "source_id", "title", "company", "location", "region",
    "category", "industry", "job_type", "experience", "work_mode",
    "city", "state", "country", "location_confidence", "demo",
    "first_detected_at", "posted_at", "application_url", "source_url",
    "availability_status", "verification_status", "last_verified_at",
    "description",
)


def clean_description(value):
    text = html.unescape(str(value or ""))
    text = re.sub(r"<(script|style)\\b[^>]*>[\\s\\S]*?</\\1>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text[:DESCRIPTION_LIMIT]


def main():
    if not SOURCE.is_file():
        raise SystemExit("jobs.json is missing")
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        raise SystemExit("jobs.json does not contain a jobs list")

    compact_jobs = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        item = {key: job[key] for key in PUBLIC_FIELDS if key in job and key != "description"}
        item["description"] = clean_description(job.get("description"))
        compact_jobs.append(item)

    output = {key: value for key, value in data.items() if key != "jobs"}
    output["total_jobs"] = len(compact_jobs)
    output["jobs"] = compact_jobs
    TARGET.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    size = TARGET.stat().st_size
    print(f"Built jobs_public.json: {len(compact_jobs)} jobs, {size:,} bytes")
    if len(compact_jobs) != len(jobs):
        raise SystemExit("Public feed job count does not match source database")


if __name__ == "__main__":
    main()
