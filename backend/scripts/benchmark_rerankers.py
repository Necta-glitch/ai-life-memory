#!/usr/bin/env python3
"""
Reranker Benchmark Script

Compares three ranking strategies using real PostgreSQL database:
1. RRF (baseline - no reranker)
2. EmbeddingReranker (cosine similarity with embeddings)
3. CrossEncoderReranker (Cross-Encoder relevance scoring)

Run with: PYTHONPATH=. python scripts/benchmark_rerankers.py
"""

import sys
import os
import time
import math
from typing import Optional, Callable

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
from app.search.evaluation.dataset import get_evaluation_cases
from app.search.evaluation.metrics import (
    precision_at_k, recall_at_k, mrr, ndcg_at_k, evaluate_ranking, RankingMetrics
)
from app.search.search_service import SearchService
from app.ai.embedding_service import EmbeddingService
from app.search.reranker import CrossEncoderReranker, EmbeddingReranker, NoOpReranker
from app.search.schemas import HybridSearchRequest, HybridSearchResult
from app.search.search_service import SearchService
from app.ai.embedding_service import EmbeddingService
from app.ai.embeddings import build_embedding_input
from app.core.config import RERANKER_TYPE, RERANKER_MODEL
from app.db.database import get_db, engine
from app.models.memory import Memory
from sqlalchemy.orm import Session
from sqlalchemy import select, func


# Configuration
K = 5  # top_k for evaluation
CANDIDATE_POOL_SIZE = 50


def get_rrf_ranking(search_service: SearchService, db: Session, query: str, user_id: str, top_k: int) -> list[int]:
    """Get RRF ranking (no reranker)."""
    original_reranker = search_service.reranker
    search_service.reranker = NoOpReranker()
    
    request = HybridSearchRequest(query=query, top_k=top_k)
    response = search_service.hybrid_search_with_rerank(
        db=db,
        request=request,
        user_id=user_id
    )
    
    search_service.reranker = original_reranker
    return [r.id for r in response.results]


def get_embedding_reranked_ranking(
    search_service: SearchService,
    db: Session,
    query: str,
    user_id: str,
    top_k: int
) -> list[int]:
    """Get ranking from EmbeddingReranker."""
    original_reranker = search_service.reranker
    search_service.reranker = EmbeddingReranker(search_service.embedding_service)
    
    request = HybridSearchRequest(query=query, top_k=top_k)
    response = search_service.hybrid_search_with_rerank(
        db=db,
        request=request,
        user_id=user_id
    )
    
    search_service.reranker = original_reranker
    return [r.id for r in response.results]


def get_cross_encoder_ranking(
    search_service: SearchService,
    db: Session,
    query: str,
    user_id: str,
    top_k: int
) -> list[int]:
    """Get ranking from CrossEncoderReranker."""
    original_reranker = search_service.reranker
    search_service.reranker = CrossEncoderReranker()
    
    request = HybridSearchRequest(query=query, top_k=top_k)
    response = search_service.hybrid_search_with_rerank(
        db=db,
        request=request,
        user_id=user_id
    )
    
    search_service.reranker = original_reranker
    return [r.id for r in response.results]


