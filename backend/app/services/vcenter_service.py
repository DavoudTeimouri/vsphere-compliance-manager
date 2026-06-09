import ssl
import re
from typing import List, Dict, Optional, Tuple
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import atexit
import logging

logger = logging.getLogger(__name__)

class VCenterService:
    def __init__(self, host: str, username: str, password: str, port: int = 443, verify_ssl: bool = False):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.verify_ssl = verify_ssl
        self.si = None

    def connect(self) -> bool:
        try:
            context = None
            if not self.verify_ssl:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            self.si = SmartConnect(
                host=self.host, user=self.username, pwd=self.password,
                port=self.port, sslContext=context
            )
            atexit.register(Disconnect, self.si)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to vCenter {self.host}: {e}")
            raise

    def disconnect(self):
        if self.si:
            try:
                Disconnect(self.si)
            except:
                pass
            self.si = None

    def get_version(self) -> str:
        if not self.si:
            return "unknown"
        return self.si.content.about.version

    def get_all_clusters(self) -> List[vim.ClusterComputeResource]:
        content = self.si.content
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.ClusterComputeResource], True)
        clusters = list(container.view)
        container.Destroy()
        return clusters

    def get_all_vms(self) -> List[vim.VirtualMachine]:
        content = self.si.content
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True)
        vms = list(container.view)
        container.Destroy()
        return vms

    def get_all_datastores(self) -> List[vim.Datastore]:
        content = self.si.content
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Datastore], True)
        datastores = list(container.view)
        container.Destroy()
        return datastores

    def get_datastore_clusters(self) -> List[vim.StoragePod]:
        content = self.si.content
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.StoragePod], True)
        pods = list(container.view)
        container.Destroy()
        return pods

    def get_cluster_hosts(self, cluster: vim.ClusterComputeResource) -> List[vim.HostSystem]:
        return list(cluster.host) if cluster.host else []

    def get_cluster_vms(self, cluster: vim.ClusterComputeResource) -> List[vim.VirtualMachine]:
        hosts = self.get_cluster_hosts(cluster)
        vms = []
        for host in hosts:
            if host.vm:
                vms.extend([vm for vm in host.vm if isinstance(vm, vim.VirtualMachine)])
        return vms

    def get_vm_disks_with_datastores(self, vm: vim.VirtualMachine) -> List[Dict]:
        disks = []
        if not vm.config:
            return disks
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                backing = device.backing
                if hasattr(backing, 'datastore') and backing.datastore:
                    ds_name = backing.datastore.name
                    ds_pod = self._get_datastore_pod(backing.datastore)
                    disks.append({
                        "label": device.deviceInfo.label if device.deviceInfo else "Unknown",
                        "datastore": ds_name,
                        "datastore_cluster": ds_pod,
                        "capacity_gb": round(device.capacityInKB / 1024 / 1024, 2) if device.capacityInKB else 0,
                        "is_iso": False
                    })
            elif isinstance(device, vim.vm.device.VirtualCdrom):
                if hasattr(device.backing, 'fileName'):
                    disks.append({
                        "label": device.deviceInfo.label if device.deviceInfo else "CD/DVD",
                        "datastore": getattr(getattr(device.backing, 'datastore', None), 'name', None),
                        "datastore_cluster": None,
                        "capacity_gb": 0,
                        "is_iso": True
                    })
        return disks

    def _get_datastore_pod(self, datastore: vim.Datastore) -> Optional[str]:
        parent = datastore.parent
        while parent:
            if isinstance(parent, vim.StoragePod):
                return parent.name
            parent = getattr(parent, 'parent', None)
        return None

    def get_drs_rules(self, cluster: vim.ClusterComputeResource) -> List[Dict]:
        rules = []
        if not cluster.configuration or not cluster.configuration.rule:
            return rules
        for rule in cluster.configuration.rule:
            if isinstance(rule, vim.cluster.AntiAffinityRuleSpec):
                vm_names = []
                for vm in (rule.vm or []):
                    try:
                        vm_names.append(vm.name)
                    except:
                        pass
                rules.append({
                    "name": rule.name,
                    "type": "anti_affinity",
                    "enabled": rule.enabled,
                    "mandatory": rule.mandatory,
                    "vms": vm_names,
                    "key": rule.key
                })
            elif isinstance(rule, vim.cluster.AffinityRuleSpec):
                vm_names = []
                for vm in (rule.vm or []):
                    try:
                        vm_names.append(vm.name)
                    except:
                        pass
                rules.append({
                    "name": rule.name,
                    "type": "affinity",
                    "enabled": rule.enabled,
                    "mandatory": rule.mandatory,
                    "vms": vm_names,
                    "key": rule.key
                })
        return rules

    def delete_drs_rule(self, cluster: vim.ClusterComputeResource, rule_key: int) -> bool:
        try:
            spec = vim.cluster.ConfigSpecEx()
            rule_spec = vim.cluster.RuleSpec()
            rule_spec.operation = vim.option.ArrayUpdateSpec.Operation.remove
            rule_spec.removeKey = rule_key
            spec.rulesSpec = [rule_spec]
            task = cluster.ReconfigureEx(spec, modify=True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete DRS rule: {e}")
            return False

    def create_anti_affinity_rule(self, cluster: vim.ClusterComputeResource,
                                   rule_name: str, vm_names: List[str]) -> bool:
        try:
            vms_in_cluster = self.get_cluster_vms(cluster)
            vm_map = {vm.name: vm for vm in vms_in_cluster}
            target_vms = [vm_map[name] for name in vm_names if name in vm_map]
            if len(target_vms) < 2:
                return False
            spec = vim.cluster.ConfigSpecEx()
            rule = vim.cluster.AntiAffinityRuleSpec()
            rule.name = rule_name
            rule.enabled = True
            rule.mandatory = False
            rule.vm = target_vms
            rule_spec = vim.cluster.RuleSpec()
            rule_spec.operation = vim.option.ArrayUpdateSpec.Operation.add
            rule_spec.info = rule
            spec.rulesSpec = [rule_spec]
            task = cluster.ReconfigureEx(spec, modify=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create DRS rule: {e}")
            return False

    def get_full_inventory(self) -> Dict:
        clusters_data = []
        clusters = self.get_all_clusters()
        for cluster in clusters:
            hosts = self.get_cluster_hosts(cluster)
            vms = self.get_cluster_vms(cluster)
            drs_rules = self.get_drs_rules(cluster)
            vm_data = []
            for vm in vms:
                if not vm.config:
                    continue
                disks = self.get_vm_disks_with_datastores(vm)
                vm_data.append({
                    "name": vm.name,
                    "power_state": str(vm.runtime.powerState) if vm.runtime else "unknown",
                    "disks": disks,
                    "host": vm.runtime.host.name if vm.runtime and vm.runtime.host else None
                })
            clusters_data.append({
                "name": cluster.name,
                "host_count": len(hosts),
                "hosts": [h.name for h in hosts],
                "vm_count": len(vm_data),
                "vms": vm_data,
                "drs_rules": drs_rules
            })
        datastores = self.get_all_datastores()
        ds_data = [{
            "name": ds.name,
            "capacity_gb": round(ds.summary.capacity / 1024**3, 2) if ds.summary else 0,
            "free_gb": round(ds.summary.freeSpace / 1024**3, 2) if ds.summary else 0,
            "type": ds.summary.type if ds.summary else "unknown"
        } for ds in datastores]
        pods = self.get_datastore_clusters()
        pod_data = [{
            "name": pod.name,
            "capacity_gb": round(pod.summary.capacity / 1024**3, 2) if pod.summary else 0,
            "free_gb": round(pod.summary.freeSpace / 1024**3, 2) if pod.summary else 0,
            "datastores": [ds.name for ds in (pod.childEntity or [])]
        } for pod in pods]
        return {
            "clusters": clusters_data,
            "datastores": ds_data,
            "datastore_clusters": pod_data
        }
