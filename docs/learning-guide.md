# OpsLab Learning Guide

## Debugging order

When something fails, move from the outside toward the dependency that failed:

1. Confirm the symptom with a repeatable request.
2. Check the workload state with `kubectl get pods -n opslab`.
3. Read recent events with `kubectl get events -n opslab --sort-by=.lastTimestamp`.
4. Inspect the relevant resource with `kubectl describe`.
5. Read application logs with `kubectl logs`.
6. Test DNS, ports, configuration, and credentials separately.
7. Apply one fix and verify both recovery and monitoring signals.

## Important boundaries

- Docker packages and runs one process environment.
- Kubernetes maintains desired workload state across containers and nodes.
- Terraform manages declarative infrastructure and records state.
- GitHub Actions executes repeatable repository workflows.
- Prometheus collects time-series metrics; Grafana visualizes and queries them.

## Useful commands

```powershell
docker compose up --build
docker compose ps
docker compose logs api

kubectl get all -n opslab
kubectl describe pod -n opslab <pod-name>
kubectl logs -n opslab <pod-name>
kubectl port-forward -n opslab service/opslab-api 8000:8000

terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan
```

