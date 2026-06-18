"""
vCenter Simulator Fixture
=========================
Simulates a realistic vCenter inventory without needing a real vCenter.
Uses vcsim (govmomi simulator) via Docker if available,
otherwise falls back to a pure-Python mock inventory generator.

Each test run generates a RANDOMIZED inventory so edge cases get covered over time.
"""
import random
import string
import pytest
from typing import List, Dict, Optional
from dataclasses import dataclass, field


# ── Data classes mirroring VCenterService output ─────────

@dataclass
class SimDisk:
    label: str
    datastore: str
    datastore_cluster: Optional[str]
    capacity_gb: float
    is_iso: bool = False

@dataclass
class SimVM:
    name: str
    power_state: str
    disks: List[SimDisk]
    host: str

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "power_state": self.power_state,
            "disks": [
                {"label": d.label, "datastore": d.datastore,
                 "datastore_cluster": d.datastore_cluster,
                 "capacity_gb": d.capacity_gb, "is_iso": d.is_iso}
                for d in self.disks
            ],
            "host": self.host,
        }

@dataclass
class SimCluster:
    name: str
    hosts: List[str]
    vms: List[SimVM]
    drs_rules: List[Dict] = field(default_factory=list)

    @property
    def host_count(self) -> int:
        return len(self.hosts)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "host_count": self.host_count,
            "hosts": self.hosts,
            "vm_count": len(self.vms),
            "vms": [v.to_dict() for v in self.vms],
            "drs_rules": self.drs_rules,
        }

@dataclass
class SimDatastore:
    name: str
    capacity_gb: float
    free_gb: float
    ds_type: str = "VMFS"

    def to_dict(self) -> Dict:
        return {"name": self.name, "capacity_gb": self.capacity_gb,
                "free_gb": self.free_gb, "type": self.ds_type}

@dataclass
class SimDatastoreCluster:
    name: str
    datastores: List[str]
    capacity_gb: float = 0.0
    free_gb: float = 0.0

    def to_dict(self) -> Dict:
        return {"name": self.name, "datastores": self.datastores,
                "capacity_gb": self.capacity_gb, "free_gb": self.free_gb}


# ── Inventory generator ───────────────────────────────────

