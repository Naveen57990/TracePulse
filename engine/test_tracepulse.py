"""
TracePulse Unit Test Suite
8/8 Deterministic tests verifying DAG parsing, critical path, percentiles, SLA evaluation, and bottleneck isolation.
"""
import unittest
from .span_graph import SpanGraph, Span
from .latency_budget import LatencyBudgetProfiler
from .bottleneck_isolator import BottleneckIsolator

class TestTracePulse(unittest.TestCase):
    def setUp(self):
        self.profiler = LatencyBudgetProfiler(sla_budget_ms=200.0)
        self.isolator = BottleneckIsolator()

    def test_span_graph_creation_and_dag_linking(self):
        graph = SpanGraph("trace-101")
        s1 = graph.add_span("s1", "GET /api/checkout", "api-gateway", 0.0, 150.0)
        s2 = graph.add_span("s2", "auth_check", "auth-service", 10.0, 20.0, parent_id="s1")
        s3 = graph.add_span("s3", "charge_card", "payment-service", 35.0, 90.0, parent_id="s1")
        
        graph.build_dag()
        self.assertEqual(len(graph.root_spans), 1)
        self.assertEqual(graph.root_spans[0].span_id, "s1")
        self.assertEqual(len(s1.children), 2)
        self.assertEqual(graph.compute_total_trace_duration(), 150.0)

    def test_critical_path_calculation(self):
        graph = SpanGraph("trace-102")
        s1 = graph.add_span("s1", "root", "gateway", 0.0, 100.0)
        s2 = graph.add_span("s2", "fast_branch", "cache", 5.0, 15.0, parent_id="s1")
        s3 = graph.add_span("s3", "slow_branch", "database", 5.0, 80.0, parent_id="s1")
        s4 = graph.add_span("s4", "db_read", "postgres", 10.0, 45.0, parent_id="s3")

        path = graph.find_critical_path()
        path_ids = [s.span_id for s in path]
        self.assertEqual(path_ids, ["s1", "s3", "s4"])

    def test_concurrency_ratio_metric(self):
        graph = SpanGraph("trace-103")
        graph.add_span("s1", "parallel_1", "worker-a", 0.0, 50.0)
        graph.add_span("s2", "parallel_2", "worker-b", 0.0, 50.0)
        # Total wall duration = 50ms, sum = 100ms -> concurrency = 2.0
        ratio = graph.compute_concurrency_ratio()
        self.assertEqual(ratio, 2.0)

    def test_service_breakdown_aggregation(self):
        graph = SpanGraph("trace-104")
        graph.add_span("s1", "op1", "order-svc", 0.0, 30.0)
        graph.add_span("s2", "op2", "order-svc", 30.0, 40.0)
        graph.add_span("s3", "op3", "inventory-svc", 70.0, 50.0, error=True)

        breakdown = graph.get_service_breakdown()
        self.assertIn("order-svc", breakdown)
        self.assertEqual(breakdown["order-svc"]["span_count"], 2)
        self.assertEqual(breakdown["order-svc"]["total_duration_ms"], 70.0)
        self.assertEqual(breakdown["inventory-svc"]["error_count"], 1)

    def test_percentile_calculation(self):
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        stats = self.profiler.calculate_percentiles(latencies)
        self.assertEqual(stats["count"], 10)
        self.assertEqual(stats["p50"], 55.0)
        self.assertEqual(stats["min"], 10.0)
        self.assertEqual(stats["max"], 100.0)
        self.assertEqual(stats["mean"], 55.0)

    def test_sla_risk_evaluation_healthy_and_breach(self):
        healthy_samples = [50.0, 60.0, 70.0, 80.0, 90.0]
        res_healthy = self.profiler.evaluate_sla_risk(healthy_samples)
        self.assertEqual(res_healthy["status"], "HEALTHY")
        self.assertEqual(res_healthy["sla_breach_rate_pct"], 0.0)

        critical_samples = [150.0, 190.0, 210.0, 250.0, 300.0]
        res_crit = self.profiler.evaluate_sla_risk(critical_samples)
        self.assertEqual(res_crit["status"], "CRITICAL_BREACH")
        self.assertGreater(res_crit["sla_breach_rate_pct"], 0.0)

    def test_service_budget_allocation(self):
        weights = {"api-gateway": 1.0, "auth-svc": 1.0, "db-query": 2.0}
        budgets = self.profiler.allocate_service_budgets(weights)
        self.assertEqual(budgets["api-gateway"], 50.0)
        self.assertEqual(budgets["auth-svc"], 50.0)
        self.assertEqual(budgets["db-query"], 100.0)
        self.assertEqual(sum(budgets.values()), 200.0)

    def test_bottleneck_isolation_and_remediation(self):
        graph = SpanGraph("trace-105")
        s1 = graph.add_span("s1", "handle_request", "web-server", 0.0, 220.0)
        s2 = graph.add_span("s2", "slow_db_scan", "postgres-db", 10.0, 180.0, parent_id="s1")
        s3 = graph.add_span("s3", "fast_cache", "redis", 5.0, 5.0, parent_id="s1")

        res = self.isolator.isolate_root_cause(graph)
        self.assertTrue(res["bottleneck_found"])
        self.assertEqual(res["primary_culprit"]["service"], "postgres-db")
        self.assertGreater(len(res["remediations"]), 0)

if __name__ == "__main__":
    unittest.main()
