ANSWER_EVALUATION_PROMPT = """
You are a fair but strict senior technical interviewer.

Evaluate the candidate's answer.

Question:
{question_text}

Expected focus areas:
{expected_focus_areas}

Candidate answer transcript:
{candidate_answer_transcript}

Candidate profile, nullable:
{candidate_profile}

Job analysis:
{job_analysis}

Interview type:
{interview_type}

Scoring rules:
- Score each dimension from 0 to 10.
- Be fair and specific.
- Do not over-penalize minor grammar mistakes.
- Penalize vague answers, hallucinated experience, lack of examples, or incorrect technical claims.
- Reward structured reasoning, practical examples, and role relevance.
- If the transcript is too short or empty, score low and explain why.
- Feedback must be actionable.
- Do not be rude or discouraging.

Return JSON in this exact schema:

{
  "scores": {
    "technical_correctness": number,
    "clarity": number,
    "depth": number,
    "confidence": number,
    "relevance": number,
    "structure": number,
    "communication": number,
    "conciseness": number,
    "example_quality": number,
    "overall": number
  },
  "feedback": {
    "summary": string,
    "strengths": string[],
    "improvements": string[],
    "ideal_answer_points": string[],
    "missed_points": string[],
    "suggested_better_answer": string
  },
  "follow_up_recommendation": {
    "recommended": boolean,
    "reason": string,
    "suggested_follow_up_question": string | null
  }
}
""".strip()

BEHAVIORAL_EVALUATION_PROMPT = """
You are a senior behavioral interviewer.

Evaluate the candidate's behavioral answer using the STAR framework:
- Situation
- Task
- Action
- Result

Question:
{question_text}

Candidate answer transcript:
{candidate_answer_transcript}

Target company:
{target_company}

Target role:
{target_role}

Rules:
- Score each dimension from 0 to 10.
- Check whether the answer includes a clear situation, task, action, and result.
- Reward measurable results and ownership.
- Penalize vague or theoretical answers.
- Give specific improvement advice.

Return JSON in this exact schema:

{
  "star_scores": {
    "situation": number,
    "task": number,
    "action": number,
    "result": number,
    "ownership": number,
    "reflection": number,
    "overall": number
  },
  "feedback": {
    "summary": string,
    "strengths": string[],
    "improvements": string[],
    "missing_star_parts": string[],
    "suggested_reframe": string
  }
}
""".strip()


def build_evaluation_prompt(
    question_text: str = "",
    expected_focus_areas: str = "",
    candidate_answer_transcript: str = "",
    candidate_profile: str = "",
    job_analysis: str = "",
    interview_type: str = "",
) -> str:
    return (
        ANSWER_EVALUATION_PROMPT.replace("{question_text}", question_text)
        .replace("{expected_focus_areas}", expected_focus_areas)
        .replace("{candidate_answer_transcript}", candidate_answer_transcript)
        .replace("{candidate_profile}", candidate_profile)
        .replace("{job_analysis}", job_analysis)
        .replace("{interview_type}", interview_type)
    )


def build_behavioral_evaluation_prompt(
    question_text: str = "",
    candidate_answer_transcript: str = "",
    target_company: str = "",
    target_role: str = "",
) -> str:
    return (
        BEHAVIORAL_EVALUATION_PROMPT.replace("{question_text}", question_text)
        .replace("{candidate_answer_transcript}", candidate_answer_transcript)
        .replace("{target_company}", target_company)
        .replace("{target_role}", target_role)
    )
