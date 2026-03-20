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
                    # Extract VLAN configuration
                    vlan_config = ""
                    if portgroup.config and portgroup.config.defaultPortConfig:
                        default_config = portgroup.config.defaultPortConfig

                        # VLAN ID extraction
                        if hasattr(default_config, "vlan") and default_config.vlan:
                            vlan_obj = default_config.vlan
                            if hasattr(vlan_obj, "vlanId"):
                                vlan_config = str(vlan_obj.vlanId)

                        # Type of port group
                        port_type = ""
                        if portgroup.config and portgroup.config.type:
                            port_type = portgroup.config.type

                        # Port binding/connectivity
                        connectivity = ""
                        if portgroup.config and portgroup.config.portgroupType:
                            connectivity = portgroup.config.portgroupType

                        # Extract security policy
                        security = getattr(default_config, "securityPolicy", None)
                        allow_promiscuous = ""
                        mac_changes = ""
                        forged_transmits = ""

                        if security:
                            allow_promiscuous = str(
                                getattr(security, "allowPromiscuous", "")
                            )
                            mac_changes = str(getattr(security, "macChanges", ""))
                            forged_transmits = str(
                                getattr(security, "forgedTransmits", "")
                            )

                        # Extract teaming policy
                        teaming = getattr(default_config, "nicTeaming", None)
                        policy = ""
                        reverse_policy = ""
                        notify_switch = ""
                        rolling_order = ""

                        if teaming:
                            policy = str(getattr(teaming, "policy", ""))
                            reverse_policy = str(getattr(teaming, "reversePolicy", ""))
                            notify_switch = str(getattr(teaming, "notifySwitches", ""))
                            rolling_order = str(getattr(teaming, "rollingOrder", ""))

                        # Extract traffic shaping
                        in_shaping = getattr(default_config, "inShapingPolicy", None)
                        out_shaping = getattr(default_config, "outShapingPolicy", None)

                        in_traffic_shaping = ""
                        in_avg = ""
                        in_peak = ""
                        in_burst = ""
                        out_traffic_shaping = ""
                        out_avg = ""
                        out_peak = ""
                        out_burst = ""

                        if in_shaping:
                            in_traffic_shaping = str(getattr(in_shaping, "enabled", ""))
                            in_avg = str(getattr(in_shaping, "averageBandwidth", ""))
                            in_peak = str(getattr(in_shaping, "peakBandwidth", ""))
                            in_burst = str(getattr(in_shaping, "burstSize", ""))

                        if out_shaping:
                            out_traffic_shaping = str(
                                getattr(out_shaping, "enabled", "")
                            )
                            out_avg = str(getattr(out_shaping, "averageBandwidth", ""))
                            out_peak = str(getattr(out_shaping, "peakBandwidth", ""))
                            out_burst = str(getattr(out_shaping, "burstSize", ""))

                        # Extract failover config
                        active_uplink = ""
                        standby_uplink = ""
                        check_beacon = ""
                        live_port_moving = ""
                        check_duplex = ""
                        check_speed = ""

                        if teaming and hasattr(teaming, "uplinkNotifyEnabled"):
                            check_beacon = str(teaming.uplinkNotifyEnabled)
                        if teaming and hasattr(teaming, "lbPolicy"):
                            active_uplink = str(teaming.lbPolicy)

                        # Extract port configuration overrides
                        block_override = ""
                        shaping_override = ""
                        vendor_override = ""
                        sec_policy_override = ""
                        teaming_override = ""
                        vlan_override = ""

                        if portgroup.config and hasattr(
                            portgroup.config, "configVersion"
                        ):
                            config_version = portgroup.config.configVersion

                        # Port count
                        num_ports = (
                            str(len(portgroup.portKeys))
                            if hasattr(portgroup, "portKeys") and portgroup.portKeys
                            else ""
                        )

                    port_data = {
                        "port": portgroup.name or "",
                        "switch": dvswitch.name or "",
                        "type": port_type if "port_type" in locals() else "",
                        "num_ports": num_ports if "num_ports" in locals() else "",
                        "vlan": vlan_config if "vlan_config" in locals() else "",
                        "speed": "",
                        "full_duplex": "",
                        "blocked": "",
                        "allow_promiscuous": allow_promiscuous
                        if "allow_promiscuous" in locals()
                        else "",
                        "mac_changes": mac_changes if "mac_changes" in locals() else "",
                        "active_uplink": active_uplink
                        if "active_uplink" in locals()
                        else "",
                        "standby_uplink": standby_uplink
                        if "standby_uplink" in locals()
                        else "",
                        "policy": policy if "policy" in locals() else "",
                        "forged_transmits": forged_transmits
                        if "forged_transmits" in locals()
                        else "",
                        "in_traffic_shaping": in_traffic_shaping
                        if "in_traffic_shaping" in locals()
                        else "",
                        "in_avg": in_avg if "in_avg" in locals() else "",
                        "in_peak": in_peak if "in_peak" in locals() else "",
                        "in_burst": in_burst if "in_burst" in locals() else "",
                        "out_traffic_shaping": out_traffic_shaping
                        if "out_traffic_shaping" in locals()
                        else "",
                        "out_avg": out_avg if "out_avg" in locals() else "",
                        "out_peak": out_peak if "out_peak" in locals() else "",
                        "out_burst": out_burst if "out_burst" in locals() else "",
                        "reverse_policy": reverse_policy
                        if "reverse_policy" in locals()
                        else "",
                        "notify_switch": notify_switch
                        if "notify_switch" in locals()
                        else "",
                        "rolling_order": rolling_order
                        if "rolling_order" in locals()
                        else "",
                        "check_beacon": check_beacon
                        if "check_beacon" in locals()
                        else "",
                        "live_port_moving": live_port_moving
                        if "live_port_moving" in locals()
                        else "",
                        "check_duplex": check_duplex
                        if "check_duplex" in locals()
                        else "",
                        "check_error_percent": "",
                        "check_speed": check_speed if "check_speed" in locals() else "",
                        "percentage": "",
                        "block_override": block_override
                        if "block_override" in locals()
                        else "",
                        "config_reset": "",
                        "shaping_override": shaping_override
                        if "shaping_override" in locals()
                        else "",
                        "vendor_config_override": vendor_override
                        if "vendor_override" in locals()
                        else "",
                        "sec_policy_override": sec_policy_override
                        if "sec_policy_override" in locals()
                        else "",
                        "teaming_override": teaming_override
                        if "teaming_override" in locals()
                        else "",
                        "vlan_override": vlan_override
                        if "vlan_override" in locals()
                        else "",
                        "object_id": portgroup._moId or "",
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    ports.append(port_data)
        except Exception:
            pass
        return ports
