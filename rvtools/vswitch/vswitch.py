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
        view_type = [vim.HostSystem]
        host_view_list = self.view_cache.get_list(view_type)

        for host in host_view_list:
            host_vswitches = self._collect_host_vswitches(host)
            vswitch_list.extend(host_vswitches)

        return vswitch_list

    def _collect_host_vswitches(self, host):
        """Collect vswitches for a single host"""
        vswitches = []
        try:
            if host.config and host.config.network and host.config.network.vswitch:
                for vswitch in host.config.network.vswitch:
                    # Extract security policy settings
                    security_policy = getattr(vswitch, "spec", None)
                    if security_policy:
                        security_policy = getattr(security_policy, "policy", None)
                    if security_policy:
                        security_policy = getattr(security_policy, "security", None)

                    # Extract traffic shaping settings
                    shaping_policy = getattr(vswitch, "spec", None)
                    if shaping_policy:
                        shaping_policy = getattr(shaping_policy, "policy", None)
                    if shaping_policy:
                        shaping_policy = getattr(shaping_policy, "shapingPolicy", None)

                    # Extract teaming policy
                    teaming_policy = getattr(vswitch, "spec", None)
                    if teaming_policy:
                        teaming_policy = getattr(teaming_policy, "policy", None)
                    if teaming_policy:
                        teaming_policy = getattr(teaming_policy, "nicTeaming", None)

                    vswitch_data = {
                        "host": host.name or "",
                        "datacenter": self._get_datacenter(host),
                        "cluster": self._get_cluster(host),
                        "switch": vswitch.name or "",
                        "num_ports": str(vswitch.numPorts) if vswitch.numPorts else "",
                        "free_ports": str(vswitch.numPortsAvailable)
                        if vswitch.numPortsAvailable
                        else "",
                        "promiscuous_mode": str(
                            getattr(security_policy, "allowPromiscuous", "")
                        )
                        if security_policy
                        else "",
                        "mac_changes": str(getattr(security_policy, "macChanges", ""))
                        if security_policy
                        else "",
                        "forged_transmits": str(
                            getattr(security_policy, "forgedTransmits", "")
                        )
                        if security_policy
                        else "",
                        "traffic_shaping": str(getattr(shaping_policy, "enabled", ""))
                        if shaping_policy
                        else "",
                        "width": str(getattr(shaping_policy, "peakBandwidth", ""))
                        if shaping_policy
                        else "",
                        "peak": str(getattr(shaping_policy, "peakBandwidth", ""))
                        if shaping_policy
                        else "",
                        "burst": str(getattr(shaping_policy, "burstSize", ""))
                        if shaping_policy
                        else "",
                        "policy": str(getattr(teaming_policy, "policy", ""))
                        if teaming_policy
                        else "",
                        "reverse_policy": str(
                            getattr(teaming_policy, "reversePolicy", "")
                        )
                        if teaming_policy
                        else "",
                        "notify_switch": str(
                            getattr(teaming_policy, "notifySwitches", "")
                        )
                        if teaming_policy
                        else "",
                        "rolling_order": str(
                            getattr(teaming_policy, "rollingOrder", "")
                        )
                        if teaming_policy
                        else "",
                        "offload": str(
                            getattr(getattr(vswitch, "spec", None), "mtu", "")
                        )
                        if getattr(vswitch, "spec", None)
                        else "",
                        "tso": "",
                        "zero_copy_xmit": "",
                        "mtu": str(vswitch.mtu) if vswitch.mtu else "",
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    vswitches.append(vswitch_data)
        except Exception:
            pass
        return vswitches

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
