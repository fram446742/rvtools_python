"""VDatastore collector - Datastore information"""
from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VDatastoreCollector(BaseCollector):
    """Collector for vDatastore sheet - Storage datastores"""

    @property
    def sheet_name(self):
        return "vDatastore"

    def collect(self):
        """Collect datastore information from vCenter"""
        datastore_list = []

        container = self.content.rootFolder
        view_type = [vim.Datastore]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        for datastore in container_view.view:
            ds_data = self._collect_datastore(datastore)
            datastore_list.append(ds_data)

        return datastore_list

    def _collect_datastore(self, datastore):
        """Collect information for a single datastore"""
        ds_data = {}

        ds_data['name'] = datastore.name or ""
        ds_data['config_status'] = str(datastore.configStatus) if datastore.configStatus else ""
        
        summary = datastore.summary if datastore.summary else None
        ds_data['address'] = summary.url if summary else ""
        ds_data['accessible'] = str(summary.accessible) if summary else ""
        ds_data['type'] = summary.type if summary else ""

        ds_data['num_vms_total'] = ""
        ds_data['num_vms'] = ""

        capacity = summary.capacity if summary else 0
        free_space = summary.freeSpace if summary else 0
        
        capacity_mib = capacity // (1024 * 1024) if capacity else 0
        ds_data['capacity_mib'] = str(capacity_mib)
        
        ds_data['provisioned_mib'] = ""
        
        free_mib = free_space // (1024 * 1024) if free_space else 0
        ds_data['in_use_mib'] = str(capacity_mib - free_mib) if capacity > 0 else ""
        ds_data['free_mib'] = str(free_mib)
        
        if capacity_mib > 0:
            free_percent = (free_mib / capacity_mib) * 100
            ds_data['free_percent'] = f"{free_percent:.2f}"
        else:
            ds_data['free_percent'] = ""

        ds_data['sioc_enabled'] = ""
        ds_data['sioc_threshold'] = ""
        
        ds_data['num_hosts'] = len(datastore.host) if datastore.host else 0
        ds_data['hosts'] = self._get_host_names(datastore)
        ds_data['cluster_name'] = ""
        ds_data['cluster_capacity_mib'] = ""
        ds_data['cluster_free_space_mib'] = ""

        ds_data['block_size'] = ""
        ds_data['max_blocks'] = ""
        ds_data['num_extents'] = ""
        ds_data['major_version'] = ""
        ds_data['version'] = ""
        ds_data['vmfs_upgradeable'] = ""
        ds_data['mha'] = ""

        ds_data['url'] = summary.url if summary else ""
        ds_data['object_id'] = datastore._moId or ""
        ds_data['vi_sdk_server'] = self.content.about.apiVersion or ""
        ds_data['vi_sdk_uuid'] = self.content.about.instanceUuid or ""

        return ds_data

    def _get_host_names(self, datastore):
        """Get comma-separated list of host names"""
        try:
            if datastore.host:
                names = [host.key.name for host in datastore.host if hasattr(host.key, 'name')]
                return ", ".join(names)
            return ""
        except Exception:
            return ""
