"""VNIC collector - Physical network NIC information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VNICCollector(BaseCollector):
    """Collector for vNIC sheet - Physical Network NICs"""

    @property
    def sheet_name(self):
        return "vNIC"

    def collect(self):
        """Collect NIC information from all hosts"""
        nic_list = []
        container = self.content.rootFolder
        view_type = [vim.HostSystem]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        for host in container_view.view:
            host_nics = self._collect_host_nics(host)
            nic_list.extend(host_nics)

        return nic_list

    def _collect_host_nics(self, host):
        """Collect NICs for a single host"""
        nics = []
        try:
            if host.config and host.config.network and host.config.network.pnic:
                for nic in host.config.network.pnic:
                    nic_data = {
                        "host": host.name or "",
                        "datacenter": self._get_datacenter(host),
                        "cluster": self._get_cluster(host),
                        "network_device": nic.device or "",
                        "driver": nic.driver or "",
                        "speed": str(nic.linkSpeed.speedMb)
                        if hasattr(nic, "linkSpeed") and nic.linkSpeed
                        else "",
                        "duplex": str(nic.linkSpeed.duplex)
                        if hasattr(nic, "linkSpeed") and nic.linkSpeed
                        else "",
                        "mac": nic.mac or "",
                        "switch": "",
                        "uplink_port": "",
                        "pci": nic.pci or "",
                        "wake_on": "",
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    nics.append(nic_data)
        except Exception:
            pass
        return nics

    def _get_datacenter(self, host):
        try:
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.Datacenter], True
            )
            return container.view[0].name if container.view else ""
        except Exception:
            return ""

    def _get_cluster(self, host):
        try:
            return host.parent.name if hasattr(host, "parent") and host.parent else ""
        except Exception:
            return ""
