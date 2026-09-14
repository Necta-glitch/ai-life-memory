from openai import OpenAI

from app.ai.rag.schemas import RAGContext, RAGSource, RAGAnswerResponse
from app.ai.rag.context import build_context_from_hybrid_results, format_context_for_llm
from app.search.search_service import SearchService
from app.search.schemas import HybridSearchRequest
from app.core.config import OPENAI_API_KEY, OPENAI_MODEL


class RAGService:
    """
    Service responsible for generating grounded answers using RAG.
    
    Architecture:
        User Question
            ↓
        Hybrid Search
            ↓
        RRF
            ↓
        Relevant Memories
            ↓
        RAG Context Builder
            ↓
        RAGContext
            ↓
        LLM
            ↓
        Grounded Answer + Sources
    """

    def __init__(
        self,
        search_service: SearchService | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.search_service = search_service or SearchService()
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

    def answer_question(
        self,
        db,
        user_id: str,
        query: str,
        top_k: int = 10,
    ) -> RAGAnswerResponse:
        """
        Generate a grounded answer for a user's question using RAG.
        
        Args:
            db: Database session
            user_id: User ID for isolation
            query: User's question
            top_k: Number of results to return
            
        Returns:
            RAGAnswerResponse with grounded answer and sources
            
        Raises:
            ValueError: If query is empty or API key not configured
            openai.APIError: If OpenAI API call fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Execute hybrid search with reranking
        hybrid_request = HybridSearchRequest(query=query.strip(), top_k=top_k)
        hybrid_response = self.search_service.hybrid_search_with_rerank(
            db=db,
            request=hybrid_request,
            user_id=user_id,
        )

        # Handle empty retrieval - don't call LLM
        if not hybrid_response.results:
            return RAGAnswerResponse(
                answer="No tengo memorias suficientes para responder esta pregunta.",
                sources=[],
                query=query.strip(),
                total_sources=0,
            )

        # Build RAG context from hybrid search results
        rag_context = build_context_from_hybrid_results(query.strip(), hybrid_response.results)

        # Format context for LLM
        context_text = format_context_for_llm(rag_context)

        # Build sources from retrieved memories (not from LLM)
        sources = [
            RAGSource(memory_id=item.memory_id, rrf_score=item.rrf_score)
            for item in rag_context.items
        ]

        # Generate answer using LLM
        answer = self._generate_answer(query.strip(), context_text)

        return RAGAnswerResponse(
            answer=answer,
            sources=sources,
            query=query.strip(),
            total_sources=len(sources),
        )

    def _generate_answer(self, query: str, context: str) -> str:
        """
        Generate answer using LLM with grounded context.
        
        Args:
            query: User's question
            context: Formatted RAG context
            
        Returns:
            Grounded answer from LLM
        """
        system_prompt = (
            "Eres un asistente de memoria personal. "
            "Responde a la pregunta del usuario utilizando SOLO la información contenida en las memorias proporcionadas. "
            "No inventes hechos. "
            "No asumas información que no esté presente. "
            "No uses conocimiento externo para llenar vacíos. "
            "Si las memorias no contienen suficiente información para responder la pregunta, "
            "di explícitamente que las memorias disponibles no contienen suficiente información. "
            "Cuando sea posible, identifica qué IDs de memoria apoyan la respuesta."
        )

        user_prompt = f"Pregunta:\n{query}\n\nMemorias recuperadas:\n{context}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content or ""