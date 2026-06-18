#!/usr/bin/env python3
"""
VCM Test Data Generator
=======================
Connects to vcsim and renames VMs to realistic names matching VCM patterns.
Run this after vcsim starts to populate realistic test data.

Usage:
    python3 seed_vcsim.py [--host localhost] [--port 8989] [--seed 42]

Requirements:
    pip install pyVmomi requests
"""
import argparse
import random
import ssl
import sys
import itertools
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect

# ── VM naming config ─────────────────────────────────────
PREFIXES = [
    "WEB", "APP", "DB", "CACHE", "PROXY",
    "WORKER", "BATCH", "MON", "KAFKA", "ELASTIC"
]
ENVS     = ["PROD", "DR", "STG", "DEV"]
SUFFIXES = ["01", "02", "03", "04", "05", "06", "07", "08"]

# ── Datastore naming config ───────────────────────────────
DS_PREFIXES = ["DS-PROD", "DS-DR", "DS-DEV", "DS-BACKUP", "DS-ISO"]


def parse_args():
    p = argparse.ArgumentParser(description="Seed vcsim with realistic VCM test data")
    p.add_argument("--host",   default="localhost")
    p.add_argument("--port",   type=int, default=8989)
    p.add_argument("--user",   default="user")
    p.add_argument("--password", default="pass")
    p.add_argument("--seed",   type=int, default=None,
                   help="Random seed (omit for different names each run)")
    p.add_argument("--prefixes", nargs="+", default=None,
                   help="VM prefixes to use e.g. --prefixes WEB APP DB")
    p.add_argument("--envs",   nargs="+", default=None,
                   help="Environments e.g. --envs PROD DR")
    p.add_argument("--dry-run", action="store_true",
                   help="Print planned renames without applying")
    return p.parse_args()


def connect(host, port, user, password):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    si = SmartConnect(host=host, user=user, pwd=password,
                      port=port, sslContext=ctx)
    print(f"✓ Connected to vcsim at {host}:{port}")
    print(f"  Version: {si.content.about.version}")
    return si


def get_all(si, obj_type):
    content   = si.content
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [obj_type], True)
    objs = list(container.view)
    container.Destroy()
    return objs


def generate_vm_names(vms, prefixes, envs, seed):
    rng = random.Random(seed)
    if seed is not None:
        print(f"  Seed: {seed}  (use same seed to reproduce these names)")
    else:
        import time
        actual_seed = int(time.time())
        rng = random.Random(actual_seed)
        print(f"  Seed: {actual_seed}  (use --seed {actual_seed} to reproduce)")

    # Build a pool of names: PREFIX-ENV-NN
    name_pool = []
    for prefix in prefixes:
        for env in envs:
            for suffix in SUFFIXES:
                name_pool.append(f"{prefix}-{env}-{suffix}")

    rng.shuffle(name_pool)

    # Assign names — cycle if more VMs than pool
    name_cycle = itertools.cycle(name_pool)
    assignments = {}
    for vm in vms:
        new_name = next(name_cycle)
        # Ensure uniqueness by appending index if collision
        base = new_name
        idx  = 2
        while new_name in assignments.values():
            new_name = f"{base}-X{idx:02d}"
            idx += 1
        assignments[vm] = new_name

    return assignments


def rename_vms(assignments, dry_run):
    print(f"\n{'DRY RUN — ' if dry_run else ''}Renaming {len(assignments)} VMs:\n")
    for vm, new_name in assignments.items():
        old_name = vm.name
        print(f"  {old_name:30s} → {new_name}")
        if not dry_run:
            try:
                spec      = vim.vm.ConfigSpec()
                spec.name = new_name
                vm.ReconfigVM_Task(spec=spec)
            except Exception as e:
                print(f"    ⚠ Failed: {e}")


def rename_datastores(si, seed, dry_run):
    rng        = random.Random(seed)
    datastores = get_all(si, vim.Datastore)
    print(f"\n{'DRY RUN — ' if dry_run else ''}Renaming {len(datastores)} datastores:\n")
    ds_names   = []
    for prefix in DS_PREFIXES:
        for i in range(1, 5):
            ds_names.append(f"{prefix}-{i:02d}")
    rng.shuffle(ds_names)
    name_cycle = itertools.cycle(ds_names)
    for ds in datastores:
        new_name = next(name_cycle)
        print(f"  {ds.name:30s} → {new_name}")
        if not dry_run:
            try:
                ds.RenameDatastore(new_name)
            except Exception as e:
                print(f"    ⚠ Failed (normal in vcsim): {e}")


def print_summary(si, assignments):
    clusters = get_all(si, vim.ClusterComputeResource)
    print("\n" + "="*60)
    print("INVENTORY SUMMARY")
    print("="*60)
    vm_name_map = {vm: name for vm, name in assignments.items()}
    for cluster in clusters:
        hosts    = list(cluster.host) if cluster.host else []
        all_vms  = []
        for host in hosts:
            if host.vm:
                all_vms.extend([v for v in host.vm if isinstance(v, vim.VirtualMachine)])
        print(f"\nCluster: {cluster.name}  ({len(hosts)} hosts, {len(all_vms)} VMs)")

        # Group by prefix
        groups = {}
        for vm in all_vms:
            name   = vm_name_map.get(vm, vm.name)
            prefix = name.split("-")[0]
            groups.setdefault(prefix, []).append(name)
        for prefix, names in sorted(groups.items()):
            print(f"  [{prefix}] {len(names)} VMs: {', '.join(sorted(names)[:4])}"
                  f"{'...' if len(names) > 4 else ''}")

    datastores = get_all(si, vim.Datastore)
    print(f"\nDatastores: {len(datastores)}")
    for ds in datastores:
        cap  = round(ds.summary.capacity / 1024**3, 0) if ds.summary else 0
        free = round(ds.summary.freeSpace / 1024**3, 0) if ds.summary else 0
        print(f"  {ds.name:30s}  {cap:.0f} GB total, {free:.0f} GB free")

    ds_clusters = get_all(si, vim.StoragePod)
    if ds_clusters:
        print(f"\nDatastore Clusters: {len(ds_clusters)}")
        for pod in ds_clusters:
            children = len(pod.childEntity) if pod.childEntity else 0
            print(f"  {pod.name:30s}  {children} datastores")
    print()


def main():
    args     = parse_args()
    prefixes = args.prefixes or PREFIXES
    envs     = args.envs     or ENVS

    print("VCM vcsim Test Data Generator")
    print("="*40)
    print(f"Host:     {args.host}:{args.port}")
    print(f"Prefixes: {prefixes}")
    print(f"Envs:     {envs}")
    print(f"Dry run:  {args.dry_run}")
    print()

    si = connect(args.host, args.port, args.user, args.password)

    vms         = get_all(si, vim.VirtualMachine)
    assignments = generate_vm_names(vms, prefixes, envs, args.seed)

    rename_vms(assignments, args.dry_run)
    rename_datastores(si, args.seed, args.dry_run)

    if not args.dry_run:
        print("\n✓ Renaming complete — refreshing summary...")
        # Re-read names from vcsim
        vms2 = get_all(si, vim.VirtualMachine)
        assignments2 = {vm: vm.name for vm in vms2}
        print_summary(si, assignments2)
    else:
        print_summary(si, assignments)

    Disconnect(si)


if __name__ == "__main__":
    main()
