"""VPort collector - vSwitch port group information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VPortCollector(BaseCollector):
    """Collector for vPort sheet - vSwitch Port Groups"""

    @property
    def sheet_name(self):
        return "vPort"

    def collect(self):
        """Collect port group information from all hosts"""
        port_list = []
        container = self.content.rootFolder
        view_type = [vim.HostSystem]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        for host in container_view.view:
            host_ports = self._collect_host_ports(host)
            port_list.extend(host_ports)

        return port_list

    def _collect_host_ports(self, host):
        """Collect port groups for a single host"""
        ports = []
        try:
            if host.config and host.config.network and host.config.network.portgroup:
                for portgroup in host.config.network.portgroup:
                    # Extract port security policy
                    security_policy = None
                    shaping_policy = None
                    teaming_policy = None
                    
                    if portgroup.spec and portgroup.spec.policy:
                        security_policy = getattr(portgroup.spec.policy, 'security', None)
                        shaping_policy = getattr(portgroup.spec.policy, 'shapingPolicy', None)
                        teaming_policy = getattr(portgroup.spec.policy, 'nicTeaming', None)
                    
                    port_data = {
                        "host": host.name or "",
                        "datacenter": self._get_datacenter(host),
                        "cluster": self._get_cluster(host),
                        "port_group": portgroup.spec.name if portgroup.spec else "",
                        "switch": portgroup.spec.vswitchName if portgroup.spec else "",
                        "vlan": str(portgroup.spec.vlanId)
                        if portgroup.spec and portgroup.spec.vlanId
                        else "",
                        "promiscuous_mode": str(getattr(security_policy, 'allowPromiscuous', '')) if security_policy else "",
                        "mac_changes": str(getattr(security_policy, 'macChanges', '')) if security_policy else "",
                        "forged_transmits": str(getattr(security_policy, 'forgedTransmits', '')) if security_policy else "",
                        "traffic_shaping": str(getattr(shaping_policy, 'enabled', '')) if shaping_policy else "",
                        "width": str(getattr(shaping_policy, 'peakBandwidth', '')) if shaping_policy else "",
                        "peak": str(getattr(shaping_policy, 'peakBandwidth', '')) if shaping_policy else "",
                        "burst": str(getattr(shaping_policy, 'burstSize', '')) if shaping_policy else "",
                        "policy": str(getattr(teaming_policy, 'policy', '')) if teaming_policy else "",
                        "reverse_policy": str(getattr(teaming_policy, 'reversePolicy', '')) if teaming_policy else "",
                        "notify_switch": str(getattr(teaming_policy, 'notifySwitches', '')) if teaming_policy else "",
                        "rolling_order": str(getattr(teaming_policy, 'rollingOrder', '')) if teaming_policy else "",
                        "offload": "",
                        "tso": "",
                        "zero_copy_xmit": "",
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    ports.append(port_data)
        except Exception:
            pass
        return ports

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
