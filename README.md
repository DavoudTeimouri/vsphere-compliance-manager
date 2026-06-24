<div align="center">

<img src="docs/screenshots/logo.svg" alt="VCM Logo" width="400" height="400" />

# vSphere Compliance Manager

### Enterprise VMware vCenter DRS & Storage Compliance Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.26+-326CE5.svg)](https://kubernetes.io)
[![Docker](https://img.shields.io/badge/Docker-24+-2496ED.svg)](https://docker.com)
[![CI](https://github.com/DavoudTeimouri/vsphere-compliance-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/DavoudTeimouri/vsphere-compliance-manager/actions)

**Status:** Active development · Current release `1.3.4-beta` (pre-release)

[🐛 Report Bug](https://github.com/davoudteimouri/vsphere-compliance-manager/issues) · [💡 Request Feature](https://github.com/davoudteimouri/vsphere-compliance-manager/issues)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Docker Images](#docker-images)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Volumes and Data](#volumes-and-data)
- [Logging](#logging)
- [Scaling](#scaling)
- [Authentication](#authentication)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Guides](#guides)
- [Testing with vcsim](#testing-with-vcsim)
- [Development](#development)
- [Contributing](#contributing)
- [Security](#security)
- [Changelog](#changelog)
- [License](#license)

---

## Overview

**vSphere Compliance Manager (VCM)** is a production-grade containerized platform that continuously monitors and enforces VMware infrastructure compliance. It connects to vCenter Server v6.x and above, analyzes VM placement, DRS rules, and storage distribution, then provides actionable reports, automated remediation, and full audit history.

---

## Features

**vCenter Integration**
Supports vCenter Server 6.0 through 8.0. Multiple connections managed from one dashboard. Credentials stored with AES-256 encryption. Auto-discovery of Clusters, Hosts, VMs, Datastores, and Datastore Clusters.

**DRS Compliance Engine**
Regex-based VM grouping. Anti-Affinity rules sized as `host_count − 1` VMs per rule. Stale VCM-managed rules removed before re-applying. Manually created rules never touched. Single-VM groups skipped and reported.

**Storage Compliance Engine**
Detects VMs sharing a Datastore or Datastore Cluster. All VM disks checked (ISO mounts excluded). Scattered VMs identified. Separation proposals generated with feasibility checks. Changes applied only after explicit approval.

**RBAC**

| Role | Capabilities |
|------|-------------|
| Admin | Full access: users, connections, settings, apply changes |
| Operator | Trigger analysis, approve DRS and storage changes, view reports |
| Viewer | Read-only: dashboards, reports, history |

**Reporting**
Full analysis history. PDF, CSV, JSON export. Scheduled analysis via cron. Storage move approval workflow with audit trail.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes / Docker                   │
│                                                          │
│  ┌────────────┐    ┌─────────────┐   ┌───────────────┐  │
│  │  Frontend  │    │   Backend   │   │    Worker     │  │
│  │  React 18  │───▶│  FastAPI    │──▶│ APScheduler   │  │
│  │  Nginx     │    │  Python 3.11│   │               │  │
│  └────────────┘    └──────┬──────┘   └───────────────┘  │
│                           │                              │
│          ┌────────────────┼───────────────┐              │
│          ▼                ▼               ▼              │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐       │
│  │  PostgreSQL  │  │  Redis   │  │   Uploads    │       │
│  │  StatefulSet │  │StatefulSet│  │     PVC      │       │
│  │  vcm_pgdata  │  │ vcm_redis│  │  vcm_uploads │       │
│  └──────────────┘  └──────────┘  └──────────────┘       │
└─────────────────────────────┬───────────────────────────┘
                              │ pyVmomi / port 443
                     ┌────────▼─────────┐
                     │  vCenter Server  │
                     │   v6.x – v8.x    │
                     └──────────────────┘
```

See [docs/architecture/README.md](docs/architecture/README.md) for full diagrams.

---

## Docker Images

Images are published to GHCR on every tagged release. Images are **never** built on branch pushes.

| Image | Registry |
|-------|----------|
| Backend | `ghcr.io/davoudteimouri/vsphere-compliance-manager/backend` |
| Frontend | `ghcr.io/davoudteimouri/vsphere-compliance-manager/frontend` |

Available tags: `1.3.4-beta`, `latest`

```bash
docker pull ghcr.io/davoudteimouri/vsphere-compliance-manager/backend:1.3.4-beta
docker pull ghcr.io/davoudteimouri/vsphere-compliance-manager/frontend:1.3.4-beta
```

Packages: [github.com/davoudteimouri/vsphere-compliance-manager/pkgs/container](https://github.com/davoudteimouri/vsphere-compliance-manager/pkgs/container/vsphere-compliance-manager%2Fbackend)

---

## Quick Start

**Option A — Pre-built images (recommended)**

```bash
git clone https://github.com/davoudteimouri/vsphere-compliance-manager.git
cd vsphere-compliance-manager
cp .env.example .env
nano .env
VCM_VERSION=1.3.4-beta docker compose up -d
```

UI available at `http://localhost:3000` · Default credentials: `admin / VCM@admin2024!`

**Option B — Test without a real vCenter**

```bash
VCM_VERSION=1.3.4-beta \
  docker compose -f docs/vcsim/docker-compose.vcsim.yml up -d
pip install pyVmomi
python3 docs/vcsim/seed_vcsim.py --seed 42
```

**Option C — Build from source**

```bash
git clone https://github.com/davoudteimouri/vsphere-compliance-manager.git
cd vsphere-compliance-manager
cp .env.example .env
nano .env
docker compose up -d --build
```

---

## Installation

### Docker Compose

```bash
cp .env.example .env
VCM_VERSION=1.3.4-beta docker compose up -d
docker compose logs -f backend
```

To upgrade:

```bash
VCM_VERSION=1.4.0 docker compose pull
VCM_VERSION=1.4.0 docker compose up -d
```

Full guide: [docs/deployment/README.md](docs/deployment/README.md)

### Kubernetes

```bash
kubectl apply -k k8s/overlays/prod/
kubectl rollout status deployment/vcm-backend -n vcm
kubectl get ingress vcm-ingress -n vcm
```

Manifest structure:

```
k8s/
  base/
    namespace.yaml          vcm namespace
    configmap.yaml          ConfigMap and Secret templates
    postgres.yaml           StatefulSet, headless Service, Secret template
    redis.yaml              StatefulSet, headless Service
    volumes/
      pvc-uploads.yaml      5Gi ReadWriteMany for multi-pod upload access
      pvc-postgres.yaml     reference — StatefulSet manages its own PVC
      pvc-redis.yaml        reference — StatefulSet manages its own PVC
    backend.yaml            Deployment, Service, ServiceAccount, HPA
    frontend.yaml           Deployment, Service, Ingress
  overlays/
    dev/                    1 replica, DEBUG logging
    staging/                2 replicas, staging hostname
    prod/                   3 replicas, production hostname, StorageClass overrides
```

To upgrade:

```bash
nano k8s/overlays/prod/kustomization.yaml
kubectl apply -k k8s/overlays/prod/
kubectl rollout status deployment/vcm-backend -n vcm
```

### Helm

```bash
helm install vcm ./deploy/helm \
  --namespace vcm \
  --create-namespace \
  --set app.version="1.3.4-beta" \
  --set app.secretKey="$(openssl rand -base64 32)" \
  --set app.adminPassword="YourPassword@123" \
  --set ingress.host="vcm.your-domain.com"
```

To upgrade:

```bash
helm upgrade vcm ./deploy/helm --reuse-values --set app.version="1.4.0"
```

---

## Configuration

Copy `.env.example` to `.env` and set these minimum required values:

```
SECRET_KEY=<random 32+ char string — run: openssl rand -base64 32>
ADMIN_PASSWORD=<strong password>
DATABASE_URL=postgresql://vcm:vcm_pass@postgres:5432/vcm_db
REDIS_URL=redis://redis:6379/0
```

LDAP / Active Directory:

```
LDAP_ENABLED=true
LDAP_SERVER_URL=ldap://dc.example.com:389
LDAP_BASE_DN=DC=example,DC=com
LDAP_BIND_DN=CN=svc-vcm,OU=ServiceAccounts,DC=example,DC=com
LDAP_BIND_PASSWORD=<service account password>
LDAP_GROUP_ADMIN=CN=vcm-admins,OU=Groups,DC=example,DC=com
LDAP_GROUP_OPERATOR=CN=vcm-operators,OU=Groups,DC=example,DC=com
```

Full reference: [`.env.example`](.env.example)

---

## Volumes and Data

VCM uses three isolated persistent storage volumes.

| Volume | Purpose | Access Mode | Recommended Size |
|--------|---------|-------------|-----------------|
| `vcm_pgdata` | PostgreSQL: users, analysis history, findings, audit log | ReadWriteOnce | 20 GB+ |
| `vcm_redis` | Redis: session cache, task queue | ReadWriteOnce | 2 GB |
| `vcm_uploads` | Logo files, exported reports | ReadWriteMany (K8s) | 5 GB+ |

**Docker Compose — volume management**

List volumes:

```bash
docker volume ls
docker volume inspect vcm_pgdata
```

Backup PostgreSQL:

```bash
docker exec vcm-backend-1 pg_dump -U vcm vcm_db > backup-$(date +%Y%m%d).sql
```

Restore PostgreSQL:

```bash
cat backup-20260619.sql | docker exec -i vcm-postgres-1 psql -U vcm vcm_db
```

Full reset (all data deleted):

```bash
docker compose down -v
VCM_VERSION=1.3.4-beta docker compose up -d
```

**Kubernetes — volume management**

PostgreSQL and Redis use StatefulSet `volumeClaimTemplates` — Kubernetes provisions their PVCs automatically. The uploads PVC requires `ReadWriteMany`.

List PVCs:

```bash
kubectl get pvc -n vcm
```

Expected output:

```
NAME                           CAPACITY   ACCESS MODES
postgres-data-vcm-postgres-0   20Gi       RWO
redis-data-vcm-redis-0         2Gi        RWO
vcm-uploads                    5Gi        RWX
```

Backup from Kubernetes:

```bash
kubectl exec -n vcm statefulset/vcm-postgres -- \
  pg_dump -U vcm vcm_db > backup-$(date +%Y%m%d).sql
```

Restore to Kubernetes:

```bash
kubectl exec -n vcm -i statefulset/vcm-postgres -- \
  psql -U vcm vcm_db < backup-20260619.sql
```

Resize uploads PVC:

```bash
kubectl patch pvc vcm-uploads -n vcm \
  -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
```

---

## Logging

All backend logs are structured JSON in production.

**Log levels**

Set `LOG_LEVEL` in `.env` or Kubernetes ConfigMap:

| Level | When to use |
|-------|-------------|
| `DEBUG` | Development and troubleshooting |
| `INFO` | Production default |
| `WARNING` | High-traffic, reduce verbosity |
| `ERROR` | Minimal logging only |

**Docker Compose**

```bash
docker compose logs -f backend
docker compose logs backend --since 1h
docker compose logs backend 2>&1 | python3 -m json.tool
```

**Kubernetes**

Follow logs:

```bash
kubectl logs -n vcm deployment/vcm-backend -f
```

Last hour only:

```bash
kubectl logs -n vcm deployment/vcm-backend --since=1h
```

All backend pods simultaneously:

```bash
kubectl logs -n vcm -l app=vcm-backend -f --max-log-requests=6
```

Filter errors:

```bash
kubectl logs -n vcm deployment/vcm-backend | grep '"level":"ERROR"'
```

**Log format (JSON)**

```json
{
  "timestamp": "2026-06-19T10:23:45.123Z",
  "level": "INFO",
  "logger": "vcm.main",
  "message": "HTTP",
  "method": "POST",
  "path": "/api/analysis/run",
  "status": 202,
  "duration_ms": 12.4
}
```

**Log aggregation**

Add these labels to your pods for Promtail / Loki:

```yaml
annotations:
  promtail.io/scrape: "true"
  promtail.io/job: "vcm-backend"
```

---

## Scaling

**Docker Compose**

```bash
VCM_VERSION=1.3.4-beta docker compose up -d --scale backend=3
```

Note: multiple backend replicas require the uploads volume to be on shared storage.

**Kubernetes — manual**

```bash
kubectl scale deployment vcm-backend -n vcm --replicas=5
kubectl scale deployment vcm-frontend -n vcm --replicas=3
```

**Kubernetes — HPA**

The backend includes an HPA by default:

```
minReplicas: 2  maxReplicas: 6
CPU target: 70%  Memory target: 80%
```

Monitor HPA:

```bash
kubectl get hpa -n vcm
kubectl describe hpa vcm-backend -n vcm
```

**Kubernetes — resource tuning**

Override limits in the prod overlay:

```yaml
patches:
  - target:
      kind: Deployment
      name: vcm-backend
    patch: |-
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/cpu
        value: "2000m"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/memory
        value: "2Gi"
```

---

## Authentication

**Local users**

Created via Admin panel. Passwords hashed with bcrypt cost 12.

If login fails, reset from inside the container:

```bash
docker exec vcm-backend-1 python scripts/reset_admin.py
docker exec vcm-backend-1 python scripts/reset_admin.py --password "NewPass@123"
```

Kubernetes:

```bash
kubectl exec -n vcm deployment/vcm-backend -- \
  python scripts/reset_admin.py --password "NewPass@123"
```

**LDAP / Active Directory**

Set `LDAP_ENABLED=true`. On first login, LDAP users are auto-provisioned:

```
vcm-admins    group → Admin role
vcm-operators group → Operator role
(no match)         → Viewer role
```

Test LDAP before enabling:

```bash
curl -s -X POST http://localhost:8000/api/settings/ldap/test \
  -H "Authorization: Bearer <admin-token>"
```

---

## Usage

**Step 1 — Add a vCenter connection**

Settings → vCenter Connections → Add Connection → Test Connection → Save.

**Step 2 — Configure patterns**

Settings → Patterns. Examples:

| Type | Regex | Matches |
|------|-------|---------|
| VM Name | `^(WEB)-` | WEB-01, WEB-02 |
| VM Name | `^(DB)-(PROD\|DR)-` | DB-PROD-01, DB-DR-02 |
| Datastore | `^(DS-PROD)-` | DS-PROD-01 |

**Step 3 — Run analysis**

Analysis → select vCenter → Run Analysis.

**Step 4 — Review and apply**

Review findings. Approve DRS changes (Operator/Admin). Approve storage proposals individually.

---

## API Reference

Interactive docs: `http://localhost:8000/docs` (Swagger) · `http://localhost:8000/redoc`

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | Public | Authenticate, returns JWT |
| GET | `/api/vcenter/` | Any | List vCenter connections |
| POST | `/api/vcenter/{id}/test` | Admin | Test vCenter connectivity |
| POST | `/api/analysis/run` | Operator+ | Trigger analysis |
| GET | `/api/analysis/{id}/findings` | Any | Get findings |
| POST | `/api/analysis/{id}/apply-drs` | Operator+ | Apply DRS changes |
| GET | `/api/reports/{id}/export` | Any | Export report (PDF/CSV/JSON) |
| GET | `/api/dashboard/summary` | Any | Dashboard KPIs |
| POST | `/api/settings/patterns` | Admin | Create pattern |
| POST | `/api/settings/ldap/test` | Admin | Test LDAP connection |

Full reference: [docs/api/README.md](docs/api/README.md)

---

## Guides

| Guide | Description |
|-------|-------------|
| [Deployment Guide](docs/deployment/README.md) | Docker Compose, Kubernetes, Helm, volumes, backup, scaling, production checklist |
| [vcsim Testing Guide](docs/vcsim/README.md) | Test without a real vCenter using the official VMware simulator |
| [Testing Guide](docs/testing/README.md) | Unit tests, integration tests, randomized vcsim fixtures |
| [API Reference](docs/api/README.md) | All endpoints, request/response formats, authentication |
| [Architecture Guide](docs/architecture/README.md) | System design, data flow, security model, DRS and storage logic |

---

## Testing with vcsim

VCM includes a complete test environment based on vcsim — the official VMware vCenter simulator. No real vCenter required.

```bash
VCM_VERSION=1.3.4-beta \
  docker compose -f docs/vcsim/docker-compose.vcsim.yml up -d

pip install pyVmomi
python3 docs/vcsim/seed_vcsim.py --seed 42
python3 docs/vcsim/seed_vcsim.py --seed 100 --prefixes WEB APP DB CACHE
```

See [docs/vcsim/README.md](docs/vcsim/README.md) for full setup, test scenarios, and API examples.

---

## Development

**Requirements:** Python 3.11+, Node.js 22+, Docker Compose v2

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
docker compose up postgres redis -d
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

**Tests**

```bash
cd backend
pytest tests/unit/ -v --cov=app
pytest tests/integration/ -v
cd ../frontend && npm test
```

**Code quality**

```bash
cd backend && ruff check . && black . && mypy app/ --ignore-missing-imports
cd frontend && npm run lint && npm run type-check
```

**Migrations**

```bash
alembic revision --autogenerate -m "add table"
alembic upgrade head
alembic downgrade -1
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

| Branch | Purpose |
|--------|---------|
| `main` | Tagged releases only |
| `develop` | Integration |
| `feat/*` | New features |
| `fix/*` | Bug fixes |
| `hotfix/*` | Critical fixes |

---

## Security

Credentials encrypted with AES-256. Passwords hashed with bcrypt cost 12. JWT tokens with configurable expiry. TLS enforced via Ingress. Full audit log.

To report a vulnerability: [Security Advisory](https://github.com/davoudteimouri/vsphere-compliance-manager/security/advisories/new)

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

Current: `1.3.4-beta` · [Releases](https://github.com/davoudteimouri/vsphere-compliance-manager/releases)

---

## License

MIT — see [LICENSE](LICENSE).

<div align="center">

[Back to top](#vsphere-compliance-manager)

</div>
