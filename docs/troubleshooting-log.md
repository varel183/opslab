# Troubleshooting Log

Use this template for every controlled failure.

## Incident template

- **Symptom:** What did the user or operator observe?
- **Evidence:** Which logs, events, metrics, or status output support the diagnosis?
- **Hypothesis:** What might explain the evidence?
- **Test:** Which safe command or experiment confirms or rejects the hypothesis?
- **Root cause:** What actually failed, and why?
- **Fix:** What restored the service?
- **Prevention:** Which validation, automation, alert, or design change prevents recurrence?

## Planned labs

1. Set the API database host to `wrong-db` and investigate readiness failures.
2. Change the API image tag to a nonexistent tag and diagnose `ImagePullBackOff`.
3. Change the Service selector and trace why traffic cannot reach healthy pods.
4. Set an unrealistically low memory limit and identify an OOM termination.
5. Manually change the Terraform-managed quota and detect configuration drift with `terraform plan`.
6. Break an API test and use the CI logs to locate the failing assertion.
7. Generate repeated 404 responses and inspect the Prometheus request counter.

## Incident 1: Kubernetes rejected the named container user

- **Symptom:** Both API pods stayed in `CreateContainerConfigError` while their image was present.
- **Evidence:** `kubectl describe pod` reported that `runAsNonRoot` could not verify the image user `opslab`.
- **Hypothesis:** Kubernetes requires a numeric UID to prove that the configured image user is not root.
- **Test:** Inspect the pod events and compare the Deployment security context with the Dockerfile `USER` instruction.
- **Root cause:** The Dockerfile used a user name; the kubelet cannot resolve image-local names before starting the container.
- **Fix:** Assign UID/GID `10001` at build time and use `USER 10001:10001`.
- **Prevention:** Use explicit high numeric IDs in images deployed with `runAsNonRoot`, and test images on Kubernetes in CI.

## Incident 2: CI could not import the application package

- **Symptom:** GitHub Actions stopped during test collection with `ModuleNotFoundError: No module named 'app'`.
- **Evidence:** Linting succeeded, but the runner invoked the standalone `pytest` executable while local verification used `python -m pytest`.
- **Hypothesis:** The two invocation methods constructed different Python import paths on the Linux runner.
- **Test:** Compare the workflow command with the exact local command that passes.
- **Root cause:** The repository root was not available on `sys.path` under the standalone CI invocation.
- **Fix:** Run tests as `python -m pytest -q` in both environments.
- **Prevention:** Keep local and CI verification commands identical and document them in one canonical place.

## Incident 3: Liveness probe restarted an API during a busy rollout

- **Symptom:** One newly deployed API container restarted once while the observability stack was starting.
- **Evidence:** Pod events showed repeated readiness timeouts followed by a liveness timeout and kubelet restart; the previous container exited cleanly with code `0`.
- **Hypothesis:** Heavy concurrent image pulls and backend startup temporarily delayed the API beyond the liveness probe's one-second timeout.
- **Test:** Inspect `kubectl describe pod` and previous container logs; the service became stable after node load dropped.
- **Root cause:** Liveness checking began without a startup probe, so Kubernetes treated slow initialization like a dead application.
- **Fix:** Add a startup probe and explicit three-second readiness/liveness timeouts.
- **Prevention:** Use startup probes for applications whose initialization time varies, especially on resource-constrained development clusters.
