import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "sources.json"
JOBS_FILE = ROOT / "jobs.json"


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default):
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def classify(title, departments):
    text = (title + " " + " ".join(departments)).lower()

    if "intern" in text:
        return "Internships"

    if any(word in text for word in [
        "finance", "accountant", "accounting",
        "treasury", "investment"
    ]):
        return "Finance"

    if any(word in text for word in [
        "engineer", "developer", "software",
        "backend", "frontend", "devops",
        "data science", "machine learning",
        "programmer", "technical"
    ]):
        return "Engineering"

    return "Technology"


def fetch_greenhouse(source):
    token = urllib.parse.quote(
        source["board_token"],
        safe=""
    )

    url = (
        "https://boards-api.greenhouse.io/v1/boards/"
        + token + "/jobs?content=true"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "JobRadarIndia/1.0",
            "Accept": "application/json"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(
            response.read().decode("utf-8")
        )

    if not isinstance(data.get("jobs"), list):
        raise ValueError("Invalid Greenhouse API response")

    return data["jobs"]


def main():
    sources_data = read_json(
        SOURCES_FILE,
        {"sources": []}
    )

    database = read_json(
        JOBS_FILE,
        {
            "last_updated": None,
            "total_jobs": 0,
            "jobs": []
        }
    )

    sources = sources_data.get("sources", [])

    if not isinstance(sources, list) or not sources:
        raise RuntimeError("No job sources configured.")

    existing_jobs = database.get("jobs", [])

    if not isinstance(existing_jobs, list):
        existing_jobs = []

    old_jobs = {
        str(job["id"]): job
        for job in existing_jobs
        if isinstance(job, dict) and job.get("id") is not None
    }

    successful_sources = 0
    successful_source_ids = set()
    new_jobs = {}

    for source in sources:

        if not source.get("enabled", False):
            continue

        if source.get("provider") != "greenhouse":
            print(
                "Unsupported provider:",
                source.get("company", "Unknown")
            )
            continue

        company = source.get("company", "Unknown")
        source_id = source.get("id", "")
        board_token = source.get("board_token", "")

        if not source_id or not board_token:
            print("Invalid source configuration:", company)
            continue

        print("Checking:", company)

        try:
            postings = fetch_greenhouse(source)

            successful_sources += 1
            successful_source_ids.add(source_id)

            for posting in postings:

                external_id = str(posting.get("id", ""))

                if not external_id:
                    continue

                job_id = source_id + "-" + external_id

                previous = old_jobs.get(job_id, {})

                title = posting.get("title", "Untitled")

                location_data = posting.get("location") or {}

                location = (
                    location_data.get("name")
                    or "Not specified"
                )

                departments = [
                    item.get("name", "")
                    for item in posting.get("departments", [])
                    if isinstance(item, dict)
                ]

                category = classify(title, departments)

                new_jobs[job_id] = {
                    "id": job_id,
                    "source_id": source_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "category": category,
                    "industry": "Not specified",
                    "job_type": "Not specified",
                    "experience": "Not specified",
                    "work_mode": "Not specified",
                    "demo": False,
                    "first_detected_at": (
                        previous.get("first_detected_at")
                        or now_utc()
                    ),
                    "posted_at": posting.get("updated_at"),
                    "application_url": posting.get(
                        "absolute_url", ""
                    ),
                    "source_url": (
                        "https://boards.greenhouse.io/"
                        + board_token
                    ),
                    "description": posting.get("content", "")
                }

            print(
                "Found",
                len(postings),
                "listings for",
                company
            )

        except Exception as error:
            print(
                "Source failed:",
                company,
                str(error)
            )

    if successful_sources == 0:
        raise RuntimeError(
            "All job sources failed. "
            "Existing jobs.json was not changed."
        )

    # Preserve previously collected jobs from failed sources.
    for job_id, job in old_jobs.items():

        source_id = job.get("source_id")

        if not source_id:
            source_id = job_id.split("-", 1)[0]

        if source_id not in successful_source_ids:
            new_jobs[job_id] = job

    result = {
        "last_updated": now_utc(),
        "total_jobs": len(new_jobs),
        "jobs": sorted(
            new_jobs.values(),
            key=lambda job: job.get(
                "first_detected_at", ""
            ),
            reverse=True
        )
    }

    with JOBS_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("--------------------------------")
    print("JobRadar update complete.")
    print("Successful sources:", successful_sources)
    print("Total jobs saved:", result["total_jobs"])
    print("--------------------------------")


if __name__ == "__main__":
    main()
