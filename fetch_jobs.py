import difflib
import html
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "sources.json"
JOBS_FILE = ROOT / "jobs.json"
DUPLICATE_AUDIT_FILE = ROOT / "duplicate_audit.json"
DUPLICATE_SIMILARITY_THRESHOLD = 0.92
REQUEST_TIMEOUT_SECONDS = 30
USER_AGENT = "JobRadarIndia/2.0 (+https://vanshrajput578.github.io/jobradar-india/)"


INDIA_KEYWORDS = [
    "india", "bharat", "andhra pradesh", "arunachal pradesh",
    "assam", "bihar", "chhattisgarh", "goa", "gujarat", "haryana",
    "himachal pradesh", "jharkhand", "karnataka", "kerala",
    "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "orissa", "punjab", "rajasthan",
    "sikkim", "tamil nadu", "telangana", "tripura", "uttar pradesh",
    "uttarakhand", "west bengal", "new delhi", "delhi", "jammu",
    "kashmir", "ladakh", "chandigarh", "puducherry", "pondicherry",
    "bengaluru", "bangalore", "mumbai", "bombay", "pune", "hyderabad",
    "chennai", "madras", "kolkata", "calcutta", "noida", "gurugram",
    "gurgaon", "ghaziabad", "meerut", "lucknow", "kanpur", "agra",
    "varanasi", "prayagraj", "allahabad", "jaipur", "ahmedabad", "surat",
    "vadodara", "baroda", "indore", "bhopal", "nagpur", "nashik",
    "kochi", "cochin", "thiruvananthapuram", "trivandrum", "coimbatore",
    "mysuru", "mysore", "mangalore", "mangaluru", "visakhapatnam", "vizag",
    "faridabad", "greater noida", "dehradun", "patna", "ranchi",
    "bhubaneswar", "ludhiana", "amritsar", "jodhpur", "udaipur", "raipur",
    "guwahati", "siliguri", "jamshedpur"
]

# Short aliases are matched as complete tokens only, never as substrings.
GLOBAL_COUNTRIES = [
    "united states", "united states of america", "usa", "u.s.a.", "us",
    "u.s.", "united kingdom", "uk", "u.k.", "canada", "australia",
    "new zealand", "singapore", "malaysia", "indonesia", "philippines",
    "thailand", "vietnam", "japan", "south korea", "republic of korea",
    "china", "hong kong", "taiwan", "germany", "france", "italy", "spain",
    "portugal", "netherlands", "the netherlands", "belgium", "switzerland",
    "sweden", "norway", "denmark", "finland", "ireland", "poland", "austria",
    "greece", "romania", "czech republic", "czechia", "hungary", "ukraine",
    "turkey", "türkiye", "united arab emirates", "uae", "saudi arabia",
    "qatar", "kuwait", "bahrain", "oman", "israel", "south africa", "nigeria",
    "kenya", "egypt", "morocco", "ghana", "brazil", "mexico", "argentina",
    "chile", "colombia", "peru", "costa rica", "panama", "bangladesh",
    "pakistan", "sri lanka", "nepal", "bhutan", "maldives", "russia",
    "iceland", "luxembourg", "estonia", "latvia", "lithuania", "slovakia",
    "slovenia", "croatia", "serbia", "bulgaria", "cyprus", "malta", "georgia",
    "armenia", "azerbaijan", "kazakhstan", "uzbekistan", "mongolia", "cambodia",
    "laos", "myanmar", "ethiopia", "tanzania", "uganda", "senegal", "tunisia",
    "algeria", "uruguay", "ecuador", "venezuela", "jamaica", "dominican republic"
]

