"""
Test constants module.
"""

import unittest

from app.constants import ERROR_MESSAGES, GRADE_POINTS, NON_GPA_GRADES


class TestConstants(unittest.TestCase):
    """Test constants module values."""

    def test_grade_points(self):
        """Test grade points mapping."""
        self.assertEqual(GRADE_POINTS["A"], 4.0)
        self.assertEqual(GRADE_POINTS["B-"], 2.7)
        self.assertEqual(GRADE_POINTS["F"], 0.0)
        self.assertIn("A+", GRADE_POINTS)

    def test_non_gpa_grades(self):
        """Test non-GPA grades set."""
        self.assertIn("TCR", NON_GPA_GRADES)
        self.assertIn("IP", NON_GPA_GRADES)
        self.assertIn("W", NON_GPA_GRADES)
        self.assertNotIn("A", NON_GPA_GRADES)

    def test_error_messages(self):
        """Test error messages constants."""
        self.assertIn("NO_FILE", ERROR_MESSAGES)
        self.assertIn("INVALID_FILE_TYPE", ERROR_MESSAGES)
        self.assertTrue(len(ERROR_MESSAGES["NO_FILE"]) > 0)


if __name__ == "__main__":
    unittest.main()
