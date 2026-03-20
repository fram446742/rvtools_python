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
        view_type = [vim.HostSystem]
        host_view_list = self.view_cache.get_list(view_type)

        for host in host_view_list:
            host_nics = self._collect_host_nics(host)
            nic_list.extend(host_nics)

        return nic_list

    def _collect_host_nics(self, host):
        """Collect NICs for a single host"""
        nics = []
        try:
            if host.config and host.config.network and host.config.network.pnic:
                for nic in host.config.network.pnic:
                    # Get driver info
                    driver = ""
                    if hasattr(nic, "driver"):
                        driver = nic.driver or ""

                    # Get linkSpeed info
                    speed = ""
                    duplex = ""
                    if hasattr(nic, "linkSpeed") and nic.linkSpeed:
                        speed = (
                            str(nic.linkSpeed.speedMb)
                            if hasattr(nic.linkSpeed, "speedMb")
                            else ""
                        )
                        duplex = (
                            str(nic.linkSpeed.duplex)
                            if hasattr(nic.linkSpeed, "duplex")
                            else ""
                        )

                    # Try to find vswitch membership
                    switch_name = ""
                    uplink_port = ""
                    if host.config.network.vswitch:
                        for vswitch in host.config.network.vswitch:
                            if vswitch.spec and vswitch.spec.bridge:
                                # Check if NIC is part of this bridge
                                if hasattr(vswitch.spec.bridge, "nicDevice"):
                                    if nic.device in vswitch.spec.bridge.nicDevice:
                                        switch_name = vswitch.name or ""
                                        uplink_port = nic.device or ""
                                        break

                    nic_data = {
                        "host": host.name or "",
                        "datacenter": self._get_datacenter(host),
                        "cluster": self._get_cluster(host),
                        "network_device": nic.device or "",
                        "driver": driver,
                        "speed": speed,
                        "duplex": duplex,
                        "mac": nic.mac or "",
                        "switch": switch_name,
                        "uplink_port": uplink_port,
                        "pci": nic.pci or "",
                        "wake_on": str(getattr(nic, "wakeOnLanSupported", ""))
                        if hasattr(nic, "wakeOnLanSupported")
                        else "",
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    nics.append(nic_data)
        except Exception:
            pass
        return nics

    def _get_datacenter(self, host):
        try:
            datacenter_list = self.view_cache.get_list([vim.Datacenter])
            return datacenter_list[0].name if datacenter_list else ""
        except Exception:
            return ""

    def _get_cluster(self, host):
        try:
            return host.parent.name if hasattr(host, "parent") and host.parent else ""
        except Exception:
            return ""
