# GPA Calculator Backend

## Project Overview
FastAPI backend for parsing USF transcript PDFs and calculating GPA.
Due: [1 week from today]
Frontend developer: Teammate (separate repo/work)

## Key Commands
- Run server: `uvicorn main:app --reload`
- Run tests: `pytest -v`
- Run specific test: `pytest tests/test_parser.py -v`
- Format code: `black .`
- Lint: `flake8`

## Project Structure
/gpa-calculator-backend
├── app/
│   ├── main.py           # FastAPI app entry
│   ├── api/
│   │   └── endpoints.py   # API routes
│   ├── services/
│   │   ├── parser.py      # PDF parsing logic
│   │   └── gpa_calculator.py  # GPA computation
│   ├── models/
│   │   └── course.py      # Pydantic models
│   └── utils/
│       └── validators.py  # Input validation
├── tests/
│   ├── test_parser.py
│   ├── test_gpa.py
│   ├── test_api.py
│   └── fixtures/
│       └── transcripts/   # Test PDFs
├── requirements.txt
└── .github/
└── workflows/
└── tests.yml      # GitHub Actions

## USF Transcript Format Rules
- Three main sections: TRANSFER CREDIT, INSTITUTION CREDIT, COURSES IN PROGRESS
- Course line format: `SUBJECT NUMBER UG Title Grade Units QualityPoints`
- Grade mappings: A=4.0, A-=3.7, B+=3.3, B=3.0, B-=2.7, C+=2.3, C=2.0, C-=1.7, D+=1.3, D=1.0, D-=0.7, F=0.0
- Non-GPA grades (exclude): P, S, U, I, IP, W, NR, AU, TCR, NG
- Transfer credits have TCR grade (exclude from GPA)
- Courses in progress have no grade yet (exclude)

## API Contract
- POST /upload - accepts PDF, returns parsed courses
- POST /gpa - accepts course list, returns cumulative GPA
- CourseRow: {subject, number, title, units, grade, source}

## Testing Strategy
- TDD: Write test first, then implementation
- Use pytest with fixtures for test transcripts
- Generate synthetic transcripts for edge cases

## Code Style
- Clean, readable, minimal dependencies
- Type hints everywhere
- Docstrings for all functions
- Handle errors gracefully with clear messages
- No over-engineering - keep it simple