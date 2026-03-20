"""VNetwork collector - VM network configuration"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties
from rvtools.utils.batch_collector import BatchPropertyCollector


class VNetworkCollector(BaseCollector):
    """Collector for vNetwork sheet - VM network adapters"""

    # Network-related properties to batch collect
    VM_PROPERTIES = [
        'config.name', 'runtime.powerState', 'config.hardware.device',
        'guest.net', 'config.annotation', 'config.guestFullName',
        'runtime.host', 'parent', 'config.uuid'
    ]

    def __init__(self, service_instance, directory):
        """Initialize with batch collector"""
        super().__init__(service_instance, directory)
        self.batch_collector = BatchPropertyCollector(self.content)

    @property
    def sheet_name(self):
        return "vNetwork"

    def collect(self):
        """Collect network information from all VMs"""
        view_type = [vim.VirtualMachine]
        vm_view_list = self.view_cache.get_list(view_type)

        # Batch collect all properties
        batch_results = self.batch_collector.collect_vm_properties(vm_view_list, self.VM_PROPERTIES)

        network_list = []

        for vm in vm_view_list:
            vm_networks = self._collect_vm_networks(vm, batch_results)
            network_list.extend(vm_networks)

        return network_list

    def _collect_vm_networks(self, vm, batch_results):
        """Collect network information for a single VM"""
        networks = []

        devices = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.hardware.device')
        if not devices:
            return networks

        # Filter to only VirtualEthernetCard devices before iterating
        nic_devices = [
            device for device in devices
            if isinstance(device, vim.vm.device.VirtualEthernetCard)
        ]

        for nic_device in nic_devices:
            network_data = self._collect_nic(vm, nic_device, batch_results)
            networks.append(network_data)

        return networks

    def _collect_nic(self, vm, nic_device, batch_results):
        """Collect information for a single NIC"""
        network_data = {}

        network_data["vm"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.name') or ""
        network_data["powerstate"] = str(
            self.batch_collector.get_vm_property_batch(vm, batch_results, 'runtime.powerState') or ""
        )

        common_props = extract_vm_common_properties(vm)

        network_data["template"] = common_props["template"]
        network_data["srm_placeholder"] = common_props["srm_placeholder"]

        network_data["nic_label"] = nic_device.deviceInfo.label or ""
        network_data["adapter"] = nic_device.deviceInfo.label or ""

        if hasattr(nic_device, "backing") and nic_device.backing:
            if hasattr(nic_device.backing, "network"):
                network_data["network"] = (
                    nic_device.backing.network.name
                    if nic_device.backing.network
                    else ""
                )
            else:
                network_data["network"] = ""
        else:
            network_data["network"] = ""

        network_data["switch"] = ""
        network_data["connected"] = (
            str(nic_device.connectable.connected) if nic_device.connectable else ""
        )
        network_data["starts_connected"] = (
            str(nic_device.connectable.startConnected) if nic_device.connectable else ""
        )
        network_data["mac_address"] = nic_device.macAddress or ""
        network_data["type"] = type(nic_device).__name__

        network_data["ipv4_address"] = self._get_ipv4(vm, batch_results)
        network_data["ipv6_address"] = self._get_ipv6(vm, batch_results)
        network_data["direct_path_io"] = ""
        network_data["internal_sort_column"] = ""

        network_data["annotation"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.annotation') or ""

        network_data["com_emc_avamar_vmware_snapshot"] = common_props.get(
            "com_emc_avamar_vmware_snapshot", ""
        )

        network_data["com_vmware_vdp2_is_protected"] = common_props.get(
            "com_vmware_vdp2_is_protected", ""
        )

        network_data["com_vmware_vdp2_protected_by"] = common_props.get(
            "com_vmware_vdp2_protected_by", ""
        )
        network_data["datacenter"] = self._get_datacenter(vm)
        network_data["cluster"] = self._get_cluster(vm)
        network_data["host"] = self._get_host(vm, batch_results)
        network_data["folder"] = self._get_folder(vm, batch_results)
        network_data["os_according_to_config"] = ""
        network_data["os_according_to_vmware_tools"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.guestFullName') or ""
        network_data["vm_id"] = vm._moId or ""
        network_data["vm_uuid"] = self.batch_collector.get_vm_property_batch(vm, batch_results, 'config.uuid') or ""
        network_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        network_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return network_data

    def _get_ipv4(self, vm, batch_results):
        """Get primary IPv4 address"""
        try:
            guest_net = self.batch_collector.get_vm_property_batch(vm, batch_results, 'guest.net')
            if guest_net:
                for net_info in guest_net:
                    if net_info.ipConfig and net_info.ipConfig.ipAddress:
                        for ip_config in net_info.ipConfig.ipAddress:
                            if ":" not in ip_config.ipAddress:
                                return ip_config.ipAddress
        except Exception:
            pass
        return ""

    def _get_ipv6(self, vm, batch_results):
        """Get primary IPv6 address"""
        try:
            guest_net = self.batch_collector.get_vm_property_batch(vm, batch_results, 'guest.net')
            if guest_net:
                for net_info in guest_net:
                    if net_info.ipConfig and net_info.ipConfig.ipAddress:
                        for ip_config in net_info.ipConfig.ipAddress:
                            if ":" in ip_config.ipAddress:
                                return ip_config.ipAddress
        except Exception:
            pass
        return ""

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
