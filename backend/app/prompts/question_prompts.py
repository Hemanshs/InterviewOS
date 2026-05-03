FIRST_QUESTION_PROMPT = """
You are a senior software engineering interviewer.

Generate the FIRST question for a mock interview.

Candidate profile, nullable:
{candidate_profile}

Job analysis:
{job_analysis}

Interview type:
{interview_type}

Difficulty:
{difficulty}

Target role:
{target_role}

Target company:
{target_company}

Rules:
- Ask only one question.
- The question must feel realistic for the target role.
- If candidate_profile contains real resume information, the question must explicitly anchor to at least one concrete item from it: a recent role, project, technology, achievement, or recommended interview topic.
- When candidate_profile exists, do not ask a generic warm-up if a resume-specific deep-dive is possible.
- Otherwise use JD/role-based questions.
- Avoid generic warm-up questions unless the profile has too little information.
- Do not include the expected answer in the question.
- Keep the question speakable for a voice interviewer.
- The question should be answerable in 60–90 seconds.
- If interview_type is "sdet", focus on testing, automation, CI/CD, reliability, or debugging.
- If interview_type is "backend", focus on APIs, databases, scalability, reliability, or services.
- If interview_type is "sde", focus on coding, problem-solving, backend, design, or project depth.
- If interview_type is "behavioral", ask a STAR-style behavioral question.

Return JSON in this exact schema:

{
  "question_text": string,
  "question_type": "technical" | "behavioral" | "resume_deep_dive" | "system_design" | "testing" | "coding",
  "difficulty": "easy" | "medium" | "hard",
  "expected_focus_areas": string[],
  "time_limit_seconds": number
}
""".strip()

NEXT_QUESTION_PROMPT = """
You are a senior technical interviewer conducting a structured mock interview.

Generate the next interview question.

Candidate profile, nullable:
{candidate_profile}

Job analysis:
{job_analysis}

Interview type:
{interview_type}

Difficulty:
{difficulty}

Previous questions:
{previous_questions}

Previous scores and feedback:
{previous_scores}

Remaining questions:
{remaining_question_count}

Rules:
- Ask only one question.
- Do not repeat previous questions.
- Cover a new useful area unless a follow-up is clearly needed.
- Increase depth if the candidate is performing well.
- Reduce complexity if the candidate is struggling.
- Adaptive difficulty rule: if the previous overall_score >= 7, increase difficulty by one level when appropriate; if overall_score <= 4, reduce difficulty by one level; otherwise maintain the same difficulty.
- If candidate_profile contains real resume information, the question must explicitly reference a concrete resume item and explore a new area from the candidate's background.
- Otherwise use JD, target role, or previous answer.
- Keep it natural for voice delivery.
- The answer should fit within 60–90 seconds.

Return JSON in this exact schema:

{
  "question_text": string,
  "question_type": "technical" | "behavioral" | "resume_deep_dive" | "system_design" | "testing" | "coding",
  "difficulty": "easy" | "medium" | "hard",
  "expected_focus_areas": string[],
  "time_limit_seconds": number
}
""".strip()

FOLLOW_UP_QUESTION_PROMPT = """
You are a senior interviewer.

Generate a follow-up question based on the candidate's previous answer.

Original question:
{question_text}

Candidate answer:
{candidate_answer}

Evaluation feedback:
{evaluation_feedback}

Candidate profile, nullable:
{candidate_profile}

Job analysis:
{job_analysis}

Rules:
- Ask only one follow-up question.
- The follow-up should test depth, clarity, or real experience.
- Do not ask a completely unrelated question.
- If the answer was weak, ask a simpler clarifying follow-up.
- If the answer was strong, ask a deeper practical follow-up.
- Keep it short and speakable.
- Do not reveal the ideal answer.

Return JSON in this exact schema:

{
  "follow_up_question": string,
  "purpose": "clarification" | "depth_check" | "real_experience_check" | "edge_case_check",
  "difficulty": "easy" | "medium" | "hard",
  "expected_focus_areas": string[]
}
""".strip()


def build_first_question_prompt(
    candidate_profile: str = "",
    job_analysis: str = "",
    interview_type: str = "",
    difficulty: str = "",
    target_role: str = "",
    target_company: str = "",
) -> str:
    return (
        FIRST_QUESTION_PROMPT.replace("{candidate_profile}", candidate_profile)
        .replace("{job_analysis}", job_analysis)
        .replace("{interview_type}", interview_type)
        .replace("{difficulty}", difficulty)
        .replace("{target_role}", target_role)
        .replace("{target_company}", target_company)
    )


def build_next_question_prompt(
    candidate_profile: str = "",
    job_analysis: str = "",
    interview_type: str = "",
    difficulty: str = "",
    previous_questions: str = "",
    previous_scores: str = "",
    remaining_question_count: str = "",
) -> str:
    return (
        NEXT_QUESTION_PROMPT.replace("{candidate_profile}", candidate_profile)
        .replace("{job_analysis}", job_analysis)
        .replace("{interview_type}", interview_type)
        .replace("{difficulty}", difficulty)
        .replace("{previous_questions}", previous_questions)
        .replace("{previous_scores}", previous_scores)
        .replace("{remaining_question_count}", remaining_question_count)
    )


def build_follow_up_question_prompt(
    question_text: str = "",
    candidate_answer: str = "",
    evaluation_feedback: str = "",
    candidate_profile: str = "",
    job_analysis: str = "",
) -> str:
    return (
        FOLLOW_UP_QUESTION_PROMPT.replace("{question_text}", question_text)
        .replace("{candidate_answer}", candidate_answer)
        .replace("{evaluation_feedback}", evaluation_feedback)
        .replace("{candidate_profile}", candidate_profile)
        .replace("{job_analysis}", job_analysis)
    )
