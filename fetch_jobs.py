import json
import re
import html
import difflib
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "sources.json"
JOBS_FILE = ROOT / "jobs.json"
DUPLICATE_AUDIT_FILE = ROOT / "duplicate_audit.json"

DUPLICATE_SIMILARITY_THRESHOLD = 0.92

INDIA_KEYWORDS = [
    "india", "bharat", "andhra pradesh", "arunachal pradesh",
    "assam", "bihar", "chhattisgarh", "goa", "gujarat", "haryana",
    "himachal pradesh", "jharkhand", "karnataka", "kerala",
    "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "punjab", "rajasthan",
    "sikkim", "tamil nadu", "telangana", "tripura", "uttar pradesh",
    "uttarakhand", "west bengal", "new delhi", "delhi", "jammu",
    "kashmir", "ladakh", "chandigarh", "puducherry", "bengaluru",
    "bangalore", "mumbai", "pune", "hyderabad", "chennai", "kolkata",
    "noida", "gurugram", "gurgaon", "ghaziabad", "meerut", "lucknow",
    "kanpur", "agra", "varanasi", "prayagraj", "jaipur", "ahmedabad",
    "surat", "vadodara", "indore", "bhopal", "nagpur", "nashik",
    "kochi", "cochin", "thiruvananthapuram", "trivandrum",
    "coimbatore", "mysuru", "mysore", "mangalore", "mangaluru",
    "visakhapatnam", "vizag", "faridabad", "greater noida",
    "dehradun", "patna", "ranchi", "bhubaneswar", "ludhiana",
    "amritsar", "jodhpur", "udaipur", "raipur", "guwahati",
    "siliguri", "jamshedpur"
]

GLOBAL_COUNTRIES = [
    "united states", "usa", "u.s.a.", "us", "united kingdom", "uk",
    "u.k.", "canada", "australia", "new zealand", "singapore",
    "malaysia", "indonesia", "philippines", "thailand", "vietnam",
    "japan", "south korea", "korea", "china", "hong kong", "taiwan",
    "germany", "france", "italy", "spain", "portugal", "netherlands",
    "belgium", "switzerland", "sweden", "norway", "denmark", "finland",
    "ireland", "poland", "austria", "greece", "romania",
    "czech republic", "czechia", "hungary", "ukraine", "turkey",
    "united arab emirates", "uae", "saudi arabia", "qatar", "kuwait",
    "bahrain", "oman", "israel", "south africa", "nigeria", "kenya",
    "egypt", "morocco", "ghana", "brazil", "mexico", "argentina",
    "chile", "colombia", "peru", "costa rica", "panama", "bangladesh",
    "pakistan", "sri lanka", "nepal", "bhutan", "maldives", "russia",
    "iceland", "luxembourg", "estonia", "latvia", "lithuania",
    "slovakia", "slovenia", "croatia", "serbia", "bulgaria", "cyprus",
    "malta", "georgia", "armenia", "azerbaijan", "kazakhstan",
    "uzbekistan", "mongolia", "cambodia", "laos", "myanmar",
    "ethiopia", "tanzania", "uganda", "senegal", "tunisia", "algeria",
    "uruguay", "ecuador", "venezuela", "jamaica", "dominican republic"
]

