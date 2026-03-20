"""VTools collector - VMware Tools information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties
from rvtools.cache_utils import ViewCache


class VToolsCollector(BaseCollector):
    """Collector for vTools sheet - VMware Tools status and version"""

    def __init__(self, service_instance, directory):
        """Initialize collector with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vTools"

    def collect(self):
        """Collect VMware Tools information from all VMs"""
        view_type = [vim.VirtualMachine]
        vm_view_list = self.view_cache.get_list(view_type)

        tools_list = []

        for vm in vm_view_list:
            tools_data = self._collect_vm_tools(vm)
            tools_list.append(tools_data)

        return tools_list

    def _collect_vm_tools(self, vm):
        """Collect VMware Tools information for a single VM"""
        tools_data = {}

        tools_data["vm"] = vm.name or ""
        tools_data["powerstate"] = (
            str(vm.runtime.powerState) if vm.runtime.powerState else ""
        )
        # Extract common VM properties

        common_props = extract_vm_common_properties(vm)

        tools_data["template"] = common_props["template"]
        tools_data["srm_placeholder"] = common_props["srm_placeholder"]

        tools_data["vm_version"] = vm.config.version or ""
        tools_data["tools"] = str(vm.guest.toolsStatus) if vm.guest.toolsStatus else ""
        tools_data["tools_version"] = vm.guest.toolsVersion or ""
        tools_data["required_version"] = vm.guest.toolsVersionStatus or ""
        tools_data["upgradeable"] = ""
        tools_data["upgrade_policy"] = ""
        tools_data["sync_time"] = ""
        tools_data["app_status"] = ""
        tools_data["heartbeat_status"] = (
            str(vm.guestHeartbeatStatus) if vm.guestHeartbeatStatus else ""
        )
        tools_data["kernel_crash_state"] = ""
        tools_data["operation_ready"] = ""
        tools_data["state_change_support"] = ""
        tools_data["interactive_guest"] = ""

        tools_data["annotation"] = vm.config.annotation or ""

        # Add custom metadata

        tools_data["com_emc_avamar_vmware_snapshot"] = common_props.get(
            "com_emc_avamar_vmware_snapshot", ""
        )

        tools_data["com_vmware_vdp2_is_protected"] = common_props.get(
            "com_vmware_vdp2_is_protected", ""
        )

        tools_data["com_vmware_vdp2_protected_by"] = common_props.get(
            "com_vmware_vdp2_protected_by", ""
        )
        tools_data["datacenter"] = self._get_datacenter(vm)
        tools_data["cluster"] = self._get_cluster(vm)
        tools_data["host"] = self._get_host(vm)
        tools_data["folder"] = self._get_folder(vm)
        tools_data["os_according_to_config"] = ""
        tools_data["os_according_to_vmware_tools"] = vm.config.guestFullName or ""
        tools_data["vmref"] = ""
        tools_data["vm_id"] = vm._moId or ""
        tools_data["vm_uuid"] = vm.config.uuid or ""
        tools_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        tools_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return tools_data

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
