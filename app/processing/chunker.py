# from langchain_text_splitters import RecursiveCharacterTextSplitter  <-- Moved inside function

def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping semantic chunks for embedding/search."""
    if text is None:
        return []
    text = text.strip()
    if not text:
        return []

    # Semantic chunking using RecursiveCharacterTextSplitter
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = text_splitter.split_text(text)
    return chunks
