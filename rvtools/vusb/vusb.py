"""VUSB collector - VM USB device information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.cache_utils import ViewCache, get_parent_object


class VUSBCollector(BaseCollector):
    """Collector for vUSB sheet - Virtual USB devices"""

    def __init__(self, service_instance, directory):
        """Initialize with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vUSB"

    def collect(self):
        """Collect USB device information from all VMs"""
        usb_list = []

        # Get all VMs using cached view
        vms = self.view_cache.get_list([vim.VirtualMachine])
        for vm in vms:
            vm_usbs = self._collect_vm_usbs(vm)
            usb_list.extend(vm_usbs)

        return usb_list

    def _collect_vm_usbs(self, vm):
        """Collect USB information for a single VM"""
        usbs = []

        if not vm.config.hardware.device:
            return usbs

        for device in vm.config.hardware.device:
            # Check for VirtualUSBController only
            if type(device).__name__ in ("VirtualUSBController",):
                usb_data = self._collect_usb(vm, device)
                usbs.append(usb_data)

        return usbs

    def _collect_usb(self, vm, usb_device):
        """Collect information for a single USB device"""
        usb_data = {}

        usb_data["vm"] = vm.name or ""
        usb_data["powerstate"] = (
            str(vm.runtime.powerState) if vm.runtime.powerState else ""
        )
        usb_data["template"] = str(vm.config.template) if vm.config.template else ""
        usb_data["srm_placeholder"] = ""

        usb_data["device_node"] = usb_device.deviceInfo.label or ""
        usb_data["device_type"] = type(usb_device).__name__
        usb_data["connected"] = (
            str(usb_device.connectable.connected)
            if hasattr(usb_device, "connectable") and usb_device.connectable
            else ""
        )
        usb_data["family"] = ""
        usb_data["speed"] = ""
        usb_data["ehci_enabled"] = ""
        usb_data["auto_connect"] = ""
        usb_data["bus_number"] = ""
        usb_data["unit_number"] = ""

        usb_data["annotation"] = vm.config.annotation or ""
        usb_data["datacenter"] = self._get_datacenter(vm)
        usb_data["cluster"] = self._get_cluster(vm)
        usb_data["host"] = self._get_host(vm)
        usb_data["folder"] = self._get_folder(vm)
        usb_data["os_according_to_config"] = ""
        usb_data["os_according_to_vmware_tools"] = vm.config.guestFullName or ""
        usb_data["vmref"] = ""
        usb_data["vm_id"] = vm._moId or ""
        usb_data["vm_uuid"] = vm.config.uuid or ""
        usb_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        usb_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return usb_data

    def _get_datacenter(self, vm):
        """Get datacenter name using cached view"""
        try:
            datacenters = self.view_cache.get_list([vim.Datacenter])
            return datacenters[0].name if datacenters else ""
        except Exception:
            return ""

    def _get_cluster(self, vm):
        """Get cluster name using cached view"""
        try:
            clusters = self.view_cache.get_list([vim.ClusterComputeResource])
            return clusters[0].name if clusters else ""
        except Exception:
            return ""

    def _get_host(self, vm):
        """Get host name"""
        try:
            return vm.runtime.host.name if vm.runtime.host else ""
        except Exception:
            return ""

    def _get_folder(self, vm):
        """Get folder name"""
        try:
            return vm.parent.name if vm.parent else ""
        except Exception:
            return ""
