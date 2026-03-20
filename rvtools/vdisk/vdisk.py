"""VDisk collector - Disk configuration and performance"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties
from rvtools.utils.batch_collector import BatchPropertyCollector


class VDiskCollector(BaseCollector):
    """Collector for vDisk sheet - Virtual disk configuration"""

    # Disk-related properties to batch collect
    VM_PROPERTIES = [
        'config.name', 'runtime.powerState', 'config.hardware.device',
        'config.annotation', 'config.guestFullName', 'runtime.host',
        'parent', 'config.uuid'
    ]

    def __init__(self, service_instance, directory):
        """Initialize with batch collector"""
        super().__init__(service_instance, directory)
        self.batch_collector = BatchPropertyCollector(self.content)

    @property
    def sheet_name(self):
        return "vDisk"

    def collect(self):
        """Collect disk information from all VMs"""
        view_type = [vim.VirtualMachine]
        vm_view_list = self.view_cache.get_list(view_type)

        # Batch collect all properties
        batch_results = self.batch_collector.collect_vm_properties(vm_view_list, self.VM_PROPERTIES)

        disk_list = []

        for vm in vm_view_list:
            vm_disks = self._collect_vm_disks(vm, batch_results)
            disk_list.extend(vm_disks)

        return disk_list

    def _collect_vm_disks(self, vm, batch_results):
        """Collect disk information for a single VM"""
        disks = []

        devices = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.hardware.device')
        if not devices:
            return disks

        # Filter to only VirtualDisk devices before iterating
        disk_devices = [
            device for device in devices
            if isinstance(device, vim.vm.device.VirtualDisk)
        ]

        for disk_device in disk_devices:
            disk_data = self._collect_disk(vm, disk_device, batch_results)
            disks.append(disk_data)

        return disks

    def _collect_disk(self, vm, disk_device, batch_results):
        """Collect information for a single disk"""
        disk_data = {}

        disk_data["vm"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.name') or ""
        disk_data["powerstate"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.powerState') or ""
        )

        # Extract common VM properties
        common_props = extract_vm_common_properties(vm)
        disk_data["template"] = common_props["template"]
        disk_data["srm_placeholder"] = common_props["srm_placeholder"]

        disk_data["disk"] = disk_device.deviceInfo.label or ""
        disk_data["disk_key"] = str(disk_device.key) if disk_device.key else ""
        disk_data["disk_uuid"] = getattr(disk_device.backing, "uuid", "") or ""
        disk_data["disk_path"] = getattr(disk_device.backing, "fileName", "") or ""

        capacity_kb = getattr(disk_device.backing, "capacityInKB", 0) or 0
        disk_data["capacity_mib"] = str(capacity_kb // 1024) if capacity_kb else ""

        disk_data["raw"] = ""
        disk_data["disk_mode"] = getattr(disk_device.backing, "diskMode", "") or ""
        disk_data["sharing_mode"] = getattr(disk_device, "shares", None) or ""
        disk_data["thin"] = ""
        disk_data["eagerly_scrub"] = ""
        disk_data["split"] = ""
        disk_data["write_through"] = ""

        disk_data["level"] = ""
        disk_data["shares"] = ""
        disk_data["reservation"] = ""
        disk_data["limit"] = ""

        disk_data["controller"] = ""
        disk_data["label"] = disk_device.deviceInfo.label or ""
        disk_data["scsi_unit"] = ""
        disk_data["unit"] = ""
        disk_data["shared_bus"] = ""
        disk_data["path"] = getattr(disk_device.backing, "fileName", "") or ""
        disk_data["raw_lun_id"] = ""
        disk_data["raw_comp_mode"] = ""
        disk_data["internal_sort_column"] = ""

        disk_data["annotation"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.annotation') or ""
        disk_data["com_emc_avamar_vmware_snapshot"] = common_props.get(
            "com_emc_avamar_vmware_snapshot", ""
        )
        disk_data["com_vmware_vdp2_is_protected"] = common_props.get(
            "com_vmware_vdp2_is_protected", ""
        )
        disk_data["com_vmware_vdp2_protected_by"] = common_props.get(
            "com_vmware_vdp2_protected_by", ""
        )
        disk_data["datacenter"] = self._get_datacenter(vm)
        disk_data["cluster"] = self._get_cluster(vm)
        disk_data["host"] = self._get_host(vm, batch_results)
        disk_data["folder"] = self._get_folder(vm, batch_results)
        disk_data["os_according_to_config"] = ""
        disk_data["os_according_to_vmware_tools"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.guestFullName') or ""
        disk_data["vm_id"] = vm._moId or ""
        disk_data["vm_uuid"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.uuid') or ""
        disk_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        disk_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return disk_data

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

    def _get_host(self, vm, batch_results):
        try:
            host = self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.host')
            return host.name if host else ""
        except Exception:
            return ""

    def _get_folder(self, vm, batch_results):
        try:
            parent = self.batch_collector.get_vm_property_batch(vm, batch_results, 'parent')
            return parent.name if parent else ""
        except Exception:
            return ""
