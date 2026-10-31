#!/usr/bin/env python3
"""Build a lightweight public job feed for the GitHub Pages frontend."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "jobs.json"
COMPANY_MASTER = ROOT / "company_master.json"
TARGET = ROOT / "jobs_public.json"
DESCRIPTION_LIMIT = 2200

PUBLIC_FIELDS = (
    "id", "source_id", "company_id", "title", "company", "location", "region",
    "category", "industry", "job_type", "experience", "work_mode",
    "city", "state", "country", "location_confidence",
    "india_eligibility", "india_eligibility_reason", "india_eligibility_confidence", "demo",
    "first_detected_at", "posted_at", "application_url", "source_url",
    "availability_status", "verification_status", "last_verified_at",
    "description",
)


def clean_description(value):
    text = html.unescape(str(value or ""))
    text = re.sub(r"<(script|style)\b[^>]*>[\s\S]*?</\1>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:DESCRIPTION_LIMIT]


def main():
    if not SOURCE.is_file():
        raise SystemExit("jobs.json is missing")
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        raise SystemExit("jobs.json does not contain a jobs list")
    if not COMPANY_MASTER.is_file():
        raise SystemExit("company_master.json is missing")
    master = json.loads(COMPANY_MASTER.read_text(encoding="utf-8"))
    source_to_company = {}
    for company in master.get("companies", []):
        company_id = str(company.get("company_id") or "").strip()
        for source_id in company.get("source_ids", []):
            source_id = str(source_id or "").strip()
            if source_id:
                previous = source_to_company.get(source_id)
                if previous and previous != company_id:
                    raise SystemExit(f"Source {source_id} maps to multiple company IDs")
                source_to_company[source_id] = company_id

    compact_jobs = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        item = {key: job[key] for key in PUBLIC_FIELDS if key in job and key != "description"}
        source_id = str(job.get("source_id") or "").strip()
        canonical_company_id = source_to_company.get(source_id)
        existing_company_id = str(job.get("company_id") or "").strip()
        if existing_company_id and canonical_company_id and existing_company_id != canonical_company_id:
            raise SystemExit(f"Job {job.get('id')} has a company_id that conflicts with source {source_id}")
        if canonical_company_id:
            item["company_id"] = canonical_company_id
        elif existing_company_id:
            item["company_id"] = existing_company_id
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
