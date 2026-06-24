# Deployment Guide

## Choosing a Deployment Method

| Method | Best For | Complexity |
|--------|----------|------------|
| [Docker Compose](#docker-compose) | Single-node, evaluation, small teams | Low |
| [Kubernetes + Kustomize](#kubernetes) | Production, HA, scaling | Medium |
| [Helm](#helm-chart) | Kubernetes with package management | Medium |

**Current release:** `1.3.3-beta`

---

## Prerequisites

- Docker 24+ and Docker Compose v2 (for Compose deployments)
- Kubernetes 1.26+ with `kubectl` (for K8s deployments)
- Nginx Ingress Controller (for K8s)
- A StorageClass supporting `ReadWriteOnce` for PostgreSQL and Redis
- A StorageClass supporting `ReadWriteMany` for uploads PVC

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
VCM_VERSION=1.3.3-beta docker compose up -d

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
# Change: newTag: "1.3.3-beta" -> newTag: "1.4.0"

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
  --set app.version="1.3.3-beta" \
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

## Resetting Admin Password

If you cannot log in, reset the admin password from inside the container:

```bash
# Docker Compose
docker exec $(docker compose ps -q backend) \
  python scripts/reset_admin.py --password "NewPassword@123"

# Kubernetes
kubectl exec -n vcm deployment/vcm-backend -- \
  python scripts/reset_admin.py --password "NewPassword@123"
```
