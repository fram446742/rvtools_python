"""VUSB collector - VM USB device information"""
from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VUSBCollector(BaseCollector):
    """Collector for vUSB sheet - Virtual USB devices"""

    @property
    def sheet_name(self):
        return "vUSB"

    def collect(self):
        """Collect USB device information from all VMs"""
        container = self.content.rootFolder
        view_type = [vim.VirtualMachine]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        usb_list = []
        
        for vm in container_view.view:
            vm_usbs = self._collect_vm_usbs(vm)
            usb_list.extend(vm_usbs)

        return usb_list

    def _collect_vm_usbs(self, vm):
        """Collect USB information for a single VM"""
        usbs = []

        if not vm.config.hardware.device:
            return usbs

        for device in vm.config.hardware.device:
            if isinstance(device, (vim.vm.device.VirtualUSBController, vim.vm.device.VirtualUSBDevice)):
                usb_data = self._collect_usb(vm, device)
                usbs.append(usb_data)

        return usbs

    def _collect_usb(self, vm, usb_device):
        """Collect information for a single USB device"""
        usb_data = {}

        usb_data['vm'] = vm.name or ""
        usb_data['powerstate'] = str(vm.runtime.powerState) if vm.runtime.powerState else ""
        usb_data['template'] = str(vm.config.template) if vm.config.template else ""
        usb_data['srm_placeholder'] = ""
        
        usb_data['device_node'] = usb_device.deviceInfo.label or ""
        usb_data['device_type'] = type(usb_device).__name__
        usb_data['connected'] = str(usb_device.connectable.connected) if hasattr(usb_device, 'connectable') and usb_device.connectable else ""
        usb_data['family'] = ""
        usb_data['speed'] = ""
        usb_data['ehci_enabled'] = ""
        usb_data['auto_connect'] = ""
        usb_data['bus_number'] = ""
        usb_data['unit_number'] = ""
        
        usb_data['annotation'] = vm.config.annotation or ""
        usb_data['datacenter'] = self._get_datacenter(vm)
        usb_data['cluster'] = self._get_cluster(vm)
        usb_data['host'] = self._get_host(vm)
        usb_data['folder'] = self._get_folder(vm)
        usb_data['os_according_to_config'] = ""
        usb_data['os_according_to_vmware_tools'] = vm.config.guestFullName or ""
        usb_data['vmref'] = ""
        usb_data['vm_id'] = vm._moId or ""
        usb_data['vm_uuid'] = vm.config.uuid or ""
        usb_data['vi_sdk_server'] = self.content.about.apiVersion or ""
        usb_data['vi_sdk_uuid'] = self.content.about.instanceUuid or ""

        return usb_data

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
