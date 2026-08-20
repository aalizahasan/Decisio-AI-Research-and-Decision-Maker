def chunk_page_texts(
    pages_data: list[dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> list[dict]:
    """
    Deterministically splits extracted PDF page texts into manageable chunks.
    
    Args:
        pages_data: List of dicts with 'page_number' and 'text'.
        chunk_size: Maximum character length per chunk (default: 1000).
        chunk_overlap: Character overlap between consecutive chunks (default: 200).
        
    Returns:
        List of dicts containing 'chunk_index', 'content', and 'page_number'.
    """
    chunks = []
    chunk_counter = 0

    for page_item in pages_data:
        page_num = page_item["page_number"]
        page_text = page_item["text"]

        if not page_text:
            continue

        # If page text fits within one chunk window
        if len(page_text) <= chunk_size:
            chunks.append({
                "chunk_index": chunk_counter,
                "content": page_text,
                "page_number": page_num
            })
            chunk_counter += 1
            continue

        # Sliding window chunking over page text
        start = 0
        text_length = len(page_text)

        while start < text_length:
            end = start + chunk_size
            chunk_str = page_text[start:end].strip()

            if chunk_str:
                chunks.append({
                    "chunk_index": chunk_counter,
                    "content": chunk_str,
                    "page_number": page_num
                })
                chunk_counter += 1

            start += (chunk_size - chunk_overlap)

    return chunks
