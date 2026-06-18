#!/usr/bin/env python3
"""
seed_vcsim.py — Randomized vCenter Inventory Seeder for VCM Testing
====================================================================

Connects to a running vcsim instance and renames VMs to realistic
names that match VCM's pattern-based analysis. Each run can be
seeded for reproducibility or fully random for broader coverage.

Usage:
    python scripts/seed_vcsim.py                         # fully random
    python scripts/seed_vcsim.py --seed 42               # reproducible
    python scripts/seed_vcsim.py --count 8 --seed 99     # 8 VMs per group
    python scripts/seed_vcsim.py --help

Requirements:
    pip install pyVmomi

Examples:
    # Basic test environment
    python scripts/seed_vcsim.py --host localhost --port 8989

    # Large randomized environment
    python scripts/seed_vcsim.py --count 10 --pattern "WEB APP DB CACHE WORKER"

    # Reproduce a specific run
    python scripts/seed_vcsim.py --seed 1234

After running, add the vcsim connection in VCM:
    Host:     localhost (or your Docker host IP)
    Port:     8989
    Username: user
    Password: pass
    SSL:      disabled
"""

import argparse
import random
import ssl
import sys
import string
from typing import List, Optional
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect

# ── Default values ────────────────────────────────────────
DEFAULT_HOST     = "localhost"
DEFAULT_PORT     = 8989
DEFAULT_USERNAME = "user"
DEFAULT_PASSWORD = "pass"
DEFAULT_PATTERNS = ["WEB", "APP", "DB", "CACHE", "PROXY", "WORKER", "BATCH", "MON"]
DEFAULT_ENVS     = ["PROD", "DEV", "DR", "STG"]
DEFAULT_COUNT    = 5

# ── Datastore name patterns for testing ──────────────────
DATASTORE_NAMES = [
    "DS-PROD-{n:02d}",
    "DS-DR-{n:02d}",
    "DS-DEV-{n:02d}",
    "DS-NFS-{n:02d}",
    "DS-SSD-{n:02d}",
]


