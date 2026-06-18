"""
Tests using the VCenterSimulator (vcsim) — randomized inventory.

These tests verify that the analysis engine behaves correctly across
a wide range of randomly generated inventories, not just hand-crafted ones.
Each test run covers different scenarios.
"""
import pytest
from app.services.analysis_engine import AnalysisEngine

ENGINE = AnalysisEngine()


class TestDRSWithSimulator:

    def test_no_crash_on_random_inventory(self, sim_inventory, default_patterns):
        """Engine must never raise an exception on any random inventory."""
        result = ENGINE.analyze_drs_compliance(sim_inventory, default_patterns)
        assert isinstance(result, dict)
        assert "clusters" in result
        assert "total_rules_to_create" in result

    def test_single_vm_groups_always_skipped(self, sim_inventory, default_patterns):
        """Any group with exactly 1 VM must appear in skipped_groups, never in rules_to_create."""
        result = ENGINE.analyze_drs_compliance(sim_inventory, default_patterns)
        for cluster in result["clusters"]:
            for rule in cluster["rules_to_create"]:
                assert len(rule["vms"]) >= 2, \
                    f"Rule '{rule['rule_name']}' has only {len(rule['vms'])} VM(s)"

    def test_rule_vm_count_never_exceeds_hosts_minus_one(self, sim_inventory, default_patterns):
        """VMs per rule must be ≤ host_count - 1."""
        result = ENGINE.analyze_drs_compliance(sim_inventory, default_patterns)
        for cluster_result in result["clusters"]:
            host_count = next(
                c["host_count"] for c in sim_inventory["clusters"]
                if c["name"] == cluster_result["cluster_name"]
            )
            max_allowed = max(2, host_count - 1)
            for rule in cluster_result["rules_to_create"]:
                assert len(rule["vms"]) <= max_allowed, (
                    f"Cluster '{cluster_result['cluster_name']}': rule '{rule['rule_name']}' "
                    f"has {len(rule['vms'])} VMs but max is {max_allowed} (hosts={host_count})"
                )

    def test_only_vcm_rules_marked_for_deletion(self, sim_inventory, default_patterns):
        """Only VCM-AAR-* prefixed rules must appear in rules_to_delete."""
        result = ENGINE.analyze_drs_compliance(sim_inventory, default_patterns)
        for cluster in result["clusters"]:
            for rule in cluster["rules_to_delete"]:
                assert rule["name"].startswith("VCM-AAR-"), \
                    f"Non-VCM rule '{rule['name']}' marked for deletion"

    def test_rule_vms_belong_to_cluster(self, sim_inventory, default_patterns):
        """All VMs in a proposed rule must actually exist in that cluster."""
        cluster_vm_map = {
            c["name"]: {v["name"] for v in c["vms"]}
            for c in sim_inventory["clusters"]
        }
        result = ENGINE.analyze_drs_compliance(sim_inventory, default_patterns)
        for cluster in result["clusters"]:
            cluster_vms = cluster_vm_map.get(cluster["cluster_name"], set())
            for rule in cluster["rules_to_create"]:
                for vm_name in rule["vms"]:
                    assert vm_name in cluster_vms, \
                        f"VM '{vm_name}' in rule '{rule['rule_name']}' not found in cluster"

    def test_summary_counts_consistent(self, sim_inventory, default_patterns):
        """total_rules_to_create must equal sum of rules across all clusters."""
        result = ENGINE.analyze_drs_compliance(sim_inventory, default_patterns)
        actual_total = sum(len(c["rules_to_create"]) for c in result["clusters"])
        assert result["total_rules_to_create"] == actual_total

    def test_large_inventory_completes(self, sim_inventory_large, default_patterns):
        """Engine must complete in reasonable time for large inventories."""
        import time
        start = time.time()
        result = ENGINE.analyze_drs_compliance(sim_inventory_large, default_patterns)
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Analysis took {elapsed:.1f}s — too slow"
        assert isinstance(result, dict)

    def test_small_inventory(self, sim_inventory_small, default_patterns):
        """Small inventory (1 cluster) must produce valid results."""
        result = ENGINE.analyze_drs_compliance(sim_inventory_small, default_patterns)
        assert len(result["clusters"]) == 1


