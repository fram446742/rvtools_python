"""VSnapshot collector - VM snapshot information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties
from rvtools.cache_utils import ViewCache


class VSnapshotCollector(BaseCollector):
    """Collector for vSnapshot sheet - VM snapshots"""

    def __init__(self, service_instance, directory):
        """Initialize collector with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vSnapshot"

    def collect(self):
        """Collect snapshot information from all VMs"""
        view_type = [vim.VirtualMachine]
        vm_view_list = self.view_cache.get_list(view_type)

        snapshot_list = []

        for vm in vm_view_list:
            vm_snapshots = self._collect_vm_snapshots(vm)
            snapshot_list.extend(vm_snapshots)

        return snapshot_list

    def _collect_vm_snapshots(self, vm):
        """Collect snapshots for a single VM"""
        snapshots = []

        if not vm.snapshot or not vm.snapshot.rootSnapshotList:
            return snapshots

        for root_snapshot in vm.snapshot.rootSnapshotList:
            self._walk_snapshots(vm, root_snapshot, snapshots)

        return snapshots

    def _walk_snapshots(self, vm, snapshot, snapshots_list):
        """Recursively walk snapshot tree"""
        snapshot_data = self._collect_snapshot(vm, snapshot)
        snapshots_list.append(snapshot_data)

        if hasattr(snapshot, "childSnapshotList"):
            for child_snapshot in snapshot.childSnapshotList:
                self._walk_snapshots(vm, child_snapshot, snapshots_list)

    def _collect_snapshot(self, vm, snapshot):
        """Collect information for a single snapshot"""
        snapshot_data = {}

        snapshot_data["vm"] = vm.name or ""
        snapshot_data["powerstate"] = (
            str(vm.runtime.powerState) if vm.runtime.powerState else ""
        )

        # Extract common VM properties
        common_props = extract_vm_common_properties(vm)
        snapshot_data["template"] = common_props["template"]
        snapshot_data["srm_placeholder"] = common_props["srm_placeholder"]

        snapshot_data["name"] = snapshot.name or ""
        snapshot_data["description"] = snapshot.description or ""
        snapshot_data["datetime"] = (
            str(snapshot.createTime) if snapshot.createTime else ""
        )
        snapshot_data["filename"] = getattr(snapshot, "vm", {}) or ""
        snapshot_data["size_mib_vmsn"] = ""
        snapshot_data["size_mib_total"] = ""
        snapshot_data["quiesced"] = str(snapshot.quiesced) if snapshot.quiesced else ""
        snapshot_data["state"] = str(snapshot.state) if snapshot.state else ""

        snapshot_data["annotation"] = vm.config.annotation or ""
        # Add custom metadata
        snapshot_data["com_emc_avamar_vmware_snapshot"] = common_props.get(
            "com_emc_avamar_vmware_snapshot", ""
        )
        snapshot_data["com_vmware_vdp2_is_protected"] = common_props.get(
            "com_vmware_vdp2_is_protected", ""
        )
        snapshot_data["com_vmware_vdp2_protected_by"] = common_props.get(
            "com_vmware_vdp2_protected_by", ""
        )
        snapshot_data["datacenter"] = self._get_datacenter(vm)
        snapshot_data["cluster"] = self._get_cluster(vm)
        snapshot_data["host"] = self._get_host(vm)
        snapshot_data["folder"] = self._get_folder(vm)
        snapshot_data["os_according_to_config"] = ""
        snapshot_data["os_according_to_vmware_tools"] = vm.config.guestFullName or ""
        snapshot_data["vm_id"] = vm._moId or ""
        snapshot_data["vm_uuid"] = vm.config.uuid or ""
        snapshot_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        snapshot_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return snapshot_data

    def _get_datacenter(self, vm):
        try:
            datacenter_list = self.view_cache.get_list([vim.Datacenter])
            return datacenter_list[0].name if datacenter_list else ""
        except Exception:
            return ""

    def _get_cluster(self, vm):
        try:
            cluster_list = self.view_cache.get_list([vim.ClusterComputeResource])
            return cluster_list[0].name if cluster_list else ""
        except Exception:
            return ""

    def _get_host(self, vm):
        try:
            return vm.runtime.host.name if vm.runtime.host else ""
        except Exception:
            return ""

    def _get_folder(self, vm):
        try:
            return vm.parent.name if vm.parent else ""
        except Exception:
            return ""
