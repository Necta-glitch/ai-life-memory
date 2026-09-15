from dataclasses import dataclass
from typing import Callable, Optional

from app.search.evaluation.dataset import EvaluationCase, get_evaluation_cases
from app.search.evaluation.metrics import RankingMetrics, evaluate_ranking
from app.search.schemas import HybridSearchResult


@dataclass
class EvaluationResult:
    """Result of evaluating a single query."""
    query: str
    rrf_ranking: list[int]
    reranked_ranking: list[int]
    relevant_ids: set[int]
    rrf_metrics: RankingMetrics
    reranked_metrics: RankingMetrics
    k: int


def evaluate_reranker(
    evaluation_cases: list,
    get_rrf_ranking: Callable[[str], list[int]],
    get_reranked_ranking: Callable[[str], list[int]],
    k: int = 5,
) -> list[EvaluationResult]:
    """
    Evaluate reranker against RRF for a set of evaluation cases.
    
    Args:
        evaluation_cases: List of EvaluationCase objects
        get_rrf_ranking: Function that returns RRF ranking for a query
        get_reranked_ranking: Function that returns reranked ranking for a query
        k: Number of top results to evaluate
        
    Returns:
        List of EvaluationResult objects
    """
    results = []
    
    for case in evaluation_cases:
        # Get RRF ranking
        rrf_ranking = get_rrf_ranking(case.query)
        
        # Get reranked ranking
        reranked_ranking = get_reranked_ranking(case.query)
        
        # Evaluate both
        rrf_metrics = evaluate_ranking(
            rrf_ranking, case.relevant_memory_ids, k
        )
        reranked_metrics = evaluate_ranking(
            reranked_ranking, case.relevant_memory_ids, k
        )
        
        results.append(EvaluationResult(
            query=case.query,
            rrf_ranking=rrf_ranking,
            reranked_ranking=reranked_ranking,
            relevant_ids=case.relevant_memory_ids,
            rrf_metrics=rrf_metrics,
            reranked_metrics=reranked_metrics,
            k=k,
        ))
    
    return results


@dataclass
class AggregatedMetrics:
    """Aggregated metrics across all evaluation cases."""
    precision_at_k: float
    recall_at_k: float
    mrr: float
    ndcg_at_k: float
    num_queries: int


def aggregate_results(results: list[EvaluationResult]) -> tuple[AggregatedMetrics, AggregatedMetrics]:
    """
    Calculate aggregate metrics for RRF and reranked results.
    
    Returns:
        Tuple of (rrf_aggregated, reranked_aggregated)
    """
    if not results:
        empty = AggregatedMetrics(0, 0, 0, 0, 0)
        return empty, empty
    
    def aggregate(metrics_list: list[RankingMetrics]) -> AggregatedMetrics:
        n = len(metrics_list)
        if n == 0:
            return AggregatedMetrics(0, 0, 0, 0, 0)
        
        return AggregatedMetrics(
            precision_at_k=sum(m.precision_at_k for m in metrics_list) / n,
            recall_at_k=sum(m.recall_at_k for m in metrics_list) / n,
            mrr=sum(m.mrr for m in metrics_list) / n,
            ndcg_at_k=sum(m.ndcg_at_k for m in metrics_list) / n,
            num_queries=n,
        )
    
    rrf_metrics = [r.rrf_metrics for r in results]
    reranked_metrics = [r.reranked_metrics for r in results]
    
    return aggregate(rrf_metrics), aggregate(reranked_metrics)


def calculate_improvement(
    rrf_agg: AggregatedMetrics,
    reranked_agg: AggregatedMetrics,
) -> dict[str, float]:
    """
    Calculate improvement from RRF to reranked.
    
    Returns:
        Dictionary with metric improvements
    """
    return {
        "precision_at_k": reranked_agg.precision_at_k - rrf_agg.precision_at_k,
        "recall_at_k": reranked_agg.recall_at_k - rrf_agg.recall_at_k,
        "mrr": reranked_agg.mrr - rrf_agg.mrr,
        "ndcg_at_k": reranked_agg.ndcg_at_k - rrf_agg.ndcg_at_k,
    }


def format_evaluation_report(
    results: list[EvaluationResult],
    rrf_agg: AggregatedMetrics,
    reranked_agg: AggregatedMetrics,
    improvements: dict[str, float],
) -> str:
    """
    Format evaluation results as a readable report.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("RERANKER EVALUATION REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Queries evaluated: {len(results)}")
    lines.append(f"K: {results[0].k if results else 0}")
    lines.append("")
    
    # Per-query results
    lines.append("PER-QUERY RESULTS")
    lines.append("-" * 60)
    for r in results:
        lines.append(f"Query: {r.query}")
        lines.append(f"  Relevant IDs: {sorted(r.relevant_ids)}")
        lines.append(f"  RRF Ranking:      {r.rrf_ranking[:5]}")
        lines.append(f"  Reranked Ranking: {r.reranked_ranking[:5]}")
        lines.append(f"  RRF MRR:      {r.rrf_metrics.mrr:.3f}")
        lines.append(f"  Reranked MRR: {r.reranked_metrics.mrr:.3f}")
        lines.append("")
    
    # Aggregate metrics
    lines.append("AGGREGATE METRICS")
    lines.append("-" * 60)
    lines.append(f"{'Metric':<20} {'RRF':>10} {'Reranker':>10} {'Improvement':>12}")
    lines.append("-" * 52)
    
    metrics_map = {
        "Precision@K": (rrf_agg.precision_at_k, reranked_agg.precision_at_k),
        "Recall@K": (rrf_agg.recall_at_k, reranked_agg.recall_at_k),
        "MRR": (rrf_agg.mrr, reranked_agg.mrr),
        "NDCG@K": (rrf_agg.ndcg_at_k, reranked_agg.ndcg_at_k),
    }
    
    for name, (rrf_val, reranked_val) in metrics_map.items():
        improvement = improvements.get(name.lower().replace("@", "_at_"), 0)
        lines.append(f"{name:<20} {rrf_val:>10.3f} {reranked_val:>10.3f} {improvement:>+12.3f}")
    
    lines.append("")
    lines.append("=" * 60)
    lines.append("IMPROVEMENTS")
    lines.append("-" * 60)
    for name, value in improvements.items():
        if abs(value) > 0.001:
            direction = "improved" if value > 0 else "regressed"
            lines.append(f"  {name}: {direction} by {abs(value):.3f}")
        else:
            lines.append(f"  {name}: no significant change")
    
    return "\n".join(lines)