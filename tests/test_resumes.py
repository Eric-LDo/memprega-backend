from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pypdf import PdfReader
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine)
    def database():
        with sessions() as session:
            yield session
    app.dependency_overrides[get_db] = database
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def payload():
    return {"name": "João da Silva", "email": "joao@example.com", "phone": "11999999999", "city": "São Paulo, SP", "title": "Analista", "summary": "Organização & colaboração <com foco> em resultados.", "experiences": [], "education": [], "skills": ["Comunicação", "Excel"], "languages": [{"name": "Inglês", "level": "Avançado"}]}


def test_lifecycle_and_privacy(client, payload):
    response = client.post("/api/v1/resumes", json=payload)
    assert response.status_code == 201
    saved = response.json()
    path = f"/api/v1/resumes/{saved['id']}"
    auth = {"Authorization": f"Bearer {saved['token']}"}
    assert client.get(path).status_code == 401
    for method, suffix in [("get", ""), ("get", "/pdf"), ("delete", "")]:
        assert getattr(client, method)(path + suffix, headers={"Authorization": "Bearer wrong"}).status_code == 404
    assert client.put(path, json=payload, headers={"Authorization": "Bearer wrong"}).status_code == 404
    assert client.get(path, headers=auth).json()["data"]["name"] == payload["name"]
    payload["title"] = "Analista sênior"
    assert client.put(path, json=payload, headers=auth).status_code == 200
    pdf = client.get(path + "/pdf", headers=auth)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.headers["cache-control"] == "no-store"
    text = "".join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages)
    assert "João da Silva" in text
    assert "Analista sênior" in text
    assert "<com foco>" in text
    assert client.delete(path, headers=auth).status_code == 204
    assert client.get(path, headers=auth).status_code == 404


@pytest.mark.parametrize("field,value", [("email", "invalid"), ("name", " "), ("portfolio", "javascript:alert(1)"), ("skills", ["x" * 81])])
def test_invalid_data(client, payload, field, value):
    payload[field] = value
    assert client.post("/api/v1/resumes", json=payload).status_code == 422


def test_dates(client, payload):
    payload["experiences"] = [{"role": "Analista", "company": "Empresa", "start": "2024-03", "end": "2023-01", "current": False}]
    assert client.post("/api/v1/resumes", json=payload).status_code == 422
    payload["experiences"][0]["current"] = True
    payload["experiences"][0]["end"] = ""
    assert client.post("/api/v1/resumes", json=payload).status_code == 201


def test_pdf_pagination(client, payload):
    payload["experiences"] = [{"role": f"Analista {i}", "company": "Empresa", "start": "2020-01", "end": "2024-01", "description": "Atendimento e organização de processos. " * 70} for i in range(8)]
    saved = client.post("/api/v1/resumes", json=payload).json()
    pdf = client.get(f"/api/v1/resumes/{saved['id']}/pdf", headers={"Authorization": f"Bearer {saved['token']}"})
    pages = PdfReader(BytesIO(pdf.content)).pages
    assert len(pages) > 1
    assert "Analista 7" in "".join(p.extract_text() for p in pages)
