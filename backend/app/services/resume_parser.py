from app.core.config import settings

USE_MOCK = settings.USE_MOCK_AI


class ResumeParserService:
    async def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """
        TODO: Use PyMuPDF (fitz) to extract text from PDF bytes.
        pip install pymupdf
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        """
        if USE_MOCK:
            return self._mock_pdf_text()
        raise NotImplementedError("Real implementation not built yet")

    async def parse_resume_with_llm(self, resume_text: str) -> dict:
        """
        TODO: Call llm_service with build_resume_analysis_prompt(resume_text).
        Parse JSON response into CandidateProfile schema.
        prompt_version = get_prompt_version("resume_analysis")
        """
        if USE_MOCK:
            return self._mock_parsed_profile()
        raise NotImplementedError("Real implementation not built yet")

    def _mock_pdf_text(self) -> str:
        return """Rahul Sharma | rahul@example.com | India
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
            "skills": ["Python", "FastAPI", "React", "Playwright", "PostgreSQL", "Docker"],
            "experience": [{
                "company": "Eltropy",
                "role": "SDET",
                "start_date": "2023-08",
                "end_date": "2025-06",
                "highlights": ["Built automation suites using Playwright", "Improved CI pipeline stability"],
            }],
            "projects": [{
                "name": "AI Resume Matcher",
                "description": "Resume-job matching tool using FastAPI and LLMs.",
                "technologies": ["FastAPI", "OpenAI", "PostgreSQL"],
            }],
            "education": [{
                "institution": "BITS Pilani Goa",
                "degree": "B.Tech Chemical Engineering",
                "start_year": 2019,
                "end_year": 2023,
            }],
        }
