<div align="center">

<img src="docs/screenshots/logo.svg" alt="VCM Logo" width="200" height="200" />

# vSphere Compliance Manager

**Enterprise VMware vCenter DRS & Storage Compliance Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.26+-326CE5.svg)](https://kubernetes.io)
[![Docker](https://img.shields.io/badge/Docker-24+-2496ED.svg)](https://docker.com)
[![CI](https://github.com/DavoudTeimouri/vsphere-compliance-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/DavoudTeimouri/vsphere-compliance-manager/actions)

**Status:** Active development · Current release `1.3.8-beta` (pre-release)

> **Pin a release:** Replace `latest` with a specific tag (e.g. `1.3.8-beta`) in all commands below.

[🐛 Report Bug](https://github.com/davoudteimouri/vsphere-compliance-manager/issues) · [💡 Request Feature](https://github.com/davoudteimouri/vsphere-compliance-manager/issues)

</div>

---

## Overview

**vSphere Compliance Manager (VCM)** is a production-grade containerized platform that continuously monitors and enforces VMware infrastructure compliance. It connects to vCenter Server v6.x–v8.x, analyzes VM placement, DRS rules, and storage distribution, then provides actionable reports, automated remediation, and full audit history.

## Features

| Feature | Description |
|---------|-------------|
| **vCenter Integration** | Multi-connection support, AES-256 credential encryption, auto-discovery of Clusters/Hosts/VMs/Datastores |
| **DRS Compliance Engine** | Regex-based VM grouping, anti-affinity rules sized as `host_count − 1`, stale rule cleanup, manual rule protection |
| **Storage Compliance Engine** | Shared datastore detection, scattered VM identification, separation proposals with feasibility checks |
| **RBAC** | Admin / Operator / Viewer roles with granular permissions |
| **Reporting** | Full analysis history, PDF/CSV/JSON export, scheduled analysis via cron |
| **Audit Trail** | Every action logged with user, timestamp, and IP address |
| **LDAP/AD** | Automatic role mapping from LDAP groups |
| **High Availability** | Kubernetes HPA (2–6 replicas), PostgreSQL/Redis StatefulSets |

## Quick Start

```bash
git clone https://github.com/davoudteimouri/vsphere-compliance-manager.git
cd vsphere-compliance-manager
cp .env.example .env
# Edit .env — set SECRET_KEY and ADMIN_PASSWORD at minimum
VCM_VERSION=latest docker compose up -d
```

UI: `http://localhost:3000` · Default: `admin / VCM@admin2024!` · API docs: `http://localhost:8000/docs`

### Test without a real vCenter

```bash
VCM_VERSION=latest docker compose -f docs/vcsim/docker-compose.vcsim.yml up -d
pip install pyVmomi
python3 docs/vcsim/seed_vcsim.py --seed 42
```
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
│  └──────────────┘  └──────────┘  └──────────────┘       │
└─────────────────────────────┬───────────────────────────┘
                              │ pyVmomi / port 443
                     ┌────────▼─────────┐
                     │  vCenter Server  │
                     │   v6.x – v8.x    │
                     └──────────────────┘
```

See [docs/architecture/README.md](docs/architecture/README.md) for full data flow diagrams.

## Docker Images

| Backend | `ghcr.io/davoudteimouri/vsphere-compliance-manager/backend` |
| Frontend | `ghcr.io/davoudteimouri/vsphere-compliance-manager/frontend` |

```bash
# Use 'latest' or pin a specific version tag
docker pull ghcr.io/davoudteimouri/vsphere-compliance-manager/backend:latest
docker pull ghcr.io/davoudteimouri/vsphere-compliance-manager/frontend:latest
```

## Deployment

| Method | Guide |
|--------|-------|
| Docker Compose | [docs/deployment](docs/deployment/README.md) |
| Kubernetes + Kustomize | [docs/deployment](docs/deployment/README.md#kubernetes) |
| Helm Chart | [docs/deployment](docs/deployment/README.md#helm-chart) |

## Configuration

Copy `.env.example` to `.env` and set:

```
SECRET_KEY=<random 32+ char string — openssl rand -base64 32>
ADMIN_PASSWORD=<strong password>
DATABASE_URL=postgresql://vcm:***@postgres:5432/vcm_db
REDIS_URL=redis://redis:***@123"
```

### LDAP / Active Directory

Set `LDAP_ENABLED=true`. On first login, LDAP users are auto-provisioned:

```
LDAP_SERVER_URL=ldap://dc.example.com:389
LDAP_BASE_DN=DC=example,DC=com
LDAP_BIND_DN=CN=svc-vcm,OU=ServiceAccounts,DC=example,DC=com
LDAP_BIND_PASSWORD=<service-account-password>
LDAP_USER_FILTER=(sAMAccountName={username})
LDAP_GROUP_ADMIN=CN=vcm-admins,OU=Groups,DC=example,DC=com
LDAP_GROUP_OPERATOR=CN=vcm-operators,OU=Groups,DC=example,DC=com
```

## API Reference

Interactive docs at `/docs` (Swagger) and `/redoc` when running.

| Group | Endpoints |
|-------|-----------|
| Auth | `POST /api/auth/login` · `GET /api/auth/me` · `PUT /api/auth/me/password` |
| Users | `GET /api/users/` · `POST /api/users/` · `PUT /api/users/{id}` · `DELETE /api/users/{id}` |
| vCenter | `GET /api/vcenter/` · `POST /api/vcenter/` · `PUT /api/vcenter/{id}` · `DELETE /api/vcenter/{id}` · `POST /api/vcenter/{id}/test` · `GET /api/vcenter/{id}/inventory` |
| Analysis | `GET /api/analysis/` · `POST /api/analysis/run` · `GET /api/analysis/{id}` · `GET /api/analysis/{id}/findings` · `POST /api/analysis/{id}/apply-drs` · `POST /api/analysis/{id}/approve-storage/{finding_id}` |
| Reports | `GET /api/reports/` · `GET /api/reports/{id}` · `GET /api/reports/{id}/export` |
| Settings | `GET /api/settings/` · `PUT /api/settings/` · `GET /api/settings/patterns` · `POST /api/settings/patterns` · `PUT /api/settings/patterns/{id}` · `DELETE /api/settings/patterns/{id}` · `POST /api/settings/ldap/test` |
| Dashboard | `GET /api/dashboard/summary` · `GET /api/dashboard/recent-findings` · `GET /api/dashboard/audit-log` |

## Testing

Three layers of tests:

| Layer | Location | Dependencies |
|-------|----------|--------------|
| Unit — Analysis Engine | `tests/unit/test_analysis_engine.py` | None |
| Unit — Security | `tests/unit/test_security.py` | None |
| Unit — vcsim (randomized) | `tests/unit/test_vcsim.py` | None |
| Integration — API | `tests/integration/test_api.py` | PostgreSQL + Redis |

```bash
# Unit tests only (no dependencies)
cd backend && pip install -r requirements.txt -r requirements-dev.txt
pytest tests/unit/ -v

# All tests (requires PostgreSQL + Redis)
docker compose up postgres redis -d
pytest tests/ -v
```

See [docs/testing/README.md](docs/testing/README.md) for vcsim testing guide.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting and security practices.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT License — see [LICENSE](LICENSE).
