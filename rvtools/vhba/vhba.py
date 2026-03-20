"""VHBA collector - Host HBA information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VHBACollector(BaseCollector):
    """Collector for vHBA sheet - Host Bus Adapters"""

    @property
    def sheet_name(self):
        return "vHBA"

    def collect(self):
        """Collect HBA information from all hosts"""
        hba_list = []
        container = self.content.rootFolder
        view_type = [vim.HostSystem]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        for host in container_view.view:
            host_hbas = self._collect_host_hbas(host)
            hba_list.extend(host_hbas)

        return hba_list

    def _collect_host_hbas(self, host):
        """Collect HBAs for a single host"""
        hbas = []
        try:
            if (
                host.config
                and host.config.storageDevice
                and host.config.storageDevice.hostBusAdapter
            ):
                for hba in host.config.storageDevice.hostBusAdapter:
                    # Extract HBA type from class name or deviceType
                    hba_type = ""
                    if hasattr(hba, 'deviceType'):
                        hba_type = hba.deviceType or ""
                    
                    # Try to determine status from HBA
                    status = ""
                    if hasattr(hba, 'status'):
                        status = str(hba.status) if hba.status else ""
                    
                    # Get model name
                    model = ""
                    if hasattr(hba, 'model'):
                        model = hba.model or ""
                    
                    # Get WWN (World Wide Name) for FC HBAs
                    wwn = ""
                    if hasattr(hba, 'portWorldWideName'):
                        wwn = str(getattr(hba, 'portWorldWideName', '')) or ""
                    elif hasattr(hba, 'wwn'):
                        wwn = str(hba.wwn) or ""
                    
                    hba_data = {
                        "host": host.name or "",
                        "datacenter": self._get_datacenter(host),
                        "cluster": self._get_cluster(host),
                        "device": hba.device or "",
                        "type": hba_type,
                        "status": status,
                        "bus": str(hba.bus) if hasattr(hba, "bus") else "",
                        "pci": hba.pciId or "",
                        "driver": hba.driver or "",
                        "model": model,
                        "wwn": wwn,
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    hbas.append(hba_data)
        except Exception:
            pass
        return hbas

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
