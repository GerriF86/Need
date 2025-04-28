from openai_agents import tool

@tool
def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract raw text from an uploaded file (PDF, DOCX, or TXT)."""
    import os, fitz, docx
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        # Use PyMuPDF to extract text from PDF
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
    elif ext == ".docx":
        document = docx.Document(file_content)
        text = "\n".join(p.text for p in document.paragraphs)
    elif ext == ".txt":
        text = file_content.decode("utf-8", errors="ignore")
    else:
        raise ValueError("Unsupported file type")
    # Basic cleanup: collapse multiple spaces/newlines
    text = " ".join(text.split())
    return text
