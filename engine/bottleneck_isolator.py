"""
TracePulse Core Engine - Root-Cause Bottleneck Isolator & Cascade Detector
Identifies anomalous microservice delays, cascade retry storms, and synthesizes remediation tactics.
"""
from typing import List, Dict, Any, Optional
from .span_graph import SpanGraph, Span

class BottleneckIsolator:
    def __init__(self, variance_threshold_ms: float = 40.0):
        self.variance_threshold_ms = variance_threshold_ms

    def isolate_root_cause(self, span_graph: SpanGraph) -> Dict[str, Any]:
        """
        Pinpoints the exact bottleneck span and service contributing most to total latency or failure.
        Uses exclusive self-time (time spent in span excluding child spans) to avoid blaming outer caller wrappers.
        """
        span_graph.build_dag()
        critical_path = span_graph.find_critical_path()
        
        if not critical_path:
            return {
                "bottleneck_found": False,
                "primary_culprit": None,
                "critical_path_latency_ms": 0.0,
                "remediations": []
            }

        crit_latency = sum(s.duration_ms for s in critical_path)
        
        # Rank critical path spans by error state first, then by exclusive self-duration
        sorted_spans = sorted(
            critical_path,
            key=lambda s: (1 if s.error else 0, s.self_duration_ms),
            reverse=True
        )
        
        primary_culprit = sorted_spans[0]
        impact_pct = round((primary_culprit.self_duration_ms / max(1.0, crit_latency)) * 100.0, 1)

        remediations = []
        if primary_culprit.error:
            remediations.append(f"Deploy circuit-breaker on `{primary_culprit.service}` to prevent upstream cascading thread pool exhaustion.")
            remediations.append(f"Implement exponential backoff with jitter on retry policy for span `{primary_culprit.name}`.")
        elif impact_pct > 40.0:
            remediations.append(f"Enable edge caching or read-replica scaling for `{primary_culprit.service}` (consumes {impact_pct}% of critical path self-time).")
            remediations.append(f"Convert synchronous RPC `{primary_culprit.name}` into asynchronous message queue processing where viable.")
        else:
            remediations.append(f"Parallelize concurrent downstream sub-calls within `{primary_culprit.service}`.")

        return {
            "bottleneck_found": True,
            "primary_culprit": {
                "span_id": primary_culprit.span_id,
                "name": primary_culprit.name,
                "service": primary_culprit.service,
                "duration_ms": primary_culprit.duration_ms,
                "self_duration_ms": primary_culprit.self_duration_ms,
                "impact_pct": impact_pct,
                "error": primary_culprit.error
            },
            "critical_path_latency_ms": round(crit_latency, 2),
            "critical_path_span_count": len(critical_path),
            "remediations": remediations
        }

    def detect_cascade_risk(self, span_graph: SpanGraph) -> Dict[str, Any]:
        """
        Detects cascading failure risks, such as high fan-out retry storms or fan-in serialization.
        """
        span_graph.build_dag()
        fan_out_map: Dict[str, int] = {}
        error_nodes: List[str] = []

        for span in span_graph.spans.values():
            if span.children:
                fan_out_map[span.service] = max(fan_out_map.get(span.service, 0), len(span.children))
            if span.error:
                error_nodes.append(span.service)

        max_fanout_svc = max(fan_out_map.items(), key=lambda x: x[1]) if fan_out_map else ("none", 0)
        
        has_cascade = len(error_nodes) >= 2 or max_fanout_svc[1] >= 5
        risk_level = "HIGH" if has_cascade else ("MEDIUM" if max_fanout_svc[1] >= 3 else "LOW")

        return {
            "risk_level": risk_level,
            "max_fan_out_service": max_fanout_svc[0],
            "max_fan_out_count": max_fanout_svc[1],
            "error_service_count": len(set(error_nodes)),
            "cascade_amplification_detected": has_cascade
        }
