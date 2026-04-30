VOICE_REWRITE_PROMPT = """
Rewrite the following interview question so it sounds natural when spoken aloud by a voice interviewer.

Rules:
- Keep the meaning unchanged.
- Make it conversational but professional.
- Avoid long nested sentences.
- Avoid symbols that sound awkward in TTS.
- Do not add extra explanation.
- Keep it under 35 words if possible.

Question:
{raw_question_text}

Return JSON:

{
  "voice_ready_text": string
}
""".strip()


def build_voice_rewrite_prompt(raw_question_text: str) -> str:
    return VOICE_REWRITE_PROMPT.replace("{raw_question_text}", raw_question_text)
