import logging
from google import genai
from app.config import settings

logger = logging.getLogger("embedding_service")

# Official embedding model for Google GenAI SDK
EMBEDDING_MODEL = "models/gemini-embedding-001"


def get_text_embedding(text: str) -> list[float]:
    """
    Generates a 3072-dimensional vector embedding for a text string using Google's Gemini SDK.
    
    Args:
        text: Text string to embed.
        
    Returns:
        List of 3072 floats representing the vector embedding.
        
    Raises:
        ValueError: If API key is unconfigured.
        RuntimeError: If embedding generation fails.
    """
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "" or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is not configured in backend environment.")

    if not text or not text.strip():
        # Return zero vector if text is empty
        return [0.0] * 3072

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )

        if response and response.embeddings and len(response.embeddings) > 0:
            return response.embeddings[0].values
        
        raise RuntimeError("No embedding values returned from Gemini API.")
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise RuntimeError(f"Embedding service error: {str(e)}")


def batch_get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generates embeddings for a batch of text strings.
    """
    return [get_text_embedding(text) for text in texts]
