class InterviewOSError(Exception):
    """Base exception for all InterviewOS service errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class LLMError(InterviewOSError):
    def __init__(self, message: str = "LLM call failed"):
        super().__init__(message, code="LLM_FAILED")


class TranscriptionError(InterviewOSError):
    def __init__(self, message: str = "Transcription failed"):
        super().__init__(message, code="TRANSCRIPTION_FAILED")


class VoiceGenerationError(InterviewOSError):
    def __init__(self, message: str = "Voice generation failed"):
        super().__init__(message, code="VOICE_GENERATION_FAILED")


class ResumeParseError(InterviewOSError):
    def __init__(self, message: str = "Resume parsing failed"):
        super().__init__(message, code="INTERNAL_ERROR")


class QuotaExceededError(InterviewOSError):
    def __init__(self, message: str = "Usage quota exceeded"):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")
