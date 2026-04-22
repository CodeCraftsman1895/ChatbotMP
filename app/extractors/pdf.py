import requests
import tempfile
import os
# from pdfminer.high_level import extract_text  <-- Moved inside function

def extract_pdf(link: str) -> dict:
    """
    Extract text from a PDF URL.

    Args:
        link (str): URL of the PDF.

    Returns:
        dict: {"content": str, "error": str or None}
    """
    if not link or not isinstance(link, str):
        return {"content": "", "error": "Invalid or missing link"}
    
    try:
        response = requests.get(link)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        from pdfminer.high_level import extract_text
        text = extract_text(tmp_path)
        os.remove(tmp_path)
        return {"content": text, "error": None}
    except Exception as e:
        return {"content": "", "error": f"PDF extraction failed {link}: {e}"}