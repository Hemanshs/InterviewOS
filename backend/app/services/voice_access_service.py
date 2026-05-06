from __future__ import annotations

from typing import Any


def get_voice_access_for_question(user: Any, question_sequence: int) -> dict:
    plan = str(getattr(getattr(user, "plan", None), "value", getattr(user, "plan", "free")))

    if plan == "pro":
        return {
            "voice_tier": "premium",
            "provider": "elevenlabs",
            "premium_allowed": True,
            "preview_used": False,
            "label": "Premium AI Voice",
            "upgrade_required": False,
        }

    if plan == "free" and question_sequence == 1:
        return {
            "voice_tier": "premium_preview",
            "provider": "elevenlabs",
            "premium_allowed": True,
            "preview_used": True,
            "label": "Premium Voice Preview",
            "upgrade_required": False,
        }

    return {
        "voice_tier": "standard",
        "provider": "browser",
        "premium_allowed": False,
        "preview_used": True,
        "label": "Standard Voice",
        "upgrade_required": True,
    }
