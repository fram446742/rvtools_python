"""DVSwitch collector - Distributed vSwitch information"""
from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class DVSwitchCollector(BaseCollector):
    """Collector for dvSwitch sheet - Distributed Virtual Switches"""

    @property
    def sheet_name(self):
        return "dvSwitch"

    def collect(self):
        """Collect distributed vswitch information from vCenter"""
        dvswitch_list = []
        try:
            container = self.content.rootFolder
            view_type = [vim.DistributedVirtualSwitch]
            container_view = self.content.viewManager.CreateContainerView(container, view_type, True)

            for dvswitch in container_view.view:
                dvs_data = self._collect_dvswitch(dvswitch)
                dvswitch_list.append(dvs_data)
        except Exception:
            pass
        return dvswitch_list

    def _collect_dvswitch(self, dvswitch):
        """Collect information for a single DVS"""
        dvs_data = {}

        dvs_data['switch'] = dvswitch.name or ""
        dvs_data['datacenter'] = self._get_datacenter(dvswitch)
        dvs_data['name'] = dvswitch.name or ""
        dvs_data['vendor'] = getattr(dvswitch.config, 'vendor', '') or ""
        dvs_data['version'] = getattr(dvswitch.config, 'version', '') or ""
        dvs_data['description'] = dvswitch.config.description if dvswitch.config else ""
        dvs_data['created'] = str(dvswitch.config.creationTime) if dvswitch.config else ""
        
        host_members = len(dvswitch.config.host) if dvswitch.config and dvswitch.config.host else 0
        dvs_data['host_members'] = str(host_members)
        
        dvs_data['max_ports'] = str(dvswitch.config.maxPorts) if dvswitch.config else ""
        dvs_data['num_ports'] = str(len(dvswitch.portgroup)) if dvswitch.portgroup else "0"
        dvs_data['num_vms'] = ""
        
        dvs_data['in_traffic_shaping'] = ""
        dvs_data['in_avg'] = ""
        dvs_data['in_peak'] = ""
        dvs_data['in_burst'] = ""
        dvs_data['out_traffic_shaping'] = ""
        dvs_data['out_avg'] = ""
        dvs_data['out_peak'] = ""
        dvs_data['out_burst'] = ""
        
        dvs_data['cdp_type'] = ""
        dvs_data['cdp_operation'] = ""
        dvs_data['lacp_name'] = ""
        dvs_data['lacp_mode'] = ""
        dvs_data['lacp_load_balance_alg'] = ""
        dvs_data['max_mtu'] = str(dvswitch.config.mtu) if dvswitch.config else ""
        dvs_data['contact'] = ""
        dvs_data['admin_name'] = ""
        dvs_data['object_id'] = dvswitch._moId or ""
        dvs_data['vi_sdk_server'] = self.content.about.apiVersion or ""
        dvs_data['vi_sdk_uuid'] = self.content.about.instanceUuid or ""

        return dvs_data

    def _get_datacenter(self, dvswitch):
        try:
            container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.Datacenter], True)
            return container.view[0].name if container.view else ""
        except Exception:
            return ""
