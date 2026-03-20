"""VHost collector - ESXi host information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VHostCollector(BaseCollector):
    """Collector for vHost sheet - ESXi Hosts"""

    @property
    def sheet_name(self):
        return "vHost"

    def collect(self):
        """Collect host information from vCenter"""
        host_list = []

        container = self.content.rootFolder
        view_type = [vim.HostSystem]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        for host in container_view.view:
            host_data = self._collect_host(host)
            host_list.append(host_data)

        return host_list

    def _collect_host(self, host):
        """Collect information for a single host"""
        host_data = {}

        host_data["host"] = host.name or ""
        host_data["datacenter"] = self._get_datacenter(host)
        host_data["cluster"] = self._get_cluster(host)
        host_data["config_status"] = str(host.configStatus) if host.configStatus else ""
        host_data["compliance_check_state"] = ""
        host_data["in_maintenance_mode"] = (
            str(host.runtime.inMaintenanceMode) if host.runtime else ""
        )
        host_data["in_quarantine_mode"] = ""
        host_data["vsan_fault_domain_name"] = ""

        summary = host.summary if host.summary else None
        hw_summary = summary.hardware if summary else None

        host_data["cpu_model"] = hw_summary.cpuModel if hw_summary else ""
        host_data["speed"] = str(hw_summary.cpuMhz) if hw_summary else ""
        host_data["ht_available"] = str(hw_summary.cpuBusHz) if hw_summary else ""
        host_data["ht_active"] = ""
        host_data["num_cpu"] = str(hw_summary.numCpuPkgs) if hw_summary else ""
        host_data["cores_per_cpu"] = str(hw_summary.numCpuCores) if hw_summary else ""
        host_data["num_cores"] = ""
        host_data["cpu_usage_percent"] = ""
        host_data["num_memory"] = str(hw_summary.memorySize) if hw_summary else ""
        host_data["memory_tiering_type"] = ""
        host_data["memory_usage_percent"] = ""
        host_data["console"] = ""
        host_data["num_nics"] = str(hw_summary.numNics) if hw_summary else ""
        host_data["num_hbas"] = str(hw_summary.numHBAs) if hw_summary else ""

        vm_summary = (
            summary.runtime.dasHostState.vmCount if summary and summary.runtime else 0
        )
        host_data["num_vms_total"] = str(vm_summary) if vm_summary else ""
        host_data["num_vms"] = str(vm_summary) if vm_summary else ""
        host_data["vms_per_core"] = ""
        host_data["num_vcpus"] = ""
        host_data["vcpus_per_core"] = ""
        host_data["vram"] = ""
        host_data["vm_used_memory"] = ""
        host_data["vm_memory_swapped"] = ""
        host_data["vm_memory_ballooned"] = ""

        host_data["vmotion_support"] = ""
        host_data["storage_vmotion_support"] = ""
        host_data["current_evc"] = ""
        host_data["max_evc"] = ""
        host_data["assigned_licenses"] = ""
        host_data["ats_heartbeat"] = ""
        host_data["ats_locking"] = ""
        host_data["current_cpu_power_man_policy"] = ""
        host_data["supported_cpu_power_man"] = ""
        host_data["host_power_policy"] = ""

        config = host.config if host.config else None
        host_data["esx_version"] = summary.config.name if summary else ""
        host_data["boot_time"] = str(host.runtime.bootTime) if host.runtime else ""
        host_data["dns_servers"] = ""
        host_data["dhcp"] = ""
        host_data["domain"] = ""
        host_data["domain_list"] = ""
        host_data["dns_search_order"] = ""
        host_data["ntp_servers"] = ""
        host_data["ntpd_running"] = ""
        host_data["time_zone"] = ""
        host_data["time_zone_name"] = ""
        host_data["gmt_offset"] = ""

        host_data["vendor"] = hw_summary.vendor if hw_summary else ""
        host_data["model"] = hw_summary.model if hw_summary else ""
        host_data["serial_number"] = hw_summary.serialNumber if hw_summary else ""
        host_data["service_tag"] = ""
        host_data["oem_specific_string"] = ""

        host_data["bios_vendor"] = ""
        host_data["bios_version"] = ""
        host_data["bios_date"] = ""
        host_data["certificate_issuer"] = ""
        host_data["certificate_start_date"] = ""
        host_data["certificate_expiry_date"] = ""
        host_data["certificate_status"] = ""
        host_data["certificate_subject"] = ""

        host_data["object_id"] = host._moId or ""
        host_data["autodeploy_machine_identity"] = ""
        host_data["uuid"] = host.hardware.systemInfo.uuid if host.hardware else ""
        host_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        host_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return host_data

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
            if hasattr(host, "parent") and host.parent:
                return host.parent.name
            return ""
        except Exception:
            return ""
