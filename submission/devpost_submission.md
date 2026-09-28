# TracePulse AI — Devpost Submission Write-Up

## 💡 Tagline
Real-Time Distributed Telemetry, Latency SLA Budget Profiler & Cascade Bottleneck Isolation Engine.

---

## 📌 Inspiration
Modern distributed microservice architectures, serverless meshes, and edge applications suffer from silent latency degradation, tail-latency amplification ($p_{99} / p_{50}$ spikes), and unisolated cascading retry storms. When an outage or SLA breach occurs, engineering teams often spend hours digging through fragmented log silos and complex APM dashboards to identify which downstream microservice stalled the critical path.

We built **TracePulse AI** to provide a zero-dependency, ultra-fast distributed tracing telemetry and latency profiler that parses trace execution DAGs in real time, calculates exact critical paths, profiles latency SLAs, and isolates root-cause bottlenecks with synthesized remediations.

---

## ⚙️ What It Does
1. **Distributed Execution DAG Analyzer**: Automatically links parent-child span hierarchies, detects concurrent parallel execution branches, and computes total wall-clock duration and critical path latency.
2. **Deterministic Latency Budgeting**: Analyzes latency quantile distributions ($p_{50}, p_{90}, p_{95}, p_{99}, p_{99.9}$), calculates SLA headroom, and tracks tail-latency amplification ratios.
3. **Exclusive Self-Time Root-Cause Isolation**: Pinpoints the exact microservice and span causing latency spikes or errors by calculating exclusive span self-time (excluding child execution), eliminating false-positive blames on outer caller wrappers.
4. **Interactive Cyberdeck Web Console**: Features live SVG trace waterfall visualizers, interactive SLA budget and traffic sliders, fault injection sandbox (DB connection exhaustion, cache miss storms, network jitter), and custom OpenTelemetry/Jaeger JSON dropzone.
5. **Tactical CLI**: Provides command-line distributed trace analysis and latency profile evaluation for CI/CD observability pipelines.

---

## 🛠️ How We Built It
- **Algorithmic Core**: Pure Python 3.10+ engine (`span_graph.py`, `latency_budget.py`, `bottleneck_isolator.py`) engineered with 100% deterministic coverage (8/8 unit tests executing in `0.000s`).
- **Interactive Web Cyberdeck**: Built with HTML5, CSS Grid/Flexbox, and modern JavaScript with luxury typography (`Plus Jakarta Sans`, `Space Grotesk`, `JetBrains Mono`) deployed globally to Vercel.
- **Automated Verification**: End-to-end unit and CLI validation with synthetic distributed trace fixtures.

---

## 🧗 Challenges We Ran Into
- **False Positive Caller Blame**: In distributed tracing, a root gateway span may show a 200ms duration simply because it is waiting for a 180ms child database query. We engineered an exclusive self-time metric that subtracts child span latencies, ensuring only the true bottleneck microservice is flagged.
- **Zero-Dependency Latency Quantiles**: Implementing smooth percentile quantile calculations ($p_{50}, p_{90}, p_{95}, p_{99}$) using linear interpolation without relying on external statistical libraries (like NumPy or SciPy) to maintain ultra-fast execution.

---

## 🏆 Accomplishments That We're Proud Of
- Passing 8/8 comprehensive deterministic unit tests in **0.000s** flat.
- Creating an intuitive, highly responsive Cyberdeck UI where any developer or judge can inject faults, adjust SLA budgets, or upload their own JSON traces.
- Delivering a production-ready solution that operates completely without external heavyweight cloud dependencies.

---

## 📚 What We Learned
- How critical path analysis in distributed tracing DAGs drastically accelerates incident response compared to aggregate service averages.
- The mathematical dynamics of tail-latency amplification ($p_{99} / p_{50}$) under varying concurrent request volumes.

---

## 🚀 What's Next for TracePulse AI
- Real-time eBPF kernel-level socket hook integration for automated zero-code span collection.
- Automated Kubernetes Horizontal Pod Autoscaler (HPA) triggers based on predicted SLA headroom degradation.
- Multi-cluster distributed span correlation across hybrid cloud environments.

---

## 🏷️ Built With
`python3`, `distributed-tracing`, `opentelemetry`, `jaeger`, `latency-budgeting`, `sla-monitoring`, `microservices`, `cyberdeck-ui`, `html5`, `css3`, `javascript`, `vercel`, `edge-computing`

---

## 🔗 Try It Out
- **Live Interactive Web Console**: [https://tracepulse-ai.vercel.app](https://tracepulse-ai.vercel.app)
- **Public GitHub Repository**: [https://github.com/Naveen57990/TracePulse](https://github.com/Naveen57990/TracePulse)
