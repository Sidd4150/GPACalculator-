"""
PDF transcript parser for USF transcripts.
"""

import re
from pathlib import Path

import pypdf
from app.constants import COURSE_SOURCES, MAX_COURSE_TITLE_LENGTH, PARSING_ARTIFACTS
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
        """Initialize the parser with unified regex pattern for course parsing."""
        # Unified pattern handles both completed and in-progress courses
        # Completed: SUBJECT NUMBER [UG] TITLE GRADE UNITS QUALITY_POINTS
        # In-progress: SUBJECT NUMBER UG TITLE UNITS (no grade/quality_points)
        self._course_pattern = re.compile(
            r"([A-Z]{2,4})\s+(\d+[A-Z]*)\s+(?:UG\s+)?(.+?)\s+"
            r"(?:([A-Z]+[+-]?|NG|TCR)\s+)?([\d.]+)(?:\s+([\d.]+))?",
            re.MULTILINE | re.DOTALL,
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

        # Define section markers in order
        section_markers = [
            ("TRANSFER CREDIT ACCEPTED BY INSTITUTION", "transfer_credit"),
            ("INSTITUTION CREDIT", "institution_credit"),
            ("COURSES IN PROGRESS", "courses_in_progress"),
        ]

        # Find all section positions
        section_positions = []
        for marker, key in section_markers:
            match = re.search(marker, text)
            if match:
                section_positions.append((match.start(), key))

        # Sort by position and extract sections
        section_positions.sort()

        for i, (start_pos, key) in enumerate(section_positions):
            # Find end position (next section start or end of relevant content)
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][0]
            else:
                # Last section - end at copyright or end of document
                copyright_match = re.search(r"© 20\d\d Ellucian", text[start_pos:])
                if copyright_match:
                    end_pos = start_pos + copyright_match.start()
                else:
                    end_pos = len(text)

            sections[key] = text[start_pos:end_pos]

        # Ensure all sections exist (empty if not found)
        for _, key in section_markers:
            if key not in sections:
                sections[key] = ""

        return sections

    def parse_section_courses(self, section_text: str) -> list[Course]:
        """
        Parse all courses from a transcript section.

        Args:
            section_text: Text content of a transcript section

        Returns:
            List of Course objects
        """
        courses = []

        # Fix spacing issues inline (handles "SpanishA" -> "Spanish A" case)
        processed_text = re.sub(
            r"([a-z])([A-Z]+[+-]?)(\s+[\d.]+\s+[\d.]+)", r"\1 \2\3", section_text
        )

        # Use unified pattern to parse all courses
        matches = self._course_pattern.findall(processed_text)

        for match in matches:
            subject, number, title, grade, units, _ = match

            # Clean title inline instead of separate pass
            title = self._clean_title_inline(title)

            # Skip obvious parsing errors or empty titles
            if "Term Totals" in title or not title:
                continue

            # If no grade was captured, it's an in-progress course
            if not grade:
                grade = "IP"

            try:
                course = Course(
                    subject=subject,
                    number=number,
                    title=title,
                    units=float(units),
                    grade=grade,
                    source=COURSE_SOURCES["PARSED"],
                )
                courses.append(course)
            except ValueError as e:
                logger.debug("Skipping course with invalid units: %s", e)
                continue

        return courses

    def _clean_title_inline(self, title: str) -> str:
        """
        Clean course title inline during parsing.

        Args:
            title: Raw course title

        Returns:
            Cleaned course title
        """
        title = title.strip()

        # Remove common parsing artifacts
        for artifact in PARSING_ARTIFACTS:
            title = re.sub(artifact, "", title, flags=re.IGNORECASE | re.DOTALL)

        # Clean up extra whitespace
        title = re.sub(r"\s+", " ", title).strip()

        # Truncate overly long titles (likely parsing errors)
        if len(title) > MAX_COURSE_TITLE_LENGTH:
            title = title[:MAX_COURSE_TITLE_LENGTH].strip()

        return title

    def parse_transcript(self, pdf_path: str) -> list[Course]:
        """
        Parse complete transcript PDF and return all courses.

        Args:
            pdf_path: Path to the PDF transcript file

        Returns:
            List of all Course objects from the transcript

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
                        courses = self.parse_section_courses(sections[section_key])
                        all_courses.extend(courses)
                        logger.debug(
                            "Parsed %d courses from %s section",
                            len(courses),
                            section_name,
                        )
                    except Exception as e:
                        logger.error("Error parsing %s section: %s", section_name, e)
                        # Continue processing other sections

            # Simple validation - ensure we found some courses
            if not all_courses:
                logger.error("No courses found in transcript")
                raise TranscriptParsingError("No courses were found in the transcript")

            logger.info(
                "Successfully parsed %d courses from transcript", len(all_courses)
            )
            return all_courses

        except (TranscriptParsingError, FileNotFoundError, ValueError, OSError):
            raise
        except Exception as e:
            logger.error("Unexpected error during transcript parsing: %s", e)
            raise TranscriptParsingError(f"Failed to parse transcript: {str(e)}") from e
