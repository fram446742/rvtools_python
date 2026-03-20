"""VCD collector - VM CD/DVD drive information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties


class VCDCollector(BaseCollector):
    """Collector for vCD sheet - Virtual CD/DVD drives"""

    @property
    def sheet_name(self):
        return "vCD"

    def collect(self):
        """Collect CD/DVD drive information from all VMs"""
        view_type = [vim.VirtualMachine]
        vm_view_list = self.view_cache.get_list(view_type)

        cd_list = []

        for vm in vm_view_list:
            vm_cds = self._collect_vm_cds(vm)
            cd_list.extend(vm_cds)

        return cd_list

    def _collect_vm_cds(self, vm):
        """Collect CD/DVD information for a single VM"""
        cds = []

        if not vm.config.hardware.device:
            return cds

        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualCdrom):
                cd_data = self._collect_cd(vm, device)
                cds.append(cd_data)

        return cds

    def _collect_cd(self, vm, cd_device):
        """Collect information for a single CD/DVD drive"""
        cd_data = {}

        cd_data["vm"] = vm.name or ""
        cd_data["powerstate"] = (
            str(vm.runtime.powerState) if vm.runtime.powerState else ""
        )
        # Extract common VM properties

        common_props = extract_vm_common_properties(vm)

        cd_data["template"] = common_props["template"]
        cd_data["srm_placeholder"] = common_props["srm_placeholder"]

        cd_data["device_node"] = cd_device.deviceInfo.label or ""
        cd_data["connected"] = (
            str(cd_device.connectable.connected) if cd_device.connectable else ""
        )
        cd_data["starts_connected"] = (
            str(cd_device.connectable.startConnected) if cd_device.connectable else ""
        )
        cd_data["device_type"] = type(cd_device).__name__

        cd_data["annotation"] = vm.config.annotation or ""

        # Add custom metadata

        cd_data["com_emc_avamar_vmware_snapshot"] = common_props.get(
            "com_emc_avamar_vmware_snapshot", ""
        )

        cd_data["com_vmware_vdp2_is_protected"] = common_props.get(
            "com_vmware_vdp2_is_protected", ""
        )

        cd_data["com_vmware_vdp2_protected_by"] = common_props.get(
            "com_vmware_vdp2_protected_by", ""
        )
        cd_data["datacenter"] = self._get_datacenter(vm)
        cd_data["cluster"] = self._get_cluster(vm)
        cd_data["host"] = self._get_host(vm)
        cd_data["folder"] = self._get_folder(vm)
        cd_data["os_according_to_config"] = ""
        cd_data["os_according_to_vmware_tools"] = vm.config.guestFullName or ""
        cd_data["vmref"] = ""
        cd_data["vm_id"] = vm._moId or ""
        cd_data["vm_uuid"] = vm.config.uuid or ""
        cd_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        cd_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return cd_data

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
