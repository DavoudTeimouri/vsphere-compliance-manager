# vcsim Testing Guide

Complete guide for testing VCM using the vCenter Simulator — no real vCenter required.

---

## 1. What is vcsim?

**vcsim** is an official VMware vCenter Server simulator built as part of the
[govmomi](https://github.com/vmware/govmomi) project. It fully implements the
vSphere SOAP/REST API and is compatible with pyVmomi out of the box.

**Simulates:**
- Datacenter / Cluster / Host / VM hierarchy
- Datastore / Datastore Cluster
- DRS Anti-Affinity and Affinity Rules
- Full vSphere API (SOAP/REST)

**Does NOT simulate:**
- Real Storage vMotion execution
- Network packet flow
- Live performance metrics (returns static values)

---

## 2. Quick Start (Docker only)

### vcsim standalone

```bash
docker run -d --name vcsim \
  -p 8989:8989 \
  vmware/vcsim:latest \
  -l :8989 \
  -dc 2 -cluster 3 -host 4 -vm 20 -ds 4 -pod 2

# Verify
curl -k https://localhost:8989/sdk
```

**vcsim flags reference:**

| Flag | Description | Recommended for full coverage |
|------|-------------|-------------------------------|
| `-dc N` | Number of Datacenters | 2 |
| `-cluster N` | Clusters per Datacenter | 3 |
| `-host N` | Hosts per Cluster | 4 |
| `-vm N` | VMs per Host | 5 |
| `-ds N` | Number of Datastores | 4 |
| `-pod N` | Datastore Clusters | 2 |

---

## 3. Full Test Environment (vcsim + VCM)

This docker-compose brings up the complete VCM stack alongside vcsim
using the published GHCR images — no build step required.

```bash
cd docs/vcsim
docker compose -f docker-compose.vcsim.yml up -d

# Check status
docker compose -f docker-compose.vcsim.yml ps

# Follow backend logs
docker compose -f docker-compose.vcsim.yml logs -f backend
```

**Services after startup:**

| Service | URL | Credentials |
|---------|-----|-------------|
| VCM UI | http://localhost:3000 | admin / VCM@admin2024! |
| VCM API (Swagger) | http://localhost:8000/docs | — |
| vcsim SDK | https://localhost:8989/sdk | user / pass |

---

## 4. Seeding vcsim with Realistic VM Names

vcsim generates VM names like `DC0_H0_VM0` which do not match VCM patterns.
Use `seed_vcsim.py` to rename them to realistic names that trigger VCM analysis.

### Prerequisites

```bash
pip install pyVmomi
```

### Basic usage (fully random each run)

```bash
python3 docs/vcsim/seed_vcsim.py
```

The script prints the seed used so you can reproduce the same inventory:

```
Seed: 1718623412  (use --seed 1718623412 to reproduce)
```

### Reproducible run

```bash
python3 docs/vcsim/seed_vcsim.py --seed 42
```

### All options

```bash
python3 docs/vcsim/seed_vcsim.py \
  --host localhost \
  --port 8989 \
  --user user \
  --password pass \
  --prefixes WEB APP DB CACHE PROXY WORKER BATCH MON \
  --envs PROD DR STG DEV \
  --seed 42 \
  --dry-run
```

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | localhost | vcsim host |
| `--port` | 8989 | vcsim port |
| `--seed` | random | Fixed seed for reproducible inventory |
| `--prefixes` | WEB APP DB CACHE PROXY WORKER BATCH MON KAFKA ELASTIC | VM name prefixes |
| `--envs` | PROD DR STG DEV | Environment suffixes |
| `--dry-run` | false | Preview renames without applying |

### Test scenarios

```bash
# Scenario 1 — minimal (2 groups, 2 environments)
python3 docs/vcsim/seed_vcsim.py \
  --prefixes WEB DB \
  --envs PROD DR \
  --seed 1

# Scenario 2 — maximum coverage (all prefixes, all environments)
python3 docs/vcsim/seed_vcsim.py \
  --prefixes WEB APP DB CACHE PROXY WORKER BATCH MON \
  --envs PROD DR STG DEV

# Scenario 3 — preview before applying
python3 docs/vcsim/seed_vcsim.py --dry-run --seed 99

# Scenario 4 — remote vcsim
python3 docs/vcsim/seed_vcsim.py \
  --host 192.168.1.100 --port 8989 --seed 42
```

### Sample output

```
VCM vcsim Test Data Generator
========================================
Host:     localhost:8989
Prefixes: ['WEB', 'APP', 'DB', 'CACHE']
Envs:     ['PROD', 'DR']
Seed:     1718623412

Renaming 20 VMs:
  DC0_H0_VM0                     → WEB-PROD-01
  DC0_H0_VM1                     → APP-PROD-01
  DC0_H1_VM0                     → DB-DR-01
  ...

============================================================
INVENTORY SUMMARY
============================================================
Cluster: DC0_C0  (4 hosts, 10 VMs)
  [APP]   2 VMs: APP-DR-01, APP-PROD-01
  [DB]    2 VMs: DB-DR-01, DB-PROD-01
  [WEB]   3 VMs: WEB-DR-01, WEB-PROD-01, WEB-PROD-02

Datastores: 4
  DS-PROD-01                       1024 GB total, 800 GB free
  DS-DR-01                         2048 GB total, 1200 GB free
```

---

## 5. Connecting VCM to vcsim

### Via UI

1. Navigate to **Settings → vCenter Connections → Add Connection**
2. Fill in:
   - **Name**: `vcsim-local`
   - **Host**: `vcsim` (if using docker-compose) or `localhost`
   - **Port**: `8989`
   - **Username**: `user`
   - **Password**: `pass`
   - **Verify SSL**: disabled
3. Click **Test Connection** — should return green
4. Click **Save**

### Via API

```bash
# Authenticate
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"VCM@admin2024!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Add vcsim connection
curl -s -X POST http://localhost:8000/api/vcenter/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "vcsim-local",
    "host": "vcsim",
    "port": 8989,
    "username": "user",
    "password": "pass",
    "verify_ssl": false
  }' | python3 -m json.tool
```

---

## 6. Configure Patterns

Add patterns that match the prefix convention used by `seed_vcsim.py`:

```bash
for PATTERN in \
  '{"name":"Web Servers","pattern_type":"vm_name","regex_pattern":"^(WEB)-"}' \
  '{"name":"App Servers","pattern_type":"vm_name","regex_pattern":"^(APP)-"}' \
  '{"name":"DB Servers","pattern_type":"vm_name","regex_pattern":"^(DB)-"}' \
  '{"name":"Cache Servers","pattern_type":"vm_name","regex_pattern":"^(CACHE)-"}' \
  '{"name":"Proxy Servers","pattern_type":"vm_name","regex_pattern":"^(PROXY)-"}' \
  '{"name":"Worker Servers","pattern_type":"vm_name","regex_pattern":"^(WORKER)-"}' \
  '{"name":"Prod Datastores","pattern_type":"datastore","regex_pattern":"^(DS-PROD)-"}' \
  '{"name":"DR Datastores","pattern_type":"datastore","regex_pattern":"^(DS-DR)-"}'; do
  curl -s -X POST http://localhost:8000/api/settings/patterns \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PATTERN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Created: {d.get(\"name\", d)}')"
done
```

---

## 7. Test Scenarios

### A — DRS Compliance

```bash
# 1. Seed inventory
python3 docs/vcsim/seed_vcsim.py --seed 100

# 2. Trigger DRS analysis
curl -s -X POST http://localhost:8000/api/analysis/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vcenter_id": 1, "analysis_type": "drs"}' | python3 -m json.tool

# 3. Wait for completion (30-60 seconds), then retrieve findings
sleep 45
curl -s "http://localhost:8000/api/analysis/1/findings?severity=warning" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### B — Storage Compliance

```bash
python3 docs/vcsim/seed_vcsim.py --seed 200

curl -s -X POST http://localhost:8000/api/analysis/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vcenter_id": 1, "analysis_type": "storage"}' | python3 -m json.tool
```

### C — Full Analysis and Apply DRS

```bash
# Trigger full analysis
RUN_ID=$(curl -s -X POST http://localhost:8000/api/analysis/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vcenter_id": 1, "analysis_type": "full"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['run_id'])")

echo "Run ID: $RUN_ID"
sleep 60

# Apply DRS rules (operator or admin role required)
curl -s -X POST "http://localhost:8000/api/analysis/$RUN_ID/apply-drs" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Export report as JSON
curl -s "http://localhost:8000/api/reports/$RUN_ID/export?format=json" \
  -H "Authorization: Bearer $TOKEN" \
  -o "vcm-report-$RUN_ID.json"

echo "Report saved: vcm-report-$RUN_ID.json"
```

### D — Re-seed and Re-analyze (randomized regression)

```bash
# Different seed each run — covers different edge cases
for SEED in 1 42 100 999 31337; do
  echo "=== Seed: $SEED ==="
  python3 docs/vcsim/seed_vcsim.py --seed $SEED
  sleep 5
  curl -s -X POST http://localhost:8000/api/analysis/run \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"vcenter_id": 1, "analysis_type": "full"}' | python3 -m json.tool
  sleep 60
done
```

---

## 8. Using Published Docker Images

The `docker-compose.vcsim.yml` file uses the pre-built images from GHCR.
To pull and run them manually:

```bash
# Pull images
docker pull ghcr.io/davoudteimouri/vsphere-compliance-manager/backend:main
docker pull ghcr.io/davoudteimouri/vsphere-compliance-manager/frontend:main

# Or a specific version (once stable releases are tagged)
docker pull ghcr.io/davoudteimouri/vsphere-compliance-manager/backend:1.0.0
docker pull ghcr.io/davoudteimouri/vsphere-compliance-manager/frontend:1.0.0
```

To override the image tag in the test compose:

```bash
BACKEND_TAG=main FRONTEND_TAG=main \
  docker compose -f docker-compose.vcsim.yml up -d
```

---

## 9. Teardown

```bash
# Stop containers (preserve data)
docker compose -f docs/vcsim/docker-compose.vcsim.yml down

# Full reset (remove volumes)
docker compose -f docs/vcsim/docker-compose.vcsim.yml down -v
```

---

## 10. Troubleshooting

| Issue | Resolution |
|-------|-----------|
| `Connection refused` on port 8989 | Wait for vcsim to fully start: `docker logs vcm-vcsim` |
| SSL error connecting to vcsim | Ensure `verify_ssl` is set to `false` |
| VM rename fails in seed script | vcsim sometimes timeouts on rename — safe to ignore, re-run seed |
| No findings generated | Verify patterns match the VM names produced by seed script |
| Analysis stuck in `running` | Check backend logs: `docker compose logs -f backend` |
| Images not found on GHCR | Ensure a push to `main` branch has triggered the CI Docker job |
