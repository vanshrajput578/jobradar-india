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


    def test_job_and_company_results_are_paginated(self):
        self.assertIn('id="jobPagination"', HTML)
        self.assertIn('id="companyPagination"', HTML)
        self.assertIn("const JOBS_PER_PAGE = 12", HTML)
        self.assertIn("const COMPANIES_PER_PAGE = 12", HTML)
        self.assertIn("function renderPager(", HTML)
        self.assertIn("rows.slice(start, start + JOBS_PER_PAGE)", HTML)
        self.assertIn("rows.slice(start, start + COMPANIES_PER_PAGE)", HTML)

    def test_company_sort_and_search_controls_are_wired(self):
        self.assertIn('id="companyDirectorySort"', HTML)
        self.assertIn('value="jobs">Most active listings', HTML)
        self.assertIn('companyDirectorySort").onchange', HTML)
        self.assertIn('companyDirectorySearch").oninput', HTML)

    def test_saved_jobs_empty_state_has_a_working_discovery_action(self):
        self.assertIn("Your shortlist starts here", HTML)
        self.assertIn('id="browseJobsFromSaved"', HTML)
        self.assertIn('showView("jobs")', HTML)

    def test_unified_visual_system_theme_and_intro_are_present(self):
        self.assertIn("JobRadar India — unified flagship interface layer", HTML)
        self.assertIn("body.dark{", HTML)
        self.assertIn('localStorage.getItem("jobradar-theme")', HTML)
        self.assertIn("prefers-color-scheme: dark", HTML)
        self.assertIn("@media(prefers-reduced-motion:reduce)", HTML.replace(" ", ""))
        for hook in ("jrIntro", "heroCanvas", "scrollProgress", "heroFeed", "hmJobs"):
            with self.subTest(hook=hook):
                self.assertIn(f'id="{hook}"', HTML)

    def test_jobs_page_has_sidebar_layout_and_company_avatar(self):
        self.assertIn('class="jobs-layout"', HTML)
        self.assertIn('class="jobs-filters"', HTML)
        self.assertIn("job-card__avatar", HTML)


if __name__ == "__main__":
    unittest.main(verbosity=2)
