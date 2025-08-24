"""
Tests for GPA calculator functionality.
"""

from app.models.course import CourseRow
from app.services.gpa_calculator import GPACalculator


class TestGPACalculator:
    """Test cases for GPA calculation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = GPACalculator()

    def test_basic_gpa_calculation_all_a_grades(self):
        """Test GPA calculation with all A grades."""
        courses = [
            CourseRow(subject="CS", number="101", title="Intro to CS", units=3.0, grade="A"),
            CourseRow(subject="MATH", number="201", title="Calculus", units=4.0, grade="A"),
            CourseRow(subject="ENGL", number="101", title="English", units=3.0, grade="A"),
        ]

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 4.0, "All A grades should result in 4.0 GPA"

    def test_basic_gpa_calculation_mixed_grades(self):
        """Test GPA calculation with mixed letter grades."""
        courses = [
            CourseRow(
                subject="CS", number="101", title="Intro to CS", units=4.0, grade="A"
            ),  # 4.0 * 4 = 16
            CourseRow(
                subject="MATH", number="201", title="Calculus", units=3.0, grade="B"
            ),  # 3.0 * 3 = 9
            CourseRow(
                subject="ENGL", number="101", title="English", units=3.0, grade="C"
            ),  # 2.0 * 3 = 6
        ]
        # Total: 31 quality points / 10 units = 3.1

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 3.1, f"Expected GPA 3.1, got {gpa}"

    def test_gpa_calculation_with_plus_minus_grades(self):
        """Test GPA calculation with plus and minus grades."""
        courses = [
            CourseRow(
                subject="CS", number="101", title="Intro to CS", units=3.0, grade="A-"
            ),  # 3.7 * 3 = 11.1
            CourseRow(
                subject="MATH", number="201", title="Calculus", units=3.0, grade="B+"
            ),  # 3.3 * 3 = 9.9
            CourseRow(
                subject="ENGL", number="101", title="English", units=3.0, grade="C-"
            ),  # 1.7 * 3 = 5.1
        ]
        # Total: 26.1 quality points / 9 units = 2.9

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 2.9, f"Expected GPA 2.9, got {gpa}"

    def test_gpa_calculation_all_grade_types(self):
        """Test GPA calculation with all standard letter grades."""
        courses = [
            CourseRow(
                subject="CS", number="101", title="Course 1", units=1.0, grade="A+"
            ),  # 4.0 * 1 = 4.0
            CourseRow(
                subject="CS", number="102", title="Course 2", units=1.0, grade="A"
            ),  # 4.0 * 1 = 4.0
            CourseRow(
                subject="CS", number="103", title="Course 3", units=1.0, grade="A-"
            ),  # 3.7 * 1 = 3.7
            CourseRow(
                subject="CS", number="104", title="Course 4", units=1.0, grade="B+"
            ),  # 3.3 * 1 = 3.3
            CourseRow(
                subject="CS", number="105", title="Course 5", units=1.0, grade="B"
            ),  # 3.0 * 1 = 3.0
            CourseRow(
                subject="CS", number="106", title="Course 6", units=1.0, grade="B-"
            ),  # 2.7 * 1 = 2.7
            CourseRow(
                subject="CS", number="107", title="Course 7", units=1.0, grade="C+"
            ),  # 2.3 * 1 = 2.3
            CourseRow(
                subject="CS", number="108", title="Course 8", units=1.0, grade="C"
            ),  # 2.0 * 1 = 2.0
            CourseRow(
                subject="CS", number="109", title="Course 9", units=1.0, grade="C-"
            ),  # 1.7 * 1 = 1.7
            CourseRow(
                subject="CS", number="110", title="Course 10", units=1.0, grade="D+"
            ),  # 1.3 * 1 = 1.3
            CourseRow(
                subject="CS", number="111", title="Course 11", units=1.0, grade="D"
            ),  # 1.0 * 1 = 1.0
            CourseRow(
                subject="CS", number="112", title="Course 12", units=1.0, grade="D-"
            ),  # 0.7 * 1 = 0.7
            CourseRow(
                subject="CS", number="113", title="Course 13", units=1.0, grade="F"
            ),  # 0.0 * 1 = 0.0
        ]
        # Total: 29.7 quality points / 13 units = 2.284..., rounded to 2.28

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 2.28, f"Expected GPA 2.28, got {gpa}"

    def test_exclude_non_gpa_grades_tcr(self):
        """Test that TCR grades are excluded from GPA calculation."""
        courses = [
            CourseRow(subject="CS", number="101", title="Intro to CS", units=3.0, grade="A"),
            CourseRow(
                subject="MATH",
                number="201",
                title="Transfer Math",
                units=4.0,
                grade="TCR",
            ),  # Should be excluded
            CourseRow(subject="ENGL", number="101", title="English", units=3.0, grade="B"),
        ]
        # Only A (3 units) and B (3 units) should count: (4.0 * 3 + 3.0 * 3) / 6 = 21 / 6 = 3.5

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 3.5, f"Expected GPA 3.5 (TCR excluded), got {gpa}"

    def test_exclude_non_gpa_grades_comprehensive(self):
        """Test that all non-GPA grades are excluded."""
        courses = [
            CourseRow(
                subject="CS", number="101", title="Graded Course", units=3.0, grade="A"
            ),  # Counts
            CourseRow(
                subject="CS", number="102", title="Pass/Fail", units=4.0, grade="P"
            ),  # Excluded
            CourseRow(
                subject="CS", number="103", title="In Progress", units=4.0, grade="IP"
            ),  # Excluded
            CourseRow(
                subject="CS", number="104", title="Withdrawn", units=3.0, grade="W"
            ),  # Excluded
            CourseRow(
                subject="CS", number="105", title="Transfer", units=4.0, grade="TCR"
            ),  # Excluded
            CourseRow(
                subject="CS", number="106", title="No Grade", units=3.0, grade="NG"
            ),  # Excluded
        ]
        # Only A (3 units) should count: 4.0 * 3 / 3 = 4.0

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 4.0, f"Expected GPA 4.0 (only A counted), got {gpa}"

    def test_empty_course_list(self):
        """Test GPA calculation with empty course list."""
        courses = []

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 0.0, "Empty course list should return 0.0 GPA"

    def test_no_gpa_courses(self):
        """Test GPA calculation when all courses are non-GPA."""
        courses = [
            CourseRow(subject="CS", number="101", title="Pass/Fail", units=3.0, grade="P"),
            CourseRow(subject="MATH", number="201", title="Transfer", units=4.0, grade="TCR"),
            CourseRow(subject="ENGL", number="101", title="Withdrawn", units=3.0, grade="W"),
        ]

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 0.0, "All non-GPA courses should return 0.0 GPA"

    def test_gpa_rounding_to_two_decimals(self):
        """Test that GPA is properly rounded to 2 decimal places."""
        courses = [
            CourseRow(subject="CS", number="101", title="Course 1", units=1.0, grade="A"),  # 4.0
            CourseRow(subject="CS", number="102", title="Course 2", units=1.0, grade="A"),  # 4.0
            CourseRow(subject="CS", number="103", title="Course 3", units=1.0, grade="B"),  # 3.0
        ]
        # Total: 11.0 quality points / 3 units = 3.6666..., should round to 3.67

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 3.67, f"Expected GPA 3.67 (rounded), got {gpa}"

    def test_gpa_rounding_edge_cases(self):
        """Test GPA rounding with various edge cases."""
        # Test case that results in 3.3333..., should round to 3.33
        courses = [
            CourseRow(subject="CS", number="101", title="Course", units=1.0, grade="A"),  # 4.0
            CourseRow(subject="CS", number="102", title="Course", units=2.0, grade="B"),  # 6.0
        ]
        # Total: 10.0 / 3 = 3.3333..., should round to 3.33
        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 3.33, f"Expected GPA 3.33, got {gpa}"

    def test_zero_credit_courses(self):
        """Test handling of zero-credit courses."""
        courses = [
            CourseRow(
                subject="CS", number="101", title="Regular Course", units=3.0, grade="A"
            ),  # Counts
            CourseRow(
                subject="CS", number="102", title="Zero Credit", units=0.0, grade="A"
            ),  # Should not count
            CourseRow(
                subject="CS", number="103", title="Regular Course", units=3.0, grade="B"
            ),  # Counts
        ]
        # Only 3.0 units A and 3.0 units B: (4.0 * 3 + 3.0 * 3) / 6 = 21 / 6 = 3.5

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 3.5, f"Expected GPA 3.5 (zero-credit excluded), got {gpa}"

    def test_mixed_gpa_and_non_gpa_courses_realistic(self):
        """Test realistic mix of GPA and non-GPA courses."""
        courses = [
            # Regular graded courses
            CourseRow(
                subject="CS",
                number="110",
                title="Intro to Computer Science I",
                units=4.0,
                grade="A+",
            ),
            CourseRow(
                subject="CS",
                number="112",
                title="Intro to Computer Science II",
                units=4.0,
                grade="A+",
            ),
            CourseRow(
                subject="CS",
                number="221",
                title="C and Systems Programming",
                units=4.0,
                grade="A",
            ),
            CourseRow(
                subject="CS",
                number="245",
                title="Data Struct & Algorithms",
                units=4.0,
                grade="A+",
            ),
            CourseRow(
                subject="MATH",
                number="201",
                title="Discrete Mathematics",
                units=4.0,
                grade="A+",
            ),
            CourseRow(
                subject="CS",
                number="362",
                title="Foundations of AI",
                units=4.0,
                grade="A",
            ),
            # Transfer credits (should be excluded)
            CourseRow(
                subject="HIST",
                number="120",
                title="History of the U.S.",
                units=4.0,
                grade="TCR",
            ),
            CourseRow(
                subject="MATH",
                number="101",
                title="Elementary Statistics",
                units=4.0,
                grade="TCR",
            ),
            CourseRow(subject="ENGL", number="1XX", title="AP English", units=4.0, grade="TCR"),
            # Courses in progress (should be excluded)
            CourseRow(subject="CS", number="256", title="Career Prep", units=2.0, grade="IP"),
            CourseRow(
                subject="CS",
                number="315",
                title="Computer Architecture",
                units=4.0,
                grade="IP",
            ),
            # Non-GPA graded course (should be excluded)
            CourseRow(subject="ENVS", number="100L", title="Laboratory", units=0.0, grade="NG"),
        ]

        # Only the regular graded courses should count:
        # A+ (4.0): 4 + 4 + 4 + 4 = 16 units * 4.0 = 64 points
        # A (4.0): 4 + 4 = 8 units * 4.0 = 32 points
        # Total: 96 points / 24 units = 4.0

        gpa = self.calculator.calculate_gpa(courses)
        assert gpa == 4.0, f"Expected GPA 4.0 (only regular grades counted), got {gpa}"

    def test_grade_point_mapping_accuracy(self):
        """Test that grade point mappings are accurate."""
        # Test each grade individually to verify mapping
        test_cases = [
            ("A+", 4.0),
            ("A", 4.0),
            ("A-", 3.7),
            ("B+", 3.3),
            ("B", 3.0),
            ("B-", 2.7),
            ("C+", 2.3),
            ("C", 2.0),
            ("C-", 1.7),
            ("D+", 1.3),
            ("D", 1.0),
            ("D-", 0.7),
            ("F", 0.0),
        ]

        for grade, expected_points in test_cases:
            courses = [
                CourseRow(subject="TEST", number="100", title="Test", units=1.0, grade=grade)
            ]
            gpa = self.calculator.calculate_gpa(courses)
            assert (
                gpa == expected_points
            ), f"Grade {grade} should map to {expected_points} points, got {gpa}"
