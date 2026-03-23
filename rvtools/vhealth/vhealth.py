"""VHealth collector - vCenter health warnings (VM config, tools, storage, security issues)"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.cache_utils import ViewCache
import logging
import time

logger = logging.getLogger("rvtools")


class VHealthCollector(BaseCollector):
    """Collector for vHealth sheet - Detects health issues across VMs and infrastructure"""

    def __init__(self, service_instance, directory):
        """Initialize with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vHealth"

    def collect(self):
        """Collect health information - VM config, Tools, storage, security issues"""
        health_list = []

        # Check VM configuration issues
        try:
            vm_warnings = self._check_vm_health()
            health_list.extend(vm_warnings)
        except Exception as e:
            logger.debug(f"Error checking VM health: {e}", exc_info=True)

        # Detect orphaned/zombie VM files in datastores
        try:
            zombie_warnings = self._detect_orphaned_files()
            health_list.extend(zombie_warnings)
        except Exception as e:
            logger.debug(f"Error detecting orphaned files: {e}", exc_info=True)

        # Check datastore health
        try:
            storage_warnings = self._check_datastore_health()
            health_list.extend(storage_warnings)
        except Exception as e:
            logger.debug(f"Error checking datastore health: {e}", exc_info=True)

        return health_list

    def _check_vm_health(self):
        """Check VMs for health issues (USB, CDROM, snapshots, tools, CPU/memory)"""
        warnings = []

        try:
            vms = self.view_cache.get_list([vim.VirtualMachine])
            vi_sdk_info = self._get_vi_sdk_info()

            for vm in vms:
                try:
                    # Skip templates for some checks
                    is_template = vm.config.template if vm.config else False

                    # Check for USB devices
                    usb_warnings = self._check_usb_devices(vm, vi_sdk_info)
                    warnings.extend(usb_warnings)

                    # Check for CDROM devices
                    cdrom_warnings = self._check_cdrom_devices(vm, vi_sdk_info)
                    warnings.extend(cdrom_warnings)

                    # Check snapshots (except templates)
                    if not is_template:
                        snapshot_warnings = self._check_snapshots(vm, vi_sdk_info)
                        warnings.extend(snapshot_warnings)

                        # Check VM Tools status
                        tools_warnings = self._check_vm_tools(vm, vi_sdk_info)
                        warnings.extend(tools_warnings)

                        # Check CPU/memory issues
                        resource_warnings = self._check_resource_allocation(vm, vi_sdk_info)
                        warnings.extend(resource_warnings)

                except Exception as e:
                    logger.debug(f"Error checking VM {vm.name}: {e}")

        except Exception as e:
            logger.debug(f"Error checking VM health: {e}", exc_info=True)

        return warnings

    def _check_usb_devices(self, vm, vi_sdk_info):
        """Check if VM has USB devices attached"""
        warnings = []

        try:
            if vm.config and vm.config.hardware and vm.config.hardware.device:
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualUSB):
                        if not device.connectable or not device.connectable.connected:
                            continue
                        warning = {
                            "name": f"{vm.name}",
                            "message": "VM has USB device attached. Check if this is intended.",
                            "message_type": "USB",
                            "vi_sdk_server": vi_sdk_info["server"],
                            "vi_sdk_uuid": vi_sdk_info["uuid"],
                        }
                        warnings.append(warning)
                        break  # Only report once per VM
        except Exception as e:
            logger.debug(f"Error checking USB devices for {vm.name}: {e}")

        return warnings

    def _check_cdrom_devices(self, vm, vi_sdk_info):
        """Check if VM has CDROM devices attached"""
        warnings = []

        try:
            if vm.config and vm.config.hardware and vm.config.hardware.device:
                for device in vm.config.hardware.device:
                    if isinstance(device, (vim.vm.device.VirtualCdrom, vim.vm.device.VirtualFloppy)):
                        # Check if device is connected
                        is_connected = False
                        if hasattr(device, 'connectable') and device.connectable:
                            is_connected = device.connectable.connected
                        if not is_connected:
                            continue
                            
                        msg_type = "CDROM" if isinstance(device, vim.vm.device.VirtualCdrom) else "Floppy"
                        warning = {
                            "name": f"{vm.name}",
                            "message": f"VM has {msg_type} device connected. Verify if this is intended.",
                            "message_type": msg_type,
                            "vi_sdk_server": vi_sdk_info["server"],
                            "vi_sdk_uuid": vi_sdk_info["uuid"],
                        }
                        warnings.append(warning)
                        break  # Only report once per VM
        except Exception as e:
            logger.debug(f"Error checking CDROM devices for {vm.name}: {e}")

        return warnings

    def _check_snapshots(self, vm, vi_sdk_info):
        """Check if VM has snapshots"""
        warnings = []

        try:
            if vm.snapshot and vm.snapshot.rootSnapshotList:
                warning = {
                    "name": f"{vm.name}",
                    "message": f"VM has {len(vm.snapshot.rootSnapshotList)} snapshot(s). Consider consolidating.",
                    "message_type": "Snapshot",
                    "vi_sdk_server": vi_sdk_info["server"],
                    "vi_sdk_uuid": vi_sdk_info["uuid"],
                }
                warnings.append(warning)
        except Exception as e:
            logger.debug(f"Error checking snapshots for {vm.name}: {e}")

        return warnings

    def _check_vm_tools(self, vm, vi_sdk_info):
        """Check VM Tools status"""
        warnings = []

        try:
            if vm.guest and hasattr(vm.guest, 'toolsStatus') and vm.guest.toolsStatus:
                tools_status = str(vm.guest.toolsStatus)
                tools_version = vm.guest.toolsVersion if vm.guest else None

                # Check for tools issues
                if tools_status not in ["toolsOk"]:
                    message = f"VM Tools status: {tools_status}"
                    if tools_version:
                        message += f" (version: {tools_version})"
                    warning = {
                        "name": f"{vm.name}",
                        "message": message + ". Consider updating or checking installation.",
                        "message_type": "VM Tools",
                        "vi_sdk_server": vi_sdk_info["server"],
                        "vi_sdk_uuid": vi_sdk_info["uuid"],
                    }
                    warnings.append(warning)
        except Exception as e:
            logger.debug(f"Error checking VM Tools for {vm.name}: {e}")

        return warnings

    def _check_resource_allocation(self, vm, vi_sdk_info):
        """Check CPU and memory allocation issues"""
        warnings = []

        try:
            if vm.config and vm.config.hardware:
                # Check for potential over-allocation or unusual configs
                cpu_count = vm.config.hardware.numCPU if vm.config.hardware.numCPU else 0
                memory_mb = vm.config.hardware.memoryMB if vm.config.hardware.memoryMB else 0

                # Check for single CPU with high memory (often a performance issue)
                if cpu_count == 1 and memory_mb > 8192:
                    warning = {
                        "name": f"{vm.name}",
                        "message": f"VM has only 1 CPU but {memory_mb}MB memory. Consider adding CPUs.",
                        "message_type": "CPU",
                        "vi_sdk_server": vi_sdk_info["server"],
                        "vi_sdk_uuid": vi_sdk_info["uuid"],
                    }
                    warnings.append(warning)
        except Exception as e:
            logger.debug(f"Error checking resource allocation for {vm.name}: {e}")

        return warnings

    def _check_datastore_health(self):
        """Check datastore capacity and health"""
        warnings = []

        try:
            datastores = self.view_cache.get_list([vim.Datastore])
            vi_sdk_info = self._get_vi_sdk_info()

            for datastore in datastores:
                try:
                    if datastore.summary and datastore.summary.capacity and datastore.summary.freeSpace:
                        capacity = datastore.summary.capacity
                        free_space = datastore.summary.freeSpace
                        used_space = capacity - free_space
                        usage_percent = (used_space / capacity * 100) if capacity > 0 else 0

                        # Alert if datastore is > 80% full
                        if usage_percent > 80:
                            warning = {
                                "name": f"{datastore.name}",
                                "message": f"Datastore {usage_percent:.1f}% full ({(free_space / (1024**3)):.1f}GB free). Consider cleanup.",
                                "message_type": "Storage",
                                "vi_sdk_server": vi_sdk_info["server"],
                                "vi_sdk_uuid": vi_sdk_info["uuid"],
                            }
                            warnings.append(warning)
                except Exception as e:
                    logger.debug(f"Error checking datastore {datastore.name}: {e}")

        except Exception as e:
            logger.debug(f"Error checking datastore health: {e}", exc_info=True)

        return warnings

    def _detect_orphaned_files(self):
        """Detect orphaned/zombie VM files in datastores"""
        warnings = []

        try:
            # Build set of registered VM file paths
            registered_files = self._build_registered_file_set()

            # Scan each datastore for orphaned files
            try:
                datastores = self.view_cache.get_list([vim.Datastore])
            except Exception as e:
                logger.debug(f"Error getting datastore list: {e}")
                return warnings

            for datastore in datastores:
                try:
                    zombie_list = self._scan_datastore_for_orphans(
                        datastore, registered_files
                    )
                    warnings.extend(zombie_list)
                except Exception as e:
                    logger.debug(f"Error scanning datastore {datastore.name}: {e}")

        except Exception as e:
            logger.debug(f"Error in orphaned file detection: {e}", exc_info=True)

        return warnings

    def _build_registered_file_set(self):
        """Build set of all registered VM file paths"""
        registered_files = set()

        try:
            vms = self.view_cache.get_list([vim.VirtualMachine])
            logger.debug(f"Found {len(vms)} VMs to check for registered files")

            for vm in vms:
                try:
                    # Collect VM config file path
                    if vm.config and vm.config.files:
                        if vm.config.files.vmPathName:
                            # Extract path without datastore name
                            path = self._extract_datastore_path(vm.config.files.vmPathName)
                            registered_files.add(path.lower())

                    # Collect all disk file paths
                    if vm.config and vm.config.hardware and vm.config.hardware.device:
                        for device in vm.config.hardware.device:
                            if isinstance(device, vim.vm.device.VirtualDisk):
                                if (
                                    hasattr(device, "backing")
                                    and device.backing
                                    and hasattr(device.backing, "fileName")
                                ):
                                    path = self._extract_datastore_path(
                                        device.backing.fileName
                                    )
                                    registered_files.add(path.lower())

                except Exception as e:
                    logger.debug(f"Error collecting VM files for {vm.name}: {e}")

        except Exception as e:
            logger.debug(f"Error building registered file set: {e}", exc_info=True)

        logger.debug(f"Total registered files: {len(registered_files)}")
        return registered_files

    def _scan_datastore_for_orphans(self, datastore, registered_files):
        """Scan a single datastore for orphaned VM files"""
        warnings = []

        try:
            if not datastore.browser:
                logger.debug(f"Datastore {datastore.name} has no browser")
                return warnings

            # Search for VM-related files
            spec = vim.host.DatastoreBrowser.SearchSpec()
            spec.matchPattern = ["*.vmx", "*.vmdk", "*.vmtx"]

            logger.debug(f"Searching datastore {datastore.name} for orphaned files...")
            task = datastore.browser.SearchDatastore(spec=spec)

            # Wait for task (with timeout)
            start_time = time.time()
            timeout = 60  # 60 second timeout per datastore
            
            while True:
                # Get current task state
                task_state = str(task.info.state)
                logger.debug(f"Task state for {datastore.name}: {task_state}")
                
                if task_state == "success":
                    break
                elif task_state == "error":
                    logger.debug(f"Task error for {datastore.name}: {task.info.error}")
                    break
                elif task_state in ["running", "queued"]:
                    if time.time() - start_time > timeout:
                        logger.debug(f"Datastore scan timeout for {datastore.name}")
                        break
                    time.sleep(0.5)
                else:
                    logger.debug(f"Unknown task state for {datastore.name}: {task_state}")
                    break

            if str(task.info.state) == "success":
                result = task.info.result
                if result:
                    logger.debug(f"Found {len(result.file) if hasattr(result, 'file') and result.file else 0} files in {datastore.name}")
                    warnings.extend(
                        self._process_datastore_search_results(
                            result, datastore.name, registered_files
                        )
                    )
            else:
                logger.debug(f"Task failed for datastore {datastore.name}, state: {task.info.state}")

        except Exception as e:
            logger.debug(f"Error scanning datastore {datastore.name}: {e}", exc_info=True)

        return warnings

    def _process_datastore_search_results(self, search_results, datastore_name, registered_files):
        """Process files found in datastore search for orphaned entries"""
        warnings = []

        try:
            if not hasattr(search_results, "file") or not search_results.file:
                return warnings

            vi_sdk_info = self._get_vi_sdk_info()

            for file_entry in search_results.file:
                try:
                    if not hasattr(file_entry, "path"):
                        continue

                    file_path = file_entry.path
                    file_path_lower = file_path.lower()

                    # Check if this file is registered
                    if file_path_lower not in registered_files:
                        # This is an orphaned/zombie file
                        message = self._get_zombie_message(file_path)
                        full_path = f"[{datastore_name}] {file_path}"

                        warning = {
                            "name": full_path,
                            "message": message,
                            "message_type": "Zombie",
                            "vi_sdk_server": vi_sdk_info["server"],
                            "vi_sdk_uuid": vi_sdk_info["uuid"],
                        }
                        warnings.append(warning)

                except Exception as e:
                    logger.debug(f"Error processing file entry: {e}")

        except Exception as e:
            logger.debug(f"Error processing search results: {e}")

        return warnings

    def _extract_datastore_path(self, full_path):
        """Extract path relative to datastore from full path like [datastore] path"""
        if not full_path:
            return ""

        # Format: "[datastore_name] /path/to/file"
        if "[" in full_path and "]" in full_path:
            # Extract part after "]"
            parts = full_path.split("]", 1)
            if len(parts) > 1:
                return parts[1].strip()

        return full_path

    def _get_zombie_message(self, file_path):
        """Get appropriate message based on file type"""
        file_lower = file_path.lower()

        if file_lower.endswith(".vmx"):
            return "Possibly a Zombie VM! Please check."
        elif file_lower.endswith(".vmtx"):
            return "Possibly a Zombie Template! Please check."
        elif file_lower.endswith(".vmdk"):
            return "Possibly a Zombie vmdk file! Please check."
        else:
            return "Possibly an orphaned file! Please check."

    def _get_vi_sdk_info(self):
        """Extract VI SDK information"""
        return {
            "server": self.content.about.apiVersion or "",
            "uuid": self.content.about.instanceUuid or "",
        }
