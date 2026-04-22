def extract_note(content) -> dict:
    """
    Extract text from a note content.

    Args:
        content (dict): Note document.

    Returns:
        dict: {"content": str, "error": str or None}
    """
    body = content.get("body", "")
    if not body:
        return {"content": "", "error": "Note body is empty"}
    return {"content": body, "error": None}