REMOTE_KEYWORDS = [
    "remote", "work from anywhere", "anywhere", "distributed",
    "home based", "home-based", "work from home", "wfh"
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
        pattern = r"(?<![a-z])" + re.escape(keyword) + r"(?![a-z])"
        if re.search(pattern, text):
            return True
    return False


def detect_location(location):
    if not location:
        return "Unspecified", "Not specified"

    location = str(location).strip()
    if location.lower() in ["not specified", "unknown", "n/a", "none", "null"]:
        return "Unspecified", "Not specified"

    is_remote = contains_keyword(location, REMOTE_KEYWORDS)

    if contains_keyword(location, INDIA_KEYWORDS):
        return "India", "Remote" if is_remote else "Not specified"

    if contains_keyword(location, GLOBAL_COUNTRIES):
        return "Global", "Remote" if is_remote else "Not specified"

    if is_remote:
        return "Remote", "Remote"

    return "Unspecified", "Not specified"


def classify(title, departments):
    text = (title + " " + " ".join(departments)).lower()

    if "intern" in text:
        return "Internships"

    if any(word in text for word in [
        "finance", "accountant", "accounting", "treasury", "investment"
    ]):
        return "Finance"

    if any(word in text for word in [
        "engineer", "developer", "software", "backend", "frontend",
        "devops", "data science", "machine learning", "programmer",
        "technical"
    ]):
        return "Engineering"

    return "Technology"


def normalize_duplicate_text(value):
    """Normalize text for comparison; does not alter stored job data."""
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"https?://\S+", " ", value, flags=re.IGNORECASE)
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def canonicalize_application_url(value):
    """Remove tracking parameters and fragments for URL comparison."""
    value = str(value or "").strip()
    if not value:
        return ""

    try:
        parts = urllib.parse.urlsplit(value)
        host = (parts.hostname or "").lower()
        if not host:
            return value.rstrip("/")

        port = parts.port
        netloc = host if port is None else f"{host}:{port}"
        path = re.sub(r"/+", "/", parts.path or "/").rstrip("/") or "/"

        tracking_prefixes = ("utm_",)
        tracking_names = {
            "gh_src", "source", "ref", "referrer", "fbclid",
            "gclid", "mc_cid", "mc_eid"
        }

        kept_query = []
        for key, val in urllib.parse.parse_qsl(
            parts.query, keep_blank_values=True
        ):
            lowered = key.lower()
            if lowered.startswith(tracking_prefixes):
                continue
            if lowered in tracking_names:
                continue
            kept_query.append((key, val))

        query = urllib.parse.urlencode(sorted(kept_query))
        return urllib.parse.urlunsplit(
            (parts.scheme.lower() or "https", netloc, path, query, "")
        )
    except Exception:
        return value.rstrip("/")


def build_duplicate_audit(jobs):
    """
    Produce review-only candidate pairs. This function never removes,
    merges, edits, or suppresses a job.
    """
    candidates = []
    seen_pairs = set()

    def add_candidate(a, b, reason, similarity=None):
        ids = sorted([str(a.get("id", "")), str(b.get("id", ""))])
        if not ids[0] or ids[0] == ids[1] or tuple(ids) in seen_pairs:
            return
        seen_pairs.add(tuple(ids))
        item = {
            "job_a_id": ids[0],
            "job_b_id": ids[1],
            "company_a": a.get("company", ""),
            "company_b": b.get("company", ""),
            "title_a": a.get("title", ""),
            "title_b": b.get("title", ""),
            "location_a": a.get("location", ""),
            "location_b": b.get("location", ""),
            "application_url_a": a.get("application_url", ""),
            "application_url_b": b.get("application_url", ""),
            "reason": reason,
            "review_required": True,
            "automatic_action": "none"
        }
        if similarity is not None:
            item["description_similarity"] = round(similarity, 4)
        candidates.append(item)

    url_groups = {}
    for job in jobs:
        url = canonicalize_application_url(job.get("application_url"))
        if url:
            url_groups.setdefault(url, []).append(job)

    for grouped_jobs in url_groups.values():
        if len(grouped_jobs) > 1:
            first = grouped_jobs[0]
            for other in grouped_jobs[1:]:
                add_candidate(first, other, "same_canonical_application_url")

    # Compare only jobs sharing normalized company, title, and location.
    identity_groups = {}
    for job in jobs:
        company = normalize_duplicate_text(job.get("company"))
        title = normalize_duplicate_text(job.get("title"))
        location = normalize_duplicate_text(job.get("location"))
        if not company or not title:
            continue
        key = (company, title, location)
        identity_groups.setdefault(key, []).append(job)

    for grouped_jobs in identity_groups.values():
        if len(grouped_jobs) < 2:
            continue

        for index, first in enumerate(grouped_jobs):
            text_a = normalize_duplicate_text(first.get("description"))
            for second in grouped_jobs[index + 1:]:
                text_b = normalize_duplicate_text(second.get("description"))

                if not text_a or not text_b:
                    continue

                similarity = difflib.SequenceMatcher(
                    None, text_a, text_b, autojunk=False
                ).ratio()

                if similarity >= DUPLICATE_SIMILARITY_THRESHOLD:
                    add_candidate(
                        first,
                        second,
                        "same_company_title_location_and_similar_description",
                        similarity
                    )

    candidates.sort(
        key=lambda item: (
            item.get("reason", ""),
            -item.get("description_similarity", 1.0),
            item.get("job_a_id", ""),
            item.get("job_b_id", "")
        )
    )

    return {
        "generated_at": now_utc(),
        "total_jobs_checked": len(jobs),
        "candidate_pairs": len(candidates),
        "description_similarity_threshold": DUPLICATE_SIMILARITY_THRESHOLD,
        "review_required": True,
        "automatic_deletion_enabled": False,
        "automatic_merge_enabled": False,
        "candidates": candidates
    }


