"""
TracePulse Core Engine - Distributed Span Graph (DAG) & Critical Path Analyzer
Analyzes distributed trace spans, constructs call hierarchy DAGs, and detects critical execution paths.
"""
from typing import Dict, List, Any, Optional, Set
import math

class Span:
    def __init__(
        self,
        span_id: str,
        name: str,
        service: str,
        start_ms: float,
        duration_ms: float,
        parent_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        error: bool = False
    ):
        self.span_id = span_id
        self.name = name
        self.service = service
        self.start_ms = start_ms
        self.duration_ms = duration_ms
        self.end_ms = start_ms + duration_ms
        self.parent_id = parent_id
        self.tags = tags or {}
        self.error = error
        self.children: List[Span] = []

    @property
    def self_duration_ms(self) -> float:
        """Calculates exclusive self-time by subtracting direct children durations from total duration."""
        children_dur = sum(c.duration_ms for c in self.children)
        return max(0.0, round(self.duration_ms - children_dur, 2))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "name": self.name,
            "service": self.service,
            "start_ms": round(self.start_ms, 2),
            "duration_ms": round(self.duration_ms, 2),
            "self_duration_ms": self.self_duration_ms,
            "end_ms": round(self.end_ms, 2),
            "parent_id": self.parent_id,
            "tags": self.tags,
            "error": self.error,
            "children_count": len(self.children)
        }

class SpanGraph:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.spans: Dict[str, Span] = {}
        self.root_spans: List[Span] = []

    def add_span(
        self,
        span_id: str,
        name: str,
        service: str,
        start_ms: float,
        duration_ms: float,
        parent_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        error: bool = False
    ) -> Span:
        span = Span(
            span_id=span_id,
            name=name,
            service=service,
            start_ms=start_ms,
            duration_ms=duration_ms,
            parent_id=parent_id,
            tags=tags,
            error=error
        )
        self.spans[span_id] = span
        return span

    def build_dag(self) -> None:
        """Links child spans to parent spans and identifies root spans."""
        self.root_spans = []
        for span in self.spans.values():
            span.children = []

        for span in self.spans.values():
            if span.parent_id and span.parent_id in self.spans:
                self.spans[span.parent_id].children.append(span)
            else:
                self.root_spans.append(span)

    def compute_total_trace_duration(self) -> float:
        """Calculates total wall-clock duration of the trace from first start to last end."""
        if not self.spans:
            return 0.0
        earliest_start = min(s.start_ms for s in self.spans.values())
        latest_end = max(s.end_ms for s in self.spans.values())
        return max(0.0, latest_end - earliest_start)

    def find_critical_path(self) -> List[Span]:
        """
        Calculates the critical execution path (longest sequential latency path in DAG).
        """
        self.build_dag()
        if not self.root_spans:
            return []

        def get_critical_path_recursive(current: Span) -> List[Span]:
            if not current.children:
                return [current]
            
            longest_child_path: List[Span] = []
            max_child_latency = -1.0
            
            for child in current.children:
                sub_path = get_critical_path_recursive(child)
                sub_latency = sum(s.duration_ms for s in sub_path)
                if sub_latency > max_child_latency:
                    max_child_latency = sub_latency
                    longest_child_path = sub_path
                    
            return [current] + longest_child_path

        # Find best root path
        best_path: List[Span] = []
        max_duration = -1.0
        for root in self.root_spans:
            path = get_critical_path_recursive(root)
            path_dur = sum(s.duration_ms for s in path)
            if path_dur > max_duration:
                max_duration = path_dur
                best_path = path

        return best_path

    def compute_concurrency_ratio(self) -> float:
        """
        Ratio of sum of individual span durations over total wall-clock duration.
        A ratio > 1.0 indicates concurrent parallel execution.
        """
        total_wall = self.compute_total_trace_duration()
        if total_wall <= 0.0:
            return 1.0
        sum_durations = sum(s.duration_ms for s in self.spans.values())
        return round(sum_durations / total_wall, 2)

    def get_service_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Aggregates execution time and error counts per microservice."""
        self.build_dag()
        breakdown: Dict[str, Dict[str, Any]] = {}
        for span in self.spans.values():
            svc = span.service
            if svc not in breakdown:
                breakdown[svc] = {
                    "total_duration_ms": 0.0,
                    "self_duration_ms": 0.0,
                    "span_count": 0,
                    "error_count": 0
                }
            breakdown[svc]["total_duration_ms"] += span.duration_ms
            breakdown[svc]["self_duration_ms"] += span.self_duration_ms
            breakdown[svc]["span_count"] += 1
            if span.error:
                breakdown[svc]["error_count"] += 1

        for svc in breakdown:
            breakdown[svc]["total_duration_ms"] = round(breakdown[svc]["total_duration_ms"], 2)
            breakdown[svc]["self_duration_ms"] = round(breakdown[svc]["self_duration_ms"], 2)
            breakdown[svc]["avg_duration_ms"] = round(
                breakdown[svc]["total_duration_ms"] / max(1, breakdown[svc]["span_count"]), 2
            )
        return breakdown
