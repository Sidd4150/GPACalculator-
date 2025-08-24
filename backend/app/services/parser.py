"""
PDF transcript parser for USF transcripts.
"""

import re
from typing import List, Dict
from pathlib import Path

import pypdf
from app.models.course import CourseRow
from app.exceptions import FileError, ParsingError
from app.constants import PARSING_ARTIFACTS, TRANSCRIPT_SECTIONS
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
        # Pattern for courses with grades (works for both institution and transfer credit)
        self.course_with_grade_pattern = re.compile(
            r"([A-Z]{2,6})\s+(\d+[A-Z]*|\d*XX)\s+(?:UG\s+)?(.+?)\s+([A-Z]+[+-]?|NG|TCR)\s+([\d.]+)\s+([\d.]+)",
            re.MULTILINE | re.DOTALL,
        )

        # Pattern for courses in progress (no final grade, just units)
        self.progress_pattern = re.compile(
            r"([A-Z]{2,6})\s+(\d+[A-Z]*|\d*XX)\s+UG\s+(.+?)\s+([\d.]+)$", re.MULTILINE
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

        # File validation should be done by the validation service before calling this method

        text = ""
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)

                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    logger.error("PDF file is encrypted")
                    raise FileError("PDF file is encrypted and cannot be read")

                # Check if PDF has pages
                if len(pdf_reader.pages) == 0:
                    logger.error("PDF file has no pages")
                    raise FileError("PDF file contains no pages")

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
            raise FileError(f"PDF file is corrupted or invalid: {str(e)}") from e
        except (OSError, IOError) as e:
            logger.error("Error reading PDF file: %s", e)
            raise FileError(f"Error reading PDF file: {str(e)}") from e

        # Validate extracted text
        if not text.strip():
            logger.error("No text extracted from PDF")
            raise ParsingError("No text could be extracted from the PDF file")

        # Basic transcript validation
        if "TRANSCRIPT" not in text.upper() and "ACADEMIC" not in text.upper():
            logger.warning("PDF may not be a transcript - missing expected keywords")
            # Don't raise error here, as some transcripts might not have these exact words

        return text

    def identify_sections(self, text: str) -> Dict[str, str]:
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
            # Find end of institution section - look for "COURSES IN PROGRESS" or "TRANSCRIPT TOTALS"
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

    def parse_section_courses(
        self, section_text: str, section_name: str
    ) -> List[CourseRow]:
        """
        Parse all courses from a transcript section.

        Args:
            section_text: Text content of a transcript section
            section_name: Name of the section (for logging/debugging)

        Returns:
            List of CourseRow objects
        """
        courses = []

        # First, try to find courses with grades (both institution and transfer)
        # Use line-by-line parsing for better reliability
        lines = section_text.split("\n")
        line_pattern = re.compile(
            r"([A-Z]{2,6})\s+(\d+[A-Z]*|\d*XX)\s+(?:UG\s+)?(.+?)\s+([A-Z]+[+-]?|NG|TCR)\s+([\d.]+)\s+([\d.]+)"
        )

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = line_pattern.search(line)
            if match:
                subject, number, title, grade, units, _ = match.groups()
                try:
                    course = CourseRow(
                        subject=subject,
                        number=number,
                        title=title.strip(),
                        units=float(units),
                        grade=grade,
                    )
                    courses.append(course)
                    continue
                except (ValueError, TypeError, AttributeError):
                    continue

        # Always use the global pattern to catch multi-line courses
        matches = self.course_with_grade_pattern.findall(section_text)
        for match in matches:
            subject, number, title, grade, units, _ = match
            # Check if we already added this course from line-by-line parsing
            duplicate = any(
                c.subject == subject
                and c.number == number
                and abs(c.units - float(units)) < 0.01
                for c in courses
            )  # Use units for better duplicate detection
            if not duplicate:
                try:
                    course = CourseRow(
                        subject=subject,
                        number=number,
                        title=title.strip(),
                        units=float(units),
                        grade=grade,
                    )
                    courses.append(course)
                except (ValueError, TypeError, AttributeError):
                    continue

        # Handle courses in progress (no final grade)
        if section_name == "COURSES IN PROGRESS":
            matches = self.progress_pattern.findall(section_text)
            for match in matches:
                subject, number, title, units = match
                try:
                    course = CourseRow(
                        subject=subject,
                        number=number,
                        title=title.strip(),
                        units=float(units),
                        grade="IP",  # Mark as In Progress
                    )
                    courses.append(course)
                except (ValueError, TypeError, AttributeError):
                    continue

        return courses

    def clean_and_enhance_courses(self, courses: List[CourseRow]) -> List[CourseRow]:
        """
        Clean and enhance parsed courses with specific USF transcript rules.

        Args:
            courses: List of parsed CourseRow objects

        Returns:
            List of cleaned and enhanced CourseRow objects
        """
        cleaned_courses = []

        for course in courses:
            # Handle special cases

            # Don't skip "DO NOT PRINT" courses - clean their titles instead

            # Clean up corrupted titles that contain extra text from parsing errors
            clean_title = course.title

            # Remove common parsing artifacts
            for artifact in PARSING_ARTIFACTS:
                clean_title = re.sub(
                    artifact, "", clean_title, flags=re.IGNORECASE | re.DOTALL
                )

            # Clean up extra whitespace
            clean_title = re.sub(r"\s+", " ", clean_title).strip()

            # Handle courses with special number formats (4XX, 1XX, etc.)
            clean_number = course.number

            # Only include courses with reasonable title lengths
            if len(clean_title) > 100:
                # Probably a parsing error - truncate at first major section
                clean_title = clean_title[:100].strip()

            # Skip courses with empty titles after cleaning
            if not clean_title:
                continue

            # Create cleaned course
            try:
                cleaned_course = CourseRow(
                    subject=course.subject,
                    number=clean_number,
                    title=clean_title,
                    units=course.units,
                    grade=course.grade,
                )
                cleaned_courses.append(cleaned_course)
            except (ValueError, TypeError, AttributeError):
                # Skip courses that fail validation
                continue

        return cleaned_courses

    def parse_transcript(self, pdf_path: str) -> List[CourseRow]:
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
            if total_section_length < 100:  # Very basic validation
                logger.warning("Transcript sections seem unusually short")

            all_courses = []

            # Parse each section
            if sections["transfer_credit"]:
                try:
                    transfer_courses = self.parse_section_courses(
                        sections["transfer_credit"], "TRANSFER CREDIT"
                    )
                    all_courses.extend(transfer_courses)
                except (ValueError, AttributeError, TypeError) as e:
                    logger.error("Error parsing transfer credit section: %s", e)
                    # Continue processing other sections

            if sections["institution_credit"]:
                try:
                    institution_courses = self.parse_section_courses(
                        sections["institution_credit"], "INSTITUTION CREDIT"
                    )
                    all_courses.extend(institution_courses)
                except (ValueError, AttributeError, TypeError) as e:
                    logger.error("Error parsing institution credit section: %s", e)
                    # Continue processing other sections

            if sections["courses_in_progress"]:
                try:
                    progress_courses = self.parse_section_courses(
                        sections["courses_in_progress"], "COURSES IN PROGRESS"
                    )
                    all_courses.extend(progress_courses)
                except (ValueError, AttributeError, TypeError) as e:
                    logger.error("Error parsing courses in progress section: %s", e)
                    # Continue processing other sections

            # Clean and enhance the courses
            try:
                cleaned_courses = self.clean_and_enhance_courses(all_courses)
            except (ValueError, AttributeError, TypeError) as e:
                logger.error("Error cleaning courses: %s", e)
                # Return uncleaned courses rather than failing completely
                cleaned_courses = all_courses

            # Final validation
            if not cleaned_courses:
                logger.error("No courses found in transcript")
                raise ParsingError(
                    "No courses were found in the transcript",
                    f"Sections found: {list(sections.keys())}, Total text length: {len(text)}",
                )

            # Validate course quality
            valid_courses = [
                c for c in cleaned_courses if c.subject and c.number and c.title
            ]
            if (
                len(valid_courses) < len(cleaned_courses) * 0.8
            ):  # Less than 80% valid courses
                logger.warning(
                    "Low quality parsing: %d/%d courses are valid",
                    len(valid_courses),
                    len(cleaned_courses),
                )
                raise ParsingError(
                    "Transcript format may not be supported",
                    f"Only {len(valid_courses)} out of {len(cleaned_courses)} courses parsed successfully",
                )

            logger.info(
                "Successfully parsed %d courses from transcript", len(cleaned_courses)
            )
            return cleaned_courses

        except (FileError, ParsingError):
            # Re-raise these specific errors
            raise
        except FileNotFoundError:
            # Re-raise file not found
            raise
        except Exception as e:
            logger.error("Unexpected error during transcript parsing: %s", e)
            raise ParsingError(f"Failed to parse transcript: {str(e)}") from e
