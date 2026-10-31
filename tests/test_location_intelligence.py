import unittest

from fetch_jobs import classify_india_eligibility, detect_location, detect_location_details, make_job


class LocationIntelligenceTests(unittest.TestCase):
    def test_city_and_state_are_inferred_from_known_indian_city(self):
        details = detect_location_details("Bengaluru, Karnataka, India")
        self.assertEqual(details["country"], "India")
        self.assertEqual(details["state"], "Karnataka")
        self.assertEqual(details["city"], "Bengaluru")
        self.assertEqual(details["region"], "India")
        self.assertEqual(details["location_confidence"], "high")

    def test_city_alias_normalizes_to_canonical_city(self):
        details = detect_location_details("Gurgaon, Haryana")
        self.assertEqual(details["city"], "Gurugram")
        self.assertEqual(details["state"], "Haryana")

    def test_state_only_does_not_invent_city(self):
        details = detect_location_details("Kerala, India")
        self.assertEqual(details["country"], "India")
        self.assertEqual(details["state"], "Kerala")
        self.assertIsNone(details["city"])

    def test_global_country_is_normalized(self):
        details = detect_location_details("London, United Kingdom")
        self.assertEqual(details["country"], "United Kingdom")
        self.assertEqual(details["region"], "Global")
        self.assertIsNone(details["state"])
        self.assertIsNone(details["city"])

    def test_remote_without_country_does_not_guess_country(self):
        details = detect_location_details("Remote - Work from anywhere")
        self.assertEqual(details["region"], "Remote")
        self.assertEqual(details["work_mode"], "Remote")
        self.assertIsNone(details["country"])
        self.assertEqual(details["location_confidence"], "medium")

    def test_ambiguous_location_remains_unspecified(self):
        details = detect_location_details("Springfield")
        self.assertEqual(details["region"], "Unspecified")
        self.assertIsNone(details["country"])
        self.assertIsNone(details["state"])
        self.assertIsNone(details["city"])
        self.assertEqual(details["location_confidence"], "low")

    def test_existing_region_work_mode_api_remains_compatible(self):
        self.assertEqual(detect_location("Remote - Bengaluru, India"), ("India", "Remote"))

    def test_make_job_includes_structured_location_fields(self):
        job = make_job(
            {"id": "sample", "company": "Sample Co", "board_token": "sample"},
            {
                "id": 123,
                "title": "Software Engineer",
                "location": {"name": "Noida, Uttar Pradesh, India"},
                "absolute_url": "https://example.com/jobs/123",
                "content": "Role description",
            },
            {},
        )
        self.assertEqual(job["id"], "sample-123")
        self.assertEqual(job["country"], "India")
        self.assertEqual(job["state"], "Uttar Pradesh")
        self.assertEqual(job["city"], "Noida")
        self.assertEqual(job["location_confidence"], "high")


if __name__ == "__main__":
    unittest.main(verbosity=2)
