from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL


class EmbeddingService:
    """
    Service responsible for generating embeddings using OpenAI's text-embedding-3-small.
    
    Architecture:
        text -> EmbeddingService -> OpenAI -> list[float] (1536 dimensions)
    """

    EMBEDDING_DIMENSIONS = 1536

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_EMBEDDING_MODEL
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is not configured")
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def get_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of 1536 floats representing the embedding
            
        Raises:
            ValueError: If text is empty or embedding dimensions are invalid
            openai.APIError: If OpenAI API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        response = self.client.embeddings.create(
            model=self.model,
            input=text.strip(),
            dimensions=self.EMBEDDING_DIMENSIONS,
        )

        embedding = response.data[0].embedding

        if len(embedding) != self.EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Expected embedding with {self.EMBEDDING_DIMENSIONS} dimensions, "
                f"got {len(embedding)}"
            )

        return embedding