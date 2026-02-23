"""Document reader -- hybrid PDF processing.

- Resume/Portfolio PDF -> pdf2image + Claude Vision (complex layouts)
- LinkedIn PDF -> pdfplumber text extraction (clean, fast, cheap)
"""

from __future__ import annotations

import base64
import io
import json
from typing import Any

import pdfplumber
from PIL import Image

from core.bedrock_client import BedrockClient
from tools.registry import register_tool


def _pdf_to_images(pdf_bytes: bytes, dpi: int = 150) -> list[str]:
    """Convert PDF bytes to base64-encoded PNG images using pdf2image.

    Falls back to pypdfium2 if poppler is not installed (Windows).
    """
    try:
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        result = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            result.append(base64.standard_b64encode(buf.getvalue()).decode())
        return result
    except Exception:
        # Fallback: pypdfium2 (no poppler needed)
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(pdf_bytes)
        result = []
        for page in pdf:
            bitmap = page.render(scale=dpi / 72)
            img = bitmap.to_pil()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            result.append(base64.standard_b64encode(buf.getvalue()).decode())
        return result


def _vision_extract(image_b64_list: list[str], document_type: str) -> dict:
    """Use Claude Vision to extract structured content from PDF page images."""
    llm = BedrockClient(model="haiku")

    prompts = {
        "resume": (
            "You are a resume parser using Vision. Analyze this document image and extract:\n"
            "- name, contact info\n"
            "- summary/objective\n"
            "- work_experience: list of {company, title, dates, description}\n"
            "- education: list of {school, degree, dates}\n"
            "- skills: list of technical and soft skills\n"
            "- projects: list of {name, description, technologies}\n"
            "- certifications: list\n"
            "- languages: list\n"
            "Return ONLY valid JSON."
        ),
        "other": (
            "You are a document analyzer using Vision. Extract all structured content "
            "from this document image. Return ONLY valid JSON with appropriate keys."
        ),
    }

    # Build multimodal content
    content: list[dict[str, Any]] = []
    for img_b64 in image_b64_list:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": img_b64},
        })
    content.append({
        "type": "text",
        "text": "Extract structured data from the document above.",
    })

    system = prompts.get(document_type, prompts["other"])
    result = llm.invoke(
        messages=[{"role": "user", "content": content}],
        system=system,
        max_tokens=4096,
        temperature=0.1,
    )

    text = ""
    for block in result.get("content", []):
        if block["type"] == "text":
            text += block["text"]

    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"raw_text": text}


def _pdfplumber_extract(pdf_bytes: bytes) -> dict:
    """Use pdfplumber for clean text extraction (LinkedIn PDFs)."""
    llm = BedrockClient(model="haiku")

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        pages_text = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    full_text = "\n\n---PAGE BREAK---\n\n".join(pages_text)

    system = (
        "You are a LinkedIn profile parser. The text below was extracted from a LinkedIn PDF. "
        "Extract structured data. Return ONLY valid JSON."
    )
    prompt = f"""Parse this LinkedIn profile text:

{full_text}

Return JSON with:
- "name": full name
- "headline": LinkedIn headline
- "summary": about section
- "experience": list of {{"company": "", "title": "", "dates": "", "description": ""}}
- "education": list of {{"school": "", "degree": "", "dates": ""}}
- "skills": list of skills
- "certifications": list
- "languages": list
- "recommendations": list of {{"recommender": "", "text": ""}}
- "volunteer": list (if any)"""

    text, _ = llm.converse(
        messages=[{"role": "user", "content": prompt}],
        system=system,
        max_tokens=4096,
        temperature=0.1,
    )

    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"raw_text": text}


@register_tool(
    name="document_reader",
    description=(
        "Read a PDF document and extract structured content. "
        "LinkedIn PDFs use fast text extraction; Resume/other PDFs use Vision for complex layouts."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "S3 key or local path to PDF"},
            "document_type": {
                "type": "string",
                "enum": ["resume", "linkedin", "other"],
                "description": "Type of document for optimized extraction",
            },
        },
        "required": ["file_path", "document_type"],
    },
)
def document_reader(file_path: str, document_type: str) -> dict:
    """Hybrid document reader.

    - linkedin: pdfplumber (text extraction) -> LLM structuring
    - resume/other: pdf2image -> Claude Vision
    """
    # Load PDF bytes (from S3 or local)
    if file_path.startswith("sessions/") or file_path.startswith("s3://"):
        from core.s3_client import download_file

        s3_key = file_path.replace("s3://", "").split("/", 1)[-1] if "s3://" in file_path else file_path
        pdf_bytes = download_file(s3_key)
    else:
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

    if document_type == "linkedin":
        result = _pdfplumber_extract(pdf_bytes)
    else:
        images = _pdf_to_images(pdf_bytes)
        result = _vision_extract(images, document_type)

    result["_meta"] = {
        "document_type": document_type,
        "extraction_method": "pdfplumber" if document_type == "linkedin" else "vision",
    }
    return result