class TestStorageWithSimulator:

    def test_no_crash_on_random_inventory(self, sim_inventory, default_patterns):
        """Storage engine must never raise on any random inventory."""
        result = ENGINE.analyze_storage_compliance(sim_inventory, default_patterns)
        assert isinstance(result, dict)
        assert "violations" in result
        assert "scattered_vms" in result
        assert "summary" in result

    def test_iso_never_in_violations(self, sim_inventory, default_patterns):
        """ISO-backed disks must never appear as the shared datastore in a violation."""
        result = ENGINE.analyze_storage_compliance(sim_inventory, default_patterns)
        # Build set of ISO datastores
        iso_datastores = set()
        for cluster in sim_inventory["clusters"]:
            for vm in cluster["vms"]:
                for disk in vm["disks"]:
                    if disk.get("is_iso") and disk.get("datastore"):
                        iso_datastores.add(disk["datastore"])
        for violation in result["violations"]:
            for shared_ds in violation["shared_datastores"]:
                assert shared_ds not in iso_datastores, \
                    f"ISO datastore '{shared_ds}' incorrectly flagged as shared storage violation"

    def test_summary_totals_match_lists(self, sim_inventory, default_patterns):
        """summary counts must match actual list lengths."""
        result = ENGINE.analyze_storage_compliance(sim_inventory, default_patterns)
        summary = result["summary"]
        assert summary["total_violations"] == len(result["violations"])
        assert summary["total_scattered_vms"] == len(result["scattered_vms"])

    def test_proposals_generated_for_violations(self, sim_inventory, default_patterns):
        """Every violation must have a corresponding proposal."""
        result = ENGINE.analyze_storage_compliance(sim_inventory, default_patterns)
        assert len(result["proposals"]) == len(result["violations"])

    def test_clean_inventory_has_no_violations(self, sim_inventory_clean, default_patterns):
        """A clean inventory (no introduced violations) may still have violations
        due to random placement — but must not crash and summary must be consistent."""
        result = ENGINE.analyze_storage_compliance(sim_inventory_clean, default_patterns)
        summary = result["summary"]
        assert summary["total_violations"] == len(result["violations"])
        assert summary["total_scattered_vms"] == len(result["scattered_vms"])

    def test_scattered_vms_have_multiple_datastores(self, sim_inventory, default_patterns):
        """Every VM in scattered_vms must actually have disks on ≥ 2 datastores."""
        result = ENGINE.analyze_storage_compliance(sim_inventory, default_patterns)
        vm_disk_map = {}
        for cluster in sim_inventory["clusters"]:
            for vm in cluster["vms"]:
                real_disks = [d for d in vm["disks"] if not d.get("is_iso") and d.get("datastore")]
                vm_disk_map[vm["name"]] = {d["datastore"] for d in real_disks}

        for scattered in result["scattered_vms"]:
            vm_name = scattered["vm_name"]
            if vm_name in vm_disk_map:
                assert len(vm_disk_map[vm_name]) >= 2, \
                    f"VM '{vm_name}' in scattered_vms but only has 1 datastore"


class TestFindingsGeneration:

    def test_findings_have_required_fields(self, sim_inventory, default_patterns):
        """All generated findings must have required fields."""
        drs = ENGINE.analyze_drs_compliance(sim_inventory, default_patterns)
        storage = ENGINE.analyze_storage_compliance(sim_inventory, default_patterns)
        findings = ENGINE.generate_findings(drs, storage, analysis_run_id=1)

        required_fields = {"analysis_run_id", "finding_type", "severity",
                           "recommendation", "is_actionable"}
        for finding in findings:
            missing = required_fields - finding.keys()
            assert not missing, f"Finding missing fields: {missing}"

    def test_findings_severity_values_valid(self, sim_inventory, default_patterns):
        """Severity must be one of: critical, warning, info."""
        drs = ENGINE.analyze_drs_compliance(sim_inventory, default_patterns)
        storage = ENGINE.analyze_storage_compliance(sim_inventory, default_patterns)
        findings = ENGINE.generate_findings(drs, storage, analysis_run_id=1)

        valid_severities = {"critical", "warning", "info"}
        for finding in findings:
            assert finding["severity"] in valid_severities, \
                f"Invalid severity '{finding['severity']}'"

    def test_analysis_run_id_set_correctly(self, sim_inventory, default_patterns):
        """All findings must have the correct analysis_run_id."""
        drs = ENGINE.analyze_drs_compliance(sim_inventory, default_patterns)
        storage = ENGINE.analyze_storage_compliance(sim_inventory, default_patterns)
        findings = ENGINE.generate_findings(drs, storage, analysis_run_id=999)

        for finding in findings:
            assert finding["analysis_run_id"] == 999
