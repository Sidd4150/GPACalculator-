# GPA Calculator

## Project Overview
Full-stack GPA calculator for parsing USF transcript PDFs and calculating GPA.
- Backend: FastAPI (your responsibility)
- Frontend: React/Next.js (teammate's responsibility, same repo)
- Deployment: Backend on Render (via Dockerfile), Frontend on Netlify/Vercel

## Key Commands (Backend)
- Run server: `uvicorn backend.app.main:app --reload`
- Run tests: `cd backend && pytest -v`
- Run specific test: `cd backend && pytest tests/test_parser.py -v`
- Format code: `cd backend && black .`
- Lint: `cd backend && pylint app/`

## Project Structure
/gpa-calculator/
├── backend/                    # FastAPI backend (your work)
│   ├── app/
│   │   ├── main.py            # FastAPI app entry
│   │   ├── api/
│   │   │   └── endpoints.py   # API routes
│   │   ├── services/
│   │   │   ├── parser.py      # PDF parsing logic
│   │   │   ├── gpa_calculator.py  # GPA computation
│   │   │   └── validation.py  # Input validation
│   │   ├── models/
│   │   │   └── course.py      # Pydantic models
│   │   ├── utils/
│   │   │   ├── exception_handler.py  # Error handling
│   │   │   └── logger.py      # Logging setup
│   │   ├── config.py          # App configuration
│   │   ├── constants.py       # App constants
│   │   └── exceptions.py      # Custom exceptions
│   ├── tests/
│   │   ├── conftest.py        # Test configuration
│   │   ├── test_*.py          # Test files
│   │   └── fixtures/
│   │       └── transcripts/   # Test PDFs
│   └── requirements.txt
├── frontend/                   # Future React frontend (teammate's work)
├── Dockerfile                 # Docker configuration for Render deployment
└── README.md                  # Project documentation

## USF Transcript Format Rules
- Three main sections: TRANSFER CREDIT, INSTITUTION CREDIT, COURSES IN PROGRESS
- Institution Credit Course line format: `SUBJECT NUMBER UG Title Grade Units QualityPoints`
- Grade mappings: A=4.0, A-=3.7, B+=3.3, B=3.0, B-=2.7, C+=2.3, C=2.0, C-=1.7, D+=1.3, D=1.0, D-=0.7, F=0.0
- Non-GPA grades (exclude): P, S, U, I, IP, W, NR, AU, TCR, NG
- Transfer credits have TCR grade (exclude from GPA)
- Courses in progress have no grade yet (exclude)

## API Contract
- POST /api/v1/upload - accepts PDF, returns parsed courses
- POST /api/v1/gpa - accepts course list, returns cumulative GPA
- GET /api/v1/health - health check endpoint
- CourseRow: {subject, number, title, units, grade, source}

## Testing Strategy
- TDD: Write test first, then implementation
- Use pytest with fixtures for test transcripts

## Code Style
- Clean, readable, minimal dependencies
- Type hints everywhere
- Docstrings for all functions
- Handle errors gracefully with clear messages
- No over-engineering - keep it simple