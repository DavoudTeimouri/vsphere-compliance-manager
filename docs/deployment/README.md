# Deployment Guide

## Choosing a Deployment Method

| Method | Best For | Complexity |
|--------|----------|------------|
| [Docker Compose](#docker-compose) | Single-node, evaluation, small teams | Low |
| [Kubernetes + Kustomize](#kubernetes) | Production, HA, scaling | Medium |
| [Helm](#helm-chart) | Kubernetes with package management | Medium |

**Current release:** `latest` (or pin to a specific version tag)

> Replace `$VCM_VERSION` with a specific tag (e.g. `1.3.8-beta`) to pin a release. Omit it to use `latest`.

---

## Prerequisites

- Docker 24+ and Docker Compose v2 (for Compose deployments)
- Kubernetes 1.26+ with `kubectl` (for K8s deployments)
- Nginx Ingress Controller (for K8s)
- A StorageClass supporting `ReadWriteOnce` for PostgreSQL and Redis
- A StorageClass supporting `ReadWriteMany` for uploads PVC

> **Always get the latest image:** Before starting, pull the newest image:
> ```powershell
> docker compose pull
> docker compose up -d
> ```
> Without `pull`, Docker uses the locally cached image which may be outdated.

---

## Docker Compose

### Minimum Requirements
- 2 vCPU / 4 GB RAM / 30 GB disk

### Setup

```bash
git clone https://github.com/davoudteimouri/vsphere-compliance-manager.git
cd vsphere-compliance-manager

cp .env.example .env
# Edit .env — set SECRET_KEY and ADMIN_PASSWORD at minimum
nano .env

# Start all services
VCM_VERSION=latest docker compose up -d

# Check status
docker compose ps
docker compose logs -f backend
```

The UI is available at **http://your-host:3000**

### Volumes

Docker Compose creates three named volumes:

| Volume | Purpose | Size |
|--------|---------|------|
| `vcm_pgdata` | PostgreSQL data | Grows with usage |
| `vcm_redis` | Redis persistence | ~256 MB max |
| `vcm_uploads` | Logos and exports | ~5 GB recommended |

```bash
# Inspect volumes
docker volume ls | grep vcm
docker volume inspect vcm_pgdata

# Backup PostgreSQL
docker exec vcm-backend-1 pg_dump -U vcm vcm_db > backup.sql

# Restore
cat backup.sql | docker exec -i vcm-postgres-1 psql -U vcm vcm_db
```

### Upgrading

```bash
# Set new version
export VCM_VERSION=1.4.0

# Pull new images and restart
docker compose pull
docker compose up -d

# Check logs
docker compose logs -f backend
```

---

## Kubernetes

### Directory Structure

```
k8s/
├── base/                    # Base manifests applied to all environments
│   ├── namespace.yaml       # vcm namespace
│   ├── configmap.yaml       # Config + secret templates
│   ├── postgres.yaml        # PostgreSQL StatefulSet + Service + Secret template
│   ├── redis.yaml           # Redis StatefulSet + Service
│   ├── volumes/
│   │   ├── pvc-uploads.yaml # Uploads PersistentVolumeClaim (ReadWriteMany)
│   │   ├── pvc-postgres.yaml# Reference only (StatefulSet manages its own PVC)
│   │   └── pvc-redis.yaml   # Reference only (StatefulSet manages its own PVC)
│   ├── backend.yaml         # Backend Deployment + Service + SA + HPA
│   └── frontend.yaml        # Frontend Deployment + Service + Ingress
└── overlays/
    ├── dev/                 # Dev overrides (lower replicas, debug logging)
    ├── staging/             # Staging overrides
    └── prod/                # Production overrides (scale, StorageClass, hostname)
```

### Initial Deployment

```bash
# 1. Create namespace and secrets
kubectl create namespace vcm

kubectl create secret generic vcm-secrets \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="" \
  --from-literal=ADMIN_PASSWORD="YourSecurePassword@123" \
  --from-literal=ADMIN_EMAIL="admin@your-domain.com" \
  -n vcm

kubectl create secret generic vcm-postgres-secret \
  --from-literal=POSTGRES_USER=vcm \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 24)" \
  -n vcm

# 2. Edit prod overlay — set your hostname and StorageClass
nano k8s/overlays/prod/kustomization.yaml

# 3. Apply
kubectl apply -k k8s/overlays/prod/

# 4. Watch rollout
kubectl rollout status statefulset/vcm-postgres -n vcm
kubectl rollout status statefulset/vcm-redis -n vcm
kubectl rollout status deployment/vcm-backend -n vcm
kubectl rollout status deployment/vcm-frontend -n vcm

# 5. Get Ingress address
kubectl get ingress vcm-ingress -n vcm
```

### Volumes in Kubernetes

PostgreSQL and Redis use **StatefulSet VolumeClaimTemplates** — Kubernetes
manages their PVCs automatically:

```bash
# List all VCM PVCs
kubectl get pvc -n vcm

# NAME                          STATUS   VOLUME      CAPACITY
# postgres-data-vcm-postgres-0  Bound    pvc-abc123  20Gi
# redis-data-vcm-redis-0        Bound    pvc-def456  2Gi
# vcm-uploads                   Bound    pvc-ghi789  5Gi
```

The uploads PVC (`vcm-uploads`) requires `ReadWriteMany` because multiple
backend pods need to access it simultaneously. Use an NFS-backed StorageClass
or a cloud provider that supports `ReadWriteMany` (e.g. AWS EFS, GCP Filestore,
Azure Files).

### Upgrading

```bash
# Edit the image tag in prod overlay
nano k8s/overlays/prod/kustomization.yaml
# Change: newTag: "1.3.6-beta" -> newTag: "1.4.0"

# Apply — Kubernetes performs a rolling update
kubectl apply -k k8s/overlays/prod/

# Watch
kubectl rollout status deployment/vcm-backend -n vcm
```

### Backup and Restore

```bash
# Backup PostgreSQL
kubectl exec -n vcm statefulset/vcm-postgres -- \
  pg_dump -U vcm vcm_db > vcm-backup-$(date +%Y%m%d).sql

# Restore
kubectl exec -n vcm -i statefulset/vcm-postgres -- \
  psql -U vcm vcm_db < vcm-backup-20260619.sql
```

---

## Helm Chart

The Helm chart uses the same images and configuration as the Kustomize manifests.

```bash
# Install
helm install vcm ./deploy/helm \
  --namespace vcm \
  --create-namespace \
  --set app.version="latest" \
  --set app.secretKey="$(openssl rand -base64 32)" \
  --set app.adminPassword="YourSecurePassword@123" \
  --set ingress.host="vcm.your-domain.com" \
  --set postgres.storageClass="standard" \
  --set uploads.storageClass="nfs-client"

# Upgrade to a new version
helm upgrade vcm ./deploy/helm \
  --reuse-values \
  --set app.version="1.4.0"

# Check status
helm status vcm -n vcm
```

---

## Production Checklist

- [ ] `SECRET_KEY` is a random 32+ character string (`openssl rand -base64 32`)
- [ ] `ADMIN_PASSWORD` changed from default
- [ ] PostgreSQL password set in `vcm-postgres-secret`
- [ ] TLS certificate configured on the Ingress
- [ ] StorageClass set for all PVCs
- [ ] `ReadWriteMany` StorageClass available for uploads PVC
- [ ] Database backup scheduled (cron + pg_dump)
- [ ] Log aggregation connected (Loki, ELK, etc.)
- [ ] Resource limits reviewed for your cluster size
- [ ] Network Policy restricting DB access to backend only (optional)

---

## Troubleshooting

### "duplicate key value violates unique constraint pg_type_typname_nsp_index"

**Cause:** The backend stores PostgreSQL ENUM types (`userrole`, `analysistype`, `analysisstatus`) in the database. If you change the image version but keep the same database volume, the old ENUM types may conflict with the new image's schema.

**Fix:** Always remove volumes when switching versions:

```powershell
# Remove old containers and volumes for a clean start
docker compose down -v
# Then start fresh
docker compose up -d
```

> **Important:** Before running `docker compose down -v`, ensure you have backed up any data you want to keep (e.g., analysis history, vCenter connections). Volumes are permanently deleted.

### Login fails after restart

**Cause:** The admin user was created in a previous run but the password hash may differ between versions.

**Fix:** Reset the admin password:

```powershell
docker exec vcm-test-backend python scripts/reset_admin.py --password "VCM@admin2024!"
```

Or for a fresh start (removes all data):

```powershell
docker compose down -v
docker compose up -d
```

### Changes not reflected after `git pull`

Docker caches images. After pulling new code, rebuild:

```powershell
docker compose down
docker compose build --no-cache
docker compose up -d
```

Or use the `latest` image tag which is rebuilt on every release:

```powershell
$env:VCM_VERSION="latest"; docker compose up -d
```

### "How am I using the latest image?"

To verify which image tag your containers are running:

```powershell
# Check the image currently used by the backend container
docker inspect vcm-backend-1 --format='{{.Config.Image}}'
```

Output example: `ghcr.io/davoudteimouri/vsphere-compliance-manager/backend:latest`

If you see a specific version tag (e.g. `1.3.6-beta`) instead of `latest`, you are running an old image. To always get the latest:

```powershell
# Pull the latest image explicitly
docker compose pull
docker compose up -d
```

Or check the GitHub Releases page to see available tags:
https://github.com/DavoudTeimouri/vsphere-compliance-manager/releases

If you cannot log in, reset the admin password from inside the container:

```bash
# Docker Compose
docker exec $(docker compose ps -q backend) \
  python scripts/reset_admin.py --password "NewPassword@123"

# Kubernetes
kubectl exec -n vcm deployment/vcm-backend -- \
  python scripts/reset_admin.py --password "NewPassword@123"
```
