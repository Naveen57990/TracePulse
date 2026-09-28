#!/usr/bin/env python3
"""
TracePulse Tactical CLI
Command-line utility for distributed trace analysis, percentile profiling, and bottleneck isolation.
"""
import sys
import json
import argparse
from typing import List, Dict, Any
from tracepulse.engine.span_graph import SpanGraph
from tracepulse.engine.latency_budget import LatencyBudgetProfiler
from tracepulse.engine.bottleneck_isolator import BottleneckIsolator

def cmd_analyze(args):
    """Analyzes a trace JSON file or synthetic fixture."""
    with open(args.file, 'r') as f:
        data = json.load(f)

    graph = SpanGraph(data.get("trace_id", "trace-cli"))
    for s in data.get("spans", []):
        graph.add_span(
            span_id=s["span_id"],
            name=s["name"],
            service=s["service"],
            start_ms=float(s["start_ms"]),
            duration_ms=float(s["duration_ms"]),
            parent_id=s.get("parent_id"),
            error=bool(s.get("error", False))
        )

    graph.build_dag()
    crit_path = graph.find_critical_path()
    total_dur = graph.compute_total_trace_duration()
    concurrency = graph.compute_concurrency_ratio()
    breakdown = graph.get_service_breakdown()

    isolator = BottleneckIsolator()
    root_cause = isolator.isolate_root_cause(graph)
    cascade = isolator.detect_cascade_risk(graph)

    print("=" * 60)
    print(f"📊 TRACEPULSE ANALYSIS: {graph.trace_id}")
    print("=" * 60)
    print(f"• Total Wall Duration : {total_dur:.2f} ms")
    print(f"• Total Spans          : {len(graph.spans)}")
    print(f"• Concurrency Ratio    : {concurrency}x")
    print(f"• Critical Path Spans  : {len(crit_path)} ({root_cause['critical_path_latency_ms']} ms)")
    print(f"• Cascade Risk Level   : {cascade['risk_level']}")
    
    if root_cause["bottleneck_found"] and root_cause["primary_culprit"]:
        c = root_cause["primary_culprit"]
        print(f"\n🚨 PRIMARY BOTTLENECK: {c['service']} -> {c['name']}")
        print(f"  - Duration : {c['duration_ms']:.2f} ms (Self: {c['self_duration_ms']:.2f} ms, Impact: {c['impact_pct']}%)")
        print("  - Remediations:")
        for rem in root_cause["remediations"]:
            print(f"    * {rem}")

    print("\n📦 SERVICE BREAKDOWN:")
    for svc, b in breakdown.items():
        print(f"  [{svc}] Spans: {b['span_count']} | Self: {b['self_duration_ms']}ms | Total: {b['total_duration_ms']}ms | Errors: {b['error_count']}")
    print("=" * 60)

def cmd_latency(args):
    """Evaluates latency sample percentiles and SLA breach risk."""
    profiler = LatencyBudgetProfiler(sla_budget_ms=args.sla)
    with open(args.file, 'r') as f:
        data = json.load(f)
    
    latencies = [float(x) for x in data.get("latencies", [])]
    result = profiler.evaluate_sla_risk(latencies)
    stats = result["stats"]

    print("=" * 60)
    print(f"⏱️ TRACEPULSE LATENCY PROFILE (SLA Budget: {args.sla} ms)")
    print("=" * 60)
    print(f"• Status            : {result['status']}")
    print(f"• Breach Rate       : {result['sla_breach_rate_pct']}%")
    print(f"• SLA Headroom      : {result['headroom_ms']} ms")
    print(f"• Tail Amplification: {result['tail_amplification_ratio']}x (p99/p50)")
    print(f"• Percentiles       : p50={stats['p50']}ms | p90={stats['p90']}ms | p95={stats['p95']}ms | p99={stats['p99']}ms")
    print(f"• Range             : min={stats['min']}ms | mean={stats['mean']}ms | max={stats['max']}ms (N={stats['count']})")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="TracePulse Distributed Telemetry & Latency Profiler CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Analyze distributed trace DAG and isolate bottlenecks")
    p_analyze.add_argument("--file", "-f", required=True, help="Path to trace JSON file")
    p_analyze.set_defaults(func=cmd_analyze)

    # latency
    p_latency = subparsers.add_parser("latency", help="Profile latency percentiles and SLA budget compliance")
    p_latency.add_argument("--file", "-f", required=True, help="Path to latency array JSON file")
    p_latency.add_argument("--sla", type=float, default=200.0, help="SLA target latency in ms")
    p_latency.set_defaults(func=cmd_latency)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
