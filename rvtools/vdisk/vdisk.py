"""VDisk collector - Disk configuration and performance"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties


class VDiskCollector(BaseCollector):
    """Collector for vDisk sheet - Virtual disk configuration"""

    @property
    def sheet_name(self):
        return "vDisk"

    def collect(self):
        """Collect disk information from all VMs"""
        container = self.content.rootFolder
        view_type = [vim.VirtualMachine]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        disk_list = []

        for vm in container_view.view:
            vm_disks = self._collect_vm_disks(vm)
            disk_list.extend(vm_disks)

        return disk_list

    def _collect_vm_disks(self, vm):
        """Collect disk information for a single VM"""
        disks = []

        if not vm.config.hardware.device:
            return disks

        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                disk_data = self._collect_disk(vm, device)
                disks.append(disk_data)

        return disks

    def _collect_disk(self, vm, disk_device):
        """Collect information for a single disk"""
        disk_data = {}

        disk_data["vm"] = vm.name or ""
        disk_data["powerstate"] = (
            str(vm.runtime.powerState) if vm.runtime.powerState else ""
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

        disk_data["annotation"] = vm.config.annotation or ""
        # Add custom metadata
        disk_data["com_emc_avamar_vmware_snapshot"] = common_props.get("com_emc_avamar_vmware_snapshot", "")
        disk_data["com_vmware_vdp2_is_protected"] = common_props.get("com_vmware_vdp2_is_protected", "")
        disk_data["com_vmware_vdp2_protected_by"] = common_props.get("com_vmware_vdp2_protected_by", "")
        disk_data["datacenter"] = self._get_datacenter(vm)
        disk_data["cluster"] = self._get_cluster(vm)
        disk_data["host"] = self._get_host(vm)
        disk_data["folder"] = self._get_folder(vm)
        disk_data["os_according_to_config"] = ""
        disk_data["os_according_to_vmware_tools"] = vm.config.guestFullName or ""
        disk_data["vm_id"] = vm._moId or ""
        disk_data["vm_uuid"] = vm.config.uuid or ""
        disk_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        disk_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return disk_data

    def _get_datacenter(self, vm):
        try:
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.Datacenter], True
            )
            return container.view[0].name if container.view else ""
        except Exception:
            return ""

    def _get_cluster(self, vm):
        try:
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.ClusterComputeResource], True
            )
            return container.view[0].name if container.view else ""
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
