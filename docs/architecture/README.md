# Architecture Overview

## System Components

```
┌──────────────────────────────────────────────────────────────────┐
│                          Kubernetes / Docker                      │
│                                                                    │
│  ┌─────────────────┐      ┌───────────────────────────────────┐  │
│  │    Frontend      │      │            Backend                │  │
│  │                  │      │                                   │  │
│  │  React 18 + TS   │◀────▶│  FastAPI  (Python 3.11)          │  │
│  │  Vite            │      │  ├── Auth Router (JWT / LDAP)    │  │
│  │  TanStack Query  │      │  ├── vCenter Router              │  │
│  │  Zustand         │      │  ├── Analysis Router             │  │
│  │  Nginx           │      │  ├── Reports Router              │  │
│  └─────────────────┘      │  └── Settings Router             │  │
│                            └──────────────┬────────────────────┘  │
│                                           │                        │
│  ┌──────────────────┐   ┌────────────────▼──────────────────┐    │
│  │      Redis        │   │           PostgreSQL 15            │    │
│  │  Session cache    │   │  ┌──────────────────────────┐    │    │
│  │  Task queue       │   │  │ users                    │    │    │
│  └──────────────────┘   │  │ vcenter_connections       │    │    │
│                            │  │ analysis_runs             │    │    │
│  ┌──────────────────┐   │  │ analysis_findings         │    │    │
│  │  APScheduler      │   │  │ drs_rule_history          │    │    │
│  │  (background)     │   │  │ storage_move_history      │    │    │
│  │  Cron-based runs  │   │  │ app_settings              │    │    │
│  └──────────────────┘   │  │ pattern_configs           │    │    │
│                            │  │ audit_logs                │    │    │
│                            │  └──────────────────────────┘    │    │
│                            └───────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────  ┘
                                   │ pyVmomi (port 443)
                          ┌────────▼─────────────┐
                          │   vCenter Server      │
                          │   v6.0 – v8.0         │
                          │                       │
                          │  ┌──────┐ ┌────────┐ │
                          │  │Cluster│ │Datastore│ │
                          │  └──────┘ └────────┘ │
                          └───────────────────────┘
```

## Data Flow — Analysis Run

```
User triggers analysis
        │
        ▼
POST /api/analysis/run
        │
        ▼
AnalysisRun created (status=pending)
        │
        ▼
Background task spawned
        │
        ├──► VCenterService.connect()
        │         └── pyVmomi SmartConnect
        │
        ├──► VCenterService.get_full_inventory()
        │         ├── All Clusters + Hosts
        │         ├── All VMs + Disk backing
        │         └── All Datastores + DS Clusters
        │
        ├──► AnalysisEngine.analyze_drs_compliance()
        │         ├── Group VMs by Regex pattern
        │         ├── Calculate rule sizing (hosts - 1)
        │         └── Generate rules_to_create / rules_to_delete
        │
        ├──► AnalysisEngine.analyze_storage_compliance()
        │         ├── Detect VMs sharing datastores
        │         ├── Detect scattered VM disks
        │         └── Generate separation proposals
        │
        ├──► Persist findings to DB
        │
        └──► AnalysisRun status=completed
```

## Security Model

| Layer | Mechanism |
|-------|-----------|
| Transport | HTTPS (TLS via Ingress) |
| Authentication | JWT (HS256) or LDAP |
| Password storage | bcrypt (cost 12) |
| Credential storage | AES-256 (Fernet) |
| Authorization | Role-based (Admin / Operator / Viewer) |
| Audit | Full action log in `audit_logs` table |
| Secrets in K8s | Kubernetes Secrets (recommend sealing with Sealed Secrets or Vault) |

## Storage Compliance Logic

```
For each VM group (matched by Regex):
  For each pair of VMs (A, B) in the group:
    Get all non-ISO disks of A  → set of datastores / DS clusters
    Get all non-ISO disks of B  → set of datastores / DS clusters

    If intersection is non-empty → VIOLATION
      Severity = critical (if shared DS cluster)
      Severity = warning  (if shared raw datastore only)

For each individual VM:
  If disks span > 1 datastore or > 1 DS cluster → SCATTERED
  Proposal: consolidate to datastore with most free space
```

## DRS Rule Logic

```
For each cluster C with N hosts:
  For each VM group G matched in C with M VMs:
    If M == 1:
      Skip (report only — single VM needs no rule)
    If N < 2:
      Skip (anti-affinity impossible on 1-host cluster)
    Else:
      max_per_rule = N - 1   (ensures each rule can spread across all hosts)
      Split G into batches of max_per_rule
      For each batch with ≥ 2 VMs:
        Create rule: VCM-AAR-{cluster}-{group}[-{n}]
      
  Before creating: delete all existing VCM-AAR-* rules in C
  Non-VCM rules are never touched
```
