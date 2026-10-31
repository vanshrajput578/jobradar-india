import unittest
from fetch_jobs import reconcile_jobs


class VerificationTests(unittest.TestCase):
    def test_present_job_is_active_and_verified(self):
        jobs, events = reconcile_jobs(
            [{"id": "acme-1", "source_id": "acme", "availability_status": "closed"}],
            {"acme": {"acme-1": {"id": "acme-1", "source_id": "acme", "title": "Engineer"}}},
            {"acme"}, set(), "2026-10-31T00:00:00+00:00"
        )
        self.assertEqual(jobs[0]["availability_status"], "active")
        self.assertEqual(jobs[0]["verification_status"], "verified")
        self.assertEqual(len(events), 1)

    def test_missing_job_from_successful_source_is_closed_not_deleted(self):
        jobs, _ = reconcile_jobs(
            [{"id": "acme-1", "source_id": "acme", "availability_status": "active"}],
            {"acme": {}}, {"acme"}, set(), "2026-10-31T00:00:00+00:00"
        )
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["availability_status"], "closed")
        self.assertIn("not proof", jobs[0]["verification_reason"])

    def test_failed_source_never_closes_job_or_overwrites_last_verified(self):
        jobs, events = reconcile_jobs(
            [{"id": "acme-1", "source_id": "acme", "availability_status": "active",
              "last_verified_at": "2026-10-30T00:00:00+00:00"}],
            {}, set(), {"acme"}, "2026-10-31T00:00:00+00:00"
        )
        self.assertEqual(jobs[0]["availability_status"], "active")
        self.assertEqual(jobs[0]["verification_status"], "unverified")
        self.assertEqual(jobs[0]["last_verified_at"], "2026-10-30T00:00:00+00:00")
        self.assertEqual(events, [])

    def test_reactivation_removes_closed_at_and_appends_history(self):
        jobs, _ = reconcile_jobs(
            [{"id": "acme-1", "source_id": "acme", "availability_status": "closed",
              "closed_at": "2026-10-29T00:00:00+00:00",
              "status_history": [{"availability_status": "closed"}]}],
            {"acme": {"acme-1": {"id": "acme-1", "source_id": "acme"}}},
            {"acme"}, set(), "2026-10-31T00:00:00+00:00"
        )
        self.assertEqual(jobs[0]["availability_status"], "active")
        self.assertNotIn("closed_at", jobs[0])
        self.assertEqual(jobs[0]["status_history"][-1]["availability_status"], "active")


if __name__ == "__main__":
    unittest.main()
