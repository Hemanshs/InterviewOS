RESUME_ANALYSIS_PROMPT = """
You are a senior technical recruiter and resume parser.

Analyze the resume text and extract structured candidate information.

Rules:
- Do not invent missing details.
- If a field is not present, return null or an empty array.
- Extract skills only if they appear directly or are strongly implied by projects/experience.
- Identify the candidate's strongest technical areas.
- Identify possible interview focus areas.

Resume text:
{resume_text}

Return JSON in this exact schema:

{
  "candidate_name": string | null,
  "email": string | null,
  "phone": string | null,
  "location": string | null,
  "summary": string | null,
  "total_experience_years": number | null,
  "current_or_latest_role": string | null,
  "skills": {
    "languages": string[],
    "frameworks": string[],
    "databases": string[],
    "cloud_devops": string[],
    "testing_tools": string[],
    "other": string[]
  },
  "experience": [
    {
      "company": string | null,
      "role": string | null,
      "start_date": string | null,
      "end_date": string | null,
      "responsibilities": string[],
      "achievements": string[],
      "technologies": string[]
    }
  ],
  "projects": [
    {
      "name": string | null,
      "description": string | null,
      "technologies": string[],
      "interview_focus": string[]
    }
  ],
  "education": [
    {
      "institution": string | null,
      "degree": string | null,
      "field": string | null,
      "start_year": number | null,
      "end_year": number | null
    }
  ],
  "strength_areas": string[],
  "possible_weak_areas": string[],
  "recommended_interview_topics": string[]
}
""".strip()

JD_ANALYSIS_PROMPT = """
You are a senior technical recruiter.

Analyze the job description and extract the role expectations.

Rules:
- Do not invent requirements.
- Separate must-have skills from nice-to-have skills.
- Identify likely interview topics.
- Identify what the interviewer may test deeply.

Target role:
{target_role}

Target company:
{target_company}

Job description:
{job_description}

Return JSON in this exact schema:

{
  "role_title": string | null,
  "company": string | null,
  "seniority_level": string | null,
  "must_have_skills": string[],
  "nice_to_have_skills": string[],
  "responsibilities": string[],
  "technical_domains": string[],
  "likely_interview_topics": string[],
  "behavioral_traits_expected": string[],
  "system_design_relevance": "low" | "medium" | "high",
  "coding_relevance": "low" | "medium" | "high",
  "testing_relevance": "low" | "medium" | "high",
  "backend_relevance": "low" | "medium" | "high"
}
""".strip()

NO_RESUME_FALLBACK_PROMPT = """
You are a senior software engineering interviewer.

The candidate has not uploaded a resume.

Do not invent candidate experience, companies, projects, education, or skills.

Use only the available information:
- interview type
- difficulty
- target role
- target company
- job description analysis
- user-provided skills, if any
- user-provided experience level, if any

If specific candidate background is missing, ask role-based questions instead of resume-based questions.

Interview type:
{interview_type}

Difficulty:
{difficulty}

Target role:
{target_role}

Target company:
{target_company}

Job analysis:
{job_analysis}

User-provided skills:
{user_provided_skills}

User experience level:
{user_experience_level}

Return JSON in this exact schema:

{
  "context_mode": "no_resume",
  "safe_assumptions": string[],
  "missing_context": string[],
  "recommended_question_strategy": string[],
  "first_question_suggestion": {
    "question_text": string,
    "question_type": "technical" | "behavioral" | "system_design" | "testing" | "coding",
    "difficulty": "easy" | "medium" | "hard",
    "expected_focus_areas": string[],
    "time_limit_seconds": number
  }
}
""".strip()


def build_resume_analysis_prompt(resume_text: str) -> str:
    return RESUME_ANALYSIS_PROMPT.replace("{resume_text}", resume_text)


def build_jd_analysis_prompt(
    job_description: str,
    target_role: str = "",
    target_company: str = "",
) -> str:
    return (
        JD_ANALYSIS_PROMPT.replace("{job_description}", job_description)
        .replace("{target_role}", target_role)
        .replace("{target_company}", target_company)
    )


def build_no_resume_fallback_prompt(
    interview_type: str,
    difficulty: str,
    target_role: str = "",
    target_company: str = "",
    job_analysis: str = "",
    user_provided_skills: str = "",
    user_experience_level: str = "",
) -> str:
    return (
        NO_RESUME_FALLBACK_PROMPT.replace("{interview_type}", interview_type)
        .replace("{difficulty}", difficulty)
        .replace("{target_role}", target_role)
        .replace("{target_company}", target_company)
        .replace("{job_analysis}", job_analysis)
        .replace("{user_provided_skills}", user_provided_skills)
        .replace("{user_experience_level}", user_experience_level)
    )
