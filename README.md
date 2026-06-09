<div align="center">

<img src="docs/screenshots/logo.png" alt="VCM Logo" width="120" height="120" />

# vSphere Compliance Manager

### Enterprise VMware vCenter DRS & Storage Compliance Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.26+-326CE5.svg)](https://kubernetes.io)
[![Docker](https://img.shields.io/badge/Docker-24+-2496ED.svg)](https://docker.com)
[![CI](https://github.com/DavoudTeimouri/vsphere-compliance-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/DavoudTeimouri/vsphere-compliance-manager/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](https://github.com/DavoudTeimouri/vsphere-compliance-manager)

---

**Automate VMware DRS Anti-Affinity rules and Storage placement compliance across your entire vCenter infrastructure.**

[📖 Documentation](#documentation) · [🚀 Quick Start](#quick-start) · [🐛 Report Bug](https://github.com/DavoudTeimouri/vsphere-compliance-manager/issues) · [💡 Request Feature](https://github.com/DavoudTeimouri/vsphere-compliance-manager/issues)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
  - [Docker Compose](#docker-compose)
  - [Kubernetes](#kubernetes)
  - [Helm Chart](#helm-chart)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Development](#development)
- [Contributing](#contributing)
- [Security](#security)
- [Changelog](#changelog)
- [License](#license)

---

## 🎯 Overview

**vSphere Compliance Manager (VCM)** is a production-grade, containerized platform that continuously monitors and enforces VMware infrastructure compliance policies. It connects to vCenter Server (v6.x and above), analyzes VM placement, DRS rules, and storage distribution — then provides actionable reports, automated remediation, and full audit history.

> Designed for VMware administrators who manage multiple clusters and need consistent enforcement of anti-affinity policies and storage separation rules at scale.

---

## ✨ Features

### 🔌 vCenter Integration
- Supports **vCenter Server 6.0, 6.5, 6.7, 7.0, 8.0**
- Multiple vCenter connections managed from one dashboard
- Secure credential storage with AES-256 encryption
- Auto-discovery of Clusters, Hosts, VMs, Datastores, and Datastore Clusters

### 🧠 DRS Compliance Engine
- Pattern-based VM grouping using **configurable Regex**
- Auto-generates Anti-Affinity rules per cluster, per VM group
- Rule sizing: `VMs per rule = host_count − 1` (ensures spread across all hosts)
- Skips groups with a single VM (reported, not errored)
- Deletes stale VCM-managed rules before re-applying
- Preserves manually created rules (only touches `VCM-AAR-*` prefixed rules)

### 🗄️ Storage Compliance Engine
- Detects VMs in the same group sharing a **Datastore or Datastore Cluster**
- Checks **all VM disks** (not just primary) — mounted ISOs are excluded
- Identifies **scattered VMs** with disks spread across multiple datastores
- Generates consolidation & separation **proposals with feasibility checks**
- Applies changes only after explicit user approval (never auto-applies storage moves)

### 👥 Authentication & RBAC
| Role | Capabilities |
|------|-------------|
| **Admin** | Full access: manage users, vCenter connections, settings, apply changes |
| **Operator** | Trigger analysis, approve & apply DRS/storage changes, view reports |
| **Viewer** | Read-only: dashboards, reports, history |

- Local username/password with bcrypt hashing
- **LDAP / Active Directory** integration with group-to-role mapping
- JWT-based session tokens

### 📊 Reporting & History
- Full history of every analysis run with timestamps
- Per-finding tracking: created, actioned, skipped
- DRS rule create/delete history per cluster
- Storage move approval workflow with audit trail
- Export reports to **PDF / CSV / JSON**
- Scheduled analysis with configurable intervals (cron-based)

### ⚙️ Settings & Configuration
- All sensitive settings (credentials, tokens) stored **AES-256 encrypted**
- Configurable VM name patterns (Regex)
- Configurable DRS role naming template
- Custom logo upload for white-labeling
- Analysis schedule (interval or cron expression)
- LDAP/AD server configuration with test connection

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────┐ │
│  │   Frontend   │   │   Backend    │   │  Scheduler  │ │
│  │   React/TS   │──▶│  FastAPI     │──▶│  APScheduler│ │
│  │   Nginx      │   │  Python 3.11 │   │             │ │
│  └──────────────┘   └──────┬───────┘   └─────────────┘ │
│                            │                             │
│  ┌─────────────────────────▼────────────────────────┐   │
│  │                   PostgreSQL                      │   │
│  │   Users │ Analysis Runs │ Findings │ Audit Logs   │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌───────────────────────┐  ┌──────────────────────┐    │
│  │         Redis         │  │      Persistent      │    │
│  │   Cache / Sessions    │  │       Storage        │    │
│  └───────────────────────┘  └──────────────────────┘    │
└────────────────────────────┬────────────────────────────┘
                             │  pyVmomi / REST
                    ┌────────▼─────────┐
                    │  vCenter Server  │
                    │   (v6.x – v8.x)  │
                    └──────────────────┘
```

See [docs/architecture/](docs/architecture/) for detailed diagrams.

---

## 🚀 Quick Start

### Prerequisites
- Docker 24+ and Docker Compose v2
- OR: Kubernetes 1.26+ cluster with `kubectl` configured
- vCenter Server 6.0 or later with read/write API access

### 1 — Clone the repository

```bash
git clone https://github.com/DavoudTeimouri/vsphere-compliance-manager.git
cd vsphere-compliance-manager
```

### 2 — Configure environment

```bash
cp .env.example .env
# Edit .env with your values (see Configuration section)
```

### 3 — Start with Docker Compose

```bash
docker compose up -d
```

The UI will be available at **http://localhost:3000**
Default admin credentials: `admin / VCM@admin2024!` *(change immediately)*

---

## 📦 Installation

### Docker Compose

Suitable for single-node deployments and development.

```bash
# Production-like setup
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker compose logs -f backend

# Scale workers
docker compose up -d --scale worker=3
```

### Kubernetes

```bash
# Apply base manifests
kubectl apply -k k8s/base/

# Check rollout
kubectl rollout status deployment/vcm-backend -n vcm
kubectl rollout status deployment/vcm-frontend -n vcm

# Get the service URL
kubectl get svc vcm-frontend -n vcm
```

### Helm Chart

```bash
# Add the chart repo (if published)
helm repo add vcm https://DavoudTeimouri.github.io/vsphere-compliance-manager
helm repo update

# Install with custom values
helm install vcm vcm/vsphere-compliance-manager \
  --namespace vcm --create-namespace \
  --values deploy/helm/values.yaml \
  --set secrets.secretKey="your-secret-key" \
  --set vcenter.defaultHost="vcenter.example.com"
```

See [`deploy/helm/values.yaml`](deploy/helm/values.yaml) for all configurable options.

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in the values:

```dotenv
# ── Application ──────────────────────────────────────────
SECRET_KEY=change-me-to-a-long-random-string-in-production
ENCRYPTION_KEY=                         # Auto-generated if empty
ACCESS_TOKEN_EXPIRE_MINUTES=480

# ── Database ─────────────────────────────────────────────
DATABASE_URL=postgresql://vcm:vcm_pass@postgres:5432/vcm_db

# ── Redis ────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── Initial Admin User ───────────────────────────────────
ADMIN_USERNAME=admin
ADMIN_PASSWORD=VCM@admin2024!
ADMIN_EMAIL=admin@example.com

# ── LDAP / Active Directory (optional) ───────────────────
LDAP_ENABLED=false
LDAP_SERVER_URL=ldap://dc.example.com:389
LDAP_BASE_DN=DC=example,DC=com
LDAP_BIND_DN=CN=svc-vcm,OU=Service Accounts,DC=example,DC=com
LDAP_BIND_PASSWORD=
LDAP_USER_FILTER=(sAMAccountName={username})
LDAP_GROUP_ADMIN=CN=vcm-admins,OU=Groups,DC=example,DC=com
LDAP_GROUP_OPERATOR=CN=vcm-operators,OU=Groups,DC=example,DC=com
LDAP_USE_SSL=false

# ── Analysis Defaults ────────────────────────────────────
ANALYSIS_SCHEDULE_CRON=0 2 * * *        # Daily at 02:00
ANALYSIS_TIMEOUT_SECONDS=3600
```

All sensitive values in the database are additionally encrypted with the `ENCRYPTION_KEY`.

---

## 🔐 Authentication

### Local Authentication
Users are created via the Admin panel or seeded at startup. Passwords are hashed with **bcrypt** (cost factor 12).

### LDAP / Active Directory
Set `LDAP_ENABLED=true` and configure the LDAP settings. On first login, LDAP users are auto-provisioned in the local database with the role mapped from their group membership:

```
LDAP group: vcm-admins   → Role: Admin
LDAP group: vcm-operators → Role: Operator
(no matching group)       → Role: Viewer
```

Use the **Settings → Authentication** page to test the LDAP connection and validate group mappings before enabling.

---

## 📖 Usage

### 1. Add a vCenter Connection
Navigate to **Settings → vCenter Connections** → click **Add Connection**. Provide the hostname, port, and credentials. Use **Test Connection** to verify before saving.

### 2. Configure Patterns
Go to **Settings → Patterns**. Add Regex patterns to identify VM groups:

| Pattern Type | Example Regex | Matches |
|---|---|---|
| VM Name | `^(WEB)-\d+` | WEB-01, WEB-02, ... |
| VM Name | `^([A-Z]+-[A-Z]+)-` | APP-PROD-01, DB-PROD-02 |
| Datastore | `^DS-(PROD\|DR)-` | DS-PROD-01, DS-DR-01 |

### 3. Run Analysis
Go to **Analysis** → select your vCenter → click **Run Analysis**. The engine will:
1. Collect full inventory (Clusters, VMs, Datastores)
2. Group VMs by your configured patterns
3. Evaluate DRS and Storage compliance
4. Generate findings and proposals

### 4. Review & Apply
- **DRS Rules**: Review proposed rules → click **Apply DRS Changes** (Operator/Admin only)
- **Storage**: Review proposals → click **Approve** on individual moves → the system will track each move
- All actions are logged in the **Audit Log**

---

## 📡 API Reference

The REST API is documented with Swagger UI:
- **Development**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Authenticate, get JWT token |
| `GET` | `/api/vcenter/` | List vCenter connections |
| `POST` | `/api/analysis/run` | Trigger a new analysis |
| `GET` | `/api/analysis/{id}/findings` | Get findings for an analysis run |
| `POST` | `/api/analysis/{id}/apply-drs` | Apply DRS rule changes |
| `GET` | `/api/reports/` | List historical reports |
| `GET` | `/api/reports/{id}/export` | Export report (PDF/CSV/JSON) |
| `GET` | `/api/dashboard/summary` | Get dashboard KPIs |

Full API docs: [docs/api/README.md](docs/api/README.md)

---

## 🛠️ Development

### Requirements
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 15 (or use Docker)

### Backend Setup

```bash
cd backend

# Create virtualenv
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start dependencies
docker compose up postgres redis -d

# Run database migrations
alembic upgrade head

# Seed initial data
python scripts/seed.py

# Start dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

npm install
npm run dev          # Starts on http://localhost:3000
```

### Running Tests

```bash
# Backend unit tests
cd backend
pytest tests/unit/ -v --cov=app --cov-report=html

# Backend integration tests (requires running DB)
pytest tests/integration/ -v

# Frontend tests
cd frontend
npm test
npm run test:coverage
```

### Code Quality

```bash
# Backend
ruff check .
mypy app/
black .

# Frontend
npm run lint
npm run type-check
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description of change"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before submitting a PR.

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feat/my-feature`
3. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/): `feat: add LDAP group sync`
4. **Push** and open a **Pull Request** against `develop`

### Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready, tagged releases |
| `develop` | Integration branch for features |
| `feat/*` | New features |
| `fix/*` | Bug fixes |
| `hotfix/*` | Critical production fixes |
| `release/*` | Release preparation |

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

---

## 🔒 Security

- All secrets are stored encrypted (AES-256 via Fernet)
- Passwords hashed with bcrypt (cost 12)
- JWT tokens with configurable expiry
- HTTPS enforced in production (configure TLS in Ingress)
- Role-based access control on all mutation endpoints
- Full audit log of all user actions and system changes
- No credentials are ever logged

To report a security vulnerability, please see [SECURITY.md](SECURITY.md). **Do not open a public issue.**

---

## 📄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full release history.

---

## 📜 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

Made with ❤️ for VMware administrators everywhere

[⬆ Back to top](#vsphere-compliance-manager)

</div>
