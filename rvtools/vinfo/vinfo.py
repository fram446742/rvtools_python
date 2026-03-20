"""VInfo collector - Main VM information sheet"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.cache_utils import ViewCache
from rvtools.vm_utils import extract_vm_common_properties
from rvtools.utils.batch_collector import BatchPropertyCollector


class VInfoCollector(BaseCollector):
    """Collector for vInfo sheet - main VM information"""

    # All vInfo properties to batch collect for performance
    VM_PROPERTIES = [
        'config.name', 'runtime.powerState', 'config.hardware.numCPU',
        'config.hardware.memoryMB', 'summary.quickStats.guestMemoryUsage',
        'config.uuid', 'config.annotation', 'config.guestFullName',
        'config.files.vmPathName', 'runtime.consolidationNeeded',
        'config.bootOptions.bootDelay', 'config.bootOptions.bootRetryDelay',
        'config.bootOptions.bootRetryEnabled', 'config.bootOptions.rebootPowerOff',
        'config.bootOptions.efiSecureBootEnabled', 'config.firmware', 'config.version',
        'config.files.logDirectory', 'config.files.snapshotDirectory',
        'config.files.suspendDirectory', 'runtime.suspendTime', 'config.createDate',
        'config.changeVersion', 'runtime.connectionState', 'guest.guestState',
        'guestHeartbeatStatus', 'config.latencySensitivity', 'config.changeTrackingEnabled',
        'config.memoryHotAddEnabled', 'runtime.faultToleranceState', 'config.ftInfo',
        'configStatus', 'guest.hostName', 'guest.customizationInfo', 'guest.ipAddress',
        'runtime.host', 'resourcePool', 'parent', 'parentVApp', 'config.dasVmProtection',
        'network', 'layout.disk', 'config.hardware.device'
    ]

    def __init__(self, service_instance, directory):
        """Initialize with cache and batch collector"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)
        self.batch_collector = BatchPropertyCollector(self.content)

    @property
    def sheet_name(self):
        return "vInfo"

    def collect(self):
        """Collect VM information from vCenter"""
        server_list = []

        # Get all VMs using cached view
        vms = self.view_cache.get_list([vim.VirtualMachine])
        
        # Batch collect all properties in single API call
        batch_results = self.batch_collector.collect_vm_properties(vms, self.VM_PROPERTIES)
        
        for vm in vms:
            vinfo_data = self._collect_vm_info(vm, batch_results)
            server_list.append(vinfo_data)

        return server_list

    def _collect_vm_info(self, vm, batch_results):
        """Collect all fields for a single VM - 93 properties total"""
        vinfo_data = {}

        # Basic VM info
        vinfo_data["vm"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.name') or ""
        vinfo_data["powerstate"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.powerState') or ""
        )

        # Extract common VM properties
        common_props = extract_vm_common_properties(vm)
        vinfo_data["template"] = common_props["template"]
        vinfo_data["srm_placeholder"] = common_props["srm_placeholder"]

        vinfo_data["config_status"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'configStatus') or ""
        )
        vinfo_data["dns_name"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'guest.hostName') or ""
        vinfo_data["connection_state"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.connectionState') or ""
        )
        vinfo_data["guest_state"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'guest.guestState') or ""
        vinfo_data["heartbeat"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'guestHeartbeatStatus') or ""
        )

        # Consolidation & Memory
        vinfo_data["consolidation_needed"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.consolidationNeeded') or ""
        )
        power_state = self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.powerState')
        vinfo_data["poweron"] = "Yes" if (power_state == "poweredOn") else "No"
        
        mem_hot_add = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.memoryHotAddEnabled')
        vinfo_data["suspended_to_memory"] = "Yes" if mem_hot_add else "No"
        
        vinfo_data["suspend_time"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.suspendTime') or ""
        )
        vinfo_data["suspend_interval"] = ""
        vinfo_data["creation_date"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.createDate') or ""
        )
        vinfo_data["change_version"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.changeVersion') or ""

        # CPU info
        vinfo_data["cpus"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.hardware.numCPU') or ""
        )
        vinfo_data["overall_cpu_readiness"] = ""

        vinfo_data["memory"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.hardware.memoryMB') or ""
        )
        guest_mem = self.batch_collector.get_vm_property_batch(vm, batch_results, 'summary.quickStats.guestMemoryUsage')
        vinfo_data["active_memory"] = str(guest_mem) if guest_mem else ""

        # Devices & Disks
        network = self.batch_collector.get_vm_property_batch(vm, batch_results, 'network')
        vinfo_data["nics"] = str(len(network)) if network else "0"
        
        layout_disk = self.batch_collector.get_vm_property_batch(vm, batch_results, 'layout.disk')
        vinfo_data["disks"] = str(len(layout_disk)) if layout_disk else "0"
        
        vinfo_data["total_disk_capacity_mib"] = self._get_total_disk_capacity(vm, batch_results)
        vinfo_data["fixed_passthru_hotplug"] = ""
        vinfo_data["min_required_evc_mode_key"] = ""

        latency_sens = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.latencySensitivity')
        vinfo_data["latency_sensitivity"] = (
            getattr(latency_sens, "level", "") or ""
        ) if latency_sens else ""
        
        vinfo_data["op_notification_timeout"] = ""
        vinfo_data["enableuuid"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.uuid') or ""
        
        cbt_enabled = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.changeTrackingEnabled')
        vinfo_data["cbt"] = "Yes" if cbt_enabled else "No"
        
        vinfo_data["primary_ip_address"] = self._get_primary_ip(vm, batch_results)

        # Networks
        vinfo_data["network_01"] = self._get_network(vm, 0, batch_results)
        vinfo_data["network_02"] = self._get_network(vm, 1, batch_results)
        vinfo_data["network_03"] = self._get_network(vm, 2, batch_results)
        vinfo_data["network_04"] = self._get_network(vm, 3, batch_results)
        vinfo_data["network_05"] = self._get_network(vm, 4, batch_results)
        vinfo_data["network_06"] = self._get_network(vm, 5, batch_results)
        vinfo_data["network_07"] = self._get_network(vm, 6, batch_results)
        vinfo_data["network_08"] = self._get_network(vm, 7, batch_results)

        vinfo_data["num_monitors"] = self._get_video_monitors(vm, batch_results)
        vinfo_data["video_ram_kb"] = self._get_video_ram(vm, batch_results)

        # Resource pool & folders
        vinfo_data["resource_pool"] = self._get_resource_pool(vm, batch_results)
        vinfo_data["folder_id"] = getattr(vm.parent, "_moId", "") or ""
        vinfo_data["folder"] = self._get_folder(vm, batch_results)
        vinfo_data["vapp"] = self._get_vapp(vm, batch_results)

        # DAS Protection
        das_prot = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.dasVmProtection')
        vinfo_data["das_protection"] = "Yes" if das_prot else "No"

        # Fault Tolerance
        ft_state = self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.faultToleranceState')
        vinfo_data["ft_state"] = str(ft_state) if ft_state else ""
        
        ft_info = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.ftInfo')
        vinfo_data["ft_role"] = (
            getattr(ft_info, "role", "") or ""
        ) if ft_info else ""
        
        vinfo_data["ft_latency"] = ""
        vinfo_data["ft_bandwidth"] = ""
        vinfo_data["ft_sec_latency"] = ""
        vinfo_data["vm_failover_in_progress"] = ""

        # Performance/Storage
        vinfo_data["provisioned_mib"] = ""
        vinfo_data["in_use_mib"] = ""
        vinfo_data["unshared_mib"] = ""

        # HA Configuration
        vinfo_data["ha_restart_priority"] = self._get_ha_restart_priority(vm, batch_results)
        vinfo_data["ha_isolation_response"] = self._get_ha_isolation_response(vm, batch_results)
        vinfo_data["ha_vm_monitoring"] = self._get_ha_monitoring(vm, batch_results)
        vinfo_data["cluster_rule_s"] = ""
        vinfo_data["cluster_rule_name_s"] = ""

        # Boot Options
        vinfo_data["boot_required"] = ""
        vinfo_data["boot_delay"] = ""
        vinfo_data["boot_retry_delay"] = ""
        vinfo_data["boot_retry_enabled"] = ""
        vinfo_data["boot_bios_setup"] = ""
        vinfo_data["reboot_poweroff"] = ""
        vinfo_data["efi_secure_boot"] = ""

        # Firmware & Hardware
        vinfo_data["firmware"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.firmware') or ""
        vinfo_data["hw_version"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.version') or ""
        vinfo_data["hw_upgrade_status"] = ""
        vinfo_data["hw_upgrade_policy"] = ""
        vinfo_data["hw_target"] = ""

        # Paths
        vinfo_data["path"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.files.vmPathName') or ""
        vinfo_data["log_directory"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.files.logDirectory') or ""
        vinfo_data["snapshot_directory"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.files.snapshotDirectory') or ""
        vinfo_data["suspend_directory"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.files.suspendDirectory') or ""

        # Annotation & Metadata
        vinfo_data["annotation"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.annotation') or ""
        vinfo_data["com_emc_avamar_vmware_snapshot"] = common_props.get(
            "com_emc_avamar_vmware_snapshot", ""
        )
        vinfo_data["com_vmware_vdp2_is_protected"] = common_props.get(
            "com_vmware_vdp2_is_protected", ""
        )
        vinfo_data["com_vmware_vdp2_protected_by"] = common_props.get(
            "com_vmware_vdp2_protected_by", ""
        )

        # Infrastructure
        vinfo_data["datacenter"] = self._get_datacenter()
        vinfo_data["cluster"] = self._get_cluster()
        vinfo_data["host"] = self._get_host(vm, batch_results)
        vinfo_data["os_according_to_the_configuration_file"] = ""
        vinfo_data["os_according_to_the_vmware_tools"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.guestFullName') or ""

        # Guest Info
        vinfo_data["customization_info"] = (
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'guest.customizationInfo') or ""
        )
        vinfo_data["guest_detailed_data"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'guest.hostName') or ""

        # IDs & SDKInfo
        vinfo_data["vm_id"] = vm._moId or ""
        vinfo_data["smbios_uuid"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.uuid') or ""
        vinfo_data["vm_uuid"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.uuid') or ""
        vinfo_data["vi_sdk_server_type"] = self.content.about.apiType or ""
        vinfo_data["vi_sdk_api_version"] = self.content.about.apiVersion or ""
        vinfo_data["vi_sdk_server"] = self.content.about.name or ""
        vinfo_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return vinfo_data

    def _get_network(self, vm, index, batch_results):
        """Get network name at specified index"""
        try:
            network = self.batch_collector.get_vm_property_batch(vm, batch_results, 'network')
            return network[index].name if network and index < len(network) and network[index].name else ""
        except (IndexError, TypeError):
            return ""

    def _get_video_monitors(self, vm, batch_results):
        """Get number of video monitors"""
        devices = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.hardware.device')
        if devices:
            for device in devices:
                if hasattr(device, '_wsdlName') and device._wsdlName == "VirtualMachineVideoCard":
                    return str(device.numDisplays) if device.numDisplays else ""
        return ""

    def _get_video_ram(self, vm, batch_results):
        """Get video RAM in KB"""
        devices = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.hardware.device')
        if devices:
            for device in devices:
                if hasattr(device, '_wsdlName') and device._wsdlName == "VirtualMachineVideoCard":
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

    def _get_host(self, vm, batch_results):
        """Get host name for VM"""
        try:
            host = self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.host')
            if host:
                return host.name or ""
        except Exception:
            pass
        return ""

    def _get_total_disk_capacity(self, vm, batch_results):
        """Calculate total disk capacity in MiB"""
        try:
            total_kb = 0
            devices = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.hardware.device')
            if devices:
                for device in devices:
                    if isinstance(device, vim.vm.device.VirtualDisk):
                        capacity_kb = getattr(device.backing, "capacityInKB", 0) or 0
                        total_kb += capacity_kb
            return str(total_kb // 1024) if total_kb else ""
        except Exception:
            return ""

    def _get_primary_ip(self, vm, batch_results):
        """Get primary IP address"""
        try:
            ip_address = self.batch_collector.get_vm_property_batch(vm, batch_results, 'guest.ipAddress')
            if ip_address:
                return ip_address
            host_name = self.batch_collector.get_vm_property_batch(vm, batch_results, 'guest.hostName')
            if host_name:
                return host_name
        except Exception:
            pass
        return ""

    def _get_folder(self, vm, batch_results):
        """Get folder name for VM"""
        try:
            parent = self.batch_collector.get_vm_property_batch(vm, batch_results, 'parent')
            if parent and hasattr(parent, "name"):
                return parent.name or ""
        except Exception:
            pass
        return ""

    def _get_resource_pool(self, vm, batch_results):
        """Get resource pool name"""
        try:
            resource_pool = self.batch_collector.get_vm_property_batch(vm, batch_results, 'resourcePool')
            if resource_pool:
                return resource_pool.name or ""
        except Exception:
            pass
        return ""

    def _get_vapp(self, vm, batch_results):
        """Get vApp name if VM is part of one"""
        try:
            parent_vapp = self.batch_collector.get_vm_property_batch(vm, batch_results, 'parentVApp')
            if parent_vapp:
                return parent_vapp.name or ""
        except Exception:
            pass
        return ""

    def _get_ha_restart_priority(self, vm, batch_results):
        """Get HA restart priority"""
        try:
            das_protection = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.dasVmProtection')
            if das_protection:
                priority = getattr(das_protection, "restartPriority", "")
                return str(priority) if priority else ""
        except Exception:
            pass
        return ""

    def _get_ha_isolation_response(self, vm, batch_results):
        """Get HA isolation response"""
        try:
            das_protection = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.dasVmProtection')
            if das_protection:
                response = getattr(das_protection, "isolationResponse", "")
                return str(response) if response else ""
        except Exception:
            pass
        return ""

    def _get_ha_monitoring(self, vm, batch_results):
        """Get HA VM monitoring status"""
        try:
            das_protection = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.dasVmProtection')
            if das_protection:
                monitoring = getattr(das_protection, "vmMonitoring", "")
                return str(monitoring) if monitoring else ""
        except Exception:
            pass
        return ""
