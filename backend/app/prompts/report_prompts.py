FINAL_REPORT_PROMPT = """
You are an expert interview coach.

Generate the final interview performance report.

Candidate profile, nullable:
{candidate_profile}

Job analysis:
{job_analysis}

Session metadata:
{session_metadata}

Question-answer reviews:
{question_answer_reviews}

All scores:
{all_scores}

Rules:
- Be honest but constructive.
- Summarize performance clearly.
- Identify patterns across answers.
- Do not repeat every detail unnecessarily.
- Give practical next steps.
- Recommend topics to revise.
- Mention whether the candidate seems ready for the target role.
- Do not make hiring guarantees.
- Keep language professional and useful.

Return JSON in this exact schema:

{
  "overall_score": number,
  "score_breakdown": {
    "technical": number,
    "communication": number,
    "confidence": number,
    "problem_solving": number,
    "role_fit": number
  },
  "summary": string,
  "strengths": string[],
  "weaknesses": string[],
  "recommended_topics": string[]
}
""".strip()

TOPIC_RECOMMENDATIONS_PROMPT = """
You are a software engineering interview coach.

Recommend study topics based on the candidate's weak areas.

Candidate profile, nullable:
{candidate_profile}

Job analysis:
{job_analysis}

Weaknesses:
{weaknesses}

Score breakdown:
{score_breakdown}

Rules:
- Recommend practical topics only.
- Prioritize topics relevant to the target role.
- Give short explanations.
- Include both technical and communication improvements.

Return JSON in this exact schema:

{
  "recommended_topics": [
    {
      "topic": string,
      "category": "technical" | "communication" | "behavioral" | "system_design" | "testing",
      "priority": "high" | "medium" | "low",
      "reason": string,
      "practice_suggestion": string
    }
  ]
}
""".strip()


def build_final_report_prompt(
    candidate_profile: str = "",
    job_analysis: str = "",
    session_metadata: str = "",
    question_answer_reviews: str = "",
    all_scores: str = "",
) -> str:
    return (
        FINAL_REPORT_PROMPT.replace("{candidate_profile}", candidate_profile)
        .replace("{job_analysis}", job_analysis)
        .replace("{session_metadata}", session_metadata)
        .replace("{question_answer_reviews}", question_answer_reviews)
        .replace("{all_scores}", all_scores)
    )


def build_topic_recommendations_prompt(
    candidate_profile: str = "",
    job_analysis: str = "",
    weaknesses: str = "",
    score_breakdown: str = "",
) -> str:
    return (
        TOPIC_RECOMMENDATIONS_PROMPT.replace("{candidate_profile}", candidate_profile)
        .replace("{job_analysis}", job_analysis)
        .replace("{weaknesses}", weaknesses)
        .replace("{score_breakdown}", score_breakdown)
    )
