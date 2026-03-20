"""VCPU collector - CPU details and performance"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VCPUCollector(BaseCollector):
    """Collector for vCPU sheet - CPU configuration and entitlements"""

    @property
    def sheet_name(self):
        return "vCPU"

    def collect(self):
        """Collect CPU information from all VMs"""
        container = self.content.rootFolder
        view_type = [vim.VirtualMachine]
        container_view = self.content.viewManager.CreateContainerView(
            container, view_type, True
        )

        cpu_list = []

        for vm in container_view.view:
            cpu_data = self._collect_vm_cpu(vm)
            cpu_list.append(cpu_data)

        return cpu_list

    def _collect_vm_cpu(self, vm):
        """Collect CPU information for a single VM"""
        cpu_data = {}

        cpu_data["vm"] = vm.name or ""
        cpu_data["powerstate"] = (
            str(vm.runtime.powerState) if vm.runtime.powerState else ""
        )
        cpu_data["template"] = str(vm.config.template) if vm.config.template else ""
        cpu_data["srm_placeholder"] = ""

        cpu_data["cpus"] = (
            str(vm.config.hardware.numCPU) if vm.config.hardware.numCPU else ""
        )
        cpu_data["sockets"] = (
            str(vm.config.hardware.numCoresPerSocket)
            if hasattr(vm.config.hardware, "numCoresPerSocket")
            else ""
        )

        cores_per_socket = getattr(vm.config.hardware, "numCoresPerSocket", 1) or 1
        cpu_data["cores_p_s"] = str(cores_per_socket)

        cpu_data["max"] = ""
        cpu_data["overall"] = ""

        cpu_data["level"] = ""
        cpu_data["shares"] = (
            str(vm.config.cpuAllocation.shares.shares)
            if vm.config.cpuAllocation.shares
            else ""
        )
        cpu_data["reservation"] = (
            str(vm.config.cpuAllocation.reservation)
            if vm.config.cpuAllocation.reservation
            else ""
        )
        cpu_data["entitlement"] = ""
        cpu_data["drs_entitlement"] = ""
        cpu_data["limit"] = (
            str(vm.config.cpuAllocation.limit) if vm.config.cpuAllocation.limit else ""
        )

        cpu_data["hot_add"] = ""
        cpu_data["hot_remove"] = ""
        cpu_data["numa_hotadd_exposed"] = ""

        cpu_data["annotation"] = vm.config.annotation or ""
        cpu_data["datacenter"] = self._get_datacenter(vm)
        cpu_data["cluster"] = self._get_cluster(vm)
        cpu_data["host"] = self._get_host(vm)
        cpu_data["folder"] = self._get_folder(vm)
        cpu_data["os_according_to_config"] = ""
        cpu_data["os_according_to_vmware_tools"] = vm.config.guestFullName or ""
        cpu_data["vm_id"] = vm._moId or ""
        cpu_data["vm_uuid"] = vm.config.uuid or ""
        cpu_data["vi_sdk_server"] = self.content.about.apiVersion or ""
        cpu_data["vi_sdk_uuid"] = self.content.about.instanceUuid or ""

        return cpu_data

    def _get_datacenter(self, vm):
        """Get datacenter name for VM"""
        try:
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.Datacenter], True
            )
            return container.view[0].name if container.view else ""
        except Exception:
            return ""

    def _get_cluster(self, vm):
        """Get cluster name for VM"""
        try:
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.ClusterComputeResource], True
            )
            return container.view[0].name if container.view else ""
        except Exception:
            return ""

    def _get_host(self, vm):
        """Get host name for VM"""
        try:
            return vm.runtime.host.name if vm.runtime.host else ""
        except Exception:
            return ""

    def _get_folder(self, vm):
        """Get folder name for VM"""
        try:
            return vm.parent.name if vm.parent else ""
        except Exception:
            return ""
