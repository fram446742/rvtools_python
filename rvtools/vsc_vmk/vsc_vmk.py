"""VSC_VMK collector - VMKernel interface information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VSCVMKCollector(BaseCollector):
    """Collector for vSC_VMK sheet - VMKernel Interfaces"""

    @property
    def sheet_name(self):
        return "vSC_VMK"

    def collect(self):
        """Collect VMKernel interface information from all hosts"""
        vmk_list = []
        container = self.content.rootFolder
        view_type = [vim.HostSystem]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        for host in container_view.view:
            host_vmks = self._collect_host_vmks(host)
            vmk_list.extend(host_vmks)

        return vmk_list

    def _collect_host_vmks(self, host):
        """Collect VMKernel interfaces for a single host"""
        vmks = []
        try:
            if host.config and host.config.network and host.config.network.vnic:
                for vnic in host.config.network.vnic:
                    # Extract IP configuration
                    ip_address = ""
                    ip_6_address = ""
                    subnet_mask = ""
                    gateway = ""
                    ip_6_gateway = ""
                    dhcp = ""
                    
                    if vnic.spec and vnic.spec.ip:
                        ip_address = vnic.spec.ip.ipAddress or ""
                        subnet_mask = vnic.spec.ip.subnetMask or ""
                        
                        # Check for DHCP
                        if hasattr(vnic.spec.ip, 'dhcp'):
                            dhcp = str(vnic.spec.ip.dhcp) if vnic.spec.ip.dhcp else "False"
                    
                    # Get IPv6 configuration if available
                    if vnic.spec and hasattr(vnic.spec, 'ipV6'):
                        ipv6_config = getattr(vnic.spec, 'ipV6', None)
                        if ipv6_config:
                            if hasattr(ipv6_config, 'ipAddress') and ipv6_config.ipAddress:
                                if isinstance(ipv6_config.ipAddress, list) and len(ipv6_config.ipAddress) > 0:
                                    ip_6_address = ipv6_config.ipAddress[0].ipAddress or ""
                    
                    # Try to get gateway from routing config
                    if host.config.network and host.config.network.ipRouteConfig:
                        route_config = host.config.network.ipRouteConfig
                        if hasattr(route_config, 'defaultGateway') and route_config.defaultGateway:
                            gateway = route_config.defaultGateway or ""
                        if hasattr(route_config, 'ipV6DefaultGateway') and route_config.ipV6DefaultGateway:
                            ip_6_gateway = route_config.ipV6DefaultGateway or ""
                    
                    vmk_data = {
                        "host": host.name or "",
                        "datacenter": self._get_datacenter(host),
                        "cluster": self._get_cluster(host),
                        "port_group": vnic.portgroup or "",
                        "device": vnic.device or "",
                        "mac_address": vnic.mac or "",
                        "dhcp": dhcp,
                        "ip_address": ip_address,
                        "ip_6_address": ip_6_address,
                        "subnet_mask": subnet_mask,
                        "gateway": gateway,
                        "ip_6_gateway": ip_6_gateway,
                        "mtu": str(vnic.spec.mtu)
                        if vnic.spec and vnic.spec.mtu
                        else "",
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    vmks.append(vmk_data)
        except Exception:
            pass
        return vmks

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
