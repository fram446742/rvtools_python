"""VSwitch collector - vSwitch information"""
from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VSwitchCollector(BaseCollector):
    """Collector for vSwitch sheet - Virtual Switches"""

    @property
    def sheet_name(self):
        return "vSwitch"

    def collect(self):
        """Collect vswitch information from all hosts"""
        vswitch_list = []
        container = self.content.rootFolder
        view_type = [vim.HostSystem]
        container_view = self.content.viewManager.CreateContainerView(container, view_type, True)

        for host in container_view.view:
            host_vswitches = self._collect_host_vswitches(host)
            vswitch_list.extend(host_vswitches)

        return vswitch_list

    def _collect_host_vswitches(self, host):
        """Collect vswitches for a single host"""
        vswitches = []
        try:
            if host.config and host.config.network and host.config.network.vswitch:
                for vswitch in host.config.network.vswitch:
                    vswitch_data = {
                        'host': host.name or "",
                        'datacenter': self._get_datacenter(host),
                        'cluster': self._get_cluster(host),
                        'switch': vswitch.name or "",
                        'num_ports': str(vswitch.numPorts) if vswitch.numPorts else "",
                        'free_ports': str(vswitch.numPortsAvailable) if vswitch.numPortsAvailable else "",
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
                        'mtu': str(vswitch.mtu) if vswitch.mtu else "",
                        'vi_sdk_server': self.content.about.apiVersion or "",
                        'vi_sdk_uuid': self.content.about.instanceUuid or "",
                    }
                    vswitches.append(vswitch_data)
        except Exception:
            pass
        return vswitches

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