def run_benchmark():
    """Run the full benchmark."""
    print("=" * 80)
    print("RERANKER BENCHMARK: RRF vs EmbeddingReranker vs CrossEncoderReranker")
    print("=" * 80)
    print()
    
    # Get evaluation cases
    cases = get_evaluation_cases()
    print(f"Loaded {len(cases)} evaluation cases")
    print()
    
    # Check database
    with Session(engine) as db:
        total_memories = db.execute(select(func.count(Memory.id))).scalar()
        memories_with_embeddings = db.execute(
            select(func.count(Memory.id)).where(Memory.embedding.is_not(None))
        ).scalar()
        print(f"Total memories: {total_memories}")
        print(f"Memories with embeddings: {memories_with_embeddings}")
        print()
    
    if not cases:
        print("No evaluation cases found!")
        return
    
    # Initialize services
    embedding_service = EmbeddingService()
    search_service = SearchService(embedding_service=embedding_service)
    
    # Check if we can load CrossEncoder
    print("Loading CrossEncoder model...")
    load_start = time.perf_counter()
    cross_encoder = CrossEncoderReranker()
    load_time = time.perf_counter() - load_start
    print(f"Model loaded in {load_time*1000:.1f} ms")
    print(f"Model: {cross_encoder.model_name}")
    print(f"Device: {cross_encoder._device or 'auto'}")
    print()
    
    # Warm up the model
    print("Warming up CrossEncoder...")
    warm_start = time.perf_counter()
    _ = cross_encoder.rerank("warm up query", [
        type('Result', (), {
            'id': 1, 'content': 'test content', 'summary': 'test', 
            'topics': [], 'entities': [], 'source': 'text',
            'created_at': '2024-01-01T00:00:00', 'occurred_at': None,
            'rrf_score': 0.0
        })()
    ], 1)
    warm_time = time.perf_counter() - warm_start
    print(f"Warm-up inference: {warm_time*1000:.1f} ms")
    print()
    
    # Run benchmarks for each strategy
    strategies = [
        ("RRF", lambda q, db, uid, k: get_rrf_ranking(search_service, db, q, uid, k)),
        ("EmbeddingReranker", lambda q, db, uid, k: get_embedding_reranked_ranking(search_service, db, q, uid, k)),
        ("CrossEncoderReranker", lambda q, db, uid, k: get_cross_encoder_ranking(search_service, db, q, uid, k)),
    ]
    
    K = 5
    CANDIDATE_POOL = 50
    
    results = {}
    
    for name, ranker_fn in strategies:
        print(f"\n--- Benchmarking {name} ---")
        start_time = time.perf_counter()
        
        query_metrics = []
        
        for case in get_evaluation_cases():
            if not case.relevant_memory_ids:
                continue  # Skip queries with no relevant memories
                
            with Session(engine) as db:
                try:
                    ranking = ranker_fn(case.query, db, "dev-user", K)
                    
                    # Evaluate ranking
                    metrics = evaluate_ranking(
                        ranking=ranking[:K],
                        relevant_ids=case.relevant_memory_ids,
                        k=K
                    )
                    
                    query_metrics.append({
                        'query': case.query,
                        'metrics': metrics,
                        'ranking': ranking
                    })
                except Exception as e:
                    print(f"  Error on query '{case.query}': {e}")
        
        elapsed = time.perf_counter() - start_time
        
        # Aggregate metrics
        if query_metrics:
            avg_precision = sum(m['metrics'].precision_at_k for m in query_metrics) / len(query_metrics)
            avg_recall = sum(m['metrics'].recall_at_k for m in query_metrics) / len(query_metrics)
            avg_mrr = sum(m['metrics'].mrr for m in query_metrics) / len(query_metrics)
            avg_ndcg = sum(m['metrics'].ndcg_at_k for m in query_metrics) / len(query_metrics)
            
            results[name] = {
                'avg_precision': avg_precision,
                'avg_recall': avg_recall,
                'avg_mrr': avg_mrr,
                'avg_ndcg': avg_ndcg,
                'total_time': elapsed,
                'per_query': query_metrics
            }
            
            print(f"  Avg Precision@{K}: {avg_precision:.3f}")
            print(f"  Avg Recall@{K}:    {avg_recall:.3f}")
            print(f"  Avg MRR:           {avg_mrr:.3f}")
            print(f"  Avg NDCG@{K}:      {avg_ndcg:.3f}")
            print(f"  Total time:        {elapsed:.2f}s")
    
    # Print comparison table
    print("\n" + "=" * 80)
    print("QUALITY COMPARISON")
    print("=" * 80)
    print(f"{'Metric':<20} {'RRF':>10} {'Embedding':>10} {'CrossEncoder':>12} {'Emb-RRF':>10} {'CE-RRF':>10} {'CE-Emb':>10}")
    print("-" * 80)
    
    if 'RRF' in results and 'EmbeddingReranker' in results and 'CrossEncoderReranker' in results:
        rrf = results['RRF']
        emb = results['EmbeddingReranker']
        ce = results['CrossEncoderReranker']
        
        for metric_name, attr in [('Precision@5', 'avg_precision'), ('Recall@5', 'avg_recall'), 
                                   ('MRR', 'avg_mrr'), ('NDCG@5', 'avg_ndcg')]:
            rrf_val = rrf[attr]
            emb_val = emb[attr]
            ce_val = ce[attr]
            
            emb_diff = emb_val - rrf_val
            ce_diff = ce_val - rrf_val
            ce_emb_diff = ce_val - emb_val
            
            print(f"{metric_name:<20} {rrf_val:>10.3f} {emb_val:>10.3f} {ce_val:>12.3f} {emb_diff:>+10.3f} {ce_diff:>+10.3f} {ce_emb_diff:>+10.3f}")
    
    print()
    print("=" * 80)
    print("PER-QUERY ANALYSIS")
    print("=" * 80)
    
    # Per-query analysis
    for case in get_evaluation_cases():
        if not case.relevant_memory_ids:
            continue
            
        print(f"\nQuery: {case.query}")
        print(f"  Relevant IDs: {sorted(case.relevant_memory_ids)}")
        
        with Session(engine) as db:
            for name, ranker_fn in [("RRF", get_rrf_ranking), 
                                     ("Embedding", get_embedding_reranked_ranking),
                                     ("CrossEncoder", get_cross_encoder_ranking)]:
                try:
                    ranking = ranker_fn(case.query, db, "dev-user", K)
                    # Find first relevant
                    first_relevant = None
                    for i, mid in enumerate(ranking, 1):
                        if mid in case.relevant_memory_ids:
                            first_relevant = i
                            break
                    print(f"  {name}: first relevant at rank {first_relevant if first_relevant else 'N/A'}")
                except Exception as e:
                    print(f"  {name}: ERROR - {e}")
    
    # Latency benchmarks
    print("\n" + "=" * 80)
    print("LATENCY BENCHMARK")
    print("=" * 80)
    
    print(f"\nCrossEncoder Model Load Time: {load_time*1000:.1f} ms")
    print(f"First Inference (warm-up): {warm_time*1000:.1f} ms")
    
    # Measure warm inference
    print("\nMeasuring warm inference...")
    warm_times = []
    for _ in range(5):
        start = time.perf_counter()
        _ = cross_encoder.rerank("test query", [
            type('Result', (), {'id': 1, 'content': 'test', 'summary': 'test', 
                                'topics': [], 'entities': [], 'source': 'text',
                                'created_at': '2024-01-01T00:00:00', 'occurred_at': None, 'rrf_score': 0.0})()
        ], 1)
        warm_times.append(time.perf_counter() - start)
    
    avg_warm = sum(warm_times) / len(warm_times)
    print(f"Average warm inference (5 runs): {avg_warm*1000:.1f} ms")
    
    print("\n" + "=" * 80)
    print("MODEL INFORMATION")
    print("=" * 80)
    print(f"Model: BAAI/bge-reranker-v2-m3")
    print(f"Library: sentence-transformers 3.0.1")
    print(f"PyTorch version: 2.14.0")
    print(f"Device: {cross_encoder._device or 'auto'}")
    print(f"Python: 3.14")
    print()
    print("Memory usage: Not measured reliably (no resource module on macOS)")
    print()
    print("LIMITATIONS:")
    print("- Small evaluation dataset (10 queries, 9 memories)")
    print("- Not statistically significant")
    print("- Results are dataset-specific")
    print("- No statistical significance testing")


if __name__ == "__main__":
    run_benchmark()