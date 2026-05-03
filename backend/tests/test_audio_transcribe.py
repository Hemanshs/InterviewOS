import os
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app
from app.services.speech_service import SpeechService
from app.utils.audio_utils import count_words, detect_filler_words


def build_form_data(
    session_id: str | None = None,
    question_id: str | None = None,
    duration_seconds: int | float | None = 30,
    language: str = "en",
):
    data = {}
    if session_id is not None:
        data["session_id"] = session_id
    if question_id is not None:
        data["question_id"] = question_id
    if duration_seconds is not None:
        data["duration_seconds"] = str(duration_seconds)
    data["language"] = language
    return data


@pytest.mark.asyncio
async def test_successful_mock_transcription():
    transport = ASGITransport(app=app)
    session_id = str(uuid.uuid4())
    question_id = str(uuid.uuid4())

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=session_id, question_id=question_id, duration_seconds=30),
            files={"audio_file": ("answer.webm", b"fake-webm-data", "audio/webm")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert isinstance(data["transcript"], str) and data["transcript"]
    assert data["word_count"] > 0
    assert data["raw_audio_deleted"] is True
    assert "count" in data["filler_words"]
    assert "examples" in data["filler_words"]
    assert "transcription_ms" in data["latency"]


@pytest.mark.asyncio
async def test_real_mode_without_api_key_returns_clear_error(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_STT", False)
    monkeypatch.setattr(settings, "STT_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=str(uuid.uuid4()), question_id=str(uuid.uuid4())),
            files={"audio_file": ("answer.webm", b"fake-webm-data", "audio/webm")},
        )

    assert response.status_code == 500
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "TRANSCRIPTION_FAILED"
    assert (
        payload["error"]["message"]
        == "GEMINI_API_KEY is required when USE_MOCK_STT=false and STT_PROVIDER=gemini"
    )


@pytest.mark.asyncio
async def test_invalid_mime_type():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=str(uuid.uuid4()), question_id=str(uuid.uuid4())),
            files={"audio_file": ("answer.ogg", b"fake-ogg-data", "audio/ogg")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert response.json()["error"]["details"]["received_content_type"] == "audio/ogg"


@pytest.mark.asyncio
async def test_audio_mp4_is_accepted():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=str(uuid.uuid4()), question_id=str(uuid.uuid4())),
            files={"audio_file": ("answer.m4a", b"fake-mp4-data", "audio/mp4")},
        )

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_audio_aac_is_accepted():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=str(uuid.uuid4()), question_id=str(uuid.uuid4())),
            files={"audio_file": ("answer.aac", b"fake-aac-data", "audio/aac")},
        )

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_audio_x_m4a_is_accepted():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=str(uuid.uuid4()), question_id=str(uuid.uuid4())),
            files={"audio_file": ("answer.m4a", b"fake-m4a-data", "audio/x-m4a")},
        )

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_audio_mp4_with_codecs_is_accepted():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=str(uuid.uuid4()), question_id=str(uuid.uuid4())),
            files={
                "audio_file": (
                    "answer.m4a",
                    b"fake-mp4-data",
                    "audio/mp4;codecs=mp4a.40.2",
                )
            },
        )

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_video_mp4_with_codecs_is_accepted():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=str(uuid.uuid4()), question_id=str(uuid.uuid4())),
            files={
                "audio_file": (
                    "answer.mp4",
                    b"fake-video-mp4-data",
                    "video/mp4;codecs=mp4a.40.2",
                )
            },
        )

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_text_plain_is_rejected_with_received_content_type():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=str(uuid.uuid4()), question_id=str(uuid.uuid4())),
            files={"audio_file": ("answer.txt", b"not-audio", "text/plain")},
        )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert payload["error"]["details"]["received_content_type"] == "text/plain"


@pytest.mark.asyncio
async def test_file_too_large():
    transport = ASGITransport(app=app)
    oversized = b"a" * (11 * 1024 * 1024)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=str(uuid.uuid4()), question_id=str(uuid.uuid4())),
            files={"audio_file": ("answer.webm", oversized, "audio/webm")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


@pytest.mark.asyncio
async def test_duration_over_sixty_seconds():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(
                session_id=str(uuid.uuid4()),
                question_id=str(uuid.uuid4()),
                duration_seconds=95,
            ),
            files={"audio_file": ("answer.webm", b"fake-webm-data", "audio/webm")},
        )

    payload = response.json()
    assert response.status_code == 400
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert payload["error"]["details"]["max_duration_seconds"] == 60
    assert payload["error"]["details"]["received_duration_seconds"] == 95


@pytest.mark.asyncio
async def test_missing_audio_file():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=str(uuid.uuid4()), question_id=str(uuid.uuid4())),
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_missing_session_id():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id=None, question_id=str(uuid.uuid4())),
            files={"audio_file": ("answer.webm", b"fake-webm-data", "audio/webm")},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_uuid_format():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/audio/transcribe",
            data=build_form_data(session_id="not-a-uuid", question_id=str(uuid.uuid4())),
            files={"audio_file": ("answer.webm", b"fake-webm-data", "audio/webm")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_word_count_and_filler_word_detection_units():
    assert count_words("hello world test") == 3
    fillers = detect_filler_words("um I think like this is basically correct")
    assert fillers["count"] >= 2
    assert isinstance(fillers["examples"], list)


@pytest.mark.asyncio
async def test_real_transcription_attempts_temp_file_cleanup(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(settings, "USE_MOCK_STT", False)
    monkeypatch.setattr(settings, "STT_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")

    service = SpeechService()
    temp_file = tmp_path / "answer.m4a"
    cleanup_calls: list[str] = []
    deleted_remote_files: list[str] = []

    class DummyTempFile:
        def __init__(self, path: Path):
            self.name = str(path)
            self._handle = open(path, "wb")

        def write(self, data: bytes) -> int:
            return self._handle.write(data)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self._handle.close()
            return False

    class FakeUploadedFile:
        name = "files/fake-audio"

    class FakeFiles:
        async def upload(self, *, file, config=None):
            assert file == str(temp_file)
            return FakeUploadedFile()

        async def delete(self, *, name, config=None):
            deleted_remote_files.append(name)

    class FakeModels:
        async def generate_content(self, **kwargs):
            return type("FakeResponse", (), {"text": "real transcript from gemini"})()

    class FakeAsyncClient:
        def __init__(self):
            self.files = FakeFiles()
            self.models = FakeModels()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeClient:
        @property
        def aio(self):
            return FakeAsyncClient()

    monkeypatch.setattr(service, "_build_gemini_client", lambda: FakeClient())
    monkeypatch.setattr(
        service,
        "_get_gemini_types",
        lambda: SimpleNamespace(
            UploadFileConfig=lambda **kwargs: kwargs,
            GenerateContentConfig=lambda **kwargs: kwargs,
        ),
    )

    monkeypatch.setattr(
        tempfile,
        "NamedTemporaryFile",
        lambda suffix, delete: DummyTempFile(temp_file),
    )

    original_unlink = os.unlink

    def tracking_unlink(path: str):
        cleanup_calls.append(path)
        original_unlink(path)

    monkeypatch.setattr(os, "unlink", tracking_unlink)

    transcript = await service._real_transcribe(b"fake-audio-bytes", "en", "audio/mp4")

    assert transcript == "real transcript from gemini"
    assert cleanup_calls == [str(temp_file)]
    assert deleted_remote_files == ["files/fake-audio"]
    assert not temp_file.exists()
