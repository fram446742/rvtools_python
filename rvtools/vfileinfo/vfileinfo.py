"""VFileInfo collector - File information"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.cache_utils import ViewCache


class VFileInfoCollector(BaseCollector):
    """Collector for vFileInfo sheet - File information"""

    def __init__(self, service_instance, directory):
        """Initialize with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vFileInfo"

    def collect(self):
        """Collect file information from VM config files"""
        file_list = []

        try:
            # Get all VMs
            vms = self.view_cache.get_list([vim.VirtualMachine])
            
            for vm in vms:
                vm_files = self._collect_vm_files(vm)
                file_list.extend(vm_files)
        except Exception:
            pass

        return file_list

    def _collect_vm_files(self, vm):
        """Collect file information for a VM"""
        files = []
        try:
            if vm.config:
                # Main VMX file
                if vm.config.files and vm.config.files.vmPathName:
                    vmx_path = vm.config.files.vmPathName
                    file_data = {
                        "friendly_path_name": vm.name or "",
                        "file_name": self._extract_filename(vmx_path),
                        "file_type": "VMX",
                        "file_size_in_bytes": "",
                        "path": vmx_path,
                        "internal_sort_column": "1",
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    files.append(file_data)
                
                # VM memory snapshot files
                if vm.config.files and vm.config.files.snapshotDirectory:
                    snapshot_path = vm.config.files.snapshotDirectory
                    file_data = {
                        "friendly_path_name": f"{vm.name} (Snapshots)" or "",
                        "file_name": self._extract_filename(snapshot_path),
                        "file_type": "Snapshot",
                        "file_size_in_bytes": "",
                        "path": snapshot_path,
                        "internal_sort_column": "2",
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    files.append(file_data)
                
                # Virtual disks (VMDK files)
                if vm.config.hardware and vm.config.hardware.device:
                    for device in vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualDisk):
                            if device.backing and hasattr(device.backing, 'fileName'):
                                disk_path = device.backing.fileName
                                file_data = {
                                    "friendly_path_name": f"{vm.name} (Disk)" or "",
                                    "file_name": self._extract_filename(disk_path),
                                    "file_type": "VMDK",
                                    "file_size_in_bytes": str(device.capacityInBytes) if hasattr(device, 'capacityInBytes') else "",
                                    "path": disk_path,
                                    "internal_sort_column": "3",
                                    "vi_sdk_server": self.content.about.apiVersion or "",
                                    "vi_sdk_uuid": self.content.about.instanceUuid or "",
                                }
                                files.append(file_data)
        except Exception:
            pass

        return files

    def _extract_filename(self, path):
        """Extract filename from path"""
        if not path:
            return ""
        # Handle both / and \ as separators
        path = str(path)
        if "/" in path:
            return path.split("/")[-1]
        elif "\\" in path:
            return path.split("\\")[-1]
        return path