def connect(host: str, port: int, username: str, password: str):
    """Connect to vcsim with SSL verification disabled."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        si = SmartConnect(host=host, user=username, pwd=password,
                          port=port, sslContext=context)
        print(f"✓ Connected to vcsim at {host}:{port}")
        print(f"  Version: {si.content.about.version}")
        return si
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print(f"  Make sure vcsim is running: docker run -d -p {port}:{port} vmware/vcsim:latest -l 0.0.0.0:{port}")
        sys.exit(1)


def get_all_vms(si) -> List[vim.VirtualMachine]:
    content = si.content
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True)
    vms = list(container.view)
    container.Destroy()
    return vms


def get_all_clusters(si) -> List[vim.ClusterComputeResource]:
    content = si.content
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.ClusterComputeResource], True)
    clusters = list(container.view)
    container.Destroy()
    return clusters


def rename_vm(vm: vim.VirtualMachine, new_name: str) -> bool:
    """Rename a VM in vcsim."""
    try:
        vm.Rename_Task(newName=new_name)
        return True
    except Exception as e:
        print(f"  ⚠ Could not rename {vm.name} → {new_name}: {e}")
        return False


def generate_vm_names(
    patterns: List[str],
    envs: List[str],
    count: int,
    cluster_idx: int,
    rng: random.Random,
) -> List[str]:
    """
    Generate realistic VM names for a cluster.

    Format: {PREFIX}-{ENV}-{CLUSTER}{INDEX:02d}
    Example: WEB-PROD-101, APP-DR-202, DB-STG-103
    """
    names = []
    selected_patterns = rng.sample(patterns, k=min(len(patterns), rng.randint(2, 4)))
    for prefix in selected_patterns:
        env = rng.choice(envs)
        for idx in range(1, count + 1):
            name = f"{prefix}-{env}-{cluster_idx}{idx:02d}"
            names.append(name)
    # Shuffle to avoid predictable ordering
    rng.shuffle(names)
    return names


def introduce_drs_violations(vms_by_cluster: dict, rng: random.Random) -> dict:
    """
    Intentionally create scenarios that should trigger DRS violations:
    - Groups with exactly 1 VM (should be skipped)
    - Large groups needing multiple rules
    """
    violations = {}
    for cluster_name, vms in vms_by_cluster.items():
        # Add 1 singleton VM (should be reported but no rule created)
        singleton_prefixes = ["MGMT", "JUMP", "BASTION"]
        singleton = f"{rng.choice(singleton_prefixes)}-PROD-{rng.randint(10, 99)}"
        violations[cluster_name] = vms + [singleton]
    return violations


def introduce_storage_violations(si, rng: random.Random):
    """
    Print instructions for manually creating storage violation scenarios
    since vcsim doesn't support full storage vMotion simulation.
    """
    print("\n📋 Storage Violation Scenarios (manual setup in VCM):")
    print("   VCM will detect these based on VM disk placement in vcsim:")
    print("   - VMs in the same pattern group on the same datastore → violation")
    print("   - VMs with disks scattered across multiple datastores → scattered")
    print("   - ISO mounts on shared datastores → should be ignored")


def seed(
    host: str, port: int, username: str, password: str,
    patterns: List[str], envs: List[str], count: int,
    seed_value: Optional[int], dry_run: bool
):
    rng = random.Random(seed_value)
    if seed_value is not None:
        print(f"🌱 Using seed: {seed_value}")
    else:
        import time
        actual_seed = int(time.time())
        rng = random.Random(actual_seed)
        print(f"🎲 Random seed: {actual_seed}  (use --seed {actual_seed} to reproduce)")

    si = connect(host, port, username, password)

    try:
        clusters = get_all_clusters(si)
        all_vms  = get_all_vms(si)

        print(f"\n📊 vcsim inventory:")
        print(f"   Clusters: {len(clusters)}")
        print(f"   VMs (before rename): {len(all_vms)}")

        if not clusters:
            print("✗ No clusters found. Start vcsim with -cluster flag.")
            sys.exit(1)

        # Distribute VMs across clusters
        vm_queue = list(all_vms)
        rng.shuffle(vm_queue)

        vms_by_cluster = {}
        total_renamed = 0
        total_skipped = 0

        print(f"\n🔧 Renaming VMs...")

        for cluster_idx, cluster in enumerate(clusters, start=1):
            new_names = generate_vm_names(patterns, envs, count, cluster_idx, rng)
            vms_by_cluster[cluster.name] = new_names

            print(f"\n  Cluster: {cluster.name} ({cluster.host.__len__()} hosts)")

            for new_name in new_names:
                if not vm_queue:
                    print(f"    ⚠ Ran out of VMs to rename. "
                          f"Start vcsim with more -vm count.")
                    break

                vm = vm_queue.pop(0)
                old_name = vm.name

                if dry_run:
                    print(f"    [DRY RUN] {old_name} → {new_name}")
                    total_renamed += 1
                else:
                    if rename_vm(vm, new_name):
                        print(f"    ✓ {old_name} → {new_name}")
                        total_renamed += 1
                    else:
                        total_skipped += 1

        # Leave remaining VMs as-is (they have generic names like DC0_H0_VM0)
        if vm_queue:
            print(f"\n  ℹ {len(vm_queue)} VMs kept with original names (generic hosts)")

        introduce_storage_violations(si, rng)

        print(f"\n{'='*55}")
        print(f"✅ Seeding complete!")
        print(f"   Renamed: {total_renamed} VMs")
        print(f"   Skipped: {total_skipped} VMs")
        print(f"\n📌 Add this vCenter connection in VCM Settings:")
        print(f"   Name:     vcsim-test")
        print(f"   Host:     {host}")
        print(f"   Port:     {port}")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   SSL:      disabled")
        print(f"\n⚙️  Suggested patterns for VCM Settings → Patterns:")
        for p in patterns:
            print(f"   VM Name: ^({p})-  →  matches {p}-PROD-101, {p}-DR-202, ...")
        print(f"{'='*55}\n")

    finally:
        Disconnect(si)


def main():
    parser = argparse.ArgumentParser(
        description="Seed vcsim with realistic randomized VM names for VCM testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--host",     default=DEFAULT_HOST,     help="vcsim host (default: localhost)")
    parser.add_argument("--port",     default=DEFAULT_PORT,     type=int, help="vcsim port (default: 8989)")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="vcsim username (default: user)")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="vcsim password (default: pass)")
    parser.add_argument("--pattern",  default=" ".join(DEFAULT_PATTERNS),
                        help=f"Space-separated VM prefixes (default: {' '.join(DEFAULT_PATTERNS)})")
    parser.add_argument("--env",      default=" ".join(DEFAULT_ENVS),
                        help=f"Space-separated environments (default: {' '.join(DEFAULT_ENVS)})")
    parser.add_argument("--count",    default=DEFAULT_COUNT, type=int,
                        help=f"VMs per pattern group per cluster (default: {DEFAULT_COUNT})")
    parser.add_argument("--seed",     default=None, type=int,
                        help="Random seed for reproducibility (default: random)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Show what would be renamed without making changes")

    args = parser.parse_args()

    seed(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        patterns=args.pattern.split(),
        envs=args.env.split(),
        count=args.count,
        seed_value=args.seed,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
