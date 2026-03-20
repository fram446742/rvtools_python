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
        view_type = [vim.HostSystem]
        host_view_list = self.view_cache.get_list(view_type)

        for host in host_view_list:
            host_ports = self._collect_host_ports(host)
            port_list.extend(host_ports)

        return port_list

    def _collect_host_ports(self, host):
        """Collect port groups for a single host"""
        ports = []
        try:
            if host.config and host.config.network and host.config.network.portgroup:
                for portgroup in host.config.network.portgroup:
                    # Extract policies using helper method
                    policies = self._extract_portgroup_policies(portgroup)
                    security_policy = policies["security"]
                    shaping_policy = policies["shaping"]
                    teaming_policy = policies["teaming"]
                    offload_policy = policies["offload"]
                    failure_criteria = policies["failure_criteria"]

                    port_data = {
                        "host": host.name or "",
                        "datacenter": self._get_datacenter(host),
                        "cluster": self._get_cluster(host),
                        "port_group": portgroup.spec.name if portgroup.spec else "",
                        "switch": portgroup.spec.vswitchName if portgroup.spec else "",
                        "vlan": str(portgroup.spec.vlanId)
                        if portgroup.spec and portgroup.spec.vlanId
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
                        "offload": str(offload_policy) if offload_policy else "",
                        "tso": "",
                        "zero_copy_xmit": "",
                        "percentage": str(getattr(failure_criteria, "percentage", ""))
                        if failure_criteria
                        else "",
                        "full_duplex": str(getattr(failure_criteria, "fullDuplex", ""))
                        if failure_criteria
                        else "",
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    ports.append(port_data)
        except Exception:
            pass
        return ports

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

    def _extract_portgroup_policies(self, portgroup):
        """Extract security, shaping, teaming, and offload policies from portgroup"""
        security_policy = None
        shaping_policy = None
        teaming_policy = None
        offload_policy = None
        failure_criteria = None

        if portgroup.spec and portgroup.spec.policy:
            security_policy = getattr(portgroup.spec.policy, "security", None)
            shaping_policy = getattr(portgroup.spec.policy, "shapingPolicy", None)
            teaming_policy = getattr(portgroup.spec.policy, "nicTeaming", None)
            offload_policy = getattr(portgroup.spec.policy, "offloadPolicy", None)

            # Extract failure criteria if available
            if teaming_policy and hasattr(teaming_policy, "failureCriteria"):
                failure_criteria = teaming_policy.failureCriteria

        return {
            "security": security_policy,
            "shaping": shaping_policy,
            "teaming": teaming_policy,
            "offload": offload_policy,
            "failure_criteria": failure_criteria,
        }