def fetch_greenhouse(source):
    token = urllib.parse.quote(source["board_token"], safe="")
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
        data = json.loads(response.read().decode("utf-8"))

    if not isinstance(data.get("jobs"), list):
        raise ValueError("Invalid Greenhouse API response")

    return data["jobs"]


def main():
    sources_data = read_json(SOURCES_FILE, {"sources": []})
    database = read_json(
        JOBS_FILE,
        {"last_updated": None, "total_jobs": 0, "jobs": []}
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
            print("Unsupported provider:", source.get("company", "Unknown"))
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
                location = location_data.get("name") or "Not specified"

                departments = [
                    item.get("name", "")
                    for item in posting.get("departments", [])
                    if isinstance(item, dict)
                ]

                category = classify(title, departments)
                region, work_mode = detect_location(location)

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
                        previous.get("first_detected_at") or now_utc()
                    ),
                    "posted_at": posting.get("updated_at"),
                    "application_url": posting.get("absolute_url", ""),
                    "source_url": (
                        "https://boards.greenhouse.io/" + board_token
                    ),
                    "description": posting.get("content", "")
                }

            print("Found", len(postings), "listings for", company)

        except Exception as error:
            print("Source failed:", company, str(error))

    if successful_sources == 0:
        raise RuntimeError(
            "All job sources failed. Existing jobs.json was not changed."
        )

    # Preserve old jobs from sources that failed during this run.
    for job_id, job in old_jobs.items():
        source_id = job.get("source_id")
        if not source_id:
            source_id = job_id.split("-", 1)[0]

        if source_id not in successful_source_ids:
            preserved_job = dict(job)
            region, work_mode = detect_location(
                preserved_job.get("location", "Not specified")
            )
            preserved_job["region"] = region
            preserved_job["work_mode"] = work_mode
            new_jobs[job_id] = preserved_job

    jobs_list = list(new_jobs.values())

    # Create a separate review report. No job is deleted or merged.
    duplicate_audit = build_duplicate_audit(jobs_list)
    with DUPLICATE_AUDIT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            duplicate_audit,
            file,
            indent=2,
            ensure_ascii=False
        )

    india_count = sum(job.get("region") == "India" for job in jobs_list)
    global_count = sum(job.get("region") == "Global" for job in jobs_list)
    remote_count = sum(job.get("region") == "Remote" for job in jobs_list)
    unspecified_count = sum(
        job.get("region") == "Unspecified" for job in jobs_list
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
            key=lambda job: job.get("first_detected_at", ""),
            reverse=True
        )
    }

    with JOBS_FILE.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)

    print("--------------------------------")
    print("JobRadar update complete.")
    print("Successful sources:", successful_sources)
    print("Total jobs saved:", result["total_jobs"])
    print("India jobs:", india_count)
    print("Global jobs:", global_count)
    print("Remote jobs:", remote_count)
    print("Unspecified jobs:", unspecified_count)
    print("Duplicate candidate pairs:", duplicate_audit["candidate_pairs"])
    print("Report saved to:", DUPLICATE_AUDIT_FILE.name)
    print("--------------------------------")


if __name__ == "__main__":
    main()
