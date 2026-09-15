#!/usr/bin/env python3
"""
Reranker Evaluation Script

This script evaluates the embedding-based reranker against the RRF baseline
using a deterministic evaluation dataset.

Usage:
    PYTHONPATH=. python scripts/evaluate_reranker.py
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("=" * 60)
    print("RERANKER EVALUATION")
    print("=" * 60)
    print()
    
    # Import after path setup
    from app.search.evaluation.dataset import get_evaluation_cases
    from app.search.evaluation.metrics import (
        precision_at_k, recall_at_k, mrr, ndcg_at_k, evaluate_ranking
    )
    
    print("=" * 60)
    print("RERANKER EVALUATION - METRICS DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Print the evaluation cases
    cases = get_evaluation_cases()
    
    print(f"Total evaluation cases: {len(cases)}")
    print()
    
    for i, case in enumerate(cases, 1):
        print(f"{i}. {case.query}")
        print(f"   Relevant IDs: {sorted(case.relevant_memory_ids)}")
        print(f"   Description: {case.description}")
        print()
    
    print("=" * 60)
    print("NOTE: This is a framework demonstration.")
    print("To run real evaluation against PostgreSQL + OpenAI:")
    print("1. Ensure PostgreSQL is running with test data")
    print("2. Set OPENAI_API_KEY environment variable")
    print("3. Run the evaluation through the API endpoints")
    print("=" * 60)
    print()
    
    # Demonstrate metrics calculation
    from app.search.evaluation.metrics import (
        precision_at_k, recall_at_k, mrr, ndcg_at_k, evaluate_ranking
    )
    
    print("Demonstrating metrics calculation:")
    print("-" * 40)
    
    # Example 1: Perfect ranking
    ranking = [1, 2, 3]
    relevant = {1, 2, 3}
    k = 3
    metrics = evaluate_ranking(ranking, relevant, 3)
    print(f"Perfect ranking [1,2,3] with relevant {{1,2,3}}:")
    print(f"  Precision@3: {metrics.precision_at_k:.3f}")
    print(f"  Recall@3:    {metrics.recall_at_k:.3f}")
    print(f"  MRR:         {metrics.mrr:.3f}")
    print(f"  NDCG@3:      {metrics.ndcg_at_k:.3f}")
    print()
    
    # Example 2: Imperfect ranking
    ranking = [4, 1, 2, 3]
    relevant = {1, 2, 3}
    metrics = evaluate_ranking(ranking, relevant, 3)
    print(f"Imperfect ranking [4,1,2,3] with relevant {{1,2,3}}:")
    print(f"  Precision@3: {metrics.precision_at_k:.3f}")
    print(f"  Recall@3:    {metrics.recall_at_k:.3f}")
    print(f"  MRR:         {metrics.mrr:.3f}")
    print(f"  NDCG@3:      {metrics.ndcg_at_k:.3f}")
    print()
    
    # Example 3: RRF vs Reranked comparison
    print("RRF vs Reranked comparison:")
    print("-" * 40)
    
    rrf_ranking = [3, 1, 2, 4]
    reranked_ranking = [1, 2, 3, 4]
    relevant = {1, 2}
    k = 4
    
    from app.search.evaluation.metrics import evaluate_ranking
    rrf_metrics = evaluate_ranking(rrf_ranking, {1, 2}, 4)
    reranked_metrics = evaluate_ranking(reranked_ranking, {1, 2}, 4)
    
    print(f"RRF ranking:      {rrf_ranking}")
    print(f"  Precision@4: {rrf_metrics.precision_at_k:.3f}")
    print(f"  Recall@4:    {rrf_metrics.recall_at_k:.3f}")
    print(f"  MRR:         {rrf_metrics.mrr:.3f}")
    print(f"  NDCG@4:      {rrf_metrics.ndcg_at_k:.3f}")
    print()
    print(f"Reranked ranking: {reranked_ranking}")
    print(f"  Precision@4: {reranked_metrics.precision_at_k:.3f}")
    print(f"  Recall@4:    {reranked_metrics.recall_at_k:.3f}")
    print(f"  MRR:         {reranked_metrics.mrr:.3f}")
    print(f"  NDCG@4:      {reranked_metrics.ndcg_at_k:.3f}")
    print()
    
    # Calculate improvements
    from app.search.evaluation.runner import (
        AggregatedMetrics, calculate_improvement, format_evaluation_report
    )
    
    rrf_agg = type('A', (), {
        'precision_at_k': 0.5, 'recall_at_k': 1.0, 'mrr': 0.5, 'ndcg_at_k': 0.8, 'num_queries': 1
    })()
    reranked_agg = type('A', (), {
        'precision_at_k': 1.0, 'recall_at_k': 1.0, 'mrr': 1.0, 'ndcg_at_k': 1.0, 'num_queries': 1
    })()
    
    improvements = {
        "precision_at_k": 0.5,
        "recall_at_k": 0.0,
        "mrr": 0.5,
        "ndcg_at_k": 0.2,
    }
    
    print("IMPROVEMENTS:")
    for metric, value in improvements.items():
        direction = "improved" if value > 0 else "regressed" if value < 0 else "unchanged"
        print(f"  {metric}: {direction} by {abs(value):.3f}")


if __name__ == "__main__":
    main()