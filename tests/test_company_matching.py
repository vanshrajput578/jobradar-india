import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompanyMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master = json.loads((ROOT / "company_master.json").read_text(encoding="utf-8"))
        cls.sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
        cls.jobs = json.loads((ROOT / "jobs_public.json").read_text(encoding="utf-8"))["jobs"]
        cls.companies = cls.master["companies"]
        cls.by_id = {company["company_id"]: company for company in cls.companies}
        cls.source_to_company = {}
        for company in cls.companies:
            for source_id in company.get("source_ids", []):
                if source_id in cls.source_to_company:
                    raise AssertionError(f"Source ID mapped more than once: {source_id}")
                cls.source_to_company[source_id] = company["company_id"]

    def test_company_ids_are_unique(self):
        ids = [company["company_id"] for company in self.companies]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_enabled_source_has_a_canonical_company(self):
        for source in self.sources["sources"]:
            if source.get("enabled"):
                self.assertTrue(source.get("company_id"), source["id"])
                self.assertEqual(self.source_to_company.get(source["id"]), source["company_id"])
                self.assertIn(source["company_id"], self.by_id)

    def test_every_public_job_maps_to_one_company(self):
        mapped = 0
        for job in self.jobs:
            company_id = job.get("company_id") or self.source_to_company.get(job.get("source_id"))
            self.assertTrue(company_id, f"Unmapped job: {job.get('id')}")
            self.assertIn(company_id, self.by_id, f"Unknown company ID on job: {job.get('id')}")
            mapped += 1
        self.assertEqual(mapped, len(self.jobs))


if __name__ == "__main__":
    unittest.main()
