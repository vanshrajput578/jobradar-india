import json
import re
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "sources.json"
JOBS_FILE = ROOT / "jobs.json"


INDIA_KEYWORDS = [
    "india", "bharat",
    "andhra pradesh", "arunachal pradesh",
    "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana",
    "himachal pradesh", "jharkhand",
    "karnataka", "kerala", "madhya pradesh",
    "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha",
    "punjab", "rajasthan", "sikkim",
    "tamil nadu", "telangana", "tripura",
    "uttar pradesh", "uttarakhand",
    "west bengal", "new delhi", "delhi",
    "jammu", "kashmir", "ladakh",
    "chandigarh", "puducherry",
    "bengaluru", "bangalore", "mumbai",
    "pune", "hyderabad", "chennai",
    "kolkata", "noida", "gurugram",
    "gurgaon", "ghaziabad", "meerut",
    "lucknow", "kanpur", "agra",
    "varanasi", "prayagraj", "jaipur",
    "ahmedabad", "surat", "vadodara",
    "indore", "bhopal", "nagpur", "nashik",
    "kochi", "cochin", "thiruvananthapuram",
    "trivandrum", "coimbatore", "mysuru",
    "mysore", "mangalore", "mangaluru",
    "visakhapatnam", "vizag", "faridabad",
    "greater noida", "dehradun", "patna",
    "ranchi", "bhubaneswar", "ludhiana",
    "amritsar", "jodhpur", "udaipur",
    "raipur", "guwahati", "siliguri",
    "jamshedpur"
]


GLOBAL_COUNTRIES = [
    "united states", "usa", "u.s.a.", "us",
    "united kingdom", "uk", "u.k.",
    "canada", "australia", "new zealand",
    "singapore", "malaysia", "indonesia",
    "philippines", "thailand", "vietnam",
    "japan", "south korea", "korea",
    "china", "hong kong", "taiwan",
    "germany", "france", "italy", "spain",
    "portugal", "netherlands", "belgium",
    "switzerland", "sweden", "norway",
    "denmark", "finland", "ireland",
    "poland", "austria", "greece",
    "romania", "czech republic", "czechia",
    "hungary", "ukraine", "turkey",
    "united arab emirates", "uae",
    "saudi arabia", "qatar", "kuwait",
    "bahrain", "oman", "israel",
    "south africa", "nigeria", "kenya",
    "egypt", "morocco", "ghana",
    "brazil", "mexico", "argentina",
    "chile", "colombia", "peru",
    "costa rica", "panama",
    "bangladesh", "pakistan", "sri lanka",
    "nepal", "bhutan", "maldives",
    "russia", "iceland", "luxembourg",
    "estonia", "latvia", "lithuania",
    "slovakia", "slovenia", "croatia",
    "serbia", "bulgaria", "cyprus",
    "malta", "georgia", "armenia",
    "azerbaijan", "kazakhstan",
    "uzbekistan", "mongolia", "cambodia",
    "laos", "myanmar", "ethiopia",
    "tanzania", "uganda", "senegal",
    "tunisia", "algeria", "uruguay",
    "ecuador", "venezuela", "jamaica",
    "dominican republic"
]


REMOTE_KEYWORDS = [
    "remote",
    "work from anywhere",
    "anywhere",
    "distributed",
    "home based",
    "home-based",
    "work from home",
    "wfh"
]


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default):
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def contains_keyword(text, keywords):
    text = str(text).lower()

    for keyword in keywords:
        pattern = (
            r"(?<![a-z])"
            + re.escape(keyword)
            + r"(?![a-z])"
        )

        if re.search(pattern, text):
            return True

    return False


def detect_location(location):
    """
    Returns:
        region: India, Global, Remote, Unspecified
        work_mode: Remote, Not specified

    Unknown locations are never automatically
    classified as Global.
    """

    if not location:
        return "Unspecified", "Not specified"

    location = str(location).strip()

    if location.lower() in [
        "not specified",
        "unknown",
        "n/a",
        "none",
        "null"
    ]:
        return "Unspecified", "Not specified"

    is_remote = contains_keyword(
        location,
        REMOTE_KEYWORDS
    )

    # India takes priority over generic remote.
    if contains_keyword(location, INDIA_KEYWORDS):
        return "India", (
            "Remote" if is_remote else "Not specified"
        )

    # Explicit foreign country.
    if contains_keyword(location, GLOBAL_COUNTRIES):
        return "Global", (
            "Remote" if is_remote else "Not specified"
        )

    # Remote without a known country.
    if is_remote:
        return "Remote", "Remote"

    # No reliable location match.
    return "Unspecified", "Not specified"


