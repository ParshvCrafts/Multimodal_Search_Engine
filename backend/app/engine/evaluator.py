import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Set

import numpy as np
from tqdm.auto import tqdm

from backend.app.engine.search_engine import ASOSSearchEngine

logger = logging.getLogger("asos_search")

__all__ = ["EvalResult", "SearchEvaluator"]


@dataclass
class EvalResult:
    query: str
    recall_at_k: Dict[int, float]
    precision_at_k: Dict[int, float]
    mrr: float
    latency_ms: float


class SearchEvaluator:
    def __init__(self, engine: ASOSSearchEngine):
        self.engine = engine

    def evaluate_single(
        self, query: str, relevant_skus: Set[str], k_values: List[int] = [5, 10, 20]
    ) -> EvalResult:
        max_k = max(k_values)
        t0 = time.time()
        results = self.engine.search(query, top_n=max_k)
        latency = (time.time() - t0) * 1000

        retrieved = results["sku"].astype(str).tolist()
        relevant = set(str(s) for s in relevant_skus)

        recall_at, precision_at = {}, {}
        for k in k_values:
            top_k = retrieved[:k]
            found = len(set(top_k) & relevant)
            recall_at[k] = found / len(relevant) if relevant else 0.0
            precision_at[k] = found / k if k > 0 else 0.0

        mrr = 0.0
        for rank, sku in enumerate(retrieved, 1):
            if sku in relevant:
                mrr = 1.0 / rank
                break

        return EvalResult(
            query=query,
            recall_at_k=recall_at,
            precision_at_k=precision_at,
            mrr=mrr,
            latency_ms=latency,
        )

    def evaluate(
        self, test_queries: List[Dict], k_values: List[int] = [5, 10, 20]
    ) -> Dict:
        results = []
        for tq in tqdm(test_queries, desc="Evaluating"):
            try:
                res = self.evaluate_single(
                    tq["query"],
                    set(str(s) for s in tq["relevant_skus"]),
                    k_values,
                )
                results.append(res)
            except Exception as e:
                logger.warning(f"Eval failed for '{tq['query']}': {e}")

        if not results:
            return {"error": "No successful evaluations"}

        agg = {
            "n_queries": len(results),
            "avg_latency_ms": float(np.mean([r.latency_ms for r in results])),
            "median_latency_ms": float(np.median([r.latency_ms for r in results])),
            "mean_mrr": float(np.mean([r.mrr for r in results])),
        }
        for k in k_values:
            agg[f"mean_recall@{k}"] = float(
                np.mean([r.recall_at_k.get(k, 0) for r in results])
            )
            agg[f"mean_precision@{k}"] = float(
                np.mean([r.precision_at_k.get(k, 0) for r in results])
            )

        return {"aggregate": agg, "per_query": [
            {"query": r.query, "mrr": r.mrr, "latency_ms": r.latency_ms,
             "recall_at_k": r.recall_at_k, "precision_at_k": r.precision_at_k}
            for r in results
        ]}

    @staticmethod
    def print_report(report: Dict):
        agg = report.get("aggregate", {})
        print("\n" + "=" * 65)
        print("  SEARCH ENGINE EVALUATION REPORT")
        print("=" * 65)
        print(f"  Queries evaluated:   {agg.get('n_queries', 0)}")
        print(f"  Avg latency:         {agg.get('avg_latency_ms', 0):.1f} ms")
        print(f"  Mean MRR:            {agg.get('mean_mrr', 0):.4f}")
        for key, val in sorted(agg.items()):
            if "recall" in key or "precision" in key:
                print(f"  {key:25s}  {val:.4f}")
        print("=" * 65)
