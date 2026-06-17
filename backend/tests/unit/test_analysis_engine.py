"""Unit tests for AnalysisEngine — no external dependencies."""
import pytest
from app.services.analysis_engine import AnalysisEngine

ENGINE = AnalysisEngine()

PATTERNS = [
    {"pattern_type": "vm_name", "regex_pattern": r"^(WEB)-\d+"},
    {"pattern_type": "vm_name", "regex_pattern": r"^(DB)-\d+"},
    {"pattern_type": "datastore",  "regex_pattern": r"^(DS-PROD)-\d+"},
]

def _make_inventory(clusters=None, datastores=None, ds_clusters=None):
    return {
        "clusters": clusters or [],
        "datastores": datastores or [],
        "datastore_clusters": ds_clusters or [],
    }

def _make_cluster(name, host_count, vms, drs_rules=None):
    hosts = [f"esx{i:02d}.lab.local" for i in range(1, host_count + 1)]
    return {
        "name": name,
        "host_count": host_count,
        "hosts": hosts,
        "vms": vms,
        "drs_rules": drs_rules or [],
    }

def _make_vm(name, disks=None):
    return {
        "name": name,
        "power_state": "poweredOn",
        "disks": disks or [{"label": "Hard disk 1", "datastore": "DS-PROD-01",
                             "datastore_cluster": None, "capacity_gb": 100, "is_iso": False}],
        "host": "esx01.lab.local",
    }


# ── DRS Tests ────────────────────────────────────────────

class TestDRSCompliance:

    def test_single_vm_skipped(self):
        """A group with only 1 VM must be skipped, not error."""
        cluster = _make_cluster("Cluster-A", 4, [_make_vm("WEB-01")])
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_drs_compliance(inventory, PATTERNS)
        assert result["total_rules_to_create"] == 0
        skipped = result["clusters"][0]["skipped_groups"]
        assert any("WEB" in s["group"] for s in skipped)

    def test_two_vms_one_rule_created(self):
        """2 VMs in a 4-host cluster → 1 rule with both VMs."""
        vms = [_make_vm("WEB-01"), _make_vm("WEB-02")]
        cluster = _make_cluster("Cluster-A", 4, vms)
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_drs_compliance(inventory, PATTERNS)
        assert result["total_rules_to_create"] == 1
        rule = result["clusters"][0]["rules_to_create"][0]
        assert set(rule["vms"]) == {"WEB-01", "WEB-02"}

    def test_rule_size_equals_hosts_minus_one(self):
        """With 3 hosts and 4 VMs, max_per_rule=2 → 2 rules of 2 VMs each."""
        vms = [_make_vm(f"WEB-{i:02d}") for i in range(1, 5)]
        cluster = _make_cluster("Cluster-A", 3, vms)
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_drs_compliance(inventory, PATTERNS)
        rules = result["clusters"][0]["rules_to_create"]
        assert len(rules) == 2
        for rule in rules:
            assert len(rule["vms"]) == 2

    def test_single_host_cluster_skipped(self):
        """Anti-affinity is impossible on a 1-host cluster."""
        vms = [_make_vm("WEB-01"), _make_vm("WEB-02")]
        cluster = _make_cluster("Cluster-A", 1, vms)
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_drs_compliance(inventory, PATTERNS)
        assert result["total_rules_to_create"] == 0
        skipped = result["clusters"][0]["skipped_groups"]
        assert len(skipped) > 0

    def test_unmatched_vms_ignored(self):
        """VMs not matching any pattern produce no rules."""
        vms = [_make_vm("ROUTER-01"), _make_vm("ROUTER-02")]
        cluster = _make_cluster("Cluster-A", 4, vms)
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_drs_compliance(inventory, PATTERNS)
        assert result["total_rules_to_create"] == 0

    def test_vcm_rules_marked_for_deletion(self):
        """Existing VCM-AAR-* rules must be listed for deletion."""
        existing = [{"name": "VCM-AAR-Cluster-A-WEB", "type": "anti_affinity",
                     "enabled": True, "mandatory": False, "vms": [], "key": 1}]
        cluster = _make_cluster("Cluster-A", 4, [_make_vm("WEB-01")], drs_rules=existing)
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_drs_compliance(inventory, PATTERNS)
        assert len(result["clusters"][0]["rules_to_delete"]) == 1

    def test_manual_rules_not_touched(self):
        """Non-VCM rules must not appear in rules_to_delete."""
        existing = [{"name": "manual-affinity-rule", "type": "affinity",
                     "enabled": True, "mandatory": True, "vms": [], "key": 2}]
        cluster = _make_cluster("Cluster-A", 4, [_make_vm("WEB-01")], drs_rules=existing)
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_drs_compliance(inventory, PATTERNS)
        assert len(result["clusters"][0]["rules_to_delete"]) == 0

    def test_multiple_groups_in_cluster(self):
        """WEB and DB groups in same cluster produce separate rules."""
        vms = [_make_vm("WEB-01"), _make_vm("WEB-02"),
               _make_vm("DB-01"),  _make_vm("DB-02")]
        cluster = _make_cluster("Cluster-A", 4, vms)
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_drs_compliance(inventory, PATTERNS)
        assert result["total_rules_to_create"] == 2

    def test_empty_cluster_no_error(self):
        """Empty cluster must not raise exceptions."""
        cluster = _make_cluster("Cluster-Empty", 4, [])
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_drs_compliance(inventory, PATTERNS)
        assert result["total_rules_to_create"] == 0