def classify(title, departments):
    text = (
        title + " " + " ".join(departments)
    ).lower()

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

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        data = json.loads(
            response.read().decode("utf-8")
        )

    if not isinstance(data.get("jobs"), list):
        raise ValueError(
            "Invalid Greenhouse API response"
        )

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
        raise RuntimeError(
            "No job sources configured."
        )

    existing_jobs = database.get("jobs", [])

    if not isinstance(existing_jobs, list):
        existing_jobs = []

    old_jobs = {
        str(job["id"]): job
        for job in existing_jobs
        if isinstance(job, dict)
        and job.get("id") is not None
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
            print(
                "Invalid source configuration:",
                company
            )
            continue

        print("Checking:", company)

        try:
            postings = fetch_greenhouse(source)

            successful_sources += 1
            successful_source_ids.add(source_id)

            for posting in postings:

                external_id = str(
                    posting.get("id", "")
                )

                if not external_id:
                    continue

                job_id = source_id + "-" + external_id
                previous = old_jobs.get(job_id, {})

                title = posting.get(
                    "title",
                    "Untitled"
                )

                location_data = (
                    posting.get("location") or {}
                )

                location = (
                    location_data.get("name")
                    or "Not specified"
                )

                departments = [
                    item.get("name", "")
                    for item in posting.get(
                        "departments", []
                    )
                    if isinstance(item, dict)
                ]

                category = classify(
                    title,
                    departments
                )

                region, work_mode = detect_location(
                    location
                )

                new_jobs[job_id] = {
                    "id": job_id,
                    "source_id": source_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "region": region,
                    "category": category,
                    "industry": "Not specified",
                    "job_type": "Not specified",
                    "experience": "Not specified",
                    "work_mode": work_mode,
                    "demo": False,
                    "first_detected_at": (
                        previous.get(
                            "first_detected_at"
                        ) or now_utc()
                    ),
                    "posted_at": posting.get(
                        "updated_at"
                    ),
                    "application_url": posting.get(
                        "absolute_url",
                        ""
                    ),
                    "source_url": (
                        "https://boards.greenhouse.io/"
                        + board_token
                    ),
                    "description": posting.get(
                        "content",
                        ""
                    )
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

    # Preserve old jobs from failed sources.

    for job_id, job in old_jobs.items():

        source_id = job.get("source_id")

        if not source_id:
            source_id = job_id.split("-", 1)[0]

        if source_id not in successful_source_ids:

            preserved_job = dict(job)

            region, work_mode = detect_location(
                preserved_job.get(
                    "location",
                    "Not specified"
                )
            )

            preserved_job["region"] = region
            preserved_job["work_mode"] = work_mode

            new_jobs[job_id] = preserved_job

    jobs_list = list(new_jobs.values())

    india_count = sum(
        job.get("region") == "India"
        for job in jobs_list
    )

    global_count = sum(
        job.get("region") == "Global"
        for job in jobs_list
    )

    remote_count = sum(
        job.get("region") == "Remote"
        for job in jobs_list
    )

    unspecified_count = sum(
        job.get("region") == "Unspecified"
        for job in jobs_list
    )

    result = {
        "last_updated": now_utc(),
        "total_jobs": len(jobs_list),
        "india_jobs": india_count,
        "global_jobs": global_count,
        "remote_jobs": remote_count,
        "unspecified_jobs": unspecified_count,
        "jobs": sorted(
            jobs_list,
            key=lambda job: job.get(
                "first_detected_at",
                ""
            ),
            reverse=True
        )
    }

    with JOBS_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

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
    print("India jobs:", india_count)
    print("Global jobs:", global_count)
    print("Remote jobs:", remote_count)
    print("Unspecified jobs:", unspecified_count)
    print("--------------------------------")


if __name__ == "__main__":
    main()
