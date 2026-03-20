"""VNetwork collector - VM network configuration"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.vm_utils import extract_vm_common_properties
from rvtools.cache_utils import ViewCache


class VNetworkCollector(BaseCollector):
    """Collector for vNetwork sheet - VM network adapters"""

    def __init__(self, service_instance, directory):
        """Initialize collector with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vNetwork"

    def collect(self):
        """Collect network information from all VMs"""
        view_type = [vim.VirtualMachine]
        vm_view_list = self.view_cache.get_list(view_type)

        network_list = []

        for vm in vm_view_list:
            vm_networks = self._collect_vm_networks(vm)
            network_list.extend(vm_networks)

        return network_list

    def _collect_vm_networks(self, vm):
        """Collect network information for a single VM"""
        networks = []

        if not vm.config.hardware.device:
            return networks

        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                network_data = self._collect_nic(vm, device)
                networks.append(network_data)

        return networks

    def _collect_nic(self, vm, nic_device):
        """Collect information for a single NIC"""
        network_data = {}

        network_data["vm"] = vm.name or ""
        network_data["powerstate"] = (
            str(vm.runtime.powerState) if vm.runtime.powerState else ""
        )
        # Extract common VM properties

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

        network_data["ipv4_address"] = self._get_ipv4(vm)
        network_data["ipv6_address"] = self._get_ipv6(vm)
        network_data["direct_path_io"] = ""
        network_data["internal_sort_column"] = ""

        network_data["annotation"] = vm.config.annotation or ""

        # Add custom metadata

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
        network_data["host"] = self._get_host(vm)
        network_data["folder"] = self._get_folder(vm)
        network_data["os_according_to_config"] = ""
        network_data["os_according_to_vmware_tools"] = vm.config.guestFullName or ""
        network_data["vm_id"] = vm._moId or ""
        network_data["vm_uuid"] = vm.config.uuid or ""
        network_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        network_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return network_data

    def _get_ipv4(self, vm):
        """Get primary IPv4 address"""
        try:
            if vm.guest and vm.guest.net:
                for net_info in vm.guest.net:
                    if net_info.ipConfig and net_info.ipConfig.ipAddress:
                        for ip_config in net_info.ipConfig.ipAddress:
                            if ":" not in ip_config.ipAddress:
                                return ip_config.ipAddress
        except Exception:
            pass
        return ""

    def _get_ipv6(self, vm):
        """Get primary IPv6 address"""
        try:
            if vm.guest and vm.guest.net:
                for net_info in vm.guest.net:
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