# ── Storage Tests ─────────────────────────────────────────

class TestStorageCompliance:

    def _disk(self, datastore, ds_cluster=None, is_iso=False):
        return {"label": "Hard disk 1", "datastore": datastore,
                "datastore_cluster": ds_cluster, "capacity_gb": 100, "is_iso": is_iso}

    def test_vms_on_same_datastore_is_violation(self):
        """Two WEB VMs sharing DS-PROD-01 must produce a violation."""
        vms = [
            _make_vm("WEB-01", [self._disk("DS-PROD-01")]),
            _make_vm("WEB-02", [self._disk("DS-PROD-01")]),
        ]
        cluster = _make_cluster("Cluster-A", 4, vms)
        inventory = _make_inventory([cluster], datastores=[
            {"name": "DS-PROD-01", "capacity_gb": 1000, "free_gb": 500, "type": "VMFS"},
            {"name": "DS-PROD-02", "capacity_gb": 1000, "free_gb": 500, "type": "VMFS"},
        ])
        result = ENGINE.analyze_storage_compliance(inventory, PATTERNS)
        assert len(result["violations"]) >= 1
        v = result["violations"][0]
        assert "DS-PROD-01" in v["shared_datastores"]

    def test_vms_on_different_datastores_no_violation(self):
        """WEB VMs on different datastores — no violation."""
        vms = [
            _make_vm("WEB-01", [self._disk("DS-PROD-01")]),
            _make_vm("WEB-02", [self._disk("DS-PROD-02")]),
        ]
        cluster = _make_cluster("Cluster-A", 4, vms)
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_storage_compliance(inventory, PATTERNS)
        assert len(result["violations"]) == 0

    def test_iso_mount_ignored(self):
        """A shared ISO datastore must NOT trigger a violation."""
        vms = [
            _make_vm("WEB-01", [self._disk("DS-PROD-01"),
                                 self._disk("DS-ISO", is_iso=True)]),
            _make_vm("WEB-02", [self._disk("DS-PROD-02"),
                                 self._disk("DS-ISO", is_iso=True)]),
        ]
        cluster = _make_cluster("Cluster-A", 4, vms)
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_storage_compliance(inventory, PATTERNS)
        assert len(result["violations"]) == 0

    def test_scattered_vm_detected(self):
        """A VM with disks on 2 different datastores must appear in scattered_vms."""
        vms = [
            _make_vm("WEB-01", [self._disk("DS-PROD-01"), self._disk("DS-PROD-02")]),
        ]
        cluster = _make_cluster("Cluster-A", 4, vms)
        inventory = _make_inventory([cluster], datastores=[
            {"name": "DS-PROD-01", "capacity_gb": 1000, "free_gb": 800, "type": "VMFS"},
            {"name": "DS-PROD-02", "capacity_gb": 1000, "free_gb": 200, "type": "VMFS"},
        ])
        result = ENGINE.analyze_storage_compliance(inventory, PATTERNS)
        assert any(v["vm_name"] == "WEB-01" for v in result["scattered_vms"])

    def test_single_vm_group_no_violation(self):
        """A group with one VM cannot have a shared-storage violation."""
        vms = [_make_vm("WEB-01", [self._disk("DS-PROD-01")])]
        cluster = _make_cluster("Cluster-A", 4, vms)
        inventory = _make_inventory([cluster])
        result = ENGINE.analyze_storage_compliance(inventory, PATTERNS)
        assert len(result["violations"]) == 0

    def test_summary_counts_correct(self):
        """Summary totals must match actual violation and scattered VM lists."""
        vms = [
            _make_vm("WEB-01", [self._disk("DS-PROD-01")]),
            _make_vm("WEB-02", [self._disk("DS-PROD-01")]),
            _make_vm("DB-01",  [self._disk("DS-DR-01"), self._disk("DS-PROD-02")]),
        ]
        cluster = _make_cluster("Cluster-A", 4, vms)
        inventory = _make_inventory([cluster], datastores=[
            {"name": "DS-PROD-01", "capacity_gb": 1000, "free_gb": 500, "type": "VMFS"},
            {"name": "DS-PROD-02", "capacity_gb": 1000, "free_gb": 500, "type": "VMFS"},
            {"name": "DS-DR-01",   "capacity_gb": 1000, "free_gb": 500, "type": "VMFS"},
        ])
        result = ENGINE.analyze_storage_compliance(inventory, PATTERNS)
        summary = result["summary"]
        assert summary["total_violations"] == len(result["violations"])
        assert summary["total_scattered_vms"] == len(result["scattered_vms"])
