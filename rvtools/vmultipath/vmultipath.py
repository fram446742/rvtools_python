"""VMultiPath collector - Storage multipath information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.cache_utils import ViewCache


class VMultiPathCollector(BaseCollector):
    """Collector for vMultiPath sheet - Storage multipath configuration"""

    def __init__(self, service_instance, directory):
        """Initialize collector with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vMultiPath"

    def collect(self):
        """Collect multipath information from hosts"""
        multipath_list = []

        view_type = [vim.HostSystem]
        host_view_list = self.view_cache.get_list(view_type)

        for host in host_view_list:
            host_paths = self._collect_host_multipaths(host)
            multipath_list.extend(host_paths)

        return multipath_list

    def _collect_host_multipaths(self, host):
        """Collect multipath information for a single host"""
        multipaths = []

        try:
            if not host.config or not host.config.storageDevice:
                return multipaths

            storage_device = host.config.storageDevice

            if storage_device.multiPathInfo:
                for lun in storage_device.multiPathInfo.lun:
                    mp_data = self._collect_multipath_lun(host, lun)
                    multipaths.append(mp_data)
        except Exception:
            pass

        return multipaths

    def _collect_multipath_lun(self, host, lun):
        """Collect information for a single LUN"""
        mp_data = {}

        mp_data["host"] = host.name or ""
        mp_data["cluster"] = self._get_cluster(host)
        mp_data["datacenter"] = self._get_datacenter(host)
        mp_data["datastore"] = ""
        mp_data["disk"] = lun.name or ""
        mp_data["display_name"] = lun.displayName or ""
        mp_data["policy"] = str(lun.policy) if lun.policy else ""
        mp_data["oper_state"] = (
            str(lun.operationalState) if lun.operationalState else ""
        )

        paths = lun.path if lun.path else []
        for i in range(1, 9):
            path_key = f"path_{i}"
            path_state_key = f"path_{i}_state"

            if i <= len(paths):
                mp_data[path_key] = paths[i - 1].name or ""
                mp_data[path_state_key] = (
                    str(paths[i - 1].pathState) if paths[i - 1].pathState else ""
                )
            else:
                mp_data[path_key] = ""
                mp_data[path_state_key] = ""

        mp_data["vstorage"] = ""
        mp_data["queue_depth"] = str(lun.queueDepth) if lun.queueDepth else ""

        if hasattr(lun, "deviceType"):
            mp_data["vendor"] = getattr(lun, "vendor", "") or ""
            mp_data["model"] = getattr(lun, "model", "") or ""
            mp_data["revision"] = getattr(lun, "revision", "") or ""
        else:
            mp_data["vendor"] = ""
            mp_data["model"] = ""
            mp_data["revision"] = ""

        mp_data["level"] = ""
        mp_data["serial"] = getattr(lun, "serialNumber", "") or ""
        mp_data["uuid"] = lun.uuid or ""
        mp_data["object_id"] = lun._moId or ""
        mp_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        mp_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return mp_data

    def _get_datacenter(self, host):
        try:
            datacenter_list = self.view_cache.get_list([vim.Datacenter])
            return datacenter_list[0].name if datacenter_list else ""
        except Exception:
            return ""

    def _get_cluster(self, host):
        try:
            if hasattr(host, "parent") and host.parent:
                return host.parent.name
            return ""
        except Exception:
            return ""
