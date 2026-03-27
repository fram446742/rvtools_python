"""VUSB collector - VM USB device information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties
from rvtools.cache_utils import ViewCache, get_parent_object
import logging

logger = logging.getLogger("rvtools")


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
        logger.debug(f"[vUSB] Starting collection from {len(vms)} VMs")
        
        for vm in vms:
            try:
                vm_usbs = self._collect_vm_usbs(vm)
                if vm_usbs:
                    logger.debug(f"[vUSB] VM {vm.name}: found {len(vm_usbs)} USB devices")
                usb_list.extend(vm_usbs)
            except Exception as e:
                logger.debug(f"[vUSB] Error collecting USB for VM {vm.name}: {e}", exc_info=True)

        logger.debug(f"[vUSB] Collection complete: {len(usb_list)} total USB devices found")
        return usb_list

    def _collect_vm_usbs(self, vm):
        """Collect USB information for a single VM"""
        usbs = []

        if not vm.config or not vm.config.hardware or not vm.config.hardware.device:
            logger.debug(f"[vUSB] VM {vm.name}: no hardware devices")
            return usbs

        # Collect all device types for debugging
        device_types = {}
        for device in vm.config.hardware.device:
            device_type = type(device).__name__
            device_types[device_type] = device_types.get(device_type, 0) + 1

        logger.debug(f"[vUSB] VM {vm.name}: device types present: {device_types}")

        # Now collect USB devices
        for device in vm.config.hardware.device:
            device_type = type(device).__name__
            if device_type in ("VirtualUSBController", "VirtualUSBXHCIController", "VirtualUSB"):
                logger.debug(f"[vUSB] VM {vm.name}: found USB device type {device_type}")
                usb_data = self._collect_usb(vm, device)
                usbs.append(usb_data)
            elif "USB" in device_type:
                # Log any other USB-related types we might be missing
                logger.debug(f"[vUSB] VM {vm.name}: found USB-related device type {device_type} (not currently collected)")

        return usbs

    def _collect_usb(self, vm, usb_device):
        """Collect information for a single USB device"""
        usb_data = {}
        device_type = type(usb_device).__name__

        usb_data["vm"] = vm.name or ""
        usb_data["powerstate"] = (
            str(vm.runtime.powerState) if vm.runtime.powerState else ""
        )
        # Extract common VM properties

        common_props = extract_vm_common_properties(vm)

        usb_data["template"] = common_props["template"]
        usb_data["srm_placeholder"] = common_props["srm_placeholder"]

        usb_data["device_node"] = usb_device.deviceInfo.label if hasattr(usb_device, "deviceInfo") and usb_device.deviceInfo else ""
        usb_data["device_type"] = device_type
        
        # VirtualUSB devices have 'connected' property directly
        # VirtualDevice (parent) has 'connectable' property (for pluggable devices like controllers)
        if device_type == "VirtualUSB":
            usb_data["connected"] = (
                str(usb_device.connected) if hasattr(usb_device, "connected") else ""
            )
        else:
            usb_data["connected"] = (
                str(usb_device.connectable.connected)
                if hasattr(usb_device, "connectable") and usb_device.connectable
                else ""
            )
        
        # Extract USB device properties if available (VirtualUSB devices have these)
        usb_data["family"] = (
            ", ".join(usb_device.family) if hasattr(usb_device, "family") and usb_device.family else ""
        )
        usb_data["speed"] = (
            ", ".join(usb_device.speed) if hasattr(usb_device, "speed") and usb_device.speed else ""
        )
        
        # Extract controller-specific properties
        usb_data["ehci_enabled"] = (
            str(usb_device.ehciEnabled) if hasattr(usb_device, "ehciEnabled") else ""
        )
        usb_data["auto_connect"] = (
            str(usb_device.autoConnectDevices) if hasattr(usb_device, "autoConnectDevices") else ""
        )
        usb_data["bus_number"] = ""
        usb_data["unit_number"] = ""

        usb_data["annotation"] = vm.config.annotation or ""

        # Add custom metadata

        usb_data["com_emc_avamar_vmware_snapshot"] = common_props.get(
            "com_emc_avamar_vmware_snapshot", ""
        )

        usb_data["com_vmware_vdp2_is_protected"] = common_props.get(
            "com_vmware_vdp2_is_protected", ""
        )

        usb_data["com_vmware_vdp2_protected_by"] = common_props.get(
            "com_vmware_vdp2_protected_by", ""
        )
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
