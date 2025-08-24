# GPA Calculator - Full Stack Application

A FastAPI backend service for parsing USF transcript PDFs and calculating GPA, with a React frontend. This project is structured for team collaboration with separate backend and frontend development workflows.

## 🏗️ Project Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React (separate developer)
- **Deployment**: Render (backend) + Frontend hosting platform
- **API Version**: v1

## 🚀 Getting to Production - Complete Guide

### For Backend Developer (You)

#### 1. Local Development Setup

**Prerequisites:** Python 3.11+ and Git

**Setup:**
```bash
# Clone and set up the repository
git clone https://github.com/your-username/GPACalculator-.git
cd GPACalculator-/backend
pip install -r requirements.txt

# Run development server
python -m uvicorn app.main:app --reload
```

**Your API will be available at:**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health
- Upload Endpoint: http://localhost:8000/api/v1/upload
- GPA Endpoint: http://localhost:8000/api/v1/gpa

#### 2. Testing and Code Quality

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

```

#### 3. Deploy Backend to Production

**Step 1: Prepare for deployment**
- Ensure all tests pass

**Step 2: Set up Render**
1. Create account at [Render.com](https://render.com)
2. Connect your GitHub repository
3. Create a new "Web Service"

**Step 3: Configure Render deployment**
- Render will auto-detect the Dockerfile and use it for deployment
- **Environment Variables**:
  - `ENVIRONMENT=production`
  - `CORS_ORIGINS=https://your-frontend-domain.com`

**Step 4: Deploy**
Push to `main` branch - Render will automatically build using the Dockerfile.

#### 4. Share API Details with Frontend Developer

**Production API Base URL:** `https://gpacalculator-qm9d.onrender.com`

**Available Endpoints:**
- `GET /api/v1/health` - Health check
- `POST /api/v1/upload` - Upload transcript PDF
- `POST /api/v1/gpa` - Calculate GPA from course data

---

### For Frontend Developer (Your Collaborator)

#### 1. Frontend Development Setup

**Create your React application** using your preferred method (Create React App, Vite, Next.js, etc.).

**Environment Configuration:**
Create a `.env` file in your React project with:
- `REACT_APP_API_BASE_URL=http://localhost:8000` (for local development)
- `REACT_APP_API_VERSION=v1`

#### 2. Connect to Backend API

The backend provides two main endpoints you'll need to integrate:

**File Upload Endpoint:**
- **URL**: `POST /api/v1/upload`
- **Purpose**: Upload PDF transcript and get parsed course data
- **Input**: PDF file via FormData
- **Output**: Array of course objects with subject, number, title, units, and grade

**GPA Calculation Endpoint:**
- **URL**: `POST /api/v1/gpa` 
- **Purpose**: Calculate GPA from course data
- **Input**: JSON object with courses array
- **Output**: Calculated GPA as a number

#### 3. Local Development

1. Start the backend server (see backend instructions above)
2. Start your React development server
3. Your frontend will connect to the API at `http://localhost:8000`

#### 4. Deploy Frontend to Production

**Deploy to your preferred platform:**
- **Netlify**: Drag & drop build folder or connect GitHub
- **Vercel**: Connect GitHub repository
- **Other**: Any static site hosting service

**Update environment variables for production:**
- Set `REACT_APP_API_BASE_URL` to your `https://gpacalculator-qm9d.onrender.com`
- Share your production domain with backend developer for CORS configuration

---

### 🤝 Team Collaboration

#### Backend Developer Responsibilities
- Maintain API endpoints and documentation
- Deploy backend changes to Render
- Update CORS settings when frontend domain changes
- Communicate any API changes

#### Frontend Developer Responsibilities  
- Build React application using the API endpoints
- Handle file uploads and display results
- Deploy frontend to chosen platform
- Share production domain for CORS configuration

#### Key Communication Points
- **API Changes**: Backend developer notifies of endpoint modifications
- **CORS Updates**: Frontend developer shares production domain
- **Testing**: Both test integration locally before production deployment

---

## 📡 API Reference

### Upload Transcript
**Endpoint:** `POST /api/v1/upload`

Upload a PDF transcript and receive parsed course data.

**Example Response:**
```json
[
  {
    "subject": "CS",
    "number": "101",
    "title": "Intro to Computer Science",
    "units": 4.0,
    "grade": "A"
  }
]
```

### Calculate GPA
**Endpoint:** `POST /api/v1/gpa`

Calculate GPA from an array of courses.

**Example Request:**
```json
{
  "courses": [
    {
      "subject": "CS",
      "number": "101",
      "title": "Intro to Computer Science", 
      "units": 4.0,
      "grade": "A"
    }
  ]
}
```

**Example Response:** `4.0`

---

## 🔧 Development Commands

### Backend
```bash
cd backend
python -m uvicorn app.main:app --reload    # Start dev server
python -m pytest tests/ -v                # Run tests  
python -m black app tests                  # Format code
```

### Configuration

**Local development:** All settings have sensible defaults in `config.py`. No additional setup needed.

**Production deployment:** Set these environment variables in your deployment platform:
- `ENVIRONMENT=production`
- `CORS_ORIGINS=https://your-frontend-domain.com`
- `PORT` (set automatically by deployment platform)

---

## 🚨 Common Issues

### Backend
- **Tests failing**: Check test output for specific errors
- **Import errors**: Ensure you're in the `backend/` directory
- **CORS errors**: Update `CORS_ORIGINS` with correct frontend domain

### Frontend
- **API connection failed**: Verify `REACT_APP_API_BASE_URL` is correct
- **404 errors**: Ensure you're using `/api/v1/` prefix
- **File upload issues**: Check file is PDF format and under size limit

### Deployment
- **Build fails**: Test build commands locally first
- **Health check fails**: Verify `api/v1/health` endpoint works locally

---

## 📝 Project Structure

```
gpa-calculator/
├── backend/                 # Backend application
│   ├── app/                # FastAPI application
│   ├── tests/             # Test suite
│   └── requirements.txt   # Python dependencies
├── frontend/              # Future React frontend
├── Dockerfile            # Docker configuration for Render
└── README.md             # Project documentation
```

---

## 🎓 Assignment Context

This project demonstrates:
- **Clean Architecture**: Simplified, maintainable codebase
- **Test-Driven Development**: Comprehensive test coverage
- **Production Deployment**: Real-world deployment pipeline
- **Team Collaboration**: Professional development workflow
- **API Design**: RESTful endpoints with proper versioning

Perfect for demonstrating both technical depth and practical deployment skills!