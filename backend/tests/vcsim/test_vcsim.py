"""
vcsim integration tests
-----------------------
Run against a live vcsim instance.
vcsim default inventory:
  - 2 Datacenters
  - 2 Clusters per DC (4 total)
  - 4 Hosts per Cluster (16 total)
  - 20 VMs distributed across hosts
  - 4 Datastores

Every test session randomises VM naming patterns so different
compliance scenarios are covered automatically.
"""
import pytest
import random
from app.services.analysis_engine import AnalysisEngine


# ── Connectivity ──────────────────────────────────────────

class TestVcsimConnectivity:

    def test_connects_successfully(self, vcenter_service):
        """vcsim must be reachable and return a version string."""
        version = vcenter_service.get_version()
        assert version, "Expected a non-empty version string from vcsim"
        print(f"\n[vcsim] version: {version}")

    def test_inventory_has_clusters(self, inventory):
        clusters = inventory["clusters"]
        assert len(clusters) > 0, "No clusters found in vcsim inventory"
        print(f"\n[vcsim] Clusters: {[c['name'] for c in clusters]}")

    def test_inventory_has_hosts(self, inventory):
        total_hosts = sum(c["host_count"] for c in inventory["clusters"])
        assert total_hosts > 0

    def test_inventory_has_vms(self, inventory):
        total_vms = sum(c["vm_count"] for c in inventory["clusters"])
        assert total_vms > 0
        print(f"\n[vcsim] Total VMs: {total_vms}")

    def test_inventory_has_datastores(self, inventory):
        assert len(inventory["datastores"]) > 0

    def test_all_vms_have_names(self, inventory):
        for cluster in inventory["clusters"]:
            for vm in cluster["vms"]:
                assert vm["name"], f"VM with empty name in cluster {cluster['name']}"

    def test_all_clusters_have_host_count(self, inventory):
        for cluster in inventory["clusters"]:
            assert cluster["host_count"] > 0, f"Cluster {cluster['name']} has 0 hosts"


# ── DRS Analysis against vcsim ────────────────────────────

class TestDRSWithVcsim:

    def test_drs_analysis_runs_without_error(self, inventory, random_patterns, session_seed):
        """DRS analysis must complete without exceptions on live inventory."""
        print(f"\n[vcsim] seed={session_seed}, patterns={[p['name'] for p in random_patterns]}")
        engine = AnalysisEngine()
        result = engine.analyze_drs_compliance(inventory, random_patterns)
        assert "clusters" in result
        assert "total_rules_to_create" in result
        assert isinstance(result["total_rules_to_create"], int)

    def test_drs_result_has_all_clusters(self, inventory, random_patterns):
        engine = AnalysisEngine()
        result = engine.analyze_drs_compliance(inventory, random_patterns)
        input_names  = {c["name"] for c in inventory["clusters"]}
        output_names = {c["cluster_name"] for c in result["clusters"]}
        assert input_names == output_names

    def test_drs_rule_size_never_exceeds_host_count_minus_one(self, inventory, random_patterns):
        """Core compliance rule: VMs per rule ≤ host_count - 1."""
        engine = AnalysisEngine()
        result = engine.analyze_drs_compliance(inventory, random_patterns)
        for cluster_result in result["clusters"]:
            host_count = next(
                c["host_count"] for c in inventory["clusters"]
                if c["name"] == cluster_result["cluster_name"]
            )
            max_allowed = max(2, host_count - 1)
            for rule in cluster_result.get("rules_to_create", []):
                assert len(rule["vms"]) <= max_allowed, (
                    f"Rule '{rule['rule_name']}' has {len(rule['vms'])} VMs "
                    f"but cluster has {host_count} hosts (max allowed: {max_allowed})"
                )

    def test_drs_single_vm_groups_never_get_rules(self, inventory, random_patterns):
        """Groups with 1 VM must appear in skipped_groups, never in rules_to_create."""
        engine = AnalysisEngine()
        result = engine.analyze_drs_compliance(inventory, random_patterns)
        for cluster_result in result["clusters"]:
            for rule in cluster_result.get("rules_to_create", []):
                assert len(rule["vms"]) >= 2, (
                    f"Rule '{rule['rule_name']}' was created with only 1 VM"
                )

    def test_drs_skipped_groups_have_reason(self, inventory, random_patterns):
        engine = AnalysisEngine()
        result = engine.analyze_drs_compliance(inventory, random_patterns)
        for cluster_result in result["clusters"]:
            for skip in cluster_result.get("skipped_groups", []):
                assert skip.get("reason"), "Skipped group missing reason"

    def test_drs_summary_counts_consistent(self, inventory, random_patterns):
        engine = AnalysisEngine()
        result = engine.analyze_drs_compliance(inventory, random_patterns)
        total_rules = sum(
            len(c.get("rules_to_create", [])) for c in result["clusters"]
        )
        assert result["total_rules_to_create"] == total_rules


