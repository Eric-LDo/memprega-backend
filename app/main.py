import hashlib
import secrets
from typing import Annotated
from uuid import UUID
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import Resume
from app.schemas import ResumeData
from app.pdf import render_pdf

app = FastAPI(title="Me Emprega · Currículos", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type", "Authorization"])
DB = Annotated[Session, Depends(get_db)]
auth = HTTPBearer(auto_error=False)


@app.middleware("http")
async def private_responses(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/health")
def health(db: DB):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


def owned_resume(resume_id: UUID, db: DB,
                 credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(auth)]):
    if not credentials:
        raise HTTPException(401, "Credencial necessária.")
    resume = db.get(Resume, str(resume_id))
    digest = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    if not resume or not secrets.compare_digest(resume.token_hash, digest):
        raise HTTPException(404, "Currículo não encontrado.")
    return resume


Owned = Annotated[Resume, Depends(owned_resume)]


@app.post("/api/v1/resumes", status_code=201)
def create_resume(data: ResumeData, db: DB):
    token = secrets.token_urlsafe(32)
    resume = Resume(data=data.model_dump(mode="json"), token_hash=hashlib.sha256(token.encode()).hexdigest())
    db.add(resume)
    db.commit()
    return {"id": resume.id, "token": token, "data": resume.data}


@app.get("/api/v1/resumes/{resume_id}")
def read_resume(resume: Owned):
    return {"id": resume.id, "data": resume.data}


@app.put("/api/v1/resumes/{resume_id}")
def update_resume(data: ResumeData, resume: Owned, db: DB):
    resume.data = data.model_dump(mode="json")
    db.commit()
    return {"id": resume.id, "data": resume.data}


@app.delete("/api/v1/resumes/{resume_id}", status_code=204)
def delete_resume(resume: Owned, db: DB):
    db.delete(resume)
    db.commit()
    return Response(status_code=204)


@app.get("/api/v1/resumes/{resume_id}/pdf")
def download_pdf(resume: Owned):
    return Response(render_pdf(ResumeData.model_validate(resume.data)), media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="curriculo.pdf"'})
