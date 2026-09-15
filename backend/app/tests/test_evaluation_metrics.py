import pytest
import math
from app.search.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    mrr,
    dcg_at_k,
    ndcg_at_k,
    evaluate_ranking,
    RankingMetrics,
)


class TestPrecisionAtK:
    def test_precision_at_k_basic(self):
        ranking = [1, 3, 2, 4, 5]
        relevant = {1, 2}
        k = 3
        # Top 3: [1, 3, 2] -> 2 relevant out of 3
        assert precision_at_k(ranking, relevant, k) == 2 / 3

    def test_precision_at_k_all_relevant(self):
        ranking = [1, 2, 3]
        relevant = {1, 2, 3}
        k = 3
        assert precision_at_k(ranking, relevant, k) == 1.0

    def test_precision_at_k_none_relevant(self):
        ranking = [4, 5, 6]
        relevant = {1, 2}
        k = 3
        assert precision_at_k(ranking, relevant, k) == 0.0

    def test_precision_at_k_k_zero(self):
        ranking = [1, 2, 3]
        relevant = {1, 2}
        k = 0
        assert precision_at_k(ranking, relevant, k) == 0.0

    def test_precision_at_k_k_larger_than_ranking(self):
        ranking = [1, 2]
        relevant = {1, 2}
        k = 5
        assert precision_at_k(ranking, relevant, k) == 2 / 5


class TestRecallAtK:
    def test_recall_at_k_basic(self):
        ranking = [1, 3, 2, 4, 5]
        relevant = {1, 2}
        k = 3
        # Top 3: [1, 3, 2] -> 2 relevant out of 2 total relevant
        assert recall_at_k(ranking, relevant, k) == 1.0

    def test_recall_at_k_partial(self):
        ranking = [1, 3, 4]
        relevant = {1, 2, 5}
        k = 3
        # Top 3: [1, 3, 4] -> 1 relevant out of 3 total relevant
        assert recall_at_k(ranking, relevant, k) == 1 / 3

    def test_recall_at_k_no_relevant(self):
        ranking = [3, 4, 5]
        relevant = {1, 2}
        k = 3
        assert recall_at_k(ranking, relevant, k) == 0.0

    def test_recall_at_k_empty_relevant(self):
        ranking = [1, 2, 3]
        relevant = set()
        k = 3
        assert recall_at_k(ranking, relevant, k) == 0.0


class TestMRR:
    def test_mrr_first_result(self):
        ranking = [1, 2, 3, 4]
        relevant = {1}
        assert mrr(ranking, relevant) == 1.0

    def test_mrr_second_result(self):
        ranking = [3, 1, 4]
        relevant = {1}
        assert mrr(ranking, relevant) == 1 / 2

    def test_mrr_third_result(self):
        ranking = [5, 4, 1]
        relevant = {1}
        assert mrr(ranking, relevant) == 1 / 3

    def test_mrr_multiple_relevant(self):
        ranking = [5, 4, 2, 1]
        relevant = {1, 2}
        # First relevant is 2 at position 3
        assert mrr(ranking, relevant) == 1 / 3

    def test_mrr_no_relevant(self):
        ranking = [3, 4, 5]
        relevant = {1, 2}
        assert mrr(ranking, relevant) == 0.0

    def test_mrr_empty_relevant(self):
        ranking = [1, 2, 3]
        relevant = set()
        assert mrr(ranking, relevant) == 0.0


class TestDCGAtK:
    def test_dcg_basic(self):
        ranking = [1, 2, 3]
        relevant = {1, 2}
        k = 3
        # DCG = 1/log2(2) + 1/log2(3) = 1 + 0.6309 = 1.6309
        expected = 1 / math.log2(2) + 1 / math.log2(3)
        assert abs(dcg_at_k([1, 2, 3], {1, 2}, 3) - expected) < 0.001

    def test_dcg_empty(self):
        assert dcg_at_k([], {1}, 3) == 0.0


class TestNDCGAtK:
    def test_ndcg_perfect_ranking(self):
        ranking = [1, 2, 3]
        relevant = {1, 2, 3}
        # Perfect ranking should give NDCG = 1
        assert abs(ndcg_at_k(ranking, relevant, 3) - 1.0) < 0.001

    def test_ndcg_imperfect_ranking(self):
        ranking = [4, 2, 1, 3]
        relevant = {1, 2, 3}
        # Imperfect ranking with one non-relevant item at top
        ndcg = ndcg_at_k(ranking, relevant, 3)
        # NDCG should be < 1 because a non-relevant item (4) is ranked first
        assert 0 < ndcg < 1

    def test_ndcg_no_relevant(self):
        ranking = [1, 2, 3]
        relevant = {4, 5}
        assert ndcg_at_k(ranking, relevant, 3) == 0.0

    def test_ndcg_with_grades(self):
        ranking = [1, 2, 3]
        relevant = {1, 2, 3}
        grades = {1: 3.0, 2: 2.0, 3: 1.0}
        # With grades, NDCG should be 1 if order matches grades
        assert abs(ndcg_at_k(ranking, relevant, 3, grades) - 1.0) < 0.001

    def test_ndcg_k_larger_than_ranking(self):
        ranking = [1, 2]
        relevant = {1, 2}
        k = 5
        assert abs(ndcg_at_k(ranking, relevant, k) - 1.0) < 0.001


class TestEvaluateRanking:
    def test_evaluate_ranking_returns_all_metrics(self):
        ranking = [1, 3, 2, 4]
        relevant = {1, 2}
        k = 4
        
        metrics = evaluate_ranking(ranking, {1, 2}, k)
        
        assert isinstance(metrics, RankingMetrics)
        assert metrics.precision_at_k == 0.5  # 2 relevant out of 4
        assert metrics.recall_at_k == 1.0     # 2 out of 2 relevant found
        assert metrics.mrr == 1.0             # First relevant at rank 1
        assert 0 <= metrics.ndcg_at_k <= 1

    def test_evaluate_ranking_empty_ranking(self):
        ranking = []
        relevant = {1, 2}
        k = 4
        
        metrics = evaluate_ranking(ranking, relevant, 4)
        
        assert metrics.precision_at_k == 0.0
        assert metrics.recall_at_k == 0.0
        assert metrics.mrr == 0.0
        assert metrics.ndcg_at_k == 0.0

    def test_evaluate_ranking_k_larger_than_ranking(self):
        ranking = [1, 2]
        relevant = {1, 2}
        k = 5
        
        metrics = evaluate_ranking(ranking, relevant, k)
        
        assert metrics.precision_at_k == 2 / 5
        assert metrics.recall_at_k == 1.0
        assert metrics.mrr == 1.0