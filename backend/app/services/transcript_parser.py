"""
PDF transcript parser for USF transcripts.
"""

import re
from pathlib import Path

import pypdf

from app.constants import (
    COURSE_SOURCES,
    MAX_COURSE_TITLE_PARSE_LENGTH,
    MIN_PARSING_QUALITY_RATIO,
    MIN_SECTION_TEXT_LENGTH,
    PARSING_ARTIFACTS,
)
from app.exceptions import TranscriptParsingError
from app.models.course import Course
from app.utils.logger import setup_logger

logger = setup_logger("parser")


class TranscriptParser:
    """
    Parser for USF transcript PDFs.

    Handles extraction and parsing of course data from the three main sections:
    - TRANSFER CREDIT ACCEPTED BY INSTITUTION
    - INSTITUTION CREDIT
    - COURSES IN PROGRESS
    """

    def __init__(self):
        """Initialize the parser with regex patterns for course parsing."""
        # Pattern for completed courses with grades
        # Matches: SUBJECT NUMBER [UG] TITLE GRADE UNITS QUALITY_POINTS
        self._course_pattern = re.compile(
            r"([A-Z]{2,4})\s+(\d+[A-Z]*|\d*XX)\s+(?:UG\s+)?(.+?)\s+"
            r"([A-Z]+[+-]?|NG|TCR)\s+([\d.]+)\s+([\d.]+)",
            re.MULTILINE | re.DOTALL,
        )

        # Pattern for courses in progress (no final grade)
        # Matches: SUBJECT NUMBER UG TITLE UNITS
        self._progress_pattern = re.compile(
            r"([A-Z]{2,4})\s+(\d+[A-Z]*|\d*XX)\s+UG\s+(.+?)\s+([\d.]+)$", re.MULTILINE
        )

    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text content from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text as string

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            FileError: If PDF file is corrupted or unreadable
        """
        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            logger.error("PDF file not found: %s", pdf_path)
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        text = ""
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)

                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    logger.error("PDF file is encrypted")
                    raise ValueError("PDF file is encrypted and cannot be read")

                # Check if PDF has pages
                if len(pdf_reader.pages) == 0:
                    logger.error("PDF file has no pages")
                    raise ValueError("PDF file contains no pages")

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text += page_text
                        logger.debug(
                            "Extracted %d characters from page %d",
                            len(page_text),
                            page_num + 1,
                        )
                    except (pypdf.errors.PdfReadError, AttributeError, ValueError) as e:
                        logger.warning(
                            "Error extracting text from page %s: %s", page_num + 1, e
                        )
                        continue  # Try to continue with other pages

        except pypdf.errors.PdfReadError as e:
            logger.error("PDF read error: %s", e)
            raise ValueError(f"PDF file is corrupted or invalid: {str(e)}") from e
        except OSError as e:
            logger.error("Error reading PDF file: %s", e)
            raise OSError(f"Error reading PDF file: {str(e)}") from e

        # Validate extracted text
        if not text.strip():
            logger.error("No text extracted from PDF")
            raise TranscriptParsingError("No text could be extracted from the PDF file")

        # Basic transcript validation
        if "TRANSCRIPT" not in text.upper() and "ACADEMIC" not in text.upper():
            logger.warning("PDF may not be a transcript - missing expected keywords")
            # Don't raise error here, as some transcripts might not have these exact words

        return text

    def identify_sections(self, text: str) -> dict[str, str]:
        """
        Identify and extract the three main transcript sections.

        Args:
            text: Full transcript text

        Returns:
            Dictionary with section names as keys and section text as values
        """
        sections = {}

        # Find transfer credit section
        transfer_start = re.search(r"TRANSFER CREDIT ACCEPTED BY INSTITUTION", text)
        if transfer_start:
            # Find the end of transfer section - look for "INSTITUTION CREDIT"
            institution_start = re.search(r"INSTITUTION CREDIT\s+.*?-Top-", text)
            if institution_start:
                sections["transfer_credit"] = text[
                    transfer_start.start() : institution_start.start()
                ]
            else:
                # Fallback - look for just "INSTITUTION CREDIT"
                institution_start = re.search(r"INSTITUTION CREDIT", text)
                if institution_start:
                    sections["transfer_credit"] = text[
                        transfer_start.start() : institution_start.start()
                    ]
                else:
                    sections["transfer_credit"] = text[transfer_start.start() :]
        else:
            sections["transfer_credit"] = ""

        # Find institution credit section
        institution_start = re.search(r"INSTITUTION CREDIT", text)
        if institution_start:
            # Find end of institution section
            # Look for "COURSES IN PROGRESS" or "TRANSCRIPT TOTALS"
            progress_start = re.search(r"COURSES IN PROGRESS\s+.*?-Top-", text)
            totals_start = re.search(r"TRANSCRIPT TOTALS", text)

            end_pos = None
            if progress_start and totals_start:
                end_pos = min(progress_start.start(), totals_start.start())
            elif progress_start:
                end_pos = progress_start.start()
            elif totals_start:
                end_pos = totals_start.start()

            if end_pos:
                sections["institution_credit"] = text[
                    institution_start.start() : end_pos
                ]
            else:
                sections["institution_credit"] = text[institution_start.start() :]
        else:
            sections["institution_credit"] = ""

        # Find courses in progress section
        progress_start = re.search(r"COURSES IN PROGRESS\s+.*?-Top-", text)
        if progress_start:
            # Progress section goes to end of document or copyright info
            copyright_start = re.search(r"© 20\d\d Ellucian", text)

            if copyright_start:
                sections["courses_in_progress"] = text[
                    progress_start.start() : copyright_start.start()
                ]
            else:
                sections["courses_in_progress"] = text[progress_start.start() :]
        else:
            sections["courses_in_progress"] = ""

        return sections

    def _preprocess_section_text(self, text: str) -> str:
        """
        Preprocess section text to fix spacing issues that cause parsing problems.

        Handles cases where PDF extraction creates malformed text like "SpanishA"
        instead of "Spanish A", which causes regex cross-matching issues.

        Args:
            text: Raw section text

        Returns:
            Preprocessed text with fixed spacing
        """
        # Fix missing spaces between course titles and grades
        # Pattern: lowercase letter + uppercase grade + units/points
        text = re.sub(r"([a-z])([A-Z]+[+-]?)(\s+[\d.]+\s+[\d.]+)", r"\1 \2\3", text)
        return text

    def parse_section_courses(
        self, section_text: str, section_name: str
    ) -> list[Course]:
        """
        Parse all courses from a transcript section.

        Args:
            section_text: Text content of a transcript section
            section_name: Name of the section (for logging/debugging)

        Returns:
            List of CourseRow objects
        """
        courses = []

        # Preprocess text to fix spacing issues that cause parsing problems
        processed_text = self._preprocess_section_text(section_text)

        # Parse completed courses with grades
        courses.extend(self._parse_completed_courses(processed_text))

        # Handle courses in progress (no final grade)
        if section_name == "COURSES IN PROGRESS":
            courses.extend(self._parse_progress_courses(section_text))

        return courses

    def _parse_completed_courses(self, text: str) -> list[Course]:
        """
        Parse completed courses with grades from preprocessed text.

        Args:
            text: Preprocessed section text

        Returns:
            List of CourseRow objects for completed courses
        """
        courses = []
        matches = self._course_pattern.findall(text)

        for match in matches:
            subject, number, title, grade, units, _ = match
            title = title.strip()

            # Skip obvious parsing errors
            if "Term Totals" in title:
                continue

            course = self._create_course_row(subject, number, title, grade, units)
            if course:
                courses.append(course)

        return courses

    def _parse_progress_courses(self, text: str) -> list[Course]:
        """
        Parse courses in progress (no final grade) from section text.

        Args:
            text: Raw section text

        Returns:
            List of CourseRow objects for in-progress courses
        """
        courses = []
        matches = self._progress_pattern.findall(text)

        for match in matches:
            subject, number, title, units = match
            course = self._create_course_row(
                subject, number, title.strip(), "IP", units
            )
            if course:
                courses.append(course)

        return courses

    def _create_course_row(
        self, subject: str, number: str, title: str, grade: str, units: str
    ) -> Course | None:
        """
        Create a CourseRow object with validation.

        Args:
            subject: Course subject code
            number: Course number
            title: Course title
            grade: Course grade
            units: Course units as string

        Returns:
            CourseRow object or None if creation fails
        """
        try:
            return Course(
                subject=subject,
                number=number,
                title=title,
                units=float(units),
                grade=grade,
                source=COURSE_SOURCES["PARSED"],
            )
        except (ValueError, TypeError, AttributeError):
            return None

    def _clean_and_enhance_courses(self, courses: list[Course]) -> list[Course]:
        """
        Clean and enhance parsed courses with specific USF transcript rules.

        Args:
            courses: List of parsed CourseRow objects

        Returns:
            List of cleaned and enhanced CourseRow objects
        """
        cleaned_courses = []

        for course in courses:
            clean_title = self._clean_course_title(course.title)

            # Skip courses with empty titles after cleaning
            if not clean_title:
                continue

            # Create cleaned course - preserve the original source
            try:
                cleaned_course = Course(
                    subject=course.subject,
                    number=course.number,
                    title=clean_title,
                    units=course.units,
                    grade=course.grade,
                    source=course.source,
                )
            except (ValueError, TypeError, AttributeError):
                cleaned_course = None
            if cleaned_course:
                cleaned_courses.append(cleaned_course)

        return cleaned_courses

    def _clean_course_title(self, title: str) -> str:
        """
        Clean up course title by removing parsing artifacts and normalizing whitespace.

        Args:
            title: Raw course title

        Returns:
            Cleaned course title
        """
        clean_title = title

        # Remove common parsing artifacts
        for artifact in PARSING_ARTIFACTS:
            clean_title = re.sub(
                artifact, "", clean_title, flags=re.IGNORECASE | re.DOTALL
            )

        # Clean up extra whitespace
        clean_title = re.sub(r"\s+", " ", clean_title).strip()

        # Truncate overly long titles (likely parsing errors)
        if len(clean_title) > MAX_COURSE_TITLE_PARSE_LENGTH:
            clean_title = clean_title[:MAX_COURSE_TITLE_PARSE_LENGTH].strip()

        return clean_title

    def _validate_parsing_results(self, courses: list[Course]) -> None:
        """
        Validate parsing results and raise TranscriptParsingError if quality is too low.

        Args:
            courses: List of parsed courses

        Raises:
            TranscriptParsingError: If no courses found or parsing quality is too low
        """
        if not courses:
            logger.error("No courses found in transcript")
            raise TranscriptParsingError("No courses were found in the transcript")

        # Validate course quality - at least 80% should be complete
        valid_courses = [c for c in courses if c.subject and c.number and c.title]

        quality_ratio = len(valid_courses) / len(courses)
        if quality_ratio < MIN_PARSING_QUALITY_RATIO:
            logger.warning(
                "Low quality parsing: %d/%d courses are valid (%.1f%%)",
                len(valid_courses),
                len(courses),
                quality_ratio * 100,
            )
            raise TranscriptParsingError("Transcript format may not be supported")

    def parse_transcript(self, pdf_path: str) -> list[Course]:
        """
        Parse complete transcript PDF and return all courses.

        Args:
            pdf_path: Path to the PDF transcript file

        Returns:
            List of all CourseRow objects from the transcript

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            FileError: If PDF parsing fails
            ParsingError: If no courses found or transcript format is invalid
        """

        try:
            # Extract text from PDF
            text = self.extract_text(pdf_path)

            # Identify sections
            sections = self.identify_sections(text)

            # Validate that we found expected sections
            total_section_length = sum(len(section) for section in sections.values())
            if total_section_length < MIN_SECTION_TEXT_LENGTH:  # Very basic validation
                logger.warning("Transcript sections seem unusually short")

            all_courses = []

            # Parse each section
            section_parsers = [
                ("transfer_credit", "TRANSFER CREDIT"),
                ("institution_credit", "INSTITUTION CREDIT"),
                ("courses_in_progress", "COURSES IN PROGRESS"),
            ]

            for section_key, section_name in section_parsers:
                if sections[section_key]:
                    try:
                        courses = self.parse_section_courses(
                            sections[section_key], section_name
                        )
                        all_courses.extend(courses)
                        logger.debug(
                            "Parsed %d courses from %s section",
                            len(courses),
                            section_name,
                        )
                    except (ValueError, AttributeError, TypeError) as e:
                        logger.error("Error parsing %s section: %s", section_name, e)
                        # Continue processing other sections

            # Clean and enhance the courses
            try:
                cleaned_courses = self._clean_and_enhance_courses(all_courses)
            except (ValueError, AttributeError, TypeError) as e:
                logger.error("Error cleaning courses: %s", e)
                # Return uncleaned courses rather than failing completely
                cleaned_courses = all_courses

            # Final validation and logging
            self._validate_parsing_results(cleaned_courses)

            logger.info(
                "Successfully parsed %d courses from transcript", len(cleaned_courses)
            )
            return cleaned_courses

        except (TranscriptParsingError, FileNotFoundError, ValueError, OSError):
            raise
        except Exception as e:
            logger.error("Unexpected error during transcript parsing: %s", e)
            raise TranscriptParsingError(f"Failed to parse transcript: {str(e)}") from e