class VCenterSimulator:
    """
    Generates a randomized but realistic vCenter inventory.

    Seed is configurable so tests can be reproduced when a failure is found:
        sim = VCenterSimulator(seed=42)

    Default seed=None → truly random each run → covers more edge cases over time.
    """

    VM_PREFIXES   = ["WEB", "APP", "DB", "CACHE", "PROXY", "WORKER", "BATCH", "MON"]
    CLUSTER_NAMES = ["Cluster-Prod", "Cluster-Dev", "Cluster-DR", "Cluster-Test"]
    DS_PREFIXES   = ["DS-PROD", "DS-DR", "DS-DEV", "DS-BACKUP"]
    DSC_NAMES     = ["DSC-Prod", "DSC-DR", "DSC-Dev"]
    ENVS          = ["PROD", "DEV", "DR", "STG"]

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.seed = seed

    def _rand_str(self, length: int = 4) -> str:
        return ''.join(self.rng.choices(string.ascii_uppercase + string.digits, k=length))

    def generate_inventory(
        self,
        num_clusters: int = None,
        num_ds_clusters: int = None,
        introduce_violations: bool = True,
    ) -> Dict:
        """
        Generate a full randomized inventory dict matching VCenterService.get_full_inventory() format.

        Parameters
        ----------
        num_clusters       : number of clusters (default: random 2-4)
        num_ds_clusters    : number of datastore clusters (default: random 1-3)
        introduce_violations: if True, intentionally place some VMs on shared storage
                              and create some clusters with anti-affinity issues
        """
        num_clusters = num_clusters or self.rng.randint(2, 4)
        num_ds_clusters = num_ds_clusters or self.rng.randint(1, 3)

        # Build datastores and DS clusters first
        datastores, ds_clusters = self._gen_storage(num_ds_clusters)
        all_ds_names = [ds.name for ds in datastores]
        ds_to_pod = {}
        for pod in ds_clusters:
            for dsn in pod.datastores:
                ds_to_pod[dsn] = pod.name

        # Build clusters
        clusters = []
        for i in range(num_clusters):
            cluster = self._gen_cluster(i, all_ds_names, ds_to_pod, introduce_violations)
            clusters.append(cluster)

        # Optionally introduce scattered VMs
        if introduce_violations:
            self._scatter_some_vms(clusters, all_ds_names)

        return {
            "clusters": [c.to_dict() for c in clusters],
            "datastores": [ds.to_dict() for ds in datastores],
            "datastore_clusters": [dsc.to_dict() for dsc in ds_clusters],
        }

    def _gen_storage(self, num_pods: int):
        datastores = []
        ds_clusters = []
        ds_idx = 1
        for pod_i in range(num_pods):
            pod_name = f"DSC-{self.rng.choice(self.ENVS)}-{pod_i+1:02d}"
            num_ds_in_pod = self.rng.randint(2, 4)
            pod_ds_names = []
            for _ in range(num_ds_in_pod):
                prefix = self.rng.choice(self.DS_PREFIXES)
                ds_name = f"{prefix}-{ds_idx:02d}"
                cap = self.rng.choice([1024, 2048, 4096, 8192])
                free = self.rng.randint(int(cap * 0.1), int(cap * 0.8))
                datastores.append(SimDatastore(ds_name, cap, free))
                pod_ds_names.append(ds_name)
                ds_idx += 1
            total_cap = sum(ds.capacity_gb for ds in datastores if ds.name in pod_ds_names)
            total_free = sum(ds.free_gb for ds in datastores if ds.name in pod_ds_names)
            ds_clusters.append(SimDatastoreCluster(pod_name, pod_ds_names, total_cap, total_free))

        # A few standalone datastores (not in any pod)
        for _ in range(self.rng.randint(1, 3)):
            ds_name = f"DS-STANDALONE-{ds_idx:02d}"
            cap = self.rng.choice([512, 1024])
            datastores.append(SimDatastore(ds_name, cap, cap // 2))
            ds_idx += 1

        return datastores, ds_clusters

    def _gen_cluster(self, cluster_idx: int, all_ds: List[str],
                     ds_to_pod: Dict, introduce_violations: bool) -> SimCluster:
        cluster_name = f"{self.rng.choice(self.CLUSTER_NAMES)}-{cluster_idx+1:02d}"
        num_hosts = self.rng.randint(2, 6)
        hosts = [f"esx{cluster_idx+1}{h+1:02d}.vcm.lab" for h in range(num_hosts)]

        vms = []
        # Pick 2-4 VM prefixes for this cluster
        prefixes = self.rng.sample(self.VM_PREFIXES, k=self.rng.randint(2, 4))

        for prefix in prefixes:
            # Each prefix group gets 1-6 VMs
            count = self.rng.randint(1, 6)
            env = self.rng.choice(self.ENVS)
            for idx in range(1, count + 1):
                vm_name = f"{prefix}-{env}-{cluster_idx+1:01d}{idx:02d}"
                host = self.rng.choice(hosts)

                # Pick primary datastore
                primary_ds = self.rng.choice(all_ds)
                disks = [SimDisk(
                    label="Hard disk 1",
                    datastore=primary_ds,
                    datastore_cluster=ds_to_pod.get(primary_ds),
                    capacity_gb=self.rng.choice([50, 100, 200, 500]),
                )]

                # Sometimes add a second data disk on same or different DS
                if self.rng.random() < 0.3:
                    second_ds = self.rng.choice(all_ds)
                    disks.append(SimDisk(
                        label="Hard disk 2",
                        datastore=second_ds,
                        datastore_cluster=ds_to_pod.get(second_ds),
                        capacity_gb=self.rng.choice([100, 200]),
                    ))

                # Sometimes add an ISO mount
                if self.rng.random() < 0.2:
                    disks.append(SimDisk(
                        label="CD/DVD drive 1",
                        datastore="DS-ISO-01",
                        datastore_cluster=None,
                        capacity_gb=0,
                        is_iso=True,
                    ))

                vms.append(SimVM(vm_name, "poweredOn", disks, host))

        # Add an existing VCM-managed DRS rule (to test deletion logic)
        existing_rules = []
        if introduce_violations and self.rng.random() < 0.5:
            existing_rules.append({
                "name": f"VCM-AAR-{cluster_name}-WEB",
                "type": "anti_affinity",
                "enabled": True,
                "mandatory": False,
                "vms": [],
                "key": self.rng.randint(1000, 9999),
            })
        # Add a manual rule (should NOT be touched)
        if self.rng.random() < 0.3:
            existing_rules.append({
                "name": f"manual-rule-{self._rand_str()}",
                "type": "affinity",
                "enabled": True,
                "mandatory": True,
                "vms": [],
                "key": self.rng.randint(100, 999),
            })

        return SimCluster(cluster_name, hosts, vms, existing_rules)

    def _scatter_some_vms(self, clusters: List[SimCluster], all_ds: List[str]):
        """Force some VMs to have disks on multiple datastores (scattered VM scenario)."""
        for cluster in clusters:
            if not cluster.vms:
                continue
            # Pick 1-2 random VMs and scatter their disks
            victims = self.rng.sample(cluster.vms, k=min(2, len(cluster.vms)))
            for vm in victims:
                if len(all_ds) >= 2:
                    ds1, ds2 = self.rng.sample(all_ds, k=2)
                    vm.disks = [
                        SimDisk("Hard disk 1", ds1, None, 100),
                        SimDisk("Hard disk 2", ds2, None, 200),
                    ]

    def print_summary(self, inventory: Dict):
        """Print a human-readable summary of the generated inventory."""
        print(f"\n{'='*60}")
        print(f"vCenter Simulator — seed={self.seed}")
        print(f"{'='*60}")
        for c in inventory["clusters"]:
            print(f"\n  Cluster: {c['name']} ({c['host_count']} hosts, {c['vm_count']} VMs)")
            prefix_groups = {}
            for vm in c["vms"]:
                prefix = vm["name"].split("-")[0]
                prefix_groups.setdefault(prefix, []).append(vm["name"])
            for prefix, names in prefix_groups.items():
                print(f"    [{prefix}] {len(names)} VMs: {', '.join(names[:3])}{'...' if len(names)>3 else ''}")
        print(f"\n  Datastores: {len(inventory['datastores'])}")
        print(f"  DS Clusters: {len(inventory['datastore_clusters'])}")
        for dsc in inventory["datastore_clusters"]:
            print(f"    {dsc['name']}: {dsc['datastores']}")
        print()


# ── Pytest fixtures ───────────────────────────────────────

@pytest.fixture(scope="session")
def vcenter_sim():
    """Session-scoped simulator — same inventory for all tests in the session."""
    return VCenterSimulator(seed=None)  # Random each run


@pytest.fixture
def sim_inventory(vcenter_sim):
    """Function-scoped random inventory — fresh randomization per test."""
    sim = VCenterSimulator(seed=None)
    return sim.generate_inventory(introduce_violations=True)


@pytest.fixture
def sim_inventory_clean():
    """Inventory with NO intentional violations — for positive-path tests."""
    sim = VCenterSimulator(seed=42)
    return sim.generate_inventory(introduce_violations=False)


@pytest.fixture
def sim_inventory_small():
    """Minimal inventory: 1 cluster, 2 hosts, few VMs."""
    sim = VCenterSimulator(seed=7)
    return sim.generate_inventory(num_clusters=1, num_ds_clusters=1, introduce_violations=True)


@pytest.fixture
def sim_inventory_large():
    """Large inventory: 4 clusters, 3 DS clusters, many VMs."""
    sim = VCenterSimulator(seed=99)
    return sim.generate_inventory(num_clusters=4, num_ds_clusters=3, introduce_violations=True)


@pytest.fixture
def default_patterns():
    """Standard regex patterns used across tests."""
    return [
        {"pattern_type": "vm_name", "regex_pattern": r"^(WEB)-"},
        {"pattern_type": "vm_name", "regex_pattern": r"^(APP)-"},
        {"pattern_type": "vm_name", "regex_pattern": r"^(DB)-"},
        {"pattern_type": "vm_name", "regex_pattern": r"^(CACHE)-"},
        {"pattern_type": "vm_name", "regex_pattern": r"^(PROXY)-"},
        {"pattern_type": "vm_name", "regex_pattern": r"^(WORKER)-"},
        {"pattern_type": "vm_name", "regex_pattern": r"^(BATCH)-"},
        {"pattern_type": "vm_name", "regex_pattern": r"^(MON)-"},
        {"pattern_type": "datastore",  "regex_pattern": r"^(DS-PROD)-"},
        {"pattern_type": "datastore",  "regex_pattern": r"^(DS-DR)-"},
    ]
