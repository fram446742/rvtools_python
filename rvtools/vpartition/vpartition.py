"""VPartition collector - VM disk partitions information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties
from rvtools.utils.batch_collector import BatchPropertyCollector


class VPartitionCollector(BaseCollector):
    """Collector for vPartition sheet - VM guest disk partitions"""

    # Partition-related properties to batch collect
    VM_PROPERTIES = [
        'config.name', 'runtime.powerState', 'guest.disk', 'config.annotation',
        'config.guestFullName', 'runtime.host', 'parent', 'config.uuid'
    ]

    def __init__(self, service_instance, directory):
        """Initialize with batch collector"""
        super().__init__(service_instance, directory)
        self.batch_collector = BatchPropertyCollector(self.content)

    @property
    def sheet_name(self):
        return "vPartition"

    def collect(self):
        """Collect partition information from all VMs"""
        view_type = [vim.VirtualMachine]
        vm_view_list = self.view_cache.get_list(view_type)

        # Batch collect all properties
        batch_results = self.batch_collector.collect_vm_properties(vm_view_list, self.VM_PROPERTIES)

        partition_list = []

        for vm in vm_view_list:
            vm_partitions = self._collect_vm_partitions(vm, batch_results)
            partition_list.extend(vm_partitions)

        return partition_list

    def _collect_vm_partitions(self, vm, batch_results):
        """Collect partition information for a single VM"""
        partitions = []

        guest_disk = self.batch_collector.get_vm_property_batch(vm, batch_results, 'guest.disk')
        if not guest_disk:
            return partitions

        # Extract common VM properties once
        common_props = extract_vm_common_properties(vm)

        for disk_info in guest_disk:
            partition_data = {}

            partition_data["vm"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.name') or ""
            partition_data["powerstate"] = str(
                self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.powerState') or ""
            )
            partition_data["template"] = common_props["template"]
            partition_data["disk_key"] = getattr(disk_info, "key", "") or ""
            partition_data["disk"] = disk_info.diskPath or ""

            capacity_mb = getattr(disk_info, "capacity", 0) or 0
            partition_data["capacity_mib"] = (
                str(capacity_mb // (1024 * 1024)) if capacity_mb else ""
            )

            free_space_mb = getattr(disk_info, "freeSpace", 0) or 0
            partition_data["consumed_mib"] = (
                str((capacity_mb - free_space_mb) // (1024 * 1024))
                if capacity_mb
                else ""
            )
            partition_data["free_mib"] = (
                str(free_space_mb // (1024 * 1024)) if free_space_mb else ""
            )

            if capacity_mb > 0:
                free_percent = (free_space_mb / capacity_mb) * 100
                partition_data["free_percent"] = f"{free_percent:.2f}"
            else:
                partition_data["free_percent"] = ""

            partition_data["internal_sort_column"] = ""
            partition_data["annotation"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.annotation') or ""
            partition_data["com_emc_avamar_vmware_snapshot"] = common_props.get(
                "com_emc_avamar_vmware_snapshot", ""
            )
            partition_data["com_vmware_vdp2_is_protected"] = common_props.get(
                "com_vmware_vdp2_is_protected", ""
            )
            partition_data["com_vmware_vdp2_protected_by"] = common_props.get(
                "com_vmware_vdp2_protected_by", ""
            )
            partition_data["datacenter"] = self._get_datacenter(vm)
            partition_data["cluster"] = self._get_cluster(vm)
            partition_data["host"] = self._get_host(vm, batch_results)
            partition_data["folder"] = self._get_folder(vm, batch_results)
            partition_data["os_according_to_config"] = ""
            partition_data["os_according_to_vmware_tools"] = (
                self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.guestFullName') or ""
            )
            partition_data["vm_id"] = vm._moId or ""
            partition_data["vm_uuid"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.uuid') or ""
            partition_data["vi_sdk_server"] = self.content.about.apiVersion or ""
            partition_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

            partitions.append(partition_data)

        return partitions

    def _get_datacenter(self, vm):
        """Get datacenter name for VM"""
        try:
            datacenter_list = self.view_cache.get_list([vim.Datacenter])
            return datacenter_list[0].name if datacenter_list else ""
        except Exception:
            return ""

    def _get_cluster(self, vm):
        """Get cluster name for VM"""
        try:
            cluster_list = self.view_cache.get_list([vim.ClusterComputeResource])
            return cluster_list[0].name if cluster_list else ""
        except Exception:
            return ""

    def _get_host(self, vm, batch_results):
        """Get host name for VM"""
        try:
            host = self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.host')
            return host.name if host else ""
        except Exception:
            return ""

    def _get_folder(self, vm, batch_results):
        """Get folder name for VM"""
        try:
            parent = self.batch_collector.get_vm_property_batch(vm, batch_results, 'parent')
            return parent.name if parent else ""
        except Exception:
            return ""