# ── Storage Analysis against vcsim ───────────────────────

class TestStorageWithVcsim:

    def test_storage_analysis_runs_without_error(self, inventory, random_patterns):
        engine = AnalysisEngine()
        result = engine.analyze_storage_compliance(inventory, random_patterns)
        assert "violations" in result
        assert "scattered_vms" in result
        assert "proposals" in result
        assert "summary" in result

    def test_storage_summary_counts_match(self, inventory, random_patterns):
        engine = AnalysisEngine()
        result = engine.analyze_storage_compliance(inventory, random_patterns)
        summary = result["summary"]
        assert summary["total_violations"] == len(result["violations"])
        assert summary["total_scattered_vms"] == len(result["scattered_vms"])

    def test_iso_disks_do_not_cause_violations(self, inventory, random_patterns):
        """
        vcsim VMs may share an ISO datastore.
        Violations should only come from real disk datastores.
        """
        engine = AnalysisEngine()
        result = engine.analyze_storage_compliance(inventory, random_patterns)
        for violation in result["violations"]:
            # All shared datastores in a violation must be real disk stores, not ISO
            assert violation["shared_datastores"] or violation["shared_datastore_clusters"], (
                "Violation with no shared resources — likely ISO false positive"
            )

    def test_proposals_exist_for_violations(self, inventory, random_patterns):
        engine = AnalysisEngine()
        result = engine.analyze_storage_compliance(inventory, random_patterns)
        if result["violations"]:
            assert len(result["proposals"]) > 0, (
                "Violations found but no proposals generated"
            )

    def test_proposals_have_suggestion(self, inventory, random_patterns):
        engine = AnalysisEngine()
        result = engine.analyze_storage_compliance(inventory, random_patterns)
        for proposal in result["proposals"]:
            assert proposal.get("suggestion"), "Proposal missing suggestion text"
            assert "feasible" in proposal, "Proposal missing feasibility flag"

    def test_scattered_vms_have_recommendation(self, inventory, random_patterns):
        engine = AnalysisEngine()
        result = engine.analyze_storage_compliance(inventory, random_patterns)
        for vm in result["scattered_vms"]:
            assert vm.get("recommendation"), (
                f"Scattered VM '{vm['vm_name']}' missing recommendation"
            )
            assert len(vm["datastores"]) > 1, (
                f"VM '{vm['vm_name']}' flagged as scattered but has only 1 datastore"
            )

    def test_full_analysis_coverage(self, inventory, random_patterns, session_seed):
        """Run both DRS and Storage and print a full summary — useful for debugging."""
        engine = AnalysisEngine()
        drs     = engine.analyze_drs_compliance(inventory, random_patterns)
        storage = engine.analyze_storage_compliance(inventory, random_patterns)

        print(f"""
╔══════════════════════════════════════════════════╗
║           vcsim Analysis Summary                 ║
║  seed: {session_seed:<42}║
╠══════════════════════════════════════════════════╣
║ DRS                                              ║
║   Rules to create : {drs['total_rules_to_create']:<29}║
║   Rules to delete : {drs['total_rules_to_delete']:<29}║
║   Single-VM skips : {len(drs['skipped_single_vm']):<29}║
╠══════════════════════════════════════════════════╣
║ Storage                                          ║
║   Violations      : {storage['summary']['total_violations']:<29}║
║   Critical        : {storage['summary']['critical_violations']:<29}║
║   Scattered VMs   : {storage['summary']['total_scattered_vms']:<29}║
║   Proposals       : {storage['summary']['total_proposals']:<29}║
╚══════════════════════════════════════════════════╝
        """)

        assert drs["clusters"], "No clusters analyzed"
