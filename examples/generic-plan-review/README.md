# nullstate Generic Plan Review Demo

Plan-only scenario for unsupported IaC providers. This fixture intentionally exposes administrative ingress from `0.0.0.0/0` to port `22` so nullstate can produce a deterministic review finding without a live sandbox.

Use this mode when a provider cannot safely be emulated. nullstate can still preserve evidence, generate attack hypotheses, and produce a report.
