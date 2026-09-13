# GitHub Actions and Argo CD Learning Guide

This stage separates continuous integration from continuous deployment:

```text
Git push -> GitHub Actions -> test -> build -> GHCR -> update values-gitops.yaml
                                                        |
                                                        v
                                               Argo CD detects Git
                                                        |
                                                        v
                                                  Kubernetes sync
```

## 1. Publish the repository

Create an empty GitHub repository, then run from the OpsLab directory:

```powershell
git init -b main
git add .
git commit -m "feat: create OpsLab DevOps learning stack"
git remote add origin https://github.com/varel183/opslab.git
git push -u origin main
```

The workflow tests the API, builds an immutable image tagged with the Git commit SHA,
pushes it to GitHub Container Registry, and commits that exact tag to
`helm/opslab/values-gitops.yaml`.

In repository settings, Actions must have read/write workflow permissions. For a public
repository, make the GHCR package public so the local Kind cluster can pull it without an
image pull secret. Private repositories require registry credentials in Kubernetes.

## 2. Access Argo CD

Argo CD is installed in the `argocd` namespace. Forward its HTTPS service:

```powershell
kubectl port-forward service/argocd-server -n argocd 8080:443
```

Open <https://localhost:8080>. A local certificate warning is expected. The username is
`admin`. Read the generated learning password without saving it to a file:

```powershell
kubectl get secret argocd-initial-admin-secret -n argocd `
  -o jsonpath="{.data.password}" | ForEach-Object {
    [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_))
  }
```

Change the initial password after the first login.

## 3. Connect the application

The ready-to-use `argocd/application.yaml` points to the public OpsLab repository. Apply it:

```powershell
kubectl apply -f argocd/application.yaml
kubectl get applications -n argocd
```

Argo CD will render the chart, create `opslab-gitops`, and synchronize the application.

## 4. Observe self-healing

After the application is healthy, manually scale its Deployment and watch Argo CD restore
the replica count stored in Git:

```powershell
kubectl scale deployment opslab-api --replicas=4 -n opslab-gitops
kubectl get deployment -n opslab-gitops -w
```

This differs from plain Helm: Helm acts only when invoked, while Argo CD continuously
compares the cluster with Git and corrects drift.
