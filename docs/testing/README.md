# Testing Guide

## Overview

VCM has three layers of tests:

| Layer | Location | Needs vCenter? | Needs DB? |
|-------|----------|----------------|-----------|
| Unit — Analysis Engine | `tests/unit/test_analysis_engine.py` | ❌ | ❌ |
| Unit — Security | `tests/unit/test_security.py` | ❌ | ❌ |
| Unit — vcsim (randomized) | `tests/unit/test_vcsim.py` | ❌ | ❌ |
| Integration — API | `tests/integration/test_api.py` | ❌ | ✅ PostgreSQL |

---

## Running Tests Locally

### Unit tests only (no dependencies needed)

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/unit/ -v
```

### All tests (requires PostgreSQL + Redis via Docker)

```bash
docker compose up postgres redis -d
export DATABASE_URL=postgresql://vcm:vcm_pass@localhost:5432/vcm_db
export SECRET_KEY=local-dev-secret-key
export REDIS_URL=redis://localhost:6379/0
alembic upgrade head
pytest tests/ -v --cov=app --cov-report=html
```

---

## vCenter Simulator (vcsim)

Since not everyone has access to a vCenter Server, VCM includes a
**pure-Python vCenter inventory simulator** that generates realistic,
randomized infrastructure for testing.

### What it simulates

- Multiple clusters with variable host counts (2–6 hosts per cluster)
- VM groups following naming conventions (WEB, APP, DB, CACHE, etc.)
- Datastores and Datastore Clusters with realistic capacity/free space
- VMs with multiple disks on different datastores (scattered VM scenario)
- ISO-mounted CD/DVD drives (must NOT trigger storage violations)
- Existing VCM-managed DRS rules (to test deletion logic)
- Manual DRS rules (must NOT be touched)

### Randomized testing

Each test run generates a **different random inventory** so edge cases
get covered over time. When a test fails, the seed is printed so you
can reproduce it:

```python
# Reproduce a specific failing run:
sim = VCenterSimulator(seed=42)
inventory = sim.generate_inventory()
sim.print_summary(inventory)
```

### Available fixtures

```python
# In any test file — fixtures are auto-imported via conftest.py

def test_something(sim_inventory, default_patterns):
    # sim_inventory: random inventory with intentional violations
    ...

def test_clean(sim_inventory_clean, default_patterns):
    # sim_inventory_clean: seed=42, no intentional violations
    ...

def test_small(sim_inventory_small, default_patterns):
    # sim_inventory_small: 1 cluster, minimal VMs
    ...

def test_large(sim_inventory_large, default_patterns):
    # sim_inventory_large: 4 clusters, 3 DS clusters, many VMs
    ...
```

### Using vcsim in your own tests

```python
from tests.fixtures.vcenter_sim import VCenterSimulator

def test_my_scenario():
    sim = VCenterSimulator(seed=None)  # Random
    inventory = sim.generate_inventory(
        num_clusters=2,
        num_ds_clusters=2,
        introduce_violations=True,
    )
    # inventory matches VCenterService.get_full_inventory() format exactly
    sim.print_summary(inventory)
    ...
```

---

## vcsim via Docker (govmomi)

For integration tests that need a real vSphere API endpoint,
you can run [vcsim](https://github.com/vmware/govmomi/tree/main/vcsim)
(VMware's official Go-based vCenter simulator) via Docker:

```bash
# Start vcsim
docker run -d --name vcsim \
  -p 8989:8989 \
  vmware/vcsim:latest \
  -l :8989

# vcsim credentials
# URL:      https://localhost:8989/sdk
# Username: user
# Password: pass
```

Add to your `.env` for local testing with vcsim:

```dotenv
VCSIM_HOST=localhost
VCSIM_PORT=8989
VCSIM_USERNAME=user
VCSIM_PASSWORD=pass
VCSIM_VERIFY_SSL=false
```

> **Note:** vcsim simulates the vSphere API protocol but does not
> execute real vCenter operations. DRS rule creation calls succeed
> at the API level but have no effect on actual VMs.

---

## CI Behavior

- **Unit tests** run on every push and PR — fast, no external deps
- **Integration tests** run on every push with PostgreSQL + Redis services
- **vcsim tests** run as part of unit tests — randomized each CI run
- **Docker build** runs only on push to `main` or `develop`
- Coverage threshold: 70% (enforced in CI)
