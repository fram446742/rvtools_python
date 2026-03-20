"""VCPU collector - CPU details and performance"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties
from rvtools.utils.batch_collector import BatchPropertyCollector


class VCPUCollector(BaseCollector):
    """Collector for vCPU sheet - CPU configuration and entitlements"""

    # CPU-related properties to batch collect
    VM_PROPERTIES = [
        'config.name', 'runtime.powerState', 'config.hardware.numCPU',
        'config.hardware.numCoresPerSocket', 'config.cpuAllocation.shares',
        'config.cpuAllocation.reservation', 'config.cpuAllocation.limit',
        'config.annotation', 'config.guestFullName', 'runtime.host',
        'parent', 'config.uuid'
    ]

    def __init__(self, service_instance, directory):
        """Initialize with batch collector"""
        super().__init__(service_instance, directory)
        self.batch_collector = BatchPropertyCollector(self.content)

    @property
    def sheet_name(self):
        return "vCPU"

    def collect(self):
        """Collect CPU information from all VMs"""
        view_type = [vim.VirtualMachine]
        vm_view_list = self.view_cache.get_list(view_type)

        # Batch collect all properties
        batch_results = self.batch_collector.collect_vm_properties(vm_view_list, self.VM_PROPERTIES)

        cpu_list = []

        for vm in vm_view_list:
            cpu_data = self._collect_vm_cpu(vm, batch_results)
            cpu_list.append(cpu_data)

        return cpu_list

    def _collect_vm_cpu(self, vm, batch_results):
        """Collect CPU information for a single VM"""
        cpu_data = {}

        cpu_data["vm"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.name') or ""
        cpu_data["powerstate"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.powerState') or ""
        )

        # Extract common VM properties
        common_props = extract_vm_common_properties(vm)
        cpu_data["template"] = common_props["template"]
        cpu_data["srm_placeholder"] = common_props["srm_placeholder"]

        cpu_data["cpus"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.hardware.numCPU') or ""
        )
        
        cores_per_socket = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.hardware.numCoresPerSocket')
        cpu_data["sockets"] = str(cores_per_socket) if cores_per_socket else ""
        cpu_data["cores_p_s"] = str(cores_per_socket or 1)

        cpu_data["max"] = ""
        cpu_data["overall"] = ""

        cpu_data["level"] = ""
        
        cpu_allocation_shares = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.cpuAllocation.shares')
        cpu_data["shares"] = str(cpu_allocation_shares.shares) if cpu_allocation_shares else ""
        
        cpu_reservation = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.cpuAllocation.reservation')
        cpu_data["reservation"] = str(cpu_reservation) if cpu_reservation else ""
        
        cpu_data["entitlement"] = ""
        cpu_data["drs_entitlement"] = ""
        
        cpu_limit = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.cpuAllocation.limit')
        cpu_data["limit"] = str(cpu_limit) if cpu_limit else ""

        cpu_data["hot_add"] = ""
        cpu_data["hot_remove"] = ""
        cpu_data["numa_hotadd_exposed"] = ""

        cpu_data["annotation"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.annotation') or ""
        cpu_data["com_emc_avamar_vmware_snapshot"] = common_props.get(
            "com_emc_avamar_vmware_snapshot", ""
        )
        cpu_data["com_vmware_vdp2_is_protected"] = common_props.get(
            "com_vmware_vdp2_is_protected", ""
        )
        cpu_data["com_vmware_vdp2_protected_by"] = common_props.get(
            "com_vmware_vdp2_protected_by", ""
        )
        cpu_data["datacenter"] = self._get_datacenter(vm)
        cpu_data["cluster"] = self._get_cluster(vm)
        cpu_data["host"] = self._get_host(vm, batch_results)
        cpu_data["folder"] = self._get_folder(vm, batch_results)
        cpu_data["os_according_to_config"] = ""
        cpu_data["os_according_to_vmware_tools"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.guestFullName') or ""
        cpu_data["vm_id"] = vm._moId or ""
        cpu_data["vm_uuid"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.uuid') or ""
        cpu_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        cpu_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return cpu_data

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
