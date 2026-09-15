from dataclasses import dataclass
from typing import Optional
import math


def precision_at_k(ranking: list[int], relevant_ids: set[int], k: int) -> float:
    """
    Calculate Precision@K.
    
    Precision@K = number of relevant results in top K / K
    
    Args:
        ranking: List of memory IDs in ranked order
        relevant_ids: Set of relevant memory IDs
        k: Number of top results to consider
        
    Returns:
        Precision@K score between 0 and 1
    """
    if k <= 0:
        return 0.0
    
    top_k = ranking[:k]
    relevant_in_top_k = sum(1 for mid in top_k if mid in relevant_ids)
    return relevant_in_top_k / k


def recall_at_k(ranking: list[int], relevant_ids: set[int], k: int) -> float:
    """
    Calculate Recall@K.
    
    Recall@K = number of relevant results in top K / total relevant documents
    
    Args:
        ranking: List of memory IDs in ranked order
        relevant_ids: Set of relevant memory IDs
        k: Number of top results to consider
        
    Returns:
        Recall@K score between 0 and 1
    """
    if not relevant_ids or k <= 0:
        return 0.0
    
    top_k = ranking[:k]
    relevant_in_top_k = sum(1 for mid in top_k if mid in relevant_ids)
    return relevant_in_top_k / len(relevant_ids)


def mrr(ranking: list[int], relevant_ids: set[int]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).
    
    MRR = 1 / rank of first relevant result
    
    Args:
        ranking: List of memory IDs in ranked order
        relevant_ids: Set of relevant memory IDs
        
    Returns:
        MRR score between 0 and 1, or 0 if no relevant result found
    """
    if not relevant_ids:
        return 0.0
    
    for i, mid in enumerate(ranking, start=1):
        if mid in relevant_ids:
            return 1.0 / i
    
    return 0.0


def dcg_at_k(ranking: list[int], relevant_ids: set[int], k: int, 
             relevance_grades: Optional[dict[int, float]] = None) -> float:
    """
    Calculate Discounted Cumulative Gain at K.
    
    DCG@K = sum(rel_i / log2(i + 1)) for i = 1 to K
    
    Args:
        ranking: List of memory IDs in ranked order
        relevant_ids: Set of relevant memory IDs
        k: Number of top results to consider
        relevance_grades: Optional dict mapping memory_id to relevance grade (default: 1.0 for relevant, 0.0 for non-relevant)
        
    Returns:
        DCG@K score
    """
    if k <= 0:
        return 0.0
    
    top_k = ranking[:k]
    dcg = 0.0
    
    for i, mid in enumerate(top_k, start=1):
        if relevance_grades and mid in relevance_grades:
            rel = relevance_grades[mid]
        else:
            rel = 1.0 if mid in relevant_ids else 0.0
        
        if rel > 0:
            dcg += rel / math.log2(i + 1)
    
    return dcg


def ndcg_at_k(ranking: list[int], relevant_ids: set[int], k: int,
              relevance_grades: Optional[dict[int, float]] = None) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K.
    
    NDCG@K = DCG@K / IDCG@K
    
    Where IDCG is the ideal DCG (relevant items ranked first).
    
    Args:
        ranking: List of memory IDs in ranked order
        relevant_ids: Set of relevant memory IDs
        k: Number of top results to consider
        relevance_grades: Optional dict mapping memory_id to relevance grade
        
    Returns:
        NDCG@K score between 0 and 1
    """
    if not relevant_ids or k <= 0:
        return 0.0
    
    actual_dcg = dcg_at_k(ranking, relevant_ids, k, relevance_grades)
    
    # Calculate ideal DCG (relevant items ranked first)
    relevant_list = list(relevant_ids)
    if relevance_grades:
        # Sort by relevance grade descending
        relevant_list.sort(key=lambda x: relevance_grades.get(x, 0), reverse=True)
    
    ideal_ranking = relevant_list[:k]
    ideal_dcg = dcg_at_k(ideal_ranking, set(relevant_list), k, relevance_grades)
    
    if ideal_dcg == 0:
        return 0.0
    
    return actual_dcg / ideal_dcg


@dataclass
class RankingMetrics:
    """Metrics for a single ranking evaluation."""
    precision_at_k: float
    recall_at_k: float
    mrr: float
    ndcg_at_k: float
    
    def to_dict(self) -> dict:
        return {
            "precision_at_k": self.precision_at_k,
            "recall_at_k": self.recall_at_k,
            "mrr": self.mrr,
            "ndcg_at_k": self.ndcg_at_k,
        }


def evaluate_ranking(
    ranking: list[int],
    relevant_ids: set[int],
    k: int,
    relevance_grades: Optional[dict[int, float]] = None,
) -> RankingMetrics:
    """
    Evaluate a single ranking against relevant IDs.
    
    Args:
        ranking: List of memory IDs in ranked order
        relevant_ids: Set of relevant memory IDs
        k: Number of top results to consider
        relevance_grades: Optional relevance grades for NDCG
        
    Returns:
        RankingMetrics with all metrics
    """
    return RankingMetrics(
        precision_at_k=precision_at_k(ranking, relevant_ids, k),
        recall_at_k=recall_at_k(ranking, relevant_ids, k),
        mrr=mrr(ranking, relevant_ids),
        ndcg_at_k=ndcg_at_k(ranking, relevant_ids, k, relevance_grades),
    )