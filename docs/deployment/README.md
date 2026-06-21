# Deployment Guide

## Option 1 — Docker Compose (Recommended for single-node)

### Minimum Requirements
- 2 vCPU / 4 GB RAM / 20 GB disk
- Docker 24+ and Docker Compose v2

```bash
# Clone
git clone https://github.com/DavoudTeimouri/vsphere-compliance-manager.git
cd vsphere-compliance-manager

# Configure
cp .env.example .env
nano .env    # Set SECRET_KEY, ADMIN_PASSWORD, etc.

# Start
docker compose up -d

# View status
docker compose ps
docker compose logs -f backend
```

The app will be available at **http://your-host:3000**

### Upgrading

```bash
git pull
docker compose pull
docker compose up -d
docker compose exec backend alembic upgrade head
```

---

## Option 2 — Kubernetes with Kustomize

### Minimum Requirements
- Kubernetes 1.26+
- Nginx Ingress Controller
- cert-manager (for TLS, optional)
- StorageClass supporting `ReadWriteMany` (for uploads PVC)

### Steps

```bash
# 1. Create namespace and secrets
kubectl create namespace vcm

kubectl create secret generic vcm-secrets \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="" \
  --from-literal=ADMIN_PASSWORD="VCM@admin2024!" \
  -n vcm

# 2. Edit the prod overlay
nano k8s/overlays/prod/kustomization.yaml
# Set your image tags and hostname

# 3. Apply
kubectl apply -k k8s/overlays/prod/

# 4. Run DB migrations
kubectl exec -n vcm deploy/vcm-backend -- alembic upgrade head

# 5. Check status
kubectl get all -n vcm
kubectl get ingress -n vcm
```

### TLS with cert-manager

Add to your ingress in the overlay:

```yaml
annotations:
  cert-manager.io/cluster-issuer: letsencrypt-prod
```

---

## Option 3 — Helm

```bash
# Install
helm install vcm ./deploy/helm \
  --namespace vcm --create-namespace \
  --set app.secretKey="$(openssl rand -base64 32)" \
  --set app.adminPassword="VCM@admin2024!" \
  --set ingress.host="vcm.vcm.DavoudTeimouri.ir"

# Upgrade
helm upgrade vcm ./deploy/helm --reuse-values \
  --set image.tag="1.3.3-beta"
```

---

## Production Checklist

- [ ] `SECRET_KEY` is a random 32+ character string
- [ ] `ADMIN_PASSWORD` changed from default
- [ ] TLS configured on the Ingress
- [ ] PostgreSQL backups configured
- [ ] `LDAP_ENABLED` tested before enabling in prod
- [ ] Log aggregation connected (Loki, ELK, Datadog, etc.)
- [ ] Resource limits set on all containers
- [ ] Network policy restricting DB access to backend only
- [ ] Sealed Secrets or Vault used for K8s secrets management
