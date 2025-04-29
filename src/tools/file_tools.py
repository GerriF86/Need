from __future__ import annotations
from src.utils.tool_registry import tool

@tool
def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extracts text from an uploaded file (PDF, DOCX, or TXT) with improved handling:
    - Uses PyMuPDF (fitz) for PDFs.
    - Wraps DOCX bytes in a BytesIO for python-docx to parse reliably.
    - Maintains paragraph separation rather than merging everything into one line.
    - Basic text cleanup to remove excessive whitespace.

    Raises ValueError if file type is not supported.
    """
    import os
    import fitz
    import docx
    from io import BytesIO

    ext = os.path.splitext(filename)[1].lower()
    text = ""

    if ext == ".pdf":
        # Use PyMuPDF to extract text from PDF
        try:
            with fitz.open(stream=file_content, filetype="pdf") as pdf_doc:
                pages_text = []
                for page in pdf_doc:
                    pages_text.append(page.get_text("text"))  # 'text' preserves layout better than 'blocks'
                text = "\n\n".join(pages_text)
        except Exception as e:
            raise ValueError(f"Error reading PDF: {e}")

    elif ext == ".docx":
        # Wrap bytes in a BytesIO for python-docx
        try:
            file_obj = BytesIO(file_content)
            document = docx.Document(file_obj)
            paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
            text = "\n\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {e}")

    elif ext == ".txt":
        # Decode as UTF-8 (ignore errors if not valid UTF-8)
        text = file_content.decode("utf-8", errors="ignore")

    else:
        # Unsupported file type
        raise ValueError(f"Unsupported file type: {ext}")

    # --- Text Cleanup ---
    # 1) Convert all kinds of newlines to standard \n
    # 2) Strip extra trailing spaces on each line
    lines = [line.strip() for line in text.splitlines()]
    # 3) Remove empty lines that might result from repeated \n\n
    lines = [ln for ln in lines if ln]
    # Rejoin with one blank line between paragraphs
    cleaned_text = "\n\n".join(lines)

    return cleaned_text
