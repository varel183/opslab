# OpsLab: Learn DevOps by Building and Breaking a Service

OpsLab is a small FastAPI task service used to practice Docker, Kubernetes, Terraform,
GitHub Actions, Prometheus, and Grafana. The goal is not only to deploy it, but also to
create controlled failures and diagnose them from evidence.

## 1. Run the application directly

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open <http://localhost:8000/docs>. The default local database is SQLite.

Run tests:

```powershell
python -m pytest -q
```

## 2. Run with Docker Compose

Start Docker Desktop, then run:

```powershell
docker compose up --build
```

The API is available at <http://localhost:8000/docs>. Compose connects it to PostgreSQL
and stores database data in a named volume. Stop containers with `docker compose down`.
Do not add `--volumes` unless you intentionally want to delete the learning database.

## 3. Deploy to local Kubernetes

Create a local Kind cluster, build the image, and load it into the cluster:

```powershell
kind create cluster --name opslab
docker build -t opslab-api:local .
kind load docker-image opslab-api:local --name opslab
kubectl apply -k kubernetes
kubectl rollout status deployment/opslab-api -n opslab
kubectl port-forward -n opslab service/opslab-api 8000:8000
```

The included Secret contains a learning-only password committed for reproducibility.
Never commit real credentials. A production environment should use a secret manager.

Monitoring access:

```powershell
kubectl port-forward -n opslab service/prometheus 9090:9090
kubectl port-forward -n opslab service/grafana 3000:3000
```

Grafana uses `admin` / `opslab-admin` for this local lab. Prometheus is provisioned as
the default data source. Query `rate(opslab_http_requests_total[5m])` after generating
some API traffic.

## 4. Apply Terraform controls

Terraform intentionally manages infrastructure controls rather than duplicating the
application manifests. Install Terraform, deploy the Kubernetes resources above, and run:

```powershell
terraform -chdir=terraform init
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan
terraform -chdir=terraform apply
```

If your context is not `kind-opslab`, copy `terraform.tfvars.example` to
`terraform.tfvars` and change `kube_context`. Inspect it with `kubectl config get-contexts`.

## 5. CI/CD

The GitHub Actions workflow lints, tests, builds an image on pull requests, and publishes
an image to GitHub Container Registry on pushes to `main`. Repository package permissions
must allow GitHub Actions to write packages.

## Learning material

- [Learning guide](docs/learning-guide.md)
- [Helm guide](docs/helm-guide.md)
- [GitHub Actions and Argo CD guide](docs/gitops-guide.md)
- [Troubleshooting log](docs/troubleshooting-log.md)
