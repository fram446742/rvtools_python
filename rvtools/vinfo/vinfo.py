"""VInfo collector - Main VM information sheet"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.cache_utils import ViewCache
from rvtools.vm_utils import extract_vm_common_properties


class VInfoCollector(BaseCollector):
    """Collector for vInfo sheet - main VM information"""

    def __init__(self, service_instance, directory):
        """Initialize with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vInfo"

    def collect(self):
        """Collect VM information from vCenter"""
        server_list = []

        # Get all VMs using cached view
        vms = self.view_cache.get_list([vim.VirtualMachine])
        for vm in vms:
            vinfo_data = self._collect_vm_info(vm)
            server_list.append(vinfo_data)

        return server_list

    def _collect_vm_info(self, vm):
        """Collect all fields for a single VM"""
        vinfo_data = {}

        vinfo_data["vm"] = vm.name or ""
        vinfo_data["powerstate"] = (
            str(vm.runtime.powerState) if vm.runtime.powerState else ""
        )
        
        # Extract common VM properties
        common_props = extract_vm_common_properties(vm)
        vinfo_data["template"] = common_props["template"]
        vinfo_data["srm_placeholder"] = common_props["srm_placeholder"]
        
        vinfo_data["config_status"] = str(vm.configStatus) if vm.configStatus else ""
        vinfo_data["dns_name"] = vm.guest.hostName or ""
        vinfo_data["connection_state"] = (
            str(vm.runtime.connectionState) if vm.runtime.connectionState else ""
        )
        vinfo_data["guest_state"] = vm.guest.guestState or ""
        vinfo_data["heartbeat"] = (
            str(vm.guestHeartbeatStatus) if vm.guestHeartbeatStatus else ""
        )
        vinfo_data["consolidation_needed"] = (
            str(vm.runtime.consolidationNeeded)
            if vm.runtime.consolidationNeeded
            else ""
        )
        vinfo_data["suspend_time"] = (
            str(vm.runtime.suspendTime) if vm.runtime.suspendTime else ""
        )
        vinfo_data["change_version"] = vm.config.changeVersion or ""
        vinfo_data["cpus"] = (
            str(vm.config.hardware.numCPU) if vm.config.hardware.numCPU else ""
        )

        try:
            vinfo_data["latency_sensitivity"] = vm.config.latencySensitivity.level or ""
        except AttributeError:
            vinfo_data["latency_sensitivity"] = ""

        vinfo_data["memory"] = (
            str(vm.config.hardware.memoryMB) if vm.config.hardware.memoryMB else ""
        )
        vinfo_data["nics"] = str(len(vm.network)) if vm.network else "0"
        vinfo_data["disks"] = str(len(vm.layout.disk)) if vm.layout.disk else "0"

        vinfo_data["network_01"] = self._get_network(vm, 0)
        vinfo_data["network_02"] = self._get_network(vm, 1)
        vinfo_data["network_03"] = self._get_network(vm, 2)
        vinfo_data["network_04"] = self._get_network(vm, 3)

        vinfo_data["num_monitors"] = self._get_video_monitors(vm)
        vinfo_data["video_ram_kb"] = self._get_video_ram(vm)

        vinfo_data["ft_state"] = (
            str(vm.runtime.faultToleranceState)
            if vm.runtime.faultToleranceState
            else ""
        )
        vinfo_data["boot_delay"] = (
            str(vm.config.bootOptions.bootDelay)
            if vm.config.bootOptions.bootDelay
            else ""
        )
        vinfo_data["boot_retry_delay"] = (
            str(vm.config.bootOptions.bootRetryDelay)
            if vm.config.bootOptions.bootRetryDelay
            else ""
        )
        vinfo_data["boot_retry_enabled"] = (
            str(vm.config.bootOptions.bootRetryEnabled)
            if vm.config.bootOptions.bootRetryEnabled
            else ""
        )
        vinfo_data["firmware"] = vm.config.firmware or ""
        vinfo_data["path"] = vm.config.files.vmPathName or ""

        vinfo_data["datacenter"] = self._get_datacenter()
        vinfo_data["cluster"] = self._get_cluster()

        vinfo_data["os_according_to_the_vmware_tools"] = vm.config.guestFullName or ""
        vinfo_data["vm_id"] = vm._moId or ""
        vinfo_data["vm_uuid"] = vm.config.uuid or ""
        
        # Add custom metadata
        vinfo_data["com_emc_avamar_vmware_snapshot"] = common_props.get("com_emc_avamar_vmware_snapshot", "")
        vinfo_data["com_vmware_vdp2_is_protected"] = common_props.get("com_vmware_vdp2_is_protected", "")
        vinfo_data["com_vmware_vdp2_protected_by"] = common_props.get("com_vmware_vdp2_protected_by", "")

        return vinfo_data

    def _get_network(self, vm, index):
        """Get network name at specified index"""
        try:
            return vm.network[index].name if vm.network[index].name else ""
        except IndexError:
            return ""

    def _get_video_monitors(self, vm):
        """Get number of video monitors"""
        for device in vm.config.hardware.device:
            if device._wsdlName == "VirtualMachineVideoCard":
                return str(device.numDisplays) if device.numDisplays else ""
        return ""

    def _get_video_ram(self, vm):
        """Get video RAM in KB"""
        for device in vm.config.hardware.device:
            if device._wsdlName == "VirtualMachineVideoCard":
                return str(device.videoRamSizeInKB) if device.videoRamSizeInKB else ""
        return ""

    def _get_datacenter(self):
        """Get datacenter name using cached view"""
        try:
            datacenters = self.view_cache.get_list([vim.Datacenter])
            return datacenters[0].name if datacenters else ""
        except Exception:
            return ""

    def _get_cluster(self):
        """Get cluster name using cached view"""
        try:
            clusters = self.view_cache.get_list([vim.ClusterComputeResource])
            return clusters[0].name if clusters else ""
        except Exception:
            return ""

