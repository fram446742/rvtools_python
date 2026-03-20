"""VPartition collector - VM disk partitions information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties


class VPartitionCollector(BaseCollector):
    """Collector for vPartition sheet - VM guest disk partitions"""

    @property
    def sheet_name(self):
        return "vPartition"

    def collect(self):
        """Collect partition information from all VMs"""
        container = self.content.rootFolder
        view_type = [vim.VirtualMachine]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        partition_list = []

        for vm in container_view.view:
            vm_partitions = self._collect_vm_partitions(vm)
            partition_list.extend(vm_partitions)

        return partition_list

    def _collect_vm_partitions(self, vm):
        """Collect partition information for a single VM"""
        partitions = []

        if not vm.guest or not vm.guest.disk:
            return partitions

        # Extract common VM properties once
        common_props = extract_vm_common_properties(vm)

        for disk_info in vm.guest.disk:
            partition_data = {}

            partition_data["vm"] = vm.name or ""
            partition_data["powerstate"] = (
                str(vm.runtime.powerState) if vm.runtime.powerState else ""
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
            partition_data["annotation"] = vm.config.annotation or ""
            # Add custom metadata
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
            partition_data["host"] = self._get_host(vm)
            partition_data["folder"] = self._get_folder(vm)
            partition_data["os_according_to_config"] = ""
            partition_data["os_according_to_vmware_tools"] = (
                vm.config.guestFullName or ""
            )
            partition_data["vm_id"] = vm._moId or ""
            partition_data["vm_uuid"] = vm.config.uuid or ""
            partition_data["vi_sdk_server"] = self.content.about.apiVersion or ""
            partition_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

            partitions.append(partition_data)

        return partitions

    def _get_datacenter(self, vm):
        """Get datacenter name for VM"""
        try:
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.Datacenter], True
            )
            return container.view[0].name if container.view else ""
        except Exception:
            return ""

    def _get_cluster(self, vm):
        """Get cluster name for VM"""
        try:
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.ClusterComputeResource], True
            )
            return container.view[0].name if container.view else ""
        except Exception:
            return ""

    def _get_host(self, vm):
        """Get host name for VM"""
        try:
            return vm.runtime.host.name if vm.runtime.host else ""
        except Exception:
            return ""

    def _get_folder(self, vm):
        """Get folder name for VM"""
        try:
            return vm.parent.name if vm.parent else ""
        except Exception:
            return ""
