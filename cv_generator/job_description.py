"""Extract job-description text from supported in-memory uploads."""

from io import BytesIO
from pathlib import Path

from docx import Document

from .config import MAX_JOB_DESCRIPTION_CHARS


SUPPORTED_JOB_DESCRIPTION_TYPES = ("txt", "md", "docx", "pdf")


def extract_job_description(filename: str, content: bytes) -> str:
    """Return readable text from a TXT, Markdown, DOCX, or PDF upload."""
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in SUPPORTED_JOB_DESCRIPTION_TYPES:
        supported = ", ".join(value.upper() for value in SUPPORTED_JOB_DESCRIPTION_TYPES)
        raise ValueError(f"Unsupported job description file. Use {supported}.")

    try:
        if extension in {"txt", "md"}:
            text = content.decode("utf-8-sig")
        elif extension == "docx":
            document = Document(BytesIO(content))
            text = "\n".join(
                paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()
            )
        else:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except (UnicodeDecodeError, ValueError, KeyError) as error:
        raise ValueError("The job description file could not be read.") from error
    except Exception as error:
        raise ValueError(f"The {extension.upper()} job description could not be read.") from error

    text = text.strip()
    if not text:
        raise ValueError("The job description file does not contain readable text.")
    if len(text) > MAX_JOB_DESCRIPTION_CHARS:
        raise ValueError(
            f"Job descriptions must be {MAX_JOB_DESCRIPTION_CHARS:,} characters or fewer."
        )
    return text
