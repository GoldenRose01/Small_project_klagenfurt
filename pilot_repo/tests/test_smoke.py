"""Baseline smoke tests verifying repository startup and public interfaces."""

import unittest

from reporting import list_user_reports, visible_reports
from reporting.sample_data import SAMPLE_REPORTS, SAMPLE_USERS


class SmokeTests(unittest.TestCase):
    def test_sample_data_loads(self) -> None:
        self.assertEqual(len(SAMPLE_USERS), 2)
        self.assertEqual(len(SAMPLE_REPORTS), 2)

    def test_entry_points_return_lists(self) -> None:
        self.assertIsInstance(visible_reports(["alpha"], SAMPLE_REPORTS), list)
        self.assertIsInstance(list_user_reports(SAMPLE_USERS[0], SAMPLE_REPORTS), list)


if __name__ == "__main__":
    unittest.main()
