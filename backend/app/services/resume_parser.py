import fitz

from app.core.config import settings
from app.core.exceptions import ResumeParseError

MAX_RESUME_CHARS = 15000


class ResumeParserService:
    async def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract raw text from PDF bytes using PyMuPDF."""
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pages: list[str] = []
            for page in doc:
                pages.append(page.get_text())
            doc.close()
            text = "\n".join(pages).strip()
            if not text:
                if settings.USE_MOCK_LLM:
                    return self._mock_pdf_text()[:MAX_RESUME_CHARS]
                raise ResumeParseError("PDF appears to be empty or image-only (no extractable text)")
            return text[:MAX_RESUME_CHARS]
        except ResumeParseError:
            raise
        except Exception as exc:
            if settings.USE_MOCK_LLM:
                return self._mock_pdf_text()[:MAX_RESUME_CHARS]
            raise ResumeParseError(f"Failed to extract text from PDF: {str(exc)}") from exc

    async def parse_resume_with_llm(self, resume_text: str) -> dict:
        """
        Parse extracted resume text into structured CandidateProfile using Gemini.
        Returns dict matching CandidateProfile schema.
        """
        if settings.USE_MOCK_LLM:
            return self._mock_parsed_profile()

        from app.services.llm_service import LLMService

        llm = LLMService()

        try:
            return await llm.analyze_resume(resume_text)
        except Exception as exc:
            raise ResumeParseError(f"LLM resume parsing failed: {str(exc)}") from exc

    def _mock_pdf_text(self) -> str:
        return """Rahul Sharma | rahul@example.com | +91-9000000000 | India
Software Engineer with 2 years experience in FastAPI, Python, Playwright.
Experience: Eltropy — SDET (2023–2025) — Built automation suites with Playwright.
Projects: AI Resume Matcher — FastAPI, OpenAI, PostgreSQL.
Education: BITS Pilani Goa — B.Tech Chemical Engineering (2019–2023).
Skills: Python, FastAPI, React, Playwright, PostgreSQL, Docker"""

    def _mock_parsed_profile(self) -> dict:
        return {
            "candidate_name": "Rahul Sharma",
            "email": "rahul@example.com",
            "phone": "+91-9000000000",
            "location": "India",
            "summary": "Software engineer with experience in backend APIs and test automation.",
            "total_experience_years": 2.0,
            "current_or_latest_role": "SDET at Eltropy",
            "skills": {
                "languages": ["Python", "JavaScript", "TypeScript"],
                "frameworks": ["FastAPI", "React", "Playwright"],
                "databases": ["PostgreSQL", "Redis"],
                "cloud_devops": ["Docker", "GitHub Actions"],
                "testing_tools": ["Playwright", "pytest"],
                "other": [],
            },
            "experience": [
                {
                    "company": "Eltropy",
                    "role": "SDET",
                    "start_date": "2023-08",
                    "end_date": "2025-06",
                    "responsibilities": ["Built automation suites using Playwright"],
                    "achievements": ["Improved CI pipeline stability by 40%"],
                    "technologies": ["Playwright", "Python", "GitHub Actions"],
                }
            ],
            "projects": [
                {
                    "name": "AI Resume Matcher",
                    "description": "Resume-job matching tool using FastAPI and LLMs.",
                    "technologies": ["FastAPI", "OpenAI", "PostgreSQL"],
                    "interview_focus": ["API design", "LLM integration", "database design"],
                }
            ],
            "education": [
                {
                    "institution": "BITS Pilani Goa",
                    "degree": "B.Tech",
                    "field": "Chemical Engineering",
                    "start_year": 2019,
                    "end_year": 2023,
                }
            ],
            "strength_areas": ["Test automation", "Backend API development", "Python"],
            "possible_weak_areas": ["System design at scale", "Frontend architecture"],
            "recommended_interview_topics": [
                "API design and validation",
                "Test automation strategies",
                "CI/CD pipelines",
                "Python performance",
            ],
        }
