"""DVPort collector - Distributed vSwitch port information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class DVPortCollector(BaseCollector):
    """Collector for dvPort sheet - Distributed Virtual Switch Ports"""

    @property
    def sheet_name(self):
        return "dvPort"

    def collect(self):
        """Collect distributed vswitch port information from vCenter"""
        dvport_list = []
        try:
            container = self.content.rootFolder
            view_type = [vim.DistributedVirtualSwitch]
            container_view = self.content.viewManager.CreateContainerView(
                container, view_type, True
            )

            for dvswitch in container_view.view:
                dvswitch_ports = self._collect_dvswitch_ports(dvswitch)
                dvport_list.extend(dvswitch_ports)
        except Exception:
            pass
        return dvport_list

    def _collect_dvswitch_ports(self, dvswitch):
        """Collect port information for a single DVS"""
        ports = []
        try:
            if dvswitch.portgroup:
                for portgroup in dvswitch.portgroup:
                    port_data = {
                        "port": portgroup.name or "",
                        "switch": dvswitch.name or "",
                        "type": "",
                        "num_ports": "",
                        "vlan": "",
                        "speed": "",
                        "full_duplex": "",
                        "blocked": "",
                        "allow_promiscuous": "",
                        "mac_changes": "",
                        "active_uplink": "",
                        "standby_uplink": "",
                        "policy": "",
                        "forged_transmits": "",
                        "in_traffic_shaping": "",
                        "in_avg": "",
                        "in_peak": "",
                        "in_burst": "",
                        "out_traffic_shaping": "",
                        "out_avg": "",
                        "out_peak": "",
                        "out_burst": "",
                        "reverse_policy": "",
                        "notify_switch": "",
                        "rolling_order": "",
                        "check_beacon": "",
                        "live_port_moving": "",
                        "check_duplex": "",
                        "check_error_percent": "",
                        "check_speed": "",
                        "percentage": "",
                        "block_override": "",
                        "config_reset": "",
                        "shaping_override": "",
                        "vendor_config_override": "",
                        "sec_policy_override": "",
                        "teaming_override": "",
                        "vlan_override": "",
                        "object_id": portgroup._moId or "",
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    ports.append(port_data)
        except Exception:
            pass
        return ports
