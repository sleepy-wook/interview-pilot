"""File upload endpoint for resume and LinkedIn PDFs."""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF file (resume or LinkedIn export).

    Returns the saved file path for use in /interview/start.
    """
    ext = os.path.splitext(file.filename or "file.pdf")[1] or ".pdf"
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return {"filename": file.filename, "path": filepath}
