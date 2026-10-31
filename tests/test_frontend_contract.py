import unittest
from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class FrontendContractTests(unittest.TestCase):
    def test_job_discovery_keeps_hooks_and_uses_compact_filter_layout(self):
        for element_id in (
            "searchInput", "searchBtn", "jobList", "jobCount",
            "locationFilter", "companyFilter", "workFilter",
            "indiaEligibilityFilter", "statusFilter", "sortFilter",
            "statAll", "statIndia", "statGlobal", "statRemote",
            "statActive", "statClosed", "statUnverified",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', HTML)
        self.assertIn('id="advancedFilters"', HTML)
        self.assertIn("jobs-overview", HTML)
        self.assertIn('class="quick-filter-group"', HTML)

    def test_job_card_has_clear_semantic_regions(self):
        for class_name in (
            "job-card", "job-card__top", "job-card__identity",
            "job-card__meta", "job-card__actions",
        ):
            with self.subTest(class_name=class_name):
                self.assertIn(class_name, HTML)

    def test_company_directory_and_all_navigation_hooks_remain(self):
        for element_id in (
            "view-home", "view-jobs", "view-saved", "view-tracker",
            "view-tools", "view-companies", "view-company-profile",
            "view-verification", "view-about", "companyDirectorySearch",
            "companyDirectoryCategory", "companyGrid", "companyProfileJobs",
            "themeBtn", "menuBtn", "moreBtn", "navigation",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', HTML)
        self.assertIn("function routeFromHash()", HTML)
        self.assertIn('addEventListener("hashchange", routeFromHash)', HTML)


if __name__ == "__main__":
    unittest.main(verbosity=2)
