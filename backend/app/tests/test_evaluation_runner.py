import pytest
from app.search.evaluation.runner import (
    evaluate_reranker,
    aggregate_results,
    calculate_improvement,
    format_evaluation_report,
    EvaluationResult,
    AggregatedMetrics,
)
from app.search.evaluation.metrics import RankingMetrics


class TestAggregateResults:
    def test_aggregate_results(self):
        """Test aggregating metrics across multiple evaluation results."""
        rrf_metrics = [
            RankingMetrics(0.5, 1.0, 0.5, 0.8),
            RankingMetrics(0.8, 0.5, 0.8, 0.9),
            RankingMetrics(0.6, 0.8, 0.6, 0.7),
        ]
        
        reranked_metrics = [
            RankingMetrics(0.6, 0.8, 0.6, 0.7),
            RankingMetrics(0.7, 0.7, 0.7, 0.8),
            RankingMetrics(0.7, 0.6, 0.7, 0.8),
        ]
        
        # Create mock results
        class MockResult:
            def __init__(self, rrf_m, rerank_m):
                self.rrf_metrics = rrf_m
                self.reranked_metrics = rerank_m
        
        results = [
            MockResult(rrf_metrics[0], reranked_metrics[0]),
            MockResult(rrf_metrics[1], reranked_metrics[1]),
            MockResult(rrf_metrics[2], reranked_metrics[2]),
        ]
        
        rrf_agg, reranked_agg = aggregate_results(results)
        
        # Check RRF aggregate
        expected_rrf_precision = (0.5 + 0.8 + 0.6) / 3
        expected_rrf_recall = (1.0 + 0.5 + 0.8) / 3
        expected_rrf_mrr = (0.5 + 0.8 + 0.6) / 3
        expected_rrf_ndcg = (0.8 + 0.9 + 0.7) / 3
        
        assert abs(rrf_agg.precision_at_k - expected_rrf_precision) < 0.001
        assert abs(rrf_agg.recall_at_k - expected_rrf_recall) < 0.001
        assert abs(rrf_agg.mrr - expected_rrf_mrr) < 0.001
        assert abs(rrf_agg.ndcg_at_k - expected_rrf_ndcg) < 0.001
        
        # Check reranked aggregate
        expected_rerank_precision = (0.6 + 0.7 + 0.7) / 3
        expected_rerank_recall = (0.8 + 0.7 + 0.6) / 3
        expected_rerank_mrr = (0.6 + 0.7 + 0.7) / 3
        expected_rerank_ndcg = (0.7 + 0.8 + 0.8) / 3
        
        assert abs(reranked_agg.precision_at_k - expected_rerank_precision) < 0.001
        assert abs(reranked_agg.recall_at_k - expected_rerank_recall) < 0.001
        assert abs(reranked_agg.mrr - expected_rerank_mrr) < 0.001
        assert abs(reranked_agg.ndcg_at_k - expected_rerank_ndcg) < 0.001


class TestCalculateImprovement:
    def test_improvement_positive(self):
        rrf = AggregatedMetrics(0.5, 0.6, 0.5, 0.7, 10)
        reranked = AggregatedMetrics(0.7, 0.8, 0.8, 0.9, 10)
        
        improvements = calculate_improvement(rrf, reranked)
        
        assert abs(improvements["precision_at_k"] - 0.2) < 0.001
        assert abs(improvements["recall_at_k"] - 0.2) < 0.001
        assert abs(improvements["mrr"] - 0.3) < 0.001
        assert abs(improvements["ndcg_at_k"] - 0.2) < 0.001

    def test_improvement_negative(self):
        rrf = AggregatedMetrics(0.8, 0.8, 0.8, 0.8, 10)
        reranked = AggregatedMetrics(0.6, 0.6, 0.6, 0.6, 10)
        
        improvements = calculate_improvement(rrf, reranked)
        
        assert abs(improvements["precision_at_k"] + 0.2) < 0.001
        assert abs(improvements["mrr"] + 0.2) < 0.001

    def test_improvement_zero(self):
        rrf = AggregatedMetrics(0.5, 0.5, 0.5, 0.5, 10)
        reranked = AggregatedMetrics(0.5, 0.5, 0.5, 0.5, 10)
        
        improvements = calculate_improvement(rrf, reranked)
        
        for val in improvements.values():
            assert val == 0.0


class TestFormatEvaluationReport:
    def test_format_report(self):
        rrf_agg = AggregatedMetrics(0.5, 1.0, 0.5, 0.8, 1)
        reranked_agg = AggregatedMetrics(1.0, 1.0, 1.0, 1.0, 1)
        improvements = {
            "precision_at_k": 0.33,
            "recall_at_k": 0.0,
            "mrr": 0.5,
            "ndcg_at_k": 0.2,
        }
        
        results = [type('R', (), {
            'query': 'test query',
            'relevant_ids': {1, 2},
            'rrf_ranking': [2, 1, 3],
            'reranked_ranking': [1, 2, 3],
            'rrf_metrics': type('M', (), {'precision_at_k': 0.67, 'recall_at_k': 1.0, 'mrr': 0.5, 'ndcg_at_k': 0.8})(),
            'reranked_metrics': type('M', (), {'precision_at_k': 1.0, 'recall_at_k': 1.0, 'mrr': 1.0, 'ndcg_at_k': 1.0})(),
            'k': 3
        })()]
        
        report = format_evaluation_report(
            results,
            AggregatedMetrics(0.5, 1.0, 0.5, 0.8, 1),
            AggregatedMetrics(1.0, 1.0, 1.0, 1.0, 1),
            {"precision_at_k": 0.33, "recall_at_k": 0.0, "mrr": 0.5, "ndcg_at_k": 0.2}
        )
        
        assert "RERANKER EVALUATION REPORT" in report
        assert "test query" in report
        assert "precision_at_k" in report