REMOTE_KEYWORDS = [
    "remote", "work from anywhere", "anywhere", "distributed", "home based",
    "home-based", "work from home", "wfh"
]
HYBRID_KEYWORDS = ["hybrid", "partly remote", "partially remote"]
ONSITE_KEYWORDS = ["on-site", "onsite", "on site", "in-office", "in office"]


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def atomic_write_json(path, data):
    """Write JSON to a temporary file, then replace the destination atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(path.parent),
            prefix=path.name + ".", suffix=".tmp", delete=False
        ) as file:
            temp_path = Path(file.name)
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
    except Exception:
        if temp_path and temp_path.exists():
            temp_path.unlink()
        raise


def normalize_location_text(value):
    value = html.unescape(str(value or "")).lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[\u2010-\u2015]", "-", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def contains_keyword(text, keywords):
    """Match aliases on token boundaries so e.g. 'us' cannot match inside a word."""
    text = normalize_location_text(text)
    for keyword in keywords:
        keyword = normalize_location_text(keyword)
        pattern = r"(?<![a-z])" + re.escape(keyword) + r"(?![a-z])"
        if re.search(pattern, text):
            return True
    return False


def detect_work_mode(location):
    """Detect work arrangement, preferring explicit Hybrid over Remote."""
    text = normalize_location_text(location)
    has_hybrid = contains_keyword(text, HYBRID_KEYWORDS)
    has_remote = contains_keyword(text, REMOTE_KEYWORDS)
    has_onsite = contains_keyword(text, ONSITE_KEYWORDS)

    if has_hybrid or (has_remote and has_onsite):
        return "Hybrid"
    if has_remote:
        return "Remote"
    if has_onsite:
        return "On-site"
    return "Not specified"


def detect_location(location):
    """Return (region, work_mode). Region is independent of work mode."""
    text = normalize_location_text(location)
    if not text or text in {"not specified", "unknown", "n/a", "none", "null"}:
        return "Unspecified", "Not specified"

    work_mode = detect_work_mode(text)
    has_india = contains_keyword(text, INDIA_KEYWORDS)
    has_global = contains_keyword(text, GLOBAL_COUNTRIES)

    # Prefer India when India is explicitly among the listed eligible locations.
    # A multi-country role including India remains discoverable in the India filter.
    if has_india:
        return "India", work_mode
    if has_global:
        return "Global", work_mode
    if work_mode == "Remote":
        return "Remote", "Remote"
    return "Unspecified", work_mode


def classify(title, departments):
    """Keep the existing frontend category vocabulary stable."""
    title = str(title or "")
    if isinstance(departments, str):
        departments = [departments]
    text = (title + " " + " ".join(str(item) for item in departments)).lower()

    # Word boundaries prevent titles such as "Internal Auditor" becoming internships.
    if re.search(r"\b(intern|internship)\b", text):
        return "Internships"
    if any(word in text for word in [
        "finance", "accountant", "accounting", "treasury", "investment", "payroll"
    ]):
        return "Finance"
    if any(word in text for word in [
        "engineer", "developer", "software", "backend", "frontend", "devops",
        "data science", "machine learning", "programmer", "technical"
    ]):
        return "Engineering"
    return "Technology"


def normalize_duplicate_text(value):
    """Normalize text for comparison without changing the stored job description."""
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"https?://\S+", " ", value, flags=re.IGNORECASE)
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def canonicalize_application_url(value):
    """Normalize URLs while retaining parameters that may identify a job posting."""
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
        tracking_names = {
            "gh_src", "source", "ref", "referrer", "fbclid", "gclid",
            "mc_cid", "mc_eid"
        }
        kept_query = []
        for key, val in urllib.parse.parse_qsl(parts.query, keep_blank_values=True):
            lowered = key.lower()
            if lowered.startswith("utm_") or lowered in tracking_names:
                continue
            kept_query.append((key, val))
        query = urllib.parse.urlencode(sorted(kept_query))
        scheme = parts.scheme.lower() or "https"
        return urllib.parse.urlunsplit((scheme, netloc, path, query, ""))
    except (TypeError, ValueError):
        return value.rstrip("/")


def build_duplicate_audit(jobs):
    """Create review-only duplicate candidates. Never delete or merge jobs."""
    candidates = []
    seen_pairs = set()

    def add_candidate(a, b, reason, similarity=None):
        id_a = str(a.get("id", ""))
        id_b = str(b.get("id", ""))
        if not id_a or not id_b or id_a == id_b:
            return
        pair_key = tuple(sorted((id_a, id_b)))
        if pair_key in seen_pairs:
            return
        seen_pairs.add(pair_key)

        item = {
            "job_a_id": id_a,
            "job_b_id": id_b,
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

    url_groups = defaultdict(list)
    for job in jobs:
        url = canonicalize_application_url(job.get("application_url"))
        if url:
            url_groups[url].append(job)
    for grouped_jobs in url_groups.values():
        if len(grouped_jobs) > 1:
            first = grouped_jobs[0]
            for other in grouped_jobs[1:]:
                add_candidate(first, other, "same_canonical_application_url")

    identity_groups = defaultdict(list)
    for job in jobs:
        company = normalize_duplicate_text(job.get("company"))
        title = normalize_duplicate_text(job.get("title"))
        location = normalize_duplicate_text(job.get("location"))
        if company and title:
            identity_groups[(company, title, location)].append(job)

    for grouped_jobs in identity_groups.values():
        if len(grouped_jobs) < 2:
            continue
        for index, first in enumerate(grouped_jobs):
            text_a = normalize_duplicate_text(first.get("description"))
            if not text_a:
                continue
            for second in grouped_jobs[index + 1:]:
                text_b = normalize_duplicate_text(second.get("description"))
                if not text_b:
                    continue
                similarity = difflib.SequenceMatcher(
                    None, text_a, text_b, autojunk=False
                ).ratio()
                if similarity >= DUPLICATE_SIMILARITY_THRESHOLD:
                    add_candidate(
                        first, second,
                        "same_company_title_location_and_similar_description",
                        similarity
                    )

    candidates.sort(key=lambda item: (
        item.get("reason", ""),
        -item.get("description_similarity", 1.0),
        item.get("job_a_id", ""),
        item.get("job_b_id", "")
    ))

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
    token = str(source.get("board_token", "")).strip()
    if not token:
        raise ValueError("Missing Greenhouse board_token")
    token = urllib.parse.quote(token, safe="")
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise ValueError("Invalid Greenhouse API response: 'jobs' list missing")
    return payload["jobs"]


def normalize_source(source):
    if not isinstance(source, dict):
        return None
    source_id = str(source.get("id", "")).strip()
    provider = str(source.get("provider", "")).strip().lower()
    company = str(source.get("company", "Unknown")).strip() or "Unknown"
    if not source_id:
        return None
    return {
        **source,
        "id": source_id,
        "provider": provider,
        "company": company
    }


def make_job(source, posting, previous):
    if not isinstance(posting, dict):
        return None
    external_id = str(posting.get("id", "")).strip()
    if not external_id:
        return None

    title = str(posting.get("title") or "Untitled").strip()
    location_data = posting.get("location")
    if isinstance(location_data, dict):
        location = str(location_data.get("name") or "Not specified").strip()
    else:
        location = str(location_data or "Not specified").strip()

    departments_data = posting.get("departments") or []
    departments = []
    if isinstance(departments_data, list):
        departments = [
            str(item.get("name", ""))
            for item in departments_data if isinstance(item, dict)
        ]

    region, work_mode = detect_location(location)
    board_token = str(source.get("board_token", "")).strip()
    absolute_url = str(posting.get("absolute_url") or "").strip()
    if absolute_url and not absolute_url.startswith(("https://", "http://")):
        absolute_url = ""

    return {
        "id": source["id"] + "-" + external_id,
        "source_id": source["id"],
        "title": title,
        "company": source["company"],
        "location": location,
        "region": region,
        "category": classify(title, departments),
        "industry": previous.get("industry", "Not specified"),
        "job_type": previous.get("job_type", "Not specified"),
        "experience": previous.get("experience", "Not specified"),
        "work_mode": work_mode,
        "demo": False,
        "first_detected_at": previous.get("first_detected_at") or now_utc(),
        "posted_at": posting.get("updated_at") or previous.get("posted_at"),
        "application_url": absolute_url,
        "source_url": f"https://boards.greenhouse.io/{board_token}" if board_token else "",
        "description": posting.get("content") or ""
    }


def count_jobs(jobs):
    """Return counts using region and work_mode as separate dimensions."""
    return {
        "india_jobs": sum(job.get("region") == "India" for job in jobs),
        "global_jobs": sum(job.get("region") == "Global" for job in jobs),
        "remote_jobs": sum(job.get("work_mode") == "Remote" for job in jobs),
        "hybrid_jobs": sum(job.get("work_mode") == "Hybrid" for job in jobs),
        "onsite_jobs": sum(job.get("work_mode") == "On-site" for job in jobs),
        "unspecified_jobs": sum(job.get("region") == "Unspecified" for job in jobs)
    }


def main():
    sources_data = read_json(SOURCES_FILE, {"sources": []})
    database = read_json(JOBS_FILE, {"last_updated": None, "total_jobs": 0, "jobs": []})

    if not isinstance(sources_data, dict):
        raise RuntimeError("sources.json must contain a JSON object")
    sources = sources_data.get("sources", [])
    if not isinstance(sources, list) or not sources:
        raise RuntimeError("sources.json has no valid sources list")
    if not isinstance(database, dict):
        raise RuntimeError("jobs.json must contain a JSON object")
    existing_jobs = database.get("jobs", [])
    if not isinstance(existing_jobs, list):
        raise RuntimeError("jobs.json 'jobs' field must be a list")

    old_jobs = {
        str(job["id"]): job
        for job in existing_jobs
        if isinstance(job, dict) and job.get("id") is not None
    }

    successful_source_ids = set()
    new_jobs = {}
    successful_sources = 0
    failed_sources = 0

    for raw_source in sources:
        source = normalize_source(raw_source)
        if source is None:
            print("Skipping invalid source configuration:", raw_source)
            continue
        if not source.get("enabled", False):
            continue
        if source["provider"] != "greenhouse":
            print("Unsupported provider:", source["provider"], "for", source["company"])
            continue
        if not source.get("board_token"):
            print("Missing board_token for:", source["company"])
            failed_sources += 1
            continue

        print("Checking:", source["company"])
        try:
            postings = fetch_greenhouse(source)
            successful_sources += 1
            successful_source_ids.add(source["id"])
            valid_count = 0
            for posting in postings:
                job = make_job(source, posting, old_jobs.get(
                    source["id"] + "-" + str(posting.get("id", "")) if isinstance(posting, dict) else "", {}
                ))
                if job is None:
                    continue
                new_jobs[job["id"]] = job
                valid_count += 1
            print("Fetched", len(postings), "records; saved", valid_count, "valid jobs for", source["company"])
        except Exception as error:
            failed_sources += 1
            print("Source failed:", source["company"], repr(error))

    if successful_sources == 0:
        raise RuntimeError("All enabled job sources failed. Existing jobs.json was not changed.")

    # Preserve records from sources that failed or were not refreshed this run.
    # A successfully fetched source is authoritative for its current job list.
    for job_id, old_job in old_jobs.items():
        source_id = str(old_job.get("source_id") or job_id.split("-", 1)[0])
        if source_id not in successful_source_ids:
            preserved = dict(old_job)
            region, work_mode = detect_location(preserved.get("location", ""))
            preserved["region"] = region
            preserved["work_mode"] = work_mode
            new_jobs[job_id] = preserved

    jobs_list = list(new_jobs.values())
    jobs_list.sort(key=lambda job: str(job.get("first_detected_at", "")), reverse=True)

    duplicate_audit = build_duplicate_audit(jobs_list)
    counts = count_jobs(jobs_list)
    result = {
        "last_updated": now_utc(),
        "total_jobs": len(jobs_list),
        **counts,
        "jobs": jobs_list
    }

    # Write the report first; only then replace the main database atomically.
    atomic_write_json(DUPLICATE_AUDIT_FILE, duplicate_audit)
    atomic_write_json(JOBS_FILE, result)

    print("--------------------------------")
    print("JobRadar update complete.")
    print("Successful sources:", successful_sources)
    print("Failed sources:", failed_sources)
    print("Total jobs saved:", result["total_jobs"])
    print("India jobs:", counts["india_jobs"])
    print("Global jobs:", counts["global_jobs"])
    print("Remote jobs (all regions):", counts["remote_jobs"])
    print("Hybrid jobs:", counts["hybrid_jobs"])
    print("On-site jobs:", counts["onsite_jobs"])
    print("Unspecified region jobs:", counts["unspecified_jobs"])
    print("Duplicate candidate pairs:", duplicate_audit["candidate_pairs"])
    print("Duplicate report saved to:", DUPLICATE_AUDIT_FILE.name)
    print("--------------------------------")


if __name__ == "__main__":
    main()
