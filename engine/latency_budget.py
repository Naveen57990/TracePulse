"""
TracePulse Core Engine - Latency Budget & SLA Percentile Profiler
Calculates p50, p90, p95, p99 percentiles, tail-latency amplification, and SLA breach risk.
"""
from typing import List, Dict, Any, Optional
import math

class LatencyBudgetProfiler:
    def __init__(self, sla_budget_ms: float = 250.0):
        self.sla_budget_ms = max(1.0, float(sla_budget_ms))

    def calculate_percentiles(self, latencies: List[float]) -> Dict[str, float]:
        """Calculates p50, p90, p95, p99, and p99.9 percentiles for a sample of latencies."""
        if not latencies:
            return {
                "p50": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "p99_9": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0
            }

        sorted_lat = sorted(float(x) for x in latencies)
        n = len(sorted_lat)

        def get_quantile(q: float) -> float:
            idx = (n - 1) * q
            floor_idx = int(math.floor(idx))
            ceil_idx = int(math.ceil(idx))
            if floor_idx == ceil_idx:
                return sorted_lat[floor_idx]
            weight = idx - floor_idx
            return sorted_lat[floor_idx] * (1.0 - weight) + sorted_lat[ceil_idx] * weight

        return {
            "p50": round(get_quantile(0.50), 2),
            "p90": round(get_quantile(0.90), 2),
            "p95": round(get_quantile(0.95), 2),
            "p99": round(get_quantile(0.99), 2),
            "p99_9": round(get_quantile(0.999), 2),
            "mean": round(sum(sorted_lat) / n, 2),
            "min": round(sorted_lat[0], 2),
            "max": round(sorted_lat[-1], 2),
            "count": n
        }

    def evaluate_sla_risk(self, latencies: List[float]) -> Dict[str, Any]:
        """
        Evaluates SLA breach probability and headroom under current traffic profile.
        """
        stats = self.calculate_percentiles(latencies)
        if stats["count"] == 0:
            return {
                "status": "HEALTHY",
                "sla_budget_ms": self.sla_budget_ms,
                "sla_breach_rate_pct": 0.0,
                "headroom_ms": self.sla_budget_ms,
                "tail_amplification_ratio": 1.0,
                "stats": stats
            }

        breach_count = sum(1 for x in latencies if x > self.sla_budget_ms)
        breach_rate_pct = round((breach_count / len(latencies)) * 100.0, 2)
        headroom_ms = round(self.sla_budget_ms - stats["p95"], 2)

        # Tail Amplification Ratio: p99 / p50 (measures long-tail latency distortion)
        p50 = max(0.1, stats["p50"])
        tail_amp = round(stats["p99"] / p50, 2)

        if breach_rate_pct > 5.0 or headroom_ms < 0:
            status = "CRITICAL_BREACH"
        elif breach_rate_pct > 1.0 or headroom_ms < (self.sla_budget_ms * 0.15):
            status = "AT_RISK"
        else:
            status = "HEALTHY"

        return {
            "status": status,
            "sla_budget_ms": self.sla_budget_ms,
            "sla_breach_rate_pct": breach_rate_pct,
            "headroom_ms": headroom_ms,
            "tail_amplification_ratio": tail_amp,
            "stats": stats
        }

    def allocate_service_budgets(
        self,
        service_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Allocates deterministic latency SLA budgets across upstream/downstream microservices based on weight.
        """
        if not service_weights:
            return {}
        total_weight = sum(max(0.01, w) for w in service_weights.values())
        allocations = {}
        for svc, weight in service_weights.items():
            allocated_ms = round((weight / total_weight) * self.sla_budget_ms, 2)
            allocations[svc] = allocated_ms
        return allocations
