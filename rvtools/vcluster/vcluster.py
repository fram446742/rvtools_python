"""VCluster collector - Cluster information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.cache_utils import ViewCache


class VClusterCollector(BaseCollector):
    """Collector for vCluster sheet - vSphere Clusters"""

    def __init__(self, service_instance, directory):
        """Initialize collector with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vCluster"

    def collect(self):
        """Collect cluster information from vCenter"""
        cluster_list = []

        view_type = [vim.ClusterComputeResource]
        cluster_view_list = self.view_cache.get_list(view_type)

        for cluster in cluster_view_list:
            cluster_data = self._collect_cluster(cluster)
            cluster_list.append(cluster_data)

        return cluster_list

    def _collect_cluster(self, cluster):
        """Collect information for a single cluster"""
        cluster_data = {}

        cluster_data["name"] = cluster.name or ""
        cluster_data["config_status"] = (
            str(cluster.configStatus) if cluster.configStatus else ""
        )
        cluster_data["overall_status"] = (
            str(cluster.overallStatus) if cluster.overallStatus else ""
        )

        cluster_data["num_hosts"] = len(cluster.host) if cluster.host else 0
        cluster_data["num_effective_hosts"] = len(cluster.host) if cluster.host else 0

        summary = cluster.summary if cluster.summary else None
        cluster_data["total_cpu"] = (
            str(summary.totalCpu) if summary and summary.totalCpu else ""
        )
        cluster_data["num_cpu_cores"] = (
            str(summary.numCpuCores) if summary and summary.numCpuCores else ""
        )
        cluster_data["num_cpu_threads"] = (
            str(summary.numCpuThreads) if summary and summary.numCpuThreads else ""
        )
        cluster_data["effective_cpu"] = (
            str(summary.effectiveCpu) if summary and summary.effectiveCpu else ""
        )
        cluster_data["total_memory"] = (
            str(summary.totalMemory) if summary and summary.totalMemory else ""
        )
        cluster_data["effective_memory"] = (
            str(summary.effectiveMemory) if summary and summary.effectiveMemory else ""
        )

        cluster_data["num_vmotions"] = ""

        config = (
            cluster.configurationEx if hasattr(cluster, "configurationEx") else None
        )
        das_config = config.dasConfig if config else None
        drs_config = config.drsConfig if config else None

        cluster_data["ha_enabled"] = str(das_config.enabled) if das_config else ""
        cluster_data["failover_level"] = ""
        cluster_data["admission_control_enabled"] = (
            str(das_config.admissionControlEnabled) if das_config else ""
        )
        cluster_data["host_monitoring"] = ""
        cluster_data["hb_datastore_candidate_policy"] = ""
        cluster_data["isolation_response"] = ""
        cluster_data["restart_priority"] = ""
        cluster_data["cluster_settings"] = ""
        cluster_data["max_failures"] = ""
        cluster_data["max_failure_window"] = ""
        cluster_data["failure_interval"] = ""
        cluster_data["min_up_time"] = ""
        cluster_data["vm_monitoring"] = ""

        cluster_data["drs_enabled"] = str(drs_config.enabled) if drs_config else ""
        cluster_data["drs_default_vm_behavior"] = (
            str(drs_config.defaultVmBehavior) if drs_config else ""
        )
        cluster_data["drs_vmotion_rate"] = (
            str(drs_config.vmotionRate) if drs_config else ""
        )

        cluster_data["dpm_enabled"] = ""
        cluster_data["dpm_default_behavior"] = ""
        cluster_data["dpm_host_power_action_rate"] = ""

        cluster_data["object_id"] = cluster._moId or ""
        cluster_data["com_vmware_vcenter_cluster_edrs_upgrade_host_added"] = ""
        cluster_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        cluster_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return cluster_data
