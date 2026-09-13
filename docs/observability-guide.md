# OpsLab Observability Guide

This lab makes the three telemetry signals visible in one Grafana dashboard.

```text
OpsLab API -- /metrics --> Prometheus -- remote_write --> Mimir -- PromQL -- Grafana
     |
     +-- JSON stdout logs --> Alloy --> Loki ----------- LogQL ----+
     |
     +-- OTLP/HTTP traces -----------> Tempo ---------- TraceQL ---+
```

## What each component does

- **Prometheus** actively scrapes the API every five seconds. It is the collector and a
  short-term metric database.
- **Mimir** receives a copy through Prometheus `remote_write`. It represents scalable,
  long-term Prometheus-compatible metric storage.
- **Alloy** discovers Pods and forwards their stdout logs. It is the telemetry collector,
  not a database.
- **Loki** stores and searches logs by labels with LogQL.
- **Tempo** receives spans from the instrumented API over OTLP and reconstructs each
  request as a trace.
- **Grafana** queries all backends and displays metrics, logs, and traces together.

The backends use `emptyDir` for a laptop-friendly lab. Their data is intentionally
ephemeral and is lost when their Pods are recreated.

## Open the demo

Terminal 1 - Grafana:

```powershell
kubectl port-forward service/observability-grafana 3001:3000 -n observability
```

Open <http://localhost:3001/d/opslab-observability>. Anonymous read-only access is enabled.
For admin access, use `admin` / `opslab-admin` (learning environment only).

Terminal 2 - API:

```powershell
kubectl port-forward service/opslab-api 8000:8000 -n opslab-gitops
```

Generate normal, slow, and failed requests:

```powershell
1..10 | ForEach-Object { Invoke-RestMethod http://localhost:8000/health }
Invoke-RestMethod "http://localhost:8000/demo/slow?delay_ms=1500"
try { Invoke-RestMethod http://localhost:8000/demo/error } catch { $_.Exception.Message }
```

Wait about 10 seconds and refresh the dashboard:

1. **Prometheus panel:** the slow request raises p95 latency.
2. **Mimir panel:** HTTP status `200` and `500` series appear from remote-written metrics.
3. **Loki panel:** each request appears as JSON containing status, duration, and trace ID.
4. **Tempo panel:** open a trace to inspect the request span and its timing.

## Useful checks

```powershell
kubectl get applications -n argocd
kubectl get pods -n observability
kubectl logs deployment/observability-alloy -n observability
kubectl logs deployment/observability-prometheus -n observability
```

This chart is deliberately a single-node learning setup. Production deployments need
persistent object storage, authentication, TLS, retention planning, replication, and
resource sizing.
