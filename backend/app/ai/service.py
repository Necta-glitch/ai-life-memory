from openai import OpenAI

from app.ai.schemas import AIProcessingResult
from app.core.config import OPENAI_API_KEY, OPENAI_MODEL


class AIService:
    """
    Service responsible for processing memory content through OpenAI Structured Outputs.
    
    Architecture:
        MemoryService -> AIService -> OpenAI -> AIProcessingResult
    
    The OpenAI Structured Outputs feature guarantees that the response
    conforms to the provided Pydantic model schema, eliminating the need
    for fragile JSON parsing and manual validation.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is not configured")
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def process_memory(self, content: str) -> AIProcessingResult:
        """
        Process memory content through OpenAI and return validated structured result.
        
        Args:
            content: The memory content to process
            
        Returns:
            AIProcessingResult with summary, topics, and entities
            
        Raises:
            ValueError: If API key is not configured
            openai.APIError: If OpenAI API call fails
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        system_prompt = (
            "You are an AI that processes personal memories. "
            "Extract a concise summary, key topics, and named entities from the content. "
            "Return the result in the specified structured format."
        )

        user_prompt = f"Process this memory:\n\n{content}"

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=AIProcessingResult,
            temperature=0.3,
        )

        return response.choices[0].message.parsed