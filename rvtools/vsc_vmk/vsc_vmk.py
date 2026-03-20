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
        container_view = self.content.viewManager.CreateContainerView(container, view_type, True)

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
                    vmk_data = {
                        'host': host.name or "",
                        'datacenter': self._get_datacenter(host),
                        'cluster': self._get_cluster(host),
                        'port_group': vnic.portgroup or "",
                        'device': vnic.device or "",
                        'mac_address': vnic.mac or "",
                        'dhcp': "",
                        'ip_address': vnic.spec.ip.ipAddress if vnic.spec and vnic.spec.ip else "",
                        'ip_6_address': "",
                        'subnet_mask': vnic.spec.ip.subnetMask if vnic.spec and vnic.spec.ip else "",
                        'gateway': "",
                        'ip_6_gateway': "",
                        'mtu': str(vnic.spec.mtu) if vnic.spec and vnic.spec.mtu else "",
                        'vi_sdk_server': self.content.about.apiVersion or "",
                        'vi_sdk_uuid': self.content.about.instanceUuid or "",
                    }
                    vmks.append(vmk_data)
        except Exception:
            pass
        return vmks

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
