"""
vcsim conftest.py
-----------------
Builds a randomized vCenter inventory via vcsim for each test session.
vcsim must be running: vcsim -httptest.serve 127.0.0.1:8989
"""
import pytest
import os
import random
import string
from app.services.vcenter_service import VCenterService

VCSIM_HOST = os.getenv("VCSIM_HOST", "127.0.0.1")
VCSIM_PORT = int(os.getenv("VCSIM_PORT", "8989"))
VCSIM_USER = os.getenv("VCSIM_USER", "user")
VCSIM_PASS = os.getenv("VCSIM_PASS", "pass")


def _rand(prefix: str, n: int = 3) -> str:
    suffix = "".join(random.choices(string.digits, k=n))
    return f"{prefix}-{suffix}"


@pytest.fixture(scope="session")
def vcenter_service():
    """Connect to vcsim and return a live VCenterService."""
    svc = VCenterService(
        host=VCSIM_HOST,
        username=VCSIM_USER,
        password=VCSIM_PASS,
        port=VCSIM_PORT,
        verify_ssl=False,
    )
    svc.connect()
    yield svc
    svc.disconnect()


@pytest.fixture(scope="session")
def inventory(vcenter_service):
    """Pull full inventory once per test session."""
    return vcenter_service.get_full_inventory()


@pytest.fixture(scope="session")
def random_patterns():
    """
    Generate randomized VM and datastore name patterns.
    Each session picks different prefixes so tests cover
    different naming scenarios.
    """
    # Pick 2-4 random VM group prefixes
    possible_prefixes = ["WEB", "APP", "DB", "CACHE", "WORKER", "API", "PROXY", "AUTH"]
    n_groups = random.randint(2, 4)
    vm_prefixes = random.sample(possible_prefixes, n_groups)

    patterns = []
    for prefix in vm_prefixes:
        patterns.append({
            "pattern_type": "vm_name",
            "regex_pattern": rf"^({prefix})-\d+",
            "name": f"{prefix} VMs",
        })

    # Datastore pattern
    patterns.append({
        "pattern_type": "datastore",
        "regex_pattern": r"^(LocalDS_\d)",
        "name": "Local Datastores",
    })

    return patterns


@pytest.fixture(scope="session")
def session_seed():
    """Expose the random seed so test failures are reproducible."""
    seed = random.randint(0, 99999)
    random.seed(seed)
    print(f"\n[vcsim] Random seed: {seed}  "
          f"(set PYTHONHASHSEED={seed} to reproduce)")
    return seed
