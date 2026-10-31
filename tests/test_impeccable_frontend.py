import unittest
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class ImpeccableFrontendTests(unittest.TestCase):
    def test_home_has_real_search_and_location_controls(self):
        for element_id in ("homeSearchForm", "homeSearchInput", "homeLocationFilter", "homePopularSearches"):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', HTML)
        self.assertIn('addEventListener("submit"', HTML)
        self.assertIn('homeLocationFilter', HTML)
        self.assertIn('locationFilter', HTML)

    def test_responsive_navigation_has_internship_and_government_recruiter_paths(self):
        self.assertIn('id="menuBtn"', HTML)
        self.assertIn('aria-expanded="false"', HTML)
        self.assertIn('data-nav-intent="internships"', HTML)
        self.assertIn('data-nav-intent="government-recruiters"', HTML)
        self.assertIn('data-nav-intent="resources"', HTML)
        self.assertIn('function handleDiscoveryNavigation', HTML)

    def test_search_location_and_discovery_shortcuts_use_real_jobs(self):
        self.assertIn('function populateHomeLocations', HTML)
        self.assertIn('function applyHomeSearch', HTML)
        self.assertIn('allJobs.map(job => String(job.location || "").trim())', HTML)
        self.assertIn('job.title', HTML)
        self.assertIn('job.india_eligibility', HTML)

    def test_type_and_experience_filters_are_data_driven(self):
        self.assertIn('id="jobTypeFilter"', HTML)
        self.assertIn('id="experienceFilter"', HTML)
        self.assertIn('jobTypes.length ? "All job types" : "Job type not supplied by current sources"', HTML)
        self.assertIn('experiences.length ? "All experience levels" : "Experience not supplied by current sources"', HTML)
        self.assertIn('if(jobType && String(job.job_type || "") !== jobType) return false;', HTML)
        self.assertIn('if(experience && String(job.experience || "") !== experience) return false;', HTML)

    def test_accessibility_and_reduced_motion_contract_remains(self):
        self.assertIn('class="skip-link"', HTML)
        self.assertIn('aria-label="Main navigation"', HTML)
        self.assertIn('aria-label="Search jobs by title, skill or company"', HTML)
        self.assertIn('@media(prefers-reduced-motion:reduce)', HTML.replace(" ", ""))


    def test_first_visit_does_not_block_job_search_with_intro_overlay(self):
        self.assertIn("function runIntro(){", HTML)
        self.assertIn('root.classList.remove("intro-on")', HTML)
        self.assertNotIn("setTimeout(end, 3700)", HTML)

    def test_reveal_motion_is_limited_to_meaningful_content_groups(self):
        self.assertIn('".jobs > .job, .company-grid > .company-card, .tool-grid > .tool-card"', HTML)
        self.assertIn("Keep card contents immediately readable", HTML)
        self.assertNotIn(".job,.company-card,.tool-card{will-change:transform}", HTML)

    def test_job_actions_have_job_specific_accessible_names(self):
        self.assertIn('save.setAttribute("aria-label"', HTML)
        self.assertIn('save.setAttribute("aria-pressed"', HTML)
        self.assertIn('track.setAttribute("aria-label"', HTML)

    def test_theme_control_exposes_current_state_and_survives_storage_failure(self):
        self.assertIn("function syncThemeControl()", HTML)
        self.assertIn('setAttribute("aria-pressed", String(isDark))', HTML)
        self.assertIn('setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme")', HTML)
        self.assertIn('catch(error) {\n  document.body.classList.add("dark");', HTML)


if __name__ == "__main__":
    unittest.main(verbosity=2)
