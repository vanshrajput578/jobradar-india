import unittest

from fetch_jobs import (
    append_status_history,
    build_duplicate_audit,
    build_expiry_audit,
    reconcile_jobs,
    STATUS_HISTORY_LIMIT,
)


CHECKED_AT = "2026-10-31T00:00:00+00:00"


def make_existing_job(
    job_id="acme-101",
    source_id="acme",
    status="active",
    verification="verified",
):
    return {
        "id": job_id,
        "source_id": source_id,
        "title": "Software Engineer",
        "company": "Acme",
        "location": "India",
        "region": "India",
        "work_mode": "Hybrid",
        "availability_status": status,
        "verification_status": verification,
        "last_verified_at": "2026-10-30T00:00:00+00:00",
        "status_history": [],
    }


def make_fresh_job(job_id="acme-101", source_id="acme"):
    return {
        "id": job_id,
        "source_id": source_id,
        "title": "Software Engineer",
        "company": "Acme",
        "location": "India",
        "region": "India",
        "work_mode": "Hybrid",
        "application_url": "https://example.com/jobs/101",
        "description": "Software engineering role.",
    }


class VerificationTests(unittest.TestCase):

    def test_present_job_becomes_active_and_verified(self):
        existing = [
            make_existing_job(status="closed")
        ]

        fetched = {
            "acme": {
                "acme-101": make_fresh_job()
            }
        }

        jobs, events = reconcile_jobs(
            existing,
            fetched,
            {"acme"},
            set(),
            CHECKED_AT,
        )

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["availability_status"], "active")
        self.assertEqual(jobs[0]["verification_status"], "verified")
        self.assertEqual(jobs[0]["last_verified_at"], CHECKED_AT)
        self.assertNotIn("closed_at", jobs[0])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["to"], "active")

    def test_missing_job_from_successful_source_is_closed_not_deleted(self):
        existing = [
            make_existing_job(status="active")
        ]

        jobs, events = reconcile_jobs(
            existing,
            {"acme": {}},
            {"acme"},
            set(),
            CHECKED_AT,
        )

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["availability_status"], "closed")
        self.assertEqual(jobs[0]["verification_status"], "verified")
        self.assertEqual(jobs[0]["closed_at"], CHECKED_AT)
        self.assertIn("not proof", jobs[0]["verification_reason"])
        self.assertEqual(events[0]["to"], "closed")

    def test_failed_source_does_not_close_existing_job(self):
        existing = [
            make_existing_job(status="active")
        ]

        jobs, events = reconcile_jobs(
            existing,
            {},
            set(),
            {"acme"},
            CHECKED_AT,
        )

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["availability_status"], "active")
        self.assertEqual(jobs[0]["verification_status"], "unverified")
        self.assertEqual(events, [])

    def test_failed_source_preserves_last_verified_timestamp(self):
        old_timestamp = "2026-10-30T00:00:00+00:00"

        existing = [
            make_existing_job(status="active")
        ]

        jobs, _ = reconcile_jobs(
            existing,
            {},
            set(),
            {"acme"},
            CHECKED_AT,
        )

        self.assertEqual(
            jobs[0]["last_verified_at"],
            old_timestamp,
        )

        self.assertEqual(
            jobs[0]["last_check_attempt_at"],
            CHECKED_AT,
        )

    def test_closed_job_reactivation_removes_closed_at(self):
        existing_job = make_existing_job(status="closed")
        existing_job["closed_at"] = "2026-10-29T00:00:00+00:00"

        jobs, events = reconcile_jobs(
            [existing_job],
            {
                "acme": {
                    "acme-101": make_fresh_job()
                }
            },
            {"acme"},
            set(),
            CHECKED_AT,
        )

        self.assertEqual(jobs[0]["availability_status"], "active")
        self.assertNotIn("closed_at", jobs[0])
        self.assertEqual(events[0]["from"], "closed")
        self.assertEqual(events[0]["to"], "active")

    def test_unchecked_source_does_not_change_availability(self):
        existing = [
            make_existing_job(status="active")
        ]

        jobs, events = reconcile_jobs(
            existing,
            {},
            set(),
            set(),
            CHECKED_AT,
        )

        self.assertEqual(jobs[0]["availability_status"], "active")
        self.assertEqual(jobs[0]["last_verified_at"], "2026-10-30T00:00:00+00:00")
        self.assertEqual(events, [])

    def test_status_history_is_limited_to_twenty_entries(self):
        job = {
            "status_history": [
                {
                    "availability_status": "closed",
                    "changed_at": f"2026-10-{day:02d}T00:00:00+00:00",
                    "reason": "test",
                }
                for day in range(1, 21)
            ]
        }

        append_status_history(
            job,
            "active",
            "reactivated",
            CHECKED_AT,
        )

        self.assertEqual(
            len(job["status_history"]),
            STATUS_HISTORY_LIMIT,
        )

        self.assertEqual(
            job["status_history"][-1]["availability_status"],
            "active",
        )

    def test_expiry_audit_counts_and_events(self):
        jobs = [
            {
                "availability_status": "active",
                "verification_status": "verified",
            },
            {
                "availability_status": "closed",
                "verification_status": "verified",
            },
            {
                "availability_status": "active",
                "verification_status": "unverified",
            },
        ]

        events = [
            {
                "job_id": "acme-101",
                "from": "active",
                "to": "closed",
                "at": CHECKED_AT,
            }
        ]

        audit = build_expiry_audit(
            jobs,
            CHECKED_AT,
            [{"source_id": "acme", "status": "success"}],
            events,
        )

        self.assertEqual(audit["generated_at"], CHECKED_AT)
        self.assertEqual(audit["status_counts"]["active"], 2)
        self.assertEqual(audit["status_counts"]["closed"], 1)
        self.assertEqual(audit["status_counts"]["unverified"], 1)
        self.assertEqual(audit["status_events"], events)
        self.assertIs(audit["automatic_deletion_enabled"], False)

    def test_duplicate_audit_never_deletes_or_merges(self):
        jobs = [
            {
                "id": "acme-101",
                "company": "Acme",
                "title": "Software Engineer",
                "location": "India",
                "application_url": "https://example.com/jobs/101",
                "description": "Engineering role",
            },
            {
                "id": "acme-102",
                "company": "Other Company",
                "title": "Developer",
                "location": "India",
                "application_url": "https://example.com/jobs/101",
                "description": "Different role",
            },
        ]

        audit = build_duplicate_audit(jobs)

        self.assertEqual(audit["total_jobs_checked"], 2)
        self.assertEqual(audit["candidate_pairs"], 1)
        self.assertTrue(audit["review_required"])
        self.assertIs(audit["automatic_deletion_enabled"], False)
        self.assertIs(audit["automatic_merge_enabled"], False)
        self.assertTrue(audit["candidates"][0]["review_required"])
        self.assertEqual(audit["candidates"][0]["automatic_action"], "none")


if __name__ == "__main__":
    unittest.main(verbosity=2)
