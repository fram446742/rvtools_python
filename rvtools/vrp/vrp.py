"""VRP collector - Resource Pool information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VRPCollector(BaseCollector):
    """Collector for vRP sheet - Resource Pools"""

    @property
    def sheet_name(self):
        return "vRP"

    def collect(self):
        """Collect resource pool information from vCenter"""
        rp_list = []

        container = self.content.rootFolder
        view_type = [vim.ResourcePool]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        for resource_pool in container_view.view:
            rp_data = self._collect_resource_pool(resource_pool)
            rp_list.append(rp_data)

        return rp_list

    def _collect_resource_pool(self, rp):
        """Collect information for a single resource pool"""
        rp_data = {}

        rp_data["resource_pool_name"] = rp.name or ""
        rp_data["resource_pool_path"] = self._get_rp_path(rp)
        rp_data["status"] = str(rp.overallStatus) if rp.overallStatus else ""

        vms_total = len(rp.vm) if rp.vm else 0
        rp_data["num_vms_total"] = str(vms_total)
        rp_data["num_vms"] = str(vms_total)
        rp_data["num_vcpus"] = ""

        config = rp.config if rp.config else None
        cpu_alloc = config.cpuAllocation if config else None

        rp_data["cpu_limit"] = (
            str(cpu_alloc.limit) if cpu_alloc and cpu_alloc.limit else ""
        )
        rp_data["cpu_overhead_limit"] = ""
        rp_data["cpu_reservation"] = (
            str(cpu_alloc.reservation) if cpu_alloc and cpu_alloc.reservation else ""
        )
        rp_data["cpu_level"] = ""
        rp_data["cpu_shares"] = (
            str(cpu_alloc.shares.shares) if cpu_alloc and cpu_alloc.shares else ""
        )
        rp_data["cpu_expandable_reservation"] = (
            str(cpu_alloc.expandableReservation) if cpu_alloc else ""
        )

        rp_data["cpu_max_usage"] = ""
        rp_data["cpu_overall_usage"] = ""
        rp_data["cpu_reservation_used"] = ""
        rp_data["cpu_reservation_used_for_vm"] = ""
        rp_data["cpu_unreserved_for_pool"] = ""
        rp_data["cpu_unreserved_for_vm"] = ""

        mem_alloc = config.memoryAllocation if config else None

        rp_data["mem_configured"] = str(mem_alloc.limit) if mem_alloc else ""
        rp_data["mem_limit"] = str(mem_alloc.limit) if mem_alloc else ""
        rp_data["mem_overhead_limit"] = ""
        rp_data["mem_reservation"] = (
            str(mem_alloc.reservation) if mem_alloc and mem_alloc.reservation else ""
        )
        rp_data["mem_level"] = ""
        rp_data["mem_shares"] = (
            str(mem_alloc.shares.shares) if mem_alloc and mem_alloc.shares else ""
        )
        rp_data["mem_expandable_reservation"] = (
            str(mem_alloc.expandableReservation) if mem_alloc else ""
        )

        rp_data["mem_max_usage"] = ""
        rp_data["mem_overall_usage"] = ""
        rp_data["mem_reservation_used"] = ""
        rp_data["mem_reservation_used_for_vm"] = ""
        rp_data["mem_unreserved_for_pool"] = ""
        rp_data["mem_unreserved_for_vm"] = ""

        rp_data["qs_overall_cpu_demand"] = ""
        rp_data["qs_overall_cpu_usage"] = ""
        rp_data["qs_static_cpu_entitlement"] = ""
        rp_data["qs_distributed_cpu_entitlement"] = ""
        rp_data["qs_ballooned_memory"] = ""
        rp_data["qs_compressed_memory"] = ""
        rp_data["qs_consumed_overhead_memory"] = ""
        rp_data["qs_distributed_memory_entitlement"] = ""
        rp_data["qs_guest_memory_usage"] = ""
        rp_data["qs_host_memory_usage"] = ""
        rp_data["qs_overhead_memory"] = ""
        rp_data["qs_private_memory"] = ""
        rp_data["qs_shared_memory"] = ""
        rp_data["qs_static_memory_entitlement"] = ""
        rp_data["qs_swapped_memory"] = ""

        rp_data["object_id"] = rp._moId or ""
        rp_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        rp_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return rp_data

    def _get_rp_path(self, rp):
        """Get resource pool path"""
        try:
            path = []
            obj = rp
            while obj and not isinstance(obj, vim.Folder):
                path.insert(0, obj.name)
                obj = obj.parent
            return "/".join(path)
        except Exception:
            return rp.name or ""
