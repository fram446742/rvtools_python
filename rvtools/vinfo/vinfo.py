"""VInfo collector - Main VM information sheet"""
from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


def get_obj(content, vimtype):
    """Get first object of specified type"""
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True
    )
    return container.view[0].name if container.view else ""


class VInfoCollector(BaseCollector):
    """Collector for vInfo sheet - main VM information"""

    @property
    def sheet_name(self):
        return "vInfo"

    def collect(self):
        """Collect VM information from vCenter"""
        container = self.content.rootFolder
        view_type = [vim.VirtualMachine]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        server_list = []
        children = container_view.view

        for child in children:
            vinfo_data = self._collect_vm_info(child)
            server_list.append(vinfo_data)

        return server_list

    def _collect_vm_info(self, vm):
        """Collect all fields for a single VM"""
        vinfo_data = {}

        vinfo_data['vm'] = vm.name or ""
        vinfo_data['powerstate'] = str(vm.runtime.powerState) if vm.runtime.powerState else ""
        vinfo_data['template'] = str(vm.config.template) if vm.config.template else ""
        vinfo_data['config_status'] = str(vm.configStatus) if vm.configStatus else ""
        vinfo_data['dns_name'] = vm.guest.hostName or ""
        vinfo_data['connection_state'] = str(vm.runtime.connectionState) if vm.runtime.connectionState else ""
        vinfo_data['guest_state'] = vm.guest.guestState or ""
        vinfo_data['heartbeat'] = str(vm.guestHeartbeatStatus) if vm.guestHeartbeatStatus else ""
        vinfo_data['consolidation_needed'] = str(vm.runtime.consolidationNeeded) if vm.runtime.consolidationNeeded else ""
        vinfo_data['suspend_time'] = str(vm.runtime.suspendTime) if vm.runtime.suspendTime else ""
        vinfo_data['change_version'] = vm.config.changeVersion or ""
        vinfo_data['cpus'] = str(vm.config.hardware.numCPU) if vm.config.hardware.numCPU else ""
        
        try:
            vinfo_data['latency_sensitivity'] = vm.config.latencySensitivity.level or ""
        except AttributeError:
            vinfo_data['latency_sensitivity'] = ""

        vinfo_data['memory'] = str(vm.config.hardware.memoryMB) if vm.config.hardware.memoryMB else ""
        vinfo_data['nics'] = str(len(vm.network)) if vm.network else "0"
        vinfo_data['disks'] = str(len(vm.layout.disk)) if vm.layout.disk else "0"

        vinfo_data['network_01'] = self._get_network(vm, 0)
        vinfo_data['network_02'] = self._get_network(vm, 1)
        vinfo_data['network_03'] = self._get_network(vm, 2)
        vinfo_data['network_04'] = self._get_network(vm, 3)

        vinfo_data['num_monitors'] = self._get_video_monitors(vm)
        vinfo_data['video_ram_kb'] = self._get_video_ram(vm)

        vinfo_data['ft_state'] = str(vm.runtime.faultToleranceState) if vm.runtime.faultToleranceState else ""
        vinfo_data['boot_delay'] = str(vm.config.bootOptions.bootDelay) if vm.config.bootOptions.bootDelay else ""
        vinfo_data['boot_retry_delay'] = str(vm.config.bootOptions.bootRetryDelay) if vm.config.bootOptions.bootRetryDelay else ""
        vinfo_data['boot_retry_enabled'] = str(vm.config.bootOptions.bootRetryEnabled) if vm.config.bootOptions.bootRetryEnabled else ""
        vinfo_data['firmware'] = vm.config.firmware or ""
        vinfo_data['path'] = vm.config.files.vmPathName or ""
        
        vinfo_data['datacenter'] = get_obj(self.content, [vim.Datacenter])
        vinfo_data['cluster'] = get_obj(self.content, [vim.ClusterComputeResource])
        
        vinfo_data['os_according_to_the_vmware_tools'] = vm.config.guestFullName or ""
        vinfo_data['vm_id'] = vm._moId or ""
        vinfo_data['vm_uuid'] = vm.config.uuid or ""

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
            if device._wsdlName == 'VirtualMachineVideoCard':
                return str(device.numDisplays) if device.numDisplays else ""
        return ""

    def _get_video_ram(self, vm):
        """Get video RAM in KB"""
        for device in vm.config.hardware.device:
            if device._wsdlName == 'VirtualMachineVideoCard':
                return str(device.videoRamSizeInKB) if device.videoRamSizeInKB else ""
        return ""
