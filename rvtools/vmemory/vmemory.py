"""VMemory collector - Memory details and performance"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties


class VMemoryCollector(BaseCollector):
    """Collector for vMemory sheet - Memory configuration and entitlements"""

    @property
    def sheet_name(self):
        return "vMemory"

    def collect(self):
        """Collect memory information from all VMs"""
        container = self.content.rootFolder
        view_type = [vim.VirtualMachine]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        memory_list = []

        for vm in container_view.view:
            memory_data = self._collect_vm_memory(vm)
            memory_list.append(memory_data)

        return memory_list

    def _collect_vm_memory(self, vm):
        """Collect memory information for a single VM"""
        memory_data = {}

        memory_data["vm"] = vm.name or ""
        memory_data["powerstate"] = (
            str(vm.runtime.powerState) if vm.runtime.powerState else ""
        )

        # Extract common VM properties
        common_props = extract_vm_common_properties(vm)
        memory_data["template"] = common_props["template"]
        memory_data["srm_placeholder"] = common_props["srm_placeholder"]

        memory_data["size_mib"] = (
            str(vm.config.hardware.memoryMB) if vm.config.hardware.memoryMB else ""
        )
        memory_data["memory_reservation_locked_to_max"] = ""
        memory_data["overhead"] = ""
        memory_data["max"] = ""
        memory_data["consumed"] = ""
        memory_data["consumed_overhead"] = ""
        memory_data["private"] = ""
        memory_data["shared"] = ""
        memory_data["swapped"] = ""
        memory_data["ballooned"] = ""
        memory_data["active"] = ""
        memory_data["entitlement"] = ""
        memory_data["drs_entitlement"] = ""

        memory_data["level"] = ""
        memory_data["shares"] = (
            str(vm.config.memoryAllocation.shares.shares)
            if vm.config.memoryAllocation.shares
            else ""
        )
        memory_data["reservation"] = (
            str(vm.config.memoryAllocation.reservation)
            if vm.config.memoryAllocation.reservation
            else ""
        )
        memory_data["limit"] = (
            str(vm.config.memoryAllocation.limit)
            if vm.config.memoryAllocation.limit
            else ""
        )

        memory_data["hot_add"] = ""

        memory_data["annotation"] = vm.config.annotation or ""
        # Add custom metadata
        memory_data["com_emc_avamar_vmware_snapshot"] = common_props.get(
            "com_emc_avamar_vmware_snapshot", ""
        )
        memory_data["com_vmware_vdp2_is_protected"] = common_props.get(
            "com_vmware_vdp2_is_protected", ""
        )
        memory_data["com_vmware_vdp2_protected_by"] = common_props.get(
            "com_vmware_vdp2_protected_by", ""
        )
        memory_data["datacenter"] = self._get_datacenter(vm)
        memory_data["cluster"] = self._get_cluster(vm)
        memory_data["host"] = self._get_host(vm)
        memory_data["folder"] = self._get_folder(vm)
        memory_data["os_according_to_config"] = ""
        memory_data["os_according_to_vmware_tools"] = vm.config.guestFullName or ""
        memory_data["vm_id"] = vm._moId or ""
        memory_data["vm_uuid"] = vm.config.uuid or ""
        memory_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        memory_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return memory_data

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
