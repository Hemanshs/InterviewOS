import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_resume_upload_pdf_success(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_LLM", True)
    minimal_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n%%EOF"
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/resume/upload",
            files={"file": ("test_resume.pdf", minimal_pdf, "application/pdf")},
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "resume_id" in data["data"]
    assert data["data"]["file_name"] == "test_resume.pdf"


@pytest.mark.asyncio
async def test_resume_upload_rejects_non_pdf(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_LLM", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/resume/upload",
            files={
                "file": (
                    "resume.docx",
                    b"fake content",
                    "application/vnd.openxmlformats",
                )
            },
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


@pytest.mark.asyncio
async def test_resume_upload_rejects_oversized_file(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_LLM", True)
    large_content = b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/resume/upload",
            files={"file": ("big.pdf", large_content, "application/pdf")},
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


@pytest.mark.asyncio
async def test_get_latest_resume_after_upload(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_LLM", True)
    minimal_pdf = b"%PDF-1.4\n%%EOF"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/resume/upload",
            files={"file": ("cv.pdf", minimal_pdf, "application/pdf")},
            headers={"Authorization": "Bearer mock_token"},
        )
        response = await client.get(
            "/api/resume/latest",
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["file_name"] == "cv.pdf"
