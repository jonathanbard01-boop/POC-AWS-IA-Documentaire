from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_list_get_result_and_analyze_flow():
    upload = client.post(
        "/documents/upload",
        files={
            "file": (
                "sample.txt",
                b"facture creche enfant garde periode montant accueil",
                "text/plain",
            )
        },
    )
    assert upload.status_code == 200
    payload = upload.json()
    assert payload["filename"] == "sample.txt"
    assert payload["status"] == "uploaded"
    document_id = payload["document_id"]

    listing = client.get("/documents")
    assert listing.status_code == 200
    assert any(doc["document_id"] == document_id for doc in listing.json()["documents"])

    detail = client.get(f"/documents/{document_id}")
    assert detail.status_code == 200
    assert detail.json()["filename"] == "sample.txt"

    result = client.get(f"/documents/{document_id}/result")
    assert result.status_code == 200
    assert result.json()["result_available"] is False
    assert result.json()["result"] is None

    analysis = client.post(f"/documents/{document_id}/analyze")
    assert analysis.status_code == 200
    analysis_payload = analysis.json()
    assert analysis_payload["result_available"] is True
    assert analysis_payload["result"]["pages"][0]["ocr"]["word_count"] > 0
    assert "bm25_result" in analysis_payload["result"]["pages"][0]
    assert "decision" in analysis_payload["result"]["pages"][0]

    result_after_analysis = client.get(f"/documents/{document_id}/result")
    assert result_after_analysis.status_code == 200
    assert result_after_analysis.json()["result_available"] is True


def test_unknown_document_returns_404():
    response = client.get("/documents/unknown")
    assert response.status_code == 404


def test_unknown_document_analysis_returns_404():
    response = client.post("/documents/unknown/analyze")
    assert response.status_code == 404
