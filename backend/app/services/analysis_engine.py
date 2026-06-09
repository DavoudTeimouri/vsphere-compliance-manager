import re
import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class AnalysisEngine:

    def analyze_drs_compliance(self, inventory: Dict, patterns: List[Dict]) -> Dict:
        """Analyze DRS Anti-Affinity rules compliance per cluster."""
        results = {
            "clusters": [],
            "total_violations": 0,
            "total_rules_to_create": 0,
            "total_rules_to_delete": 0,
            "skipped_single_vm": []
        }
        vm_patterns = [p for p in patterns if p.get("pattern_type") == "vm_name"]
        role_pattern_cfg = next((p for p in patterns if p.get("pattern_type") == "role"), None)
        role_prefix = role_pattern_cfg["regex_pattern"] if role_pattern_cfg else "VCM-AAR-{cluster}-{group}"
        for cluster in inventory.get("clusters", []):
            cluster_name = cluster["name"]
            host_count = cluster["host_count"]
            vms = cluster["vms"]
            existing_rules = cluster["drs_rules"]
            cluster_result = {
                "cluster_name": cluster_name,
                "host_count": host_count,
                "vm_groups": [],
                "rules_to_delete": [],
                "rules_to_create": [],
                "skipped_groups": [],
                "existing_rules_count": len(existing_rules)
            }
            # Group VMs by pattern match
            vm_groups = defaultdict(list)
            for vm in vms:
                for pattern in vm_patterns:
                    try:
                        match = re.search(pattern["regex_pattern"], vm["name"], re.IGNORECASE)
                        if match:
                            group_key = match.group(0) if match.lastindex is None else match.group(1)
                            vm_groups[group_key].append(vm["name"])
                            break
                    except re.error:
                        pass
            # Find VCM-managed rules to delete
            for rule in existing_rules:
                if rule["name"].startswith("VCM-AAR-"):
                    cluster_result["rules_to_delete"].append(rule)
            # Analyze each VM group
            for group_key, group_vms in vm_groups.items():
                vm_count = len(group_vms)
                if vm_count == 1:
                    cluster_result["skipped_groups"].append({
                        "group": group_key,
                        "vms": group_vms,
                        "reason": "Only 1 VM in group - anti-affinity rule not needed"
                    })
                    results["skipped_single_vm"].append(f"{cluster_name}/{group_key}")
                    continue
                if host_count < 2:
                    cluster_result["skipped_groups"].append({
                        "group": group_key,
                        "vms": group_vms,
                        "reason": f"Cluster has only {host_count} host(s) - anti-affinity not possible"
                    })
                    continue
                # Calculate optimal rule size: VMs per rule = host_count - 1
                max_vms_per_rule = max(2, host_count - 1) if host_count > 1 else 2
                # Create rule batches
                batches = [group_vms[i:i+max_vms_per_rule] for i in range(0, len(group_vms), max_vms_per_rule)]
                for idx, batch in enumerate(batches):
                    if len(batch) < 2:
                        cluster_result["skipped_groups"].append({
                            "group": f"{group_key}_batch{idx+1}",
                            "vms": batch,
                            "reason": "Remaining VM count is 1, no rule needed"
                        })
                        continue
                    rule_name = f"VCM-AAR-{cluster_name}-{group_key}" + (f"-{idx+1}" if len(batches) > 1 else "")
                    cluster_result["rules_to_create"].append({
                        "rule_name": rule_name,
                        "vms": batch,
                        "group_key": group_key,
                        "vm_count": len(batch),
                        "max_vms_per_rule": max_vms_per_rule,
                        "rationale": f"Host count={host_count}, max VMs per rule={max_vms_per_rule}"
                    })
                cluster_result["vm_groups"].append({
                    "group_key": group_key,
                    "vm_count": vm_count,
                    "vms": group_vms
                })
            results["clusters"].append(cluster_result)
            results["total_rules_to_create"] += len(cluster_result["rules_to_create"])
            results["total_rules_to_delete"] += len(cluster_result["rules_to_delete"])
        return results

    def analyze_storage_compliance(self, inventory: Dict, patterns: List[Dict]) -> Dict:
        """Analyze storage placement compliance."""
        results = {
            "violations": [],
            "scattered_vms": [],
            "proposals": [],
            "summary": {}
        }
        ds_patterns = [p for p in patterns if p.get("pattern_type") in ("datastore", "vm_name")]
        all_datastores = {ds["name"]: ds for ds in inventory.get("datastores", [])}
        ds_clusters = {pod["name"]: pod for pod in inventory.get("datastore_clusters", [])}
        ds_to_pod = {}
        for pod_name, pod in ds_clusters.items():
            for ds_name in pod.get("datastores", []):
                ds_to_pod[ds_name] = pod_name
        # Group VMs by pattern
        vm_groups = defaultdict(list)
        all_vms_with_disks = []
        for cluster in inventory.get("clusters", []):
            for vm in cluster["vms"]:
                vm_entry = {**vm, "cluster": cluster["name"]}
                all_vms_with_disks.append(vm_entry)
                for pattern in ds_patterns:
                    try:
                        match = re.search(pattern["regex_pattern"], vm["name"], re.IGNORECASE)
                        if match:
                            gk = match.group(1) if match.lastindex else match.group(0)
                            vm_groups[gk].append(vm_entry)
                            break
                    except re.error:
                        pass
        # Check: VMs in same group should NOT share the same datastore/ds_cluster
        for group_key, group_vms in vm_groups.items():
            if len(group_vms) < 2:
                continue
            # Collect datastores per VM (excluding ISOs)
            vm_storage = {}
            for vm in group_vms:
                real_disks = [d for d in vm.get("disks", []) if not d.get("is_iso") and d.get("datastore")]
                ds_set = set()
                pod_set = set()
                for disk in real_disks:
                    ds_set.add(disk["datastore"])
                    pod = ds_to_pod.get(disk["datastore"]) or disk.get("datastore_cluster")
                    if pod:
                        pod_set.add(pod)
                vm_storage[vm["name"]] = {"datastores": ds_set, "pods": pod_set, "vm": vm}
            # Find violations: any two VMs in group sharing a datastore or ds_cluster
            vm_names = list(vm_storage.keys())
            for i in range(len(vm_names)):
                for j in range(i+1, len(vm_names)):
                    vm_a = vm_names[i]
                    vm_b = vm_names[j]
                    shared_ds = vm_storage[vm_a]["datastores"] & vm_storage[vm_b]["datastores"]
                    shared_pods = vm_storage[vm_a]["pods"] & vm_storage[vm_b]["pods"]
                    if shared_ds or shared_pods:
                        results["violations"].append({
                            "group": group_key,
                            "vm_a": vm_a,
                            "vm_b": vm_b,
                            "shared_datastores": list(shared_ds),
                            "shared_datastore_clusters": list(shared_pods),
                            "severity": "critical" if shared_pods else "warning"
                        })
        # Detect scattered VMs: VM with disks on multiple datastores
        for vm in all_vms_with_disks:
            real_disks = [d for d in vm.get("disks", []) if not d.get("is_iso") and d.get("datastore")]
            if not real_disks:
                continue
            ds_set = set(d["datastore"] for d in real_disks)
            pod_set = set(ds_to_pod.get(d["datastore"]) or d.get("datastore_cluster") or "" for d in real_disks)
            pod_set.discard("")
            if len(ds_set) > 1 or len(pod_set) > 1:
                results["scattered_vms"].append({
                    "vm_name": vm["name"],
                    "cluster": vm.get("cluster"),
                    "datastores": list(ds_set),
                    "datastore_clusters": list(pod_set),
                    "disk_count": len(real_disks),
                    "recommendation": self._generate_consolidation_proposal(
                        vm["name"], list(ds_set), list(pod_set), all_datastores, ds_clusters
                    )
                })
        # Generate proposals for violations
        for violation in results["violations"]:
            group_vms_data = [v for v in all_vms_with_disks if v["name"] in [violation["vm_a"], violation["vm_b"]]]
            available_ds = [ds for ds in all_datastores.values() if ds["free_gb"] > 50]
            available_pods = list(ds_clusters.values())
            results["proposals"].append({
                "violation": violation,
                "type": "storage_separation",
                "feasible": len(available_ds) >= 2 or len(available_pods) >= 2,
                "suggestion": self._suggest_separation(
                    violation["vm_a"], violation["vm_b"],
                    violation["shared_datastores"], violation["shared_datastore_clusters"],
                    available_ds, available_pods
                )
            })
        results["summary"] = {
            "total_violations": len(results["violations"]),
            "total_scattered_vms": len(results["scattered_vms"]),
            "total_proposals": len(results["proposals"]),
            "critical_violations": len([v for v in results["violations"] if v["severity"] == "critical"])
        }
        return results

    def _generate_consolidation_proposal(self, vm_name, datastores, pods, all_ds, all_pods) -> str:
        if len(datastores) <= 1:
            return "VM disks already on single datastore."
        best_ds = max(all_ds.values(), key=lambda d: d.get("free_gb", 0), default=None)
        if best_ds:
            return f"Consolidate all disks to '{best_ds['name']}' (most free space: {best_ds.get('free_gb', 0):.0f} GB)"
        return f"VM has disks on {len(datastores)} datastores. Manual review needed."

    def _suggest_separation(self, vm_a, vm_b, shared_ds, shared_pods, available_ds, available_pods) -> str:
        if len(available_ds) < 2 and len(available_pods) < 2:
            return f"⚠️ Only {len(available_ds)} datastore(s) available. Separation may not be possible. Review infrastructure."
        if shared_pods and len(available_pods) >= 2:
            pods_str = ", ".join(p["name"] for p in available_pods[:3])
            return f"Move '{vm_b}' disks to a different datastore cluster. Available: {pods_str}"
        if shared_ds and len(available_ds) >= 2:
            ds_str = ", ".join(d["name"] for d in available_ds[:3])
            return f"Move '{vm_b}' disks to a different datastore. Options: {ds_str}"
        return "Manual review required for optimal placement."

    def generate_findings(self, drs_results: Dict, storage_results: Dict, analysis_run_id: int) -> List[Dict]:
        findings = []
        # DRS findings
        for cluster in drs_results.get("clusters", []):
            for skip in cluster.get("skipped_groups", []):
                findings.append({
                    "analysis_run_id": analysis_run_id,
                    "finding_type": "drs_skip",
                    "severity": "info",
                    "cluster_name": cluster["cluster_name"],
                    "vm_name": ", ".join(skip["vms"]),
                    "details": skip,
                    "recommendation": skip["reason"],
                    "is_actionable": False
                })
            for rule in cluster.get("rules_to_create", []):
                findings.append({
                    "analysis_run_id": analysis_run_id,
                    "finding_type": "drs_rule_needed",
                    "severity": "warning",
                    "cluster_name": cluster["cluster_name"],
                    "vm_name": ", ".join(rule["vms"]),
                    "details": rule,
                    "recommendation": f"Create anti-affinity rule '{rule['rule_name']}' for {rule['vm_count']} VMs",
                    "is_actionable": True
                })
        # Storage findings
        for violation in storage_results.get("violations", []):
            findings.append({
                "analysis_run_id": analysis_run_id,
                "finding_type": "storage_shared",
                "severity": violation["severity"],
                "vm_name": f"{violation['vm_a']} + {violation['vm_b']}",
                "datastore_name": ", ".join(violation["shared_datastores"] + violation["shared_datastore_clusters"]),
                "details": violation,
                "recommendation": f"Separate VMs in group '{violation['group']}' across different storage",
                "is_actionable": True
            })
        for vm in storage_results.get("scattered_vms", []):
            findings.append({
                "analysis_run_id": analysis_run_id,
                "finding_type": "storage_scattered",
                "severity": "warning",
                "cluster_name": vm.get("cluster"),
                "vm_name": vm["vm_name"],
                "datastore_name": ", ".join(vm["datastores"]),
                "details": vm,
                "recommendation": vm["recommendation"],
                "is_actionable": True
            })
        return findings
