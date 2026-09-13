# Helm Learning Guide

Helm turns related Kubernetes manifests into a versioned package called a chart.
The OpsLab chart installs the API and PostgreSQL. The existing Prometheus and Grafana
installation remains in the original `opslab` namespace while you learn the core concepts.

## Render before installing

```powershell
helm lint helm/opslab
helm template opslab-helm helm/opslab -f helm/opslab/values-dev.yaml
```

Rendering is safe: it produces YAML but does not change the cluster.

## Install a release

```powershell
helm upgrade --install opslab-helm helm/opslab `
  --namespace opslab-helm `
  --create-namespace `
  -f helm/opslab/values-dev.yaml
```

`Chart.yaml` identifies the package, `values.yaml` contains defaults, templates generate
Kubernetes resources, and a release is one installed instance of the chart.

## Change and upgrade

Change `api.replicaCount` in `values-dev.yaml`, then run the same `helm upgrade --install`
command. Inspect revisions with:

```powershell
helm history opslab-helm -n opslab-helm
```

Roll back to revision 1:

```powershell
helm rollback opslab-helm 1 -n opslab-helm
```

## Remove the learning release

```powershell
helm uninstall opslab-helm -n opslab-helm
```

Deleting the namespace also deletes its PostgreSQL claim and data. Keep the original
`opslab` namespace separate so these Helm exercises cannot damage the existing lab.

