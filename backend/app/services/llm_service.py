import json
import re
from typing import Any

from app.core.config import settings
from app.core.exceptions import LLMError
from app.prompts.base_prompts import GLOBAL_SYSTEM_PROMPT, get_prompt_version
from app.prompts.evaluation_prompts import build_evaluation_prompt
from app.prompts.question_prompts import (
    build_first_question_prompt,
    build_follow_up_question_prompt,
    build_next_question_prompt,
)
from app.prompts.resume_prompts import build_resume_analysis_prompt
from app.prompts.resume_prompts import build_no_resume_fallback_prompt
from app.prompts.report_prompts import build_final_report_prompt


class LLMService:
    _PROMPT_TEXT_LIMIT = 1200
    _PROMPT_JSON_LIMIT = 1600
    _MIN_THINKING_BUDGET = 512

    def _as_string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    def _as_optional_int(self, value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _as_optional_float(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _normalize_question_type(self, value: Any) -> str:
        if not isinstance(value, str):
            return "technical"

        normalized = value.strip().lower()
        if "behavior" in normalized:
            return "behavioral"
        if "system" in normalized and "design" in normalized:
            return "system_design"
        if "test" in normalized:
            return "testing"
        if "coding" in normalized:
            return "coding"
        if "resume" in normalized:
            return "resume_deep_dive"
        return "technical"

    def _normalize_time_limit_seconds(self, value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = settings.FREE_MAX_AUDIO_SECONDS
        return max(1, min(parsed, settings.FREE_MAX_AUDIO_SECONDS))

    def _truncate_text(self, value: Any, limit: int | None = None) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        if not text:
            return ""
        max_len = limit or self._PROMPT_TEXT_LIMIT
        if len(text) <= max_len:
            return text
        return text[: max_len - 3].rstrip() + "..."

    def _compact_json_text(self, value: Any, limit: int | None = None) -> str:
        payload = json.dumps(value or {}, ensure_ascii=True, separators=(",", ":"))
        return self._truncate_text(payload, limit or self._PROMPT_JSON_LIMIT)

    def _top_combined_skills(self, skills: dict[str, Any]) -> list[str]:
        prioritized = [
            *self._as_string_list(skills.get("languages")),
            *self._as_string_list(skills.get("frameworks")),
            *self._as_string_list(skills.get("databases")),
            *self._as_string_list(skills.get("cloud_devops")),
            *self._as_string_list(skills.get("testing_tools")),
            *self._as_string_list(skills.get("other")),
        ]
        deduped: list[str] = []
        seen: set[str] = set()
        for skill in prioritized:
            normalized = skill.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(skill)
            if len(deduped) >= 8:
                break
        return deduped

    def _job_analysis_prompt_context(self, job_analysis: dict[str, Any] | None) -> str:
        if not isinstance(job_analysis, dict) or not job_analysis:
            return ""

        compact: dict[str, Any] = {}
        for key in [
            "role_title",
            "company",
            "seniority_level",
            "system_design_relevance",
            "coding_relevance",
            "testing_relevance",
            "backend_relevance",
        ]:
            value = job_analysis.get(key)
            if value not in (None, "", []):
                compact[key] = value

        for key in [
            "must_have_skills",
            "nice_to_have_skills",
            "technical_domains",
            "likely_interview_topics",
            "behavioral_traits_expected",
        ]:
            values = self._as_string_list(job_analysis.get(key))
            if values:
                compact[key] = values[:6]

        job_description = self._truncate_text(job_analysis.get("job_description"), 600)
        if job_description:
            compact["job_description_excerpt"] = job_description

        return self._compact_json_text(compact, 1000)

    def _candidate_profile_prompt_context(self, candidate_profile: dict[str, Any] | None) -> str:
        if not isinstance(candidate_profile, dict) or not candidate_profile:
            return ""

        lines: list[str] = []
        name = candidate_profile.get("candidate_name")
        role = candidate_profile.get("current_or_latest_role")
        summary = candidate_profile.get("summary")
        total_years = candidate_profile.get("total_experience_years")

        if name:
            lines.append(f"Candidate name: {name}")
        if role:
            lines.append(f"Current or latest role: {role}")
        if total_years is not None:
            lines.append(f"Total experience years: {total_years}")
        if summary:
            lines.append(f"Summary: {self._truncate_text(summary, 180)}")

        skills = candidate_profile.get("skills", {})
        if isinstance(skills, dict):
            languages = self._as_string_list(skills.get("languages"))
            frameworks = self._as_string_list(skills.get("frameworks"))
            top_skills = self._top_combined_skills(skills)
            if languages:
                lines.append(f"Languages: {', '.join(languages[:4])}")
            if frameworks:
                lines.append(f"Frameworks: {', '.join(frameworks[:4])}")
            if top_skills:
                lines.append(f"Top skills: {', '.join(top_skills[:8])}")

        experience = candidate_profile.get("experience")
        if isinstance(experience, list):
            for item in experience[:1]:
                if not isinstance(item, dict):
                    continue
                company = item.get("company") or "Unknown company"
                item_role = item.get("role") or "Unknown role"
                technologies = ", ".join(self._as_string_list(item.get("technologies"))[:4])
                achievements = self._as_string_list(item.get("achievements"))
                responsibilities = self._as_string_list(item.get("responsibilities"))
                detail_parts = [f"{item_role} at {company}"]
                if technologies:
                    detail_parts.append(f"Technologies: {technologies}")
                if achievements:
                    detail_parts.append(
                        f"Achievement: {self._truncate_text(achievements[0], 120)}"
                    )
                elif responsibilities:
                    detail_parts.append(
                        f"Responsibility: {self._truncate_text(responsibilities[0], 120)}"
                    )
                lines.append(f"Experience: {' | '.join(detail_parts)}")

        projects = candidate_profile.get("projects")
        if isinstance(projects, list):
            for item in projects[:1]:
                if not isinstance(item, dict):
                    continue
                name = item.get("name") or "Unnamed project"
                description = item.get("description")
                technologies = ", ".join(self._as_string_list(item.get("technologies"))[:4])
                focus = ", ".join(self._as_string_list(item.get("interview_focus"))[:3])
                detail_parts = [name]
                if description:
                    detail_parts.append(self._truncate_text(description, 120))
                if technologies:
                    detail_parts.append(f"Technologies: {technologies}")
                if focus:
                    detail_parts.append(f"Interview focus: {focus}")
                lines.append(f"Project: {' | '.join(detail_parts)}")

        strength_areas = self._as_string_list(candidate_profile.get("strength_areas"))
        if strength_areas:
            lines.append(f"Strength areas: {', '.join(strength_areas[:3])}")

        recommended_topics = self._as_string_list(
            candidate_profile.get("recommended_interview_topics")
        )
        if recommended_topics:
            lines.append(f"Recommended topics: {', '.join(recommended_topics[:3])}")

        return self._truncate_text("\n".join(lines), 800)

    def _looks_structured_text(self, value: str) -> bool:
        stripped = value.strip()
        return stripped.startswith("```") or stripped.startswith("{") or '"question_text"' in stripped

    def _extract_json_object_text(self, text: str) -> str | None:
        stripped = text.strip()
        if not stripped:
            return None

        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()

        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return stripped[start : end + 1]

    def _parse_jsonish_dict(self, value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            return value
        if not isinstance(value, str):
            return None
        extracted_json = self._extract_json_object_text(value)
        if not extracted_json:
            return None
        try:
            parsed = json.loads(extracted_json)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _build_gemini_client(self):
        from google import genai

        return genai.Client(api_key=settings.GEMINI_API_KEY)

    def _coerce_question_result(
        self,
        raw: dict[str, Any],
        *,
        difficulty: str,
        mode: str,
    ) -> dict[str, Any]:
        first_question_suggestion = raw.get("first_question_suggestion")
        if isinstance(first_question_suggestion, dict):
            raw = first_question_suggestion

        question_text = raw.get("question_text") or raw.get("follow_up_question")
        if not question_text:
            raise LLMError("Gemini question generation response was missing question_text")

        if isinstance(question_text, str) and self._looks_structured_text(question_text):
            return self._coerce_question_result_from_text(
                question_text,
                difficulty=raw.get("difficulty", difficulty),
                mode=mode,
            )

        return {
            "question_text": question_text,
            "question_type": self._normalize_question_type(raw.get("question_type", "technical")),
            "difficulty": raw.get("difficulty", difficulty),
            "expected_focus_areas": raw.get("expected_focus_areas", []),
            "time_limit_seconds": self._normalize_time_limit_seconds(
                raw.get("time_limit_seconds", settings.FREE_MAX_AUDIO_SECONDS)
            ),
            "prompt_version": get_prompt_version(
                "follow_up_question"
                if mode == "follow_up"
                else ("first_question" if mode == "first" else "next_question")
            ),
        }

    def _coerce_question_result_from_text(
        self,
        question_text: str,
        *,
        difficulty: str,
        mode: str,
    ) -> dict[str, Any]:
        raw_text = question_text.strip()

        outer_payload = self._parse_jsonish_dict(raw_text)
        if outer_payload:
            candidates = outer_payload.get("candidates")
            if isinstance(candidates, list) and candidates:
                candidate = candidates[0] if isinstance(candidates[0], dict) else {}
                content = candidate.get("content", {})
                parts = content.get("parts", []) if isinstance(content, dict) else []
                if isinstance(parts, list) and parts:
                    part = parts[0] if isinstance(parts[0], dict) else {}
                    nested_text = part.get("text")
                    if isinstance(nested_text, str) and nested_text.strip():
                        return self._coerce_question_result_from_text(
                            nested_text,
                            difficulty=difficulty,
                            mode=mode,
                        )

        current_text = question_text
        for _ in range(3):
            stripped = current_text.strip()
            extracted_json = self._extract_json_object_text(stripped)
            if not extracted_json:
                current_text = stripped
                break
            try:
                parsed_json = json.loads(extracted_json)
            except json.JSONDecodeError:
                current_text = stripped
                break
            if not isinstance(parsed_json, dict):
                current_text = stripped
                break
            nested_question_text = parsed_json.get("question_text") or parsed_json.get("follow_up_question")
            if isinstance(nested_question_text, str) and self._looks_structured_text(nested_question_text):
                current_text = nested_question_text
                difficulty = parsed_json.get("difficulty", difficulty)
                continue
            return self._coerce_question_result(
                parsed_json,
                difficulty=difficulty,
                mode=mode,
            )

        direct_match = re.search(
            r'"question_text"\s*:\s*"((?:[^"\\]|\\.)*)"',
            raw_text,
            flags=re.DOTALL,
        )
        if direct_match:
            extracted_question_text = bytes(
                direct_match.group(1), "utf-8"
            ).decode("unicode_escape").strip()
            if extracted_question_text and not self._looks_structured_text(extracted_question_text):
                type_match = re.search(
                    r'"question_type"\s*:\s*"((?:[^"\\]|\\.)*)"',
                    raw_text,
                    flags=re.DOTALL,
                )
                difficulty_match = re.search(
                    r'"difficulty"\s*:\s*"((?:[^"\\]|\\.)*)"',
                    raw_text,
                    flags=re.DOTALL,
                )
                return {
                    "question_text": extracted_question_text,
                    "question_type": self._normalize_question_type(
                        type_match.group(1) if type_match else "technical"
                    ),
                    "difficulty": (
                        difficulty_match.group(1).strip()
                        if difficulty_match and difficulty_match.group(1).strip()
                        else difficulty
                    ),
                    "expected_focus_areas": [],
                    "time_limit_seconds": self._normalize_time_limit_seconds(
                        (
                            re.search(
                                r'"time_limit_seconds"\s*:\s*(\d+)',
                                raw_text,
                                flags=re.DOTALL,
                            ).group(1)
                            if re.search(
                                r'"time_limit_seconds"\s*:\s*(\d+)',
                                raw_text,
                                flags=re.DOTALL,
                            )
                            else settings.FREE_MAX_AUDIO_SECONDS
                        )
                    ),
                    "prompt_version": get_prompt_version(
                        "follow_up_question"
                        if mode == "follow_up"
                        else ("first_question" if mode == "first" else "next_question")
                    ),
                }

        cleaned_question_text = current_text.strip().strip('"').strip("'")
        if not cleaned_question_text or self._looks_structured_text(cleaned_question_text):
            raise LLMError("Gemini question generation fallback returned an empty question")

        return {
            "question_text": cleaned_question_text,
            "question_type": "technical",
            "difficulty": difficulty,
            "expected_focus_areas": [],
            "time_limit_seconds": settings.FREE_MAX_AUDIO_SECONDS,
            "prompt_version": get_prompt_version(
                "follow_up_question"
                if mode == "follow_up"
                else ("first_question" if mode == "first" else "next_question")
            ),
        }

    def _coerce_evaluation_result(self, raw: dict[str, Any]) -> dict[str, Any]:
        nested = self._parse_jsonish_dict(raw.get("scores"))
        if nested:
            raw = {**raw, "scores": nested}
        nested = self._parse_jsonish_dict(raw.get("feedback"))
        if nested:
            raw = {**raw, "feedback": nested}
        nested = self._parse_jsonish_dict(raw.get("follow_up_recommendation"))
        if nested:
            raw = {**raw, "follow_up_recommendation": nested}

        scores = raw.get("scores", {})
        feedback = raw.get("feedback", {})
        follow_up = raw.get("follow_up_recommendation", {})

        return {
            "scores": {
                "technical_correctness": scores.get("technical_correctness"),
                "clarity": scores.get("clarity"),
                "depth": scores.get("depth"),
                "confidence": scores.get("confidence"),
                "relevance": scores.get("relevance"),
                "structure": scores.get("structure"),
                "communication": scores.get("communication"),
                "conciseness": scores.get("conciseness"),
                "example_quality": scores.get("example_quality"),
                "overall": scores.get("overall"),
            },
            "feedback": {
                "summary": feedback.get("summary", ""),
                "strengths": feedback.get("strengths", []),
                "improvements": feedback.get("improvements", []),
                "ideal_answer_points": feedback.get("ideal_answer_points", []),
                "missed_points": feedback.get("missed_points", []),
                "suggested_better_answer": feedback.get("suggested_better_answer", ""),
            },
            "follow_up": {
                "recommended": follow_up.get("recommended", False),
                "reason": follow_up.get("reason", ""),
                "question_text": follow_up.get("suggested_follow_up_question")
                or follow_up.get("question_text"),
            },
        }

    def _coerce_evaluation_result_from_text(self, text: str) -> dict[str, Any]:
        outer_payload = self._parse_jsonish_dict(text)
        if outer_payload:
            candidates = outer_payload.get("candidates")
            if isinstance(candidates, list) and candidates:
                candidate = candidates[0] if isinstance(candidates[0], dict) else {}
                content = candidate.get("content", {})
                parts = content.get("parts", []) if isinstance(content, dict) else []
                if isinstance(parts, list) and parts:
                    part = parts[0] if isinstance(parts[0], dict) else {}
                    nested_text = part.get("text")
                    if isinstance(nested_text, str) and nested_text.strip():
                        return self._coerce_evaluation_result_from_text(nested_text)

        current_text = text
        for _ in range(3):
            parsed = self._parse_jsonish_dict(current_text)
            if isinstance(parsed, dict):
                return self._coerce_evaluation_result(parsed)

            extracted_json = self._extract_json_object_text(current_text)
            if not extracted_json:
                break
            current_text = extracted_json

        raise LLMError("Gemini returned invalid JSON for answer evaluation")

    def _coerce_final_report_result(self, raw: dict[str, Any]) -> dict[str, Any]:
        nested = self._parse_jsonish_dict(raw.get("score_breakdown"))
        if nested:
            raw = {**raw, "score_breakdown": nested}
        nested = self._parse_jsonish_dict(raw.get("recommended_topics"))
        if nested:
            raw = {**raw, "recommended_topics": nested}

        breakdown = raw.get("score_breakdown", {})

        return {
            "overall_score": raw.get("overall_score", 0.0),
            "score_breakdown": {
                "technical": breakdown.get("technical", 0.0),
                "communication": breakdown.get("communication", 0.0),
                "confidence": breakdown.get("confidence", 0.0),
                "problem_solving": breakdown.get("problem_solving", 0.0),
                "role_fit": breakdown.get("role_fit", 0.0),
            },
            "summary": raw.get("summary", ""),
            "strengths": raw.get("strengths", []),
            "weaknesses": raw.get("weaknesses", []),
            "recommended_topics": raw.get("recommended_topics", []),
        }

    def _coerce_final_report_result_from_text(self, text: str) -> dict[str, Any]:
        outer_payload = self._parse_jsonish_dict(text)
        if outer_payload:
            candidates = outer_payload.get("candidates")
            if isinstance(candidates, list) and candidates:
                candidate = candidates[0] if isinstance(candidates[0], dict) else {}
                content = candidate.get("content", {})
                parts = content.get("parts", []) if isinstance(content, dict) else []
                if isinstance(parts, list) and parts:
                    part = parts[0] if isinstance(parts[0], dict) else {}
                    nested_text = part.get("text")
                    if isinstance(nested_text, str) and nested_text.strip():
                        return self._coerce_final_report_result_from_text(nested_text)

        current_text = text
        for _ in range(3):
            parsed = self._parse_jsonish_dict(current_text)
            if isinstance(parsed, dict):
                return self._coerce_final_report_result(parsed)

            extracted_json = self._extract_json_object_text(current_text)
            if not extracted_json:
                break
            current_text = extracted_json

        overall_match = re.search(
            r'"overall_score"\s*:\s*(-?\d+(?:\.\d+)?)',
            text,
            flags=re.DOTALL,
        )
        summary_match = re.search(
            r'"summary"\s*:\s*"((?:[^"\\]|\\.)*)"',
            text,
            flags=re.DOTALL,
        )
        if overall_match or summary_match:
            breakdown: dict[str, Any] = {}
            for key in [
                "technical",
                "communication",
                "confidence",
                "problem_solving",
                "role_fit",
            ]:
                match = re.search(
                    rf'"{key}"\s*:\s*(-?\d+(?:\.\d+)?)',
                    text,
                    flags=re.DOTALL,
                )
                if match:
                    breakdown[key] = float(match.group(1))

            def _extract_string_array(field_name: str) -> list[str]:
                match = re.search(
                    rf'"{field_name}"\s*:\s*\[(.*?)\]',
                    text,
                    flags=re.DOTALL,
                )
                if not match:
                    return []
                inner = match.group(1)
                values = re.findall(r'"((?:[^"\\]|\\.)*)"', inner, flags=re.DOTALL)
                return [
                    bytes(value, "utf-8").decode("unicode_escape").strip()
                    for value in values
                    if bytes(value, "utf-8").decode("unicode_escape").strip()
                ]

            summary = (
                bytes(summary_match.group(1), "utf-8").decode("unicode_escape").strip()
                if summary_match
                else ""
            )
            return self._coerce_final_report_result(
                {
                    "overall_score": float(overall_match.group(1)) if overall_match else 0.0,
                    "score_breakdown": breakdown,
                    "summary": summary,
                    "strengths": _extract_string_array("strengths"),
                    "weaknesses": _extract_string_array("weaknesses"),
                    "recommended_topics": _extract_string_array("recommended_topics"),
                }
            )

        raise LLMError("Gemini returned invalid JSON for final report generation")

    def _coerce_resume_profile_result(self, raw: dict[str, Any]) -> dict[str, Any]:
        skills = raw.get("skills", {})
        experience = raw.get("experience", [])
        projects = raw.get("projects", [])
        education = raw.get("education", [])
        return {
            "candidate_name": raw.get("candidate_name"),
            "email": raw.get("email"),
            "phone": raw.get("phone"),
            "location": raw.get("location"),
            "summary": raw.get("summary"),
            "total_experience_years": self._as_optional_float(
                raw.get("total_experience_years")
            ),
            "current_or_latest_role": raw.get("current_or_latest_role"),
            "skills": {
                "languages": self._as_string_list(skills.get("languages")),
                "frameworks": self._as_string_list(skills.get("frameworks")),
                "databases": self._as_string_list(skills.get("databases")),
                "cloud_devops": self._as_string_list(skills.get("cloud_devops")),
                "testing_tools": self._as_string_list(skills.get("testing_tools")),
                "other": self._as_string_list(skills.get("other")),
            },
            "experience": [
                {
                    "company": item.get("company"),
                    "role": item.get("role"),
                    "start_date": item.get("start_date"),
                    "end_date": item.get("end_date"),
                    "responsibilities": self._as_string_list(item.get("responsibilities")),
                    "achievements": self._as_string_list(item.get("achievements")),
                    "technologies": self._as_string_list(item.get("technologies")),
                }
                for item in experience
                if isinstance(item, dict)
            ],
            "projects": [
                {
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "technologies": self._as_string_list(item.get("technologies")),
                    "interview_focus": self._as_string_list(item.get("interview_focus")),
                }
                for item in projects
                if isinstance(item, dict)
            ],
            "education": [
                {
                    "institution": item.get("institution"),
                    "degree": item.get("degree"),
                    "field": item.get("field"),
                    "start_year": self._as_optional_int(item.get("start_year")),
                    "end_year": self._as_optional_int(item.get("end_year")),
                }
                for item in education
                if isinstance(item, dict)
            ],
            "strength_areas": self._as_string_list(raw.get("strength_areas")),
            "possible_weak_areas": self._as_string_list(raw.get("possible_weak_areas")),
            "recommended_interview_topics": self._as_string_list(
                raw.get("recommended_interview_topics")
            ),
        }

    def _coerce_resume_profile_result_from_text(self, text: str) -> dict[str, Any]:
        outer_payload = self._parse_jsonish_dict(text)
        if outer_payload:
            candidates = outer_payload.get("candidates")
            if isinstance(candidates, list) and candidates:
                candidate = candidates[0] if isinstance(candidates[0], dict) else {}
                content = candidate.get("content", {})
                parts = content.get("parts", []) if isinstance(content, dict) else []
                if isinstance(parts, list) and parts:
                    part = parts[0] if isinstance(parts[0], dict) else {}
                    nested_text = part.get("text")
                    if isinstance(nested_text, str) and nested_text.strip():
                        return self._coerce_resume_profile_result_from_text(nested_text)

        current_text = text
        for _ in range(3):
            parsed = self._parse_jsonish_dict(current_text)
            if isinstance(parsed, dict):
                return self._coerce_resume_profile_result(parsed)

            extracted_json = self._extract_json_object_text(current_text)
            if not extracted_json:
                break
            current_text = extracted_json

        raw_text = text.strip()

        def extract_string(field: str) -> str | None:
            match = re.search(
                rf'"{re.escape(field)}"\s*:\s*"((?:[^"\\]|\\.)*)"',
                raw_text,
                flags=re.DOTALL,
            )
            if not match:
                return None
            value = bytes(match.group(1), "utf-8").decode("unicode_escape").strip()
            return value or None

        def extract_float(field: str) -> float | None:
            match = re.search(
                rf'"{re.escape(field)}"\s*:\s*(-?\d+(?:\.\d+)?)',
                raw_text,
                flags=re.DOTALL,
            )
            if not match:
                return None
            return self._as_optional_float(match.group(1))

        def extract_list(field: str) -> list[str]:
            match = re.search(
                rf'"{re.escape(field)}"\s*:\s*\[(.*?)\]',
                raw_text,
                flags=re.DOTALL,
            )
            if not match:
                return []
            values = re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1), flags=re.DOTALL)
            return [bytes(value, "utf-8").decode("unicode_escape").strip() for value in values if value.strip()]

        salvage = {
            "candidate_name": extract_string("candidate_name"),
            "email": extract_string("email"),
            "phone": extract_string("phone"),
            "location": extract_string("location"),
            "summary": extract_string("summary"),
            "total_experience_years": extract_float("total_experience_years"),
            "current_or_latest_role": extract_string("current_or_latest_role"),
            "skills": {
                "languages": extract_list("languages"),
                "frameworks": extract_list("frameworks"),
                "databases": extract_list("databases"),
                "cloud_devops": extract_list("cloud_devops"),
                "testing_tools": extract_list("testing_tools"),
                "other": extract_list("other"),
            },
            "experience": [],
            "projects": [],
            "education": [],
            "strength_areas": extract_list("strength_areas"),
            "possible_weak_areas": extract_list("possible_weak_areas"),
            "recommended_interview_topics": extract_list("recommended_interview_topics"),
        }
        if any(
            [
                salvage["candidate_name"],
                salvage["email"],
                salvage["summary"],
                salvage["current_or_latest_role"],
                salvage["total_experience_years"] is not None,
                any(salvage["skills"].values()),
                salvage["strength_areas"],
                salvage["recommended_interview_topics"],
            ]
        ):
            return salvage

        raise LLMError("Gemini returned invalid JSON for resume analysis")

    def _require_gemini(self) -> None:
        if settings.LLM_PROVIDER != "gemini":
            raise LLMError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
        if not settings.GEMINI_API_KEY:
            raise LLMError(
                "GEMINI_API_KEY is required when USE_MOCK_LLM=false and LLM_PROVIDER=gemini"
            )

    async def _generate_gemini_json(
        self,
        *,
        prompt: str,
        purpose: str,
        model: str | None = None,
        max_output_tokens: int = 1024,
        temperature: float = 0.3,
        thinking_budget: int | None = None,
    ) -> dict[str, Any]:
        self._require_gemini()

        try:
            from google.genai import types

            client = self._build_gemini_client()
            async with client.aio as aclient:
                response = await aclient.models.generate_content(
                    model=model or settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=GLOBAL_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                        thinking_config=(
                            types.ThinkingConfig(thinking_budget=thinking_budget)
                            if thinking_budget is not None
                            else None
                        ),
                    ),
                )
        except Exception as exc:
            raise LLMError(f"Gemini {purpose} failed: {str(exc)}") from exc

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, dict):
            return parsed

        response_text = (getattr(response, "text", "") or "").strip()
        if not response_text:
            raise LLMError(f"Gemini returned an empty response for {purpose}")

        try:
            parsed_json = json.loads(response_text)
        except json.JSONDecodeError as exc:
            extracted_json = self._extract_json_object_text(response_text)
            if not extracted_json:
                raise LLMError(f"Gemini returned invalid JSON for {purpose}") from exc
            try:
                parsed_json = json.loads(extracted_json)
            except json.JSONDecodeError as extracted_exc:
                raise LLMError(f"Gemini returned invalid JSON for {purpose}") from extracted_exc

        if not isinstance(parsed_json, dict):
            raise LLMError(f"Gemini returned non-object JSON for {purpose}")
        return parsed_json

    async def _generate_gemini_text(
        self,
        *,
        prompt: str,
        purpose: str,
        model: str | None = None,
        max_output_tokens: int = 512,
        temperature: float = 0.4,
        thinking_budget: int | None = None,
    ) -> str:
        self._require_gemini()

        try:
            from google.genai import types

            client = self._build_gemini_client()
            async with client.aio as aclient:
                response = await aclient.models.generate_content(
                    model=model or settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=GLOBAL_SYSTEM_PROMPT,
                        response_mime_type="text/plain",
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                        thinking_config=(
                            types.ThinkingConfig(thinking_budget=thinking_budget)
                            if thinking_budget is not None
                            else None
                        ),
                    ),
                )
        except Exception as exc:
            raise LLMError(f"Gemini {purpose} failed: {str(exc)}") from exc

        response_text = (getattr(response, "text", "") or "").strip()
        if not response_text:
            raise LLMError(f"Gemini returned an empty response for {purpose}")
        return response_text

    async def generate_question(
        self,
        *,
        mode: str,
        sequence: int,
        interview_type: str,
        difficulty: str,
        question_count: int,
        target_role: str = "",
        target_company: str = "",
        candidate_profile: dict | None = None,
        job_analysis: dict | None = None,
        previous_questions: list[str] | None = None,
        previous_scores: list[dict] | None = None,
        previous_answer_transcript: str = "",
        evaluation_feedback: str = "",
    ) -> dict[str, Any]:
        if settings.USE_MOCK_LLM:
            return self._mock_question(sequence=sequence)

        candidate_profile_json = self._candidate_profile_prompt_context(candidate_profile)
        job_analysis_json = self._job_analysis_prompt_context(job_analysis)

        use_no_resume_prompt = False
        if mode == "first":
            if candidate_profile_json:
                prompt = build_first_question_prompt(
                    candidate_profile=candidate_profile_json,
                    job_analysis=job_analysis_json,
                    interview_type=interview_type,
                    difficulty=difficulty,
                    target_role=target_role,
                    target_company=target_company,
                )
            else:
                use_no_resume_prompt = True
                prompt = build_no_resume_fallback_prompt(
                    interview_type=interview_type,
                    difficulty=difficulty,
                    target_role=target_role,
                    target_company=target_company,
                    job_analysis=job_analysis_json,
                    user_provided_skills="",
                    user_experience_level="",
                )
        elif mode == "follow_up":
            prompt = build_follow_up_question_prompt(
                question_text=(previous_questions or [""])[-1] if previous_questions else "",
                candidate_answer=previous_answer_transcript,
                evaluation_feedback=evaluation_feedback,
                candidate_profile=candidate_profile_json,
                job_analysis=job_analysis_json,
            )
        else:
            prompt = build_next_question_prompt(
                candidate_profile=candidate_profile_json,
                job_analysis=job_analysis_json,
                interview_type=interview_type,
                difficulty=difficulty,
                previous_questions=json.dumps(previous_questions or [], ensure_ascii=True),
                previous_scores=json.dumps(previous_scores or [], ensure_ascii=True),
                remaining_question_count=str(max(question_count - sequence + 1, 0)),
            )

        if use_no_resume_prompt:
            try:
                raw = await self._generate_gemini_json(
                    prompt=prompt,
                    purpose="question generation",
                    max_output_tokens=700,
                    temperature=0.2,
                    thinking_budget=self._MIN_THINKING_BUDGET,
                )
                return self._coerce_question_result(
                    raw,
                    difficulty=difficulty,
                    mode=mode,
                )
            except LLMError:
                pass

        question_text = await self._generate_gemini_text(
            prompt=prompt,
            purpose="question generation",
            max_output_tokens=500,
            temperature=0.3,
            thinking_budget=self._MIN_THINKING_BUDGET,
        )
        return self._coerce_question_result_from_text(
            question_text,
            difficulty=difficulty,
            mode=mode,
        )

    async def evaluate_answer(
        self,
        *,
        question_text: str,
        transcript: str,
        expected_focus_areas: list[str] | None = None,
        candidate_profile: dict | None = None,
        job_analysis: dict | None = None,
        interview_type: str = "sde",
    ) -> dict[str, Any]:
        if settings.USE_MOCK_LLM:
            return self._normalize_mock_evaluation(self._mock_evaluation())
 
        prompt = build_evaluation_prompt(
            question_text=question_text,
            expected_focus_areas=self._compact_json_text(expected_focus_areas or [], 400),
            candidate_answer_transcript=self._truncate_text(transcript, 2200),
            candidate_profile=self._candidate_profile_prompt_context(candidate_profile),
            job_analysis=self._job_analysis_prompt_context(job_analysis),
            interview_type=interview_type,
        )
        try:
            raw = await self._generate_gemini_json(
                prompt=prompt,
                purpose="answer evaluation",
                max_output_tokens=1400,
                temperature=0.2,
                thinking_budget=self._MIN_THINKING_BUDGET,
            )
            return self._coerce_evaluation_result(raw)
        except LLMError:
            raw_text = await self._generate_gemini_text(
                prompt=prompt,
                purpose="answer evaluation",
                max_output_tokens=1600,
                temperature=0.2,
                thinking_budget=self._MIN_THINKING_BUDGET,
            )
            return self._coerce_evaluation_result_from_text(raw_text)
    async def generate_final_report(
        self,
        *,
        session_id: str,
        question_answer_reviews: list[dict[str, Any]],
        all_scores: list[dict[str, Any]],
        all_transcripts: list[dict[str, Any]],
        candidate_profile: dict | None = None,
        job_analysis: dict | None = None,
        session_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if settings.USE_MOCK_LLM:
            return self._mock_final_report()

        prompt = build_final_report_prompt(
            candidate_profile=self._candidate_profile_prompt_context(candidate_profile),
            job_analysis=self._job_analysis_prompt_context(job_analysis),
            session_metadata=self._compact_json_text(
                session_metadata or {"session_id": session_id},
                300,
            ),
            question_answer_reviews=self._compact_json_text(question_answer_reviews, 900),
            all_scores=self._compact_json_text(all_scores, 700),
        )
        try:
            raw = await self._generate_gemini_json(
                prompt=prompt,
                purpose="final report generation",
                model=settings.GEMINI_REPORT_MODEL or settings.GEMINI_MODEL,
                max_output_tokens=900,
                temperature=0.2,
                thinking_budget=self._MIN_THINKING_BUDGET,
            )
            return self._coerce_final_report_result(raw)
        except LLMError:
            raw_text = await self._generate_gemini_text(
                prompt=prompt,
                purpose="final report generation",
                model=settings.GEMINI_REPORT_MODEL or settings.GEMINI_MODEL,
                max_output_tokens=1000,
                temperature=0.2,
                thinking_budget=self._MIN_THINKING_BUDGET,
            )
            return self._coerce_final_report_result_from_text(raw_text)

    async def analyze_resume(self, resume_text: str) -> dict[str, Any]:
        if settings.USE_MOCK_LLM:
            from app.services.resume_parser import ResumeParserService

            return ResumeParserService()._mock_parsed_profile()

        prompt = build_resume_analysis_prompt(resume_text)
        raw_text = await self._generate_gemini_text(
            prompt=prompt,
            purpose="resume analysis",
            max_output_tokens=1800,
            temperature=0.1,
            thinking_budget=self._MIN_THINKING_BUDGET,
        )
        return self._coerce_resume_profile_result_from_text(raw_text)

    async def generate_first_question(
        self,
        candidate_profile: dict | None,
        job_analysis: dict | None,
        interview_type: str,
        difficulty: str,
        prompt_version: str,
    ) -> dict:
        return await self.generate_question(
            mode="first",
            sequence=1,
            interview_type=interview_type,
            difficulty=difficulty,
            question_count=5,
            candidate_profile=candidate_profile,
            job_analysis=job_analysis,
        )

    async def generate_next_question(
        self,
        session_context: dict,
        previous_answers: list[dict],
        sequence: int,
        prompt_version: str,
    ) -> dict:
        return await self.generate_question(
            mode="next",
            sequence=sequence,
            interview_type=session_context.get("interview_type", "sde"),
            difficulty=session_context.get("difficulty", "medium"),
            question_count=session_context.get("question_count", 5),
            target_role=session_context.get("target_role", ""),
            target_company=session_context.get("target_company", ""),
            candidate_profile=session_context.get("candidate_profile"),
            job_analysis=session_context.get("job_analysis"),
            previous_questions=[item.get("question_text", "") for item in previous_answers],
            previous_scores=[item.get("scores", {}) for item in previous_answers],
            previous_answer_transcript=previous_answers[-1].get("transcript", "") if previous_answers else "",
        )

    async def analyze_job_description(
        self,
        job_description: str,
        target_role: str,
        target_company: str,
        prompt_version: str,
    ) -> dict:
        if settings.USE_MOCK_LLM:
            return self._mock_jd_analysis()
        raise LLMError("Real Gemini job description analysis is not implemented yet")

    def _normalize_mock_evaluation(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "scores": {
                "technical_correctness": data.get("technical_score"),
                "clarity": data.get("clarity_score"),
                "depth": data.get("depth_score"),
                "confidence": data.get("confidence_score"),
                "relevance": data.get("relevance_score"),
                "structure": data.get("structure_score"),
                "communication": data.get("communication_score"),
                "conciseness": data.get("conciseness_score"),
                "example_quality": data.get("example_quality_score"),
                "overall": data.get("overall_score"),
            },
            "feedback": {
                "summary": data.get("feedback_text", ""),
                "strengths": data.get("strengths", []),
                "improvements": data.get("improvements", []),
                "ideal_answer_points": [],
                "missed_points": [],
                "suggested_better_answer": "",
            },
            "follow_up": {
                "recommended": bool(data.get("follow_up_question")),
                "reason": "",
                "question_text": data.get("follow_up_question"),
            },
        }

    def _mock_question(self, sequence: int) -> dict:
        questions = [
            "Can you walk me through how you would design a rate-limiting system for a public API?",
            "Your experience includes CI/CD pipelines. How did you handle test flakiness in automated suites?",
            "How would you approach debugging a memory leak in a long-running Python service?",
            "Describe a time you had to make a tradeoff between code quality and delivery speed.",
            "How do you ensure database queries stay performant as data grows?",
        ]
        return {
            "question_text": questions[min(sequence - 1, len(questions) - 1)],
            "question_type": "technical",
            "difficulty": "medium",
            "expected_focus_areas": ["system design", "API design", "scalability"],
            "prompt_version": get_prompt_version("first_question"),
            "audio_url": None,
            "time_limit_seconds": 60,
        }

    def _mock_evaluation(self) -> dict:
        return {
            "technical_score": 7,
            "clarity_score": 8,
            "depth_score": 6,
            "confidence_score": 7,
            "relevance_score": 9,
            "structure_score": 7,
            "communication_score": 8,
            "conciseness_score": 6,
            "example_quality_score": 5,
            "overall_score": 7.0,
            "feedback_text": "Good answer with solid understanding of the concept. Could benefit from a concrete real-world example.",
            "strengths": ["Clear explanation", "Relevant to the question"],
            "improvements": ["Add a specific example from your experience", "Go deeper on trade-offs"],
            "follow_up_question": "Can you give a specific example of when you applied this approach in production?",
        }

    def _mock_final_report(self) -> dict:
        return {
            "overall_score": 7.6,
            "score_breakdown": {
                "technical": 7.8,
                "communication": 7.2,
                "confidence": 7.0,
                "problem_solving": 8.0,
                "role_fit": 7.9,
            },
            "summary": "Strong performance across technical and reasoning areas with room to improve conciseness and structured storytelling.",
            "strengths": [
                "Solid understanding of backend API design principles",
                "Good reasoning about system trade-offs",
                "Consistent relevance to the question asked",
            ],
            "weaknesses": [
                "Answers could benefit from more concrete project examples",
                "STAR-style structure would improve behavioral answers",
            ],
            "recommended_topics": [
                "System design fundamentals",
                "Behavioral STAR method",
                "Database indexing and query optimization",
            ],
        }

    def _mock_jd_analysis(self) -> dict:
        return {
            "role_title": "Software Development Engineer",
            "company": "Example Corp",
            "seniority_level": "mid",
            "must_have_skills": ["Python", "REST APIs", "SQL"],
            "nice_to_have_skills": ["Docker", "AWS"],
            "responsibilities": ["Build backend services", "Write unit tests"],
            "technical_domains": ["backend", "databases"],
            "likely_interview_topics": ["system design", "API design", "testing"],
            "behavioral_traits_expected": ["ownership", "communication"],
            "system_design_relevance": "medium",
            "coding_relevance": "high",
            "testing_relevance": "medium",
            "backend_relevance": "high",
        }
