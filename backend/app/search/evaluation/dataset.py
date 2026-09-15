from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EvaluationCase:
    """A single evaluation case for reranker evaluation."""
    query: str
    relevant_memory_ids: set[int]
    description: str = ""


# Deterministic evaluation dataset
# Memory IDs and their content summaries for reference:
# 1: "Hoy aprendí cómo funciona Reciprocal Rank Fusion..." (RRF + semantic + keyword)
# 2: "Hoy aprendí cómo funciona Reciprocal Rank Fusion..." (RRF + search ranking + semantic + keyword)
# 3: "Estudié diferentes estrategias para combinar los resultados..." (search engines + ranking strategies)
# 4: "Aprendí cómo funcionan los embeddings y cómo la similitud coseno..." (embeddings + cosine similarity)
# 5: "Implementé una búsqueda semántica utilizando PostgreSQL, pgvector..." (semantic search + PostgreSQL + pgvector)
# 6: "Estudié búsqueda por palabras clave y cómo encontrar documentos..." (keyword searching + document retrieval)
# 7: "Aprendí sobre RRF (Reciprocal Rank Fusion) para combinar rankings..." (RRF for hybrid search)

EVALUATION_CASES = [
    EvaluationCase(
        query="¿Qué aprendí sobre Reciprocal Rank Fusion?",
        relevant_memory_ids={1, 2},
        description="Direct query about RRF - memories 1 and 2 explicitly discuss RRF",
    ),
    EvaluationCase(
        query="¿Qué es RRF?",
        relevant_memory_ids={1, 2, 7},
        description="Short form query for RRF - memories 1, 2, and 7 mention RRF",
    ),
    EvaluationCase(
        query="¿Cómo funciona la búsqueda semántica?",
        relevant_memory_ids={4, 5},
        description="Query about semantic search - memories 4 and 5 discuss embeddings and semantic search",
    ),
    EvaluationCase(
        query="búsqueda por palabras clave",
        relevant_memory_ids={6, 1, 2},
        description="Keyword search query - memories 1, 2, and 6 discuss keyword search",
    ),
    EvaluationCase(
        query="estrategias para combinar rankings",
        relevant_memory_ids={3, 1, 2},
        description="Query about ranking combination strategies - memories 1, 2, and 3",
    ),
    EvaluationCase(
        query="similitud coseno y embeddings",
        relevant_memory_ids={4, 5},
        description="Query about cosine similarity and embeddings - memories 4 and 5",
    ),
    EvaluationCase(
        query="pgvector y PostgreSQL",
        relevant_memory_ids={5},
        description="Query about pgvector/PostgreSQL - memory 5 explicitly mentions both",
    ),
    EvaluationCase(
        query="física cuántica",
        relevant_memory_ids=set(),
        description="Unrelated query - no memories about quantum physics",
    ),
    EvaluationCase(
        query="aprendí sobre búsqueda híbrida",
        relevant_memory_ids={1, 2, 7},
        description="Query about hybrid search - memories 1, 2, and 7 discuss RRF for hybrid search",
    ),
    EvaluationCase(
        query="qué es el ranking de búsqueda",
        relevant_memory_ids={3, 1, 2},
        description="Query about search ranking - memories 1, 2, and 3 discuss ranking",
    ),
]


def get_evaluation_cases() -> list:
    """Return the list of evaluation cases."""
    return EVALUATION_CASES