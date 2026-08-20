import logging
from sqlalchemy.orm import Session
from app.config import settings
from app.db.models import DocumentChunk, Document
from app.services.embedding_service import get_text_embedding

logger = logging.getLogger("retrieval_service")


def compute_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Computes cosine similarity between two float vectors.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def search_relevant_chunks(
    db: Session,
    query: str,
    document_id: int | None = None,
    top_k: int = settings.RAG_TOP_K,
    user_id: str = "default_user"
) -> list[dict]:
    """
    Retrieves the Top-K most relevant document chunks for a given query using vector similarity.
    
    Args:
        db: SQLAlchemy database session.
        query: Search query text (e.g. decision problem).
        document_id: Optional document ID filter.
        top_k: Number of relevant chunks to retrieve (default: settings.RAG_TOP_K).
        user_id: User ownership isolation key.
        
    Returns:
        List of dicts with 'content', 'page_number', 'filename', 'document_id', and 'chunk_index'.
    """
    if not query or not query.strip():
        return []

    # 1. Generate vector embedding for the query
    query_vector = get_text_embedding(query)

    is_postgres = "postgresql" in str(db.bind.url)

    if is_postgres:
        try:
            # Native pgvector cosine distance search (<=>)
            query_obj = db.query(DocumentChunk, Document.filename)\
                .join(Document, DocumentChunk.document_id == Document.id)

            if document_id:
                query_obj = query_obj.filter(DocumentChunk.document_id == document_id)

            if user_id:
                query_obj = query_obj.filter(Document.user_id == user_id)

            # Order by cosine distance ascending
            results = query_obj.order_by(DocumentChunk.embedding.cosine_distance(query_vector))\
                .limit(top_k).all()

            retrieved = []
            for chunk, filename in results:
                retrieved.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "filename": filename,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                })
            return retrieved
        except Exception as e:
            logger.warning(f"PostgreSQL vector search query failed, falling back to in-memory matching: {e}")

    # Fallback in-memory vector search for non-postgres or fallback environments
    query_obj = db.query(DocumentChunk, Document.filename)\
        .join(Document, DocumentChunk.document_id == Document.id)

    if document_id:
        query_obj = query_obj.filter(DocumentChunk.document_id == document_id)

    if user_id:
        query_obj = query_obj.filter(Document.user_id == user_id)

    all_chunks = query_obj.all()
    scored_chunks = []

    for chunk, filename in all_chunks:
        if chunk.embedding:
            # Parse embedding if stored as list
            chunk_vec = chunk.embedding
            if isinstance(chunk_vec, list):
                sim = compute_cosine_similarity(query_vector, chunk_vec)
                scored_chunks.append((sim, chunk, filename))

    # Sort by similarity descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_results = scored_chunks[:top_k]

    return [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "filename": filename,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "score": score
        }
        for score, chunk, filename in top_results
    ]
