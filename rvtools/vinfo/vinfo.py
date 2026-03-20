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
        """Collect all fields for a single VM - 93 properties total"""
        vinfo_data = {}

        # Basic VM info
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
        
        # Consolidation & Memory
        vinfo_data["consolidation_needed"] = (
            str(vm.runtime.consolidationNeeded)
            if vm.runtime.consolidationNeeded
            else ""
        )
        vinfo_data["poweron"] = "Yes" if (vm.runtime.powerState == 'poweredOn') else "No"
        vinfo_data["suspended_to_memory"] = (
            "Yes" if getattr(vm.config, 'memoryHotAddEnabled', False) else "No"
        )
        vinfo_data["suspend_time"] = (
            str(vm.runtime.suspendTime) if vm.runtime.suspendTime else ""
        )
        vinfo_data["suspend_interval"] = ""
        vinfo_data["creation_date"] = (
            str(vm.config.createDate) if vm.config.createDate else ""
        )
        vinfo_data["change_version"] = vm.config.changeVersion or ""
        
        # CPU info
        vinfo_data["cpus"] = (
            str(vm.config.hardware.numCPU) if vm.config.hardware.numCPU else ""
        )
        vinfo_data["overall_cpu_readiness"] = ""

        vinfo_data["memory"] = (
            str(vm.config.hardware.memoryMB) if vm.config.hardware.memoryMB else ""
        )
        vinfo_data["active_memory"] = (
            str(vm.summary.quickStats.guestMemoryUsage) 
            if hasattr(vm.summary.quickStats, 'guestMemoryUsage') and vm.summary.quickStats.guestMemoryUsage
            else ""
        )
        
        # Devices & Disks
        vinfo_data["nics"] = str(len(vm.network)) if vm.network else "0"
        vinfo_data["disks"] = str(len(vm.layout.disk)) if vm.layout.disk else "0"
        vinfo_data["total_disk_capacity_mib"] = self._get_total_disk_capacity(vm)
        vinfo_data["fixed_passthru_hotplug"] = ""
        vinfo_data["min_required_evc_mode_key"] = ""
        
        vinfo_data["latency_sensitivity"] = getattr(vm.config.latencySensitivity, 'level', '') or ""
        vinfo_data["op_notification_timeout"] = ""
        vinfo_data["enableuuid"] = vm.config.uuid or ""
        vinfo_data["cbt"] = (
            "Yes" if getattr(vm.config, 'changeTrackingEnabled', False) else "No"
        )
        vinfo_data["primary_ip_address"] = self._get_primary_ip(vm)
        
        # Networks
        vinfo_data["network_01"] = self._get_network(vm, 0)
        vinfo_data["network_02"] = self._get_network(vm, 1)
        vinfo_data["network_03"] = self._get_network(vm, 2)
        vinfo_data["network_04"] = self._get_network(vm, 3)
        vinfo_data["network_05"] = self._get_network(vm, 4)
        vinfo_data["network_06"] = self._get_network(vm, 5)
        vinfo_data["network_07"] = self._get_network(vm, 6)
        vinfo_data["network_08"] = self._get_network(vm, 7)

        vinfo_data["num_monitors"] = self._get_video_monitors(vm)
        vinfo_data["video_ram_kb"] = self._get_video_ram(vm)

        # Resource pool & folders
        vinfo_data["resource_pool"] = self._get_resource_pool(vm)
        vinfo_data["folder_id"] = getattr(vm.parent, '_moId', '') or ""
        vinfo_data["folder"] = self._get_folder(vm)
        vinfo_data["vapp"] = self._get_vapp(vm)
        
        # DAS Protection
        vinfo_data["das_protection"] = (
            "Yes" if getattr(vm.config, 'dasVmProtection', None) else "No"
        )
        
        # Fault Tolerance
        vinfo_data["ft_state"] = (
            str(vm.runtime.faultToleranceState)
            if vm.runtime.faultToleranceState
            else ""
        )
        vinfo_data["ft_role"] = getattr(vm.config.ftInfo, 'role', '') or "" if hasattr(vm.config, 'ftInfo') else ""
        vinfo_data["ft_latency"] = ""
        vinfo_data["ft_bandwidth"] = ""
        vinfo_data["ft_sec_latency"] = ""
        vinfo_data["vm_failover_in_progress"] = ""
        
        # Performance/Storage
        vinfo_data["provisioned_mib"] = ""
        vinfo_data["in_use_mib"] = ""
        vinfo_data["unshared_mib"] = ""
        
        # HA Configuration
        vinfo_data["ha_restart_priority"] = self._get_ha_restart_priority(vm)
        vinfo_data["ha_isolation_response"] = self._get_ha_isolation_response(vm)
        vinfo_data["ha_vm_monitoring"] = self._get_ha_monitoring(vm)
        vinfo_data["cluster_rule_s"] = ""
        vinfo_data["cluster_rule_name_s"] = ""
        
        # Boot Options
        vinfo_data["boot_required"] = ""
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
            "Yes" if vm.config.bootOptions.bootRetryEnabled else "No"
        )
        vinfo_data["boot_bios_setup"] = ""
        vinfo_data["reboot_poweroff"] = (
            "Yes" if getattr(vm.config.bootOptions, 'rebootPowerOff', False) else "No"
        )
        vinfo_data["efi_secure_boot"] = (
            "Yes" if getattr(vm.config.bootOptions, 'efiSecureBootEnabled', False) else "No"
        )
        
        # Firmware & Hardware
        vinfo_data["firmware"] = vm.config.firmware or ""
        vinfo_data["hw_version"] = vm.config.version or ""
        vinfo_data["hw_upgrade_status"] = ""
        vinfo_data["hw_upgrade_policy"] = ""
        vinfo_data["hw_target"] = ""
        
        # Paths
        vinfo_data["path"] = vm.config.files.vmPathName or ""
        vinfo_data["log_directory"] = vm.config.files.logDirectory or ""
        vinfo_data["snapshot_directory"] = vm.config.files.snapshotDirectory or ""
        vinfo_data["suspend_directory"] = vm.config.files.suspendDirectory or ""
        
        # Annotation & Metadata
        vinfo_data["annotation"] = vm.config.annotation or ""
        vinfo_data["com_emc_avamar_vmware_snapshot"] = common_props.get("com_emc_avamar_vmware_snapshot", "")
        vinfo_data["com_vmware_vdp2_is_protected"] = common_props.get("com_vmware_vdp2_is_protected", "")
        vinfo_data["com_vmware_vdp2_protected_by"] = common_props.get("com_vmware_vdp2_protected_by", "")
        
        # Infrastructure
        vinfo_data["datacenter"] = self._get_datacenter()
        vinfo_data["cluster"] = self._get_cluster()
        vinfo_data["host"] = self._get_host(vm)
        vinfo_data["os_according_to_the_configuration_file"] = ""
        vinfo_data["os_according_to_the_vmware_tools"] = vm.config.guestFullName or ""
        
        # Guest Info
        vinfo_data["customization_info"] = getattr(vm.guest, 'customizationInfo', '') or ""
        vinfo_data["guest_detailed_data"] = vm.guest.hostName or ""
        
        # IDs & SDKInfo
        vinfo_data["vm_id"] = vm._moId or ""
        vinfo_data["smbios_uuid"] = vm.config.uuid or ""
        vinfo_data["vm_uuid"] = vm.config.uuid or ""
        vinfo_data["vi_sdk_server_type"] = self.content.about.apiType or ""
        vinfo_data["vi_sdk_api_version"] = self.content.about.apiVersion or ""
        vinfo_data["vi_sdk_server"] = self.content.about.name or ""
        vinfo_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

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

    def _get_host(self, vm):
        """Get host name for VM"""
        try:
            if vm.runtime.host:
                return vm.runtime.host.name or ""
        except Exception:
            pass
        return ""

    def _get_total_disk_capacity(self, vm):
        """Calculate total disk capacity in MiB"""
        try:
            total_kb = 0
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    capacity_kb = getattr(device.backing, "capacityInKB", 0) or 0
                    total_kb += capacity_kb
            return str(total_kb // 1024) if total_kb else ""
        except Exception:
            return ""

    def _get_primary_ip(self, vm):
        """Get primary IP address"""
        try:
            if vm.guest and vm.guest.ipAddress:
                return vm.guest.ipAddress
            # Fallback to hostname if IP not available
            if vm.guest and vm.guest.hostName:
                return vm.guest.hostName
        except Exception:
            pass
        return ""

    def _get_folder(self, vm):
        """Get folder name for VM"""
        try:
            if vm.parent and hasattr(vm.parent, 'name'):
                return vm.parent.name or ""
        except Exception:
            pass
        return ""

    def _get_resource_pool(self, vm):
        """Get resource pool name"""
        try:
            if vm.resourcePool:
                return vm.resourcePool.name or ""
        except Exception:
            pass
        return ""

    def _get_vapp(self, vm):
        """Get vApp name if VM is part of one"""
        try:
            if hasattr(vm, 'parentVApp') and vm.parentVApp:
                return vm.parentVApp.name or ""
        except Exception:
            pass
        return ""

    def _get_ha_restart_priority(self, vm):
        """Get HA restart priority"""
        try:
            if hasattr(vm.config, 'dasVmProtection') and vm.config.dasVmProtection:
                priority = getattr(vm.config.dasVmProtection, 'restartPriority', '')
                return str(priority) if priority else ""
        except Exception:
            pass
        return ""

    def _get_ha_isolation_response(self, vm):
        """Get HA isolation response"""
        try:
            if hasattr(vm.config, 'dasVmProtection') and vm.config.dasVmProtection:
                response = getattr(vm.config.dasVmProtection, 'isolationResponse', '')
                return str(response) if response else ""
        except Exception:
            pass
        return ""

    def _get_ha_monitoring(self, vm):
        """Get HA VM monitoring status"""
        try:
            if hasattr(vm.config, 'dasVmProtection') and vm.config.dasVmProtection:
                monitoring = getattr(vm.config.dasVmProtection, 'vmMonitoring', '')
                return str(monitoring) if monitoring else ""
        except Exception:
            pass
        return ""


