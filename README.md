1|<div align="center">
2|
3|<img src="docs/screenshots/logo.svg" alt="VCM Logo" width="400" height="400" />
4|
5|# vSphere Compliance Manager
6|
7|### Enterprise VMware vCenter DRS & Storage Compliance Platform
8|
9|[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
10|[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
11|[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com)
12|[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
13|[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.26+-326CE5.svg)](https://kubernetes.io)
14|[![Docker](https://img.shields.io/badge/Docker-24+-2496ED.svg)](https://docker.com)
15|[![CI](https://github.com/DavoudTeimouri/vsphere-compliance-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/DavoudTeimouri/vsphere-compliance-manager/actions)
16|
17|**Status:** Active development · Current release `1.3.6-beta` (pre-release)
18|
19|[🐛 Report Bug](https://github.com/davoudteimouri/vsphere-compliance-manager/issues) · [💡 Request Feature](https://github.com/davoudteimouri/vsphere-compliance-manager/issues)
20|
21|</div>
22|
23|---
24|
25|## Table of Contents
26|
27|- [Overview](#overview)
28|- [Features](#features)
29|- [Architecture](#architecture)
30|- [Docker Images](#docker-images)
31|- [Quick Start](#quick-start)
32|- [Installation](#installation)
33|- [Configuration](#configuration)
34|- [Volumes and Data](#volumes-and-data)
35|- [Logging](#logging)
36|- [Scaling](#scaling)
37|- [Authentication](#authentication)
38|- [Usage](#usage)
39|- [API Reference](#api-reference)
40|- [Guides](#guides)
41|- [Testing with vcsim](#testing-with-vcsim)
42|- [Development](#development)
43|- [Contributing](#contributing)
44|- [Security](#security)
45|- [Changelog](#changelog)
46|- [License](#license)
47|
48|---
49|
50|## Overview
51|
52|**vSphere Compliance Manager (VCM)** is a production-grade containerized platform that continuously monitors and enforces VMware infrastructure compliance. It connects to vCenter Server v6.x and above, analyzes VM placement, DRS rules, and storage distribution, then provides actionable reports, automated remediation, and full audit history.
53|
54|---
55|
56|## Features
57|
58|**vCenter Integration**
59|Supports vCenter Server 6.0 through 8.0. Multiple connections managed from one dashboard. Credentials stored with AES-256 encryption. Auto-discovery of Clusters, Hosts, VMs, Datastores, and Datastore Clusters.
60|
61|**DRS Compliance Engine**
62|Regex-based VM grouping. Anti-Affinity rules sized as `host_count − 1` VMs per rule. Stale VCM-managed rules removed before re-applying. Manually created rules never touched. Single-VM groups skipped and reported.
63|
64|**Storage Compliance Engine**
65|Detects VMs sharing a Datastore or Datastore Cluster. All VM disks checked (ISO mounts excluded). Scattered VMs identified. Separation proposals generated with feasibility checks. Changes applied only after explicit approval.
66|
67|**RBAC**
68|
69|| Role | Capabilities |
70||------|-------------|
71|| Admin | Full access: users, connections, settings, apply changes |
72|| Operator | Trigger analysis, approve DRS and storage changes, view reports |
73|| Viewer | Read-only: dashboards, reports, history |
74|
75|**Reporting**
76|Full analysis history. PDF, CSV, JSON export. Scheduled analysis via cron. Storage move approval workflow with audit trail.
77|
78|---
79|
80|## Architecture
81|
82|```
83|┌─────────────────────────────────────────────────────────┐
84|│                    Kubernetes / Docker                   │
85|│                                                          │
86|│  ┌────────────┐    ┌─────────────┐   ┌───────────────┐  │
87|│  │  Frontend  │    │   Backend   │   │    Worker     │  │
88|│  │  React 18  │───▶│  FastAPI    │──▶│ APScheduler   │  │
89|│  │  Nginx     │    │  Python 3.11│   │               │  │
90|│  └────────────┘    └──────┬──────┘   └───────────────┘  │
91|│                           │                              │
92|│          ┌────────────────┼───────────────┐              │
93|│          ▼                ▼               ▼              │
94|│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐       │
95|│  │  PostgreSQL  │  │  Redis   │  │   Uploads    │       │
96|│  │  StatefulSet │  │StatefulSet│  │     PVC      │       │
97|│  │  vcm_pgdata  │  │ vcm_redis│  │  vcm_uploads │       │
98|│  └──────────────┘  └──────────┘  └──────────────┘       │
99|└─────────────────────────────┬───────────────────────────┘
100|                              │ pyVmomi / port 443
101|                     ┌────────▼─────────┐
102|                     │  vCenter Server  │
103|                     │   v6.x – v8.x    │
104|                     └──────────────────┘
105|```
106|
107|See [docs/architecture/README.md](docs/architecture/README.md) for full diagrams.
108|
109|---
110|
111|## Docker Images
112|
113|Images are published to GHCR on every tagged release. Images are **never** built on branch pushes.
114|
115|| Image | Registry |
116||-------|----------|
117|| Backend | `ghcr.io/davoudteimouri/vsphere-compliance-manager/backend` |
118|| Frontend | `ghcr.io/davoudteimouri/vsphere-compliance-manager/frontend` |
119|
120|Available tags: `1.3.6-beta`, `latest`
121|
122|```bash
123|docker pull ghcr.io/davoudteimouri/vsphere-compliance-manager/backend:1.3.6-beta
124|docker pull ghcr.io/davoudteimouri/vsphere-compliance-manager/frontend:1.3.6-beta
125|```
126|
127|Packages: [github.com/davoudteimouri/vsphere-compliance-manager/pkgs/container](https://github.com/davoudteimouri/vsphere-compliance-manager/pkgs/container/vsphere-compliance-manager%2Fbackend)
128|
129|---
130|
131|## Quick Start
132|
133|**Option A — Pre-built images (recommended)**
134|
135|```bash
136|git clone https://github.com/davoudteimouri/vsphere-compliance-manager.git
137|cd vsphere-compliance-manager
138|cp .env.example .env
139|nano .env
140|VCM_VERSION=1.3.6-beta docker compose up -d
141|```
142|
143|UI available at `http://localhost:3000` · Default credentials: `admin / VCM@admin2024!`
144|
145|**Option B — Test without a real vCenter**
146|
147|```bash
148|VCM_VERSION=1.3.6-beta \
149|  docker compose -f docs/vcsim/docker-compose.vcsim.yml up -d
150|pip install pyVmomi
151|python3 docs/vcsim/seed_vcsim.py --seed 42
152|```
153|
154|**Option C — Build from source**
155|
156|```bash
157|git clone https://github.com/davoudteimouri/vsphere-compliance-manager.git
158|cd vsphere-compliance-manager
159|cp .env.example .env
160|nano .env
161|docker compose up -d --build
162|```
163|
164|---
165|
166|## Installation
167|
168|### Docker Compose
169|
170|```bash
171|cp .env.example .env
172|VCM_VERSION=1.3.6-beta docker compose up -d
173|docker compose logs -f backend
174|```
175|
176|To upgrade:
177|
178|```bash
179|VCM_VERSION=1.4.0 docker compose pull
180|VCM_VERSION=1.4.0 docker compose up -d
181|```
182|
183|Full guide: [docs/deployment/README.md](docs/deployment/README.md)
184|
185|### Kubernetes
186|
187|```bash
188|kubectl apply -k k8s/overlays/prod/
189|kubectl rollout status deployment/vcm-backend -n vcm
190|kubectl get ingress vcm-ingress -n vcm
191|```
192|
193|Manifest structure:
194|
195|```
196|k8s/
197|  base/
198|    namespace.yaml          vcm namespace
199|    configmap.yaml          ConfigMap and Secret templates
200|    postgres.yaml           StatefulSet, headless Service, Secret template
201|    redis.yaml              StatefulSet, headless Service
202|    volumes/
203|      pvc-uploads.yaml      5Gi ReadWriteMany for multi-pod upload access
204|      pvc-postgres.yaml     reference — StatefulSet manages its own PVC
205|      pvc-redis.yaml        reference — StatefulSet manages its own PVC
206|    backend.yaml            Deployment, Service, ServiceAccount, HPA
207|    frontend.yaml           Deployment, Service, Ingress
208|  overlays/
209|    dev/                    1 replica, DEBUG logging
210|    staging/                2 replicas, staging hostname
211|    prod/                   3 replicas, production hostname, StorageClass overrides
212|```
213|
214|To upgrade:
215|
216|```bash
217|nano k8s/overlays/prod/kustomization.yaml
218|kubectl apply -k k8s/overlays/prod/
219|kubectl rollout status deployment/vcm-backend -n vcm
220|```
221|
222|### Helm
223|
224|```bash
225|helm install vcm ./deploy/helm \
226|  --namespace vcm \
227|  --create-namespace \
228|  --set app.version="1.3.6-beta" \
229|  --set app.secretKey="$(openssl rand -base64 32)" \
230|  --set app.adminPassword="YourPassword@123" \
231|  --set ingress.host="vcm.your-domain.com"
232|```
233|
234|To upgrade:
235|
236|```bash
237|helm upgrade vcm ./deploy/helm --reuse-values --set app.version="1.4.0"
238|```
239|
240|---
241|
242|## Configuration
243|
244|Copy `.env.example` to `.env` and set these minimum required values:
245|
246|```
247|SECRET_KEY=<random 32+ char string — run: openssl rand -base64 32>
248|ADMIN_PASSWORD=<strong password>
249|DATABASE_URL=postgresql://vcm:***@postgres:5432/vcm_db
250|REDIS_URL=redis://redis:***@123"
489|```
490|
491|Kubernetes:
492|
493|```bash
494|kubectl exec -n vcm deployment/vcm-backend -- \
495|  python scripts/reset_admin.py --password "NewPass@123"
496|```
497|
498|**LDAP / Active Directory**
499|
500|Set `LDAP_ENABLED=true`. On first login, LDAP users are auto-provisioned:
501|