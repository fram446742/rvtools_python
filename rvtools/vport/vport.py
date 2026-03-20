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
        container_view = self.content.viewManager.CreateContainerView(container, view_type, True)

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
                    port_data = {
                        'host': host.name or "",
                        'datacenter': self._get_datacenter(host),
                        'cluster': self._get_cluster(host),
                        'port_group': portgroup.spec.name if portgroup.spec else "",
                        'switch': portgroup.spec.vswitchName if portgroup.spec else "",
                        'vlan': str(portgroup.spec.vlanId) if portgroup.spec and portgroup.spec.vlanId else "",
                        'promiscuous_mode': "",
                        'mac_changes': "",
                        'forged_transmits': "",
                        'traffic_shaping': "",
                        'width': "",
                        'peak': "",
                        'burst': "",
                        'policy': "",
                        'reverse_policy': "",
                        'notify_switch': "",
                        'rolling_order': "",
                        'offload': "",
                        'tso': "",
                        'zero_copy_xmit': "",
                        'vi_sdk_server': self.content.about.apiVersion or "",
                        'vi_sdk_uuid': self.content.about.instanceUuid or "",
                    }
                    ports.append(port_data)
        except Exception:
            pass
        return ports

    def _get_datacenter(self, host):
        try:
            container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.Datacenter], True)
            return container.view[0].name if container.view else ""
        except Exception:
            return ""

    def _get_cluster(self, host):
        try:
            return host.parent.name if hasattr(host, 'parent') and host.parent else ""
        except Exception:
            return ""
