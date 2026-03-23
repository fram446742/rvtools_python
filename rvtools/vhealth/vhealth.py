"""VHealth collector - vCenter health warnings (VM config, storage, security issues)

Implements comprehensive health checks matching RVTools vHealth output with proper
separation of message (warning text with placeholders) and message_type (category).
"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.cache_utils import ViewCache
import logging
import time
import re

logger = logging.getLogger("rvtools")


class VHealthCollector(BaseCollector):
    """Collector for vHealth sheet - comprehensive health and configuration checks"""

    def __init__(self, service_instance, directory):
        """Initialize with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vHealth"

    def collect(self):
        """Collect comprehensive health information"""
        health_list = []

        # Check VM health issues
        try:
            vm_warnings = self._check_vm_health()
            health_list.extend(vm_warnings)
        except Exception as e:
            logger.debug(f"Error checking VM health: {e}", exc_info=True)

        # Check storage/datastore health
        try:
            storage_warnings = self._check_storage_health()
            health_list.extend(storage_warnings)
        except Exception as e:
            logger.debug(f"Error checking storage health: {e}", exc_info=True)

        # Check host/infrastructure health
        try:
            host_warnings = self._check_host_health()
            health_list.extend(host_warnings)
        except Exception as e:
            logger.debug(f"Error checking host health: {e}", exc_info=True)

        # Detect orphaned/zombie VM files
        try:
            zombie_warnings = self._detect_orphaned_files()
            health_list.extend(zombie_warnings)
        except Exception as e:
            logger.debug(f"Error detecting orphaned files: {e}", exc_info=True)

        return health_list

    def _check_vm_health(self):
        """Check VMs for health issues: CDROM, USB, Snapshots, Tools, Performance"""
        warnings = []

        try:
            vms = self.view_cache.get_list([vim.VirtualMachine])
            vi_sdk_info = self._get_vi_sdk_info()

            for vm in vms:
                try:
                    is_template = vm.config.template if vm.config else False

                    # Check CDROM devices
                    cdrom_warnings = self._check_cdrom_devices(vm, vi_sdk_info)
                    warnings.extend(cdrom_warnings)

                    # Check USB devices
                    usb_warnings = self._check_usb_devices(vm, vi_sdk_info)
                    warnings.extend(usb_warnings)

                    # Skip template-only checks
                    if not is_template:
                        # Check snapshots
                        snapshot_warnings = self._check_snapshots(vm, vi_sdk_info)
                        warnings.extend(snapshot_warnings)

                        # Check VM Tools status
                        tools_warnings = self._check_vm_tools(vm, vi_sdk_info)
                        warnings.extend(tools_warnings)

                        # Check folder naming consistency
                        foldername_warnings = self._check_foldername(vm, vi_sdk_info)
                        warnings.extend(foldername_warnings)

                        # Check performance optimization opportunities
                        perf_warnings = self._check_performance_tips(vm, vi_sdk_info)
                        warnings.extend(perf_warnings)

                except Exception as e:
                    logger.debug(f"Error checking VM {vm.name}: {e}")

        except Exception as e:
            logger.debug(f"Error checking VM health: {e}", exc_info=True)

        return warnings

    def _check_cdrom_devices(self, vm, vi_sdk_info):
        """Check for connected CDROM devices"""
        warnings = []
        try:
            if vm.config and vm.config.hardware and vm.config.hardware.device:
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualCdrom):
                        is_connected = (hasattr(device, 'connectable') and 
                                      device.connectable and 
                                      device.connectable.connected)
                        if is_connected:
                            # Try to get device label safely
                            device_label = "CD/DVD drive"
                            try:
                                if hasattr(device, 'deviceInfo') and device.deviceInfo:
                                    device_label = device.deviceInfo.label or device_label
                            except:
                                pass
                            
                            warning = {
                                "name": vm.name,
                                "message": f"VM has a CDROM device connected! {device_label}",
                                "message_type": "CDROM",
                                "vi_sdk_server": vi_sdk_info["server"],
                                "vi_sdk_uuid": vi_sdk_info["uuid"],
                            }
                            warnings.append(warning)
        except Exception as e:
            logger.debug(f"Error checking CDROM for {vm.name}: {e}")
        return warnings

    def _check_usb_devices(self, vm, vi_sdk_info):
        """Check for connected USB devices"""
        warnings = []
        try:
            if vm.config and vm.config.hardware and vm.config.hardware.device:
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualUSB):
                        is_connected = (hasattr(device, 'connectable') and 
                                      device.connectable and 
                                      device.connectable.connected)
                        if is_connected:
                            # Try to get device label safely
                            device_label = "USB device"
                            try:
                                if hasattr(device, 'deviceInfo') and device.deviceInfo:
                                    device_label = device.deviceInfo.label or device_label
                            except:
                                pass
                            
                            warning = {
                                "name": vm.name,
                                "message": f"VM has a USB device connected! {device_label}",
                                "message_type": "USB",
                                "vi_sdk_server": vi_sdk_info["server"],
                                "vi_sdk_uuid": vi_sdk_info["uuid"],
                            }
                            warnings.append(warning)
        except Exception as e:
            logger.debug(f"Error checking USB for {vm.name}: {e}")
        return warnings

    def _check_snapshots(self, vm, vi_sdk_info):
        """Check for active snapshots"""
        warnings = []
        try:
            if vm.snapshot and vm.snapshot.rootSnapshotList:
                for snap in vm.snapshot.rootSnapshotList:
                    snap_name = snap.name if hasattr(snap, 'name') else "Unknown"
                    warning = {
                        "name": vm.name,
                        "message": f"VM has an active snapshot! {snap_name}",
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
                if tools_status not in ["toolsOk"]:
                    warning = {
                        "name": vm.name,
                        "message": "VMware tools are out of date, not running or not installed!",
                        "message_type": "VM Tools",
                        "vi_sdk_server": vi_sdk_info["server"],
                        "vi_sdk_uuid": vi_sdk_info["uuid"],
                    }
                    warnings.append(warning)
        except Exception as e:
            logger.debug(f"Error checking VM Tools for {vm.name}: {e}")
        return warnings

    def _check_foldername(self, vm, vi_sdk_info):
        """Check for inconsistent folder naming"""
        warnings = []
        try:
            if vm.name and vm.parent:
                # Get folder name
                folder_obj = vm.parent
                folder_name = folder_obj.name if hasattr(folder_obj, 'name') else "Unknown"
                
                # Check if VM name matches folder pattern or has consistency issues
                # RVTools typically checks if folder structure is consistent
                # This is environment-specific, but we can check for obvious inconsistencies
                vm_name = vm.name
                
                # Example: if VM is in a folder but folder name doesn't match VM naming pattern
                # This depends on the environment's naming conventions
                # For now, we'll flag obvious mismatches
                if folder_name and folder_name != vm_name and not vm_name.startswith(folder_name):
                    # Could indicate inconsistent naming
                    warning = {
                        "name": vm.name,
                        "message": f"Inconsistent Foldername! VMname = {vm_name}, Foldername = {folder_name}",
                        "message_type": "Foldername",
                        "vi_sdk_server": vi_sdk_info["server"],
                        "vi_sdk_uuid": vi_sdk_info["uuid"],
                    }
                    warnings.append(warning)
        except Exception as e:
            logger.debug(f"Error checking folder name for {vm.name}: {e}")
        return warnings

    def _check_performance_tips(self, vm, vi_sdk_info):
        """Check for performance optimization opportunities"""
        warnings = []
        try:
            if vm.config and vm.config.hardware:
                cpu_count = vm.config.hardware.numCPU or 1
                memory_mb = vm.config.hardware.memoryMB or 0
                
                # Check for single vCPU with high memory (performance issue)
                if cpu_count == 1 and memory_mb >= 8192:
                    warning = {
                        "name": vm.name,
                        "message": "In-Memory VM performance improvement possible! Please check",
                        "message_type": "Performance tip",
                        "vi_sdk_server": vi_sdk_info["server"],
                        "vi_sdk_uuid": vi_sdk_info["uuid"],
                    }
                    warnings.append(warning)
        except Exception as e:
            logger.debug(f"Error checking performance tips for {vm.name}: {e}")
        return warnings

    def _check_storage_health(self):
        """Check storage and datastore health"""
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
                            free_percent = 100 - usage_percent
                            warning = {
                                "name": datastore.name,
                                "message": f"On datastore {datastore.name} is {free_percent:.1f}% disk space available! The threshold value is 20%",
                                "message_type": "Storage",
                                "vi_sdk_server": vi_sdk_info["server"],
                                "vi_sdk_uuid": vi_sdk_info["uuid"],
                            }
                            warnings.append(warning)
                except Exception as e:
                    logger.debug(f"Error checking datastore {datastore.name}: {e}")

        except Exception as e:
            logger.debug(f"Error checking storage health: {e}", exc_info=True)

        return warnings

    def _check_host_health(self):
        """Check host/cluster infrastructure health"""
        warnings = []
        try:
            hosts = self.view_cache.get_list([vim.HostSystem])
            vi_sdk_info = self._get_vi_sdk_info()

            for host in hosts:
                try:
                    # Check for CPU overcommit per core
                    if host.summary and host.summary.hardware:
                        num_cpus = host.summary.hardware.numCpuCores or 1
                        # This is a simplified check - actual CPU per core stats would come from performance manager
                        # Placeholder for future enhancement
                        pass

                except Exception as e:
                    logger.debug(f"Error checking host {host.name}: {e}")

        except Exception as e:
            logger.debug(f"Error checking host health: {e}", exc_info=True)

        return warnings

    def _detect_orphaned_files(self):
        """Detect orphaned/zombie VM files in datastores"""
        warnings = []

        try:
            registered_files = self._build_registered_file_set()
            datastores = self.view_cache.get_list([vim.Datastore])

            for datastore in datastores:
                try:
                    zombie_list = self._scan_datastore_for_orphans(datastore, registered_files)
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
            logger.debug(f"Building registered files from {len(vms)} VMs")

            for vm in vms:
                try:
                    # Collect VM config file path
                    if vm.config and vm.config.files and vm.config.files.vmPathName:
                        path = self._extract_datastore_path(vm.config.files.vmPathName).lower()
                        registered_files.add(path)
                        logger.debug(f"VM {vm.name}: registered config file {path}")

                    # Collect disk file paths
                    if vm.config and vm.config.hardware and vm.config.hardware.device:
                        for device in vm.config.hardware.device:
                            if isinstance(device, vim.vm.device.VirtualDisk):
                                if (hasattr(device, "backing") and device.backing and 
                                    hasattr(device.backing, "fileName")):
                                    path = self._extract_datastore_path(device.backing.fileName).lower()
                                    registered_files.add(path)
                                    logger.debug(f"VM {vm.name}: registered disk {path}")

                except Exception as e:
                    logger.debug(f"Error collecting VM files for {vm.name}: {e}")

            logger.debug(f"Total registered files: {len(registered_files)}")

        except Exception as e:
            logger.debug(f"Error building registered file set: {e}", exc_info=True)

        return registered_files

    def _scan_datastore_for_orphans(self, datastore, registered_files):
        """Scan a single datastore for orphaned VM files - searches all directories"""
        warnings = []

        try:
            if not datastore.browser:
                return warnings

            logger.debug(f"Searching datastore {datastore.name} for orphaned files... (registered files: {len(registered_files)})")
            datastore_path = f"[{datastore.name}]"
            
            # Search root and collect all warnings
            warnings.extend(
                self._search_datastore_path(datastore, datastore_path, registered_files)
            )

        except Exception as e:
            logger.debug(f"Error scanning datastore {datastore.name}: {e}", exc_info=True)

        return warnings

    def _search_datastore_path(self, datastore, datastore_path, registered_files):
        """Search a specific datastore path for orphaned files"""
        warnings = []

        try:
            # First search for matching files AT THIS LEVEL
            spec = vim.host.DatastoreBrowser.SearchSpec()
            spec.matchPattern = ["*.vmx", "*.vmdk", "*.vmtx"]
            
            try:
                task = datastore.browser.SearchDatastore_Task(datastore_path, spec)
            except vim.fault.NoPermission as e:
                logger.debug(f"Permission denied searching {datastore_path}: {e}")
                return warnings
            except Exception as e:
                logger.debug(f"Error initiating search on {datastore_path}: {e}")
                return warnings

            # Wait for task with timeout
            start_time = time.time()
            timeout = 60
            
            while True:
                task_state = str(task.info.state)
                if task_state == "success":
                    break
                elif task_state == "error":
                    logger.debug(f"Task error for {datastore_path}: {task.info.error}")
                    break
                elif task_state in ["running", "queued"]:
                    if time.time() - start_time > timeout:
                        logger.debug(f"Datastore scan timeout for {datastore_path}")
                        break
                    time.sleep(0.5)
                else:
                    break

            if str(task.info.state) == "success" and task.info.result:
                # Log all files found
                file_count = 0
                if hasattr(task.info.result, "file") and task.info.result.file:
                    file_count = len(task.info.result.file)
                logger.debug(f"Search at {datastore_path} found {file_count} matching files")
                
                result_warnings = self._process_datastore_search_results(
                    task.info.result, datastore.name, registered_files
                )
                logger.debug(f"Found {len(result_warnings)} orphaned files at {datastore_path}")
                warnings.extend(result_warnings)
            else:
                logger.debug(f"No results from search at {datastore_path} (state: {str(task.info.state)})")

            # NOW: Explicitly search for subdirectories
            # We do this by searching without matchPattern to get ALL files including folders
            logger.debug(f"Searching for subdirectories at {datastore_path}")
            try:
                dir_spec = vim.host.DatastoreBrowser.SearchSpec()
                # Don't set matchPattern - this will return all entries including directories
                dir_spec.details = vim.host.DatastoreBrowser.FileInfo.Details()
                dir_spec.details.fileOwner = True
                dir_spec.details.fileSize = True
                dir_spec.details.modification = True
                
                dir_task = datastore.browser.SearchDatastore_Task(datastore_path, dir_spec)
            except Exception as e:
                logger.debug(f"Could not enumerate directory contents at {datastore_path}: {e}")
                return warnings

            # Wait for directory enumeration
            start_time = time.time()
            while True:
                task_state = str(dir_task.info.state)
                if task_state == "success":
                    break
                elif task_state == "error":
                    logger.debug(f"Dir enum error at {datastore_path}: {dir_task.info.error}")
                    break
                elif task_state in ["running", "queued"]:
                    if time.time() - start_time > timeout:
                        logger.debug(f"Dir enum timeout for {datastore_path}")
                        break
                    time.sleep(0.5)
                else:
                    break

            # Extract subdirectories from enumeration results
            if str(dir_task.info.state) == "success" and dir_task.info.result:
                subdirs = []
                if hasattr(dir_task.info.result, "file") and dir_task.info.result.file:
                    logger.debug(f"Directory enumeration at {datastore_path} returned {len(dir_task.info.result.file)} entries")
                    for i, file_entry in enumerate(dir_task.info.result.file):
                        # Try multiple ways to identify directories
                        try:
                            is_dir = False
                            attrs = []
                            
                            # Method 1: Check fileType attribute
                            if hasattr(file_entry, "fileType"):
                                file_type_str = str(file_entry.fileType)
                                attrs.append(f"fileType={file_type_str}")
                                if "directory" in file_type_str.lower():
                                    is_dir = True
                            
                            # Method 2: Check for key/keyName which might indicate a resource
                            if hasattr(file_entry, "key"):
                                attrs.append(f"hasKey=True")
                            
                            # Method 3: Check if there's a folderFileInfo
                            if hasattr(file_entry, "folderFileInfo"):
                                attrs.append(f"hasFolderFileInfo=True")
                                is_dir = True  # If it has folderFileInfo, it's likely a folder
                            
                            # Method 4: Heuristic - if path doesn't start with . and doesn't have an extension, it might be a directory
                            path = getattr(file_entry, "path", "NOPATH")
                            if not path.startswith(".") and "." not in path.split("/")[-1]:
                                # Looks like it might be a directory
                                attrs.append(f"looksLikeDir=True")
                                # But only if fileType wasn't explicitly something else
                                if not hasattr(file_entry, "fileType"):
                                    is_dir = True
                            
                            # Log first 10 entries with all attributes
                            if i < 10:
                                logger.debug(f"  Entry {i}: path={path}, {', '.join(attrs)}, isDir={is_dir}")
                            
                            if is_dir and hasattr(file_entry, "path"):
                                subdir_name = file_entry.path
                                logger.debug(f"  -> IDENTIFIED AS DIRECTORY: {subdir_name}")
                                subdirs.append(subdir_name)
                        except Exception as e:
                            logger.debug(f"Error checking entry {i}: {e}")
                            continue
                
                logger.debug(f"Found {len(subdirs)} subdirectories to recursively search at {datastore_path}")
                
                # Recursively search each subdirectory
                for subdir_name in subdirs:
                    if datastore_path.endswith("]"):
                        # First level: [datastore]
                        subdir_path = f"{datastore_path} {subdir_name}"
                    else:
                        # Nested level: [datastore] path/to/dir
                        subdir_path = f"{datastore_path}/{subdir_name}"
                    
                    logger.debug(f"Recursively searching subdirectory: {subdir_path}")
                    warnings.extend(
                        self._search_datastore_path(datastore, subdir_path, registered_files)
                    )
            else:
                logger.debug(f"No directory enumeration results from {datastore_path}")

        except Exception as e:
            logger.debug(f"Error searching datastore path {datastore_path}: {e}", exc_info=True)

        return warnings


    def _process_datastore_search_results(self, search_results, datastore_name, registered_files):
        """Process files found in datastore search for orphaned entries"""
        warnings = []

        try:
            if not hasattr(search_results, "file") or not search_results.file:
                return warnings

            vi_sdk_info = self._get_vi_sdk_info()
            logger.debug(f"Processing {len(search_results.file)} files from datastore search")

            for file_entry in search_results.file:
                try:
                    if not hasattr(file_entry, "path"):
                        continue

                    # Normalize path for comparison (handle different separators)
                    file_path = file_entry.path.lower()
                    file_path_normalized = file_path.replace("\\", "/")
                    
                    logger.debug(f"Checking file: {file_entry.path}")
                    
                    # Check if file is in registered files
                    is_registered = (file_path_normalized in registered_files)
                    
                    # For -flat.vmdk files, check if the main .vmdk is registered
                    # (flat files are automatic components of VMDK files)
                    if not is_registered and file_path_normalized.endswith("-flat.vmdk"):
                        main_vmdk = file_path_normalized.replace("-flat.vmdk", ".vmdk")
                        is_registered = (main_vmdk in registered_files)
                        if is_registered:
                            logger.debug(f"  -> Registered as component of {main_vmdk}")
                        else:
                            logger.debug(f"  -> Orphaned (-flat.vmdk without main .vmdk)")
                    
                    # Also check with different path separators in case registered files use backslashes
                    if not is_registered:
                        file_path_backslash = file_path.replace("/", "\\")
                        is_registered = (file_path_backslash in registered_files)
                        if is_registered:
                            logger.debug(f"  -> Registered (backslash path format)")
                    
                    if is_registered:
                        logger.debug(f"  -> Registered")
                    else:
                        logger.debug(f"  -> ORPHANED")
                    
                    if not is_registered:
                        full_path = f"[{datastore_name}] {file_entry.path}"
                        
                        # Determine message based on file extension
                        if file_path.endswith(".vmdk"):
                            msg = "Possibly a Zombie vmdk file! Please check."
                        elif file_path.endswith(".vmx"):
                            msg = "Possibly a Zombie VM! Please check."
                        elif file_path.endswith(".vmtx"):
                            msg = "Possibly a Zombie Template! Please check."
                        else:
                            msg = "Possibly an orphaned file! Please check."

                        warning = {
                            "name": full_path,
                            "message": msg,
                            "message_type": "Zombie",
                            "vi_sdk_server": vi_sdk_info["server"],
                            "vi_sdk_uuid": vi_sdk_info["uuid"],
                        }
                        warnings.append(warning)
                        logger.debug(f"Added orphaned file: {full_path}")

                except Exception as e:
                    logger.debug(f"Error processing file entry: {e}")

        except Exception as e:
            logger.debug(f"Error processing search results: {e}")

        return warnings

    def _extract_datastore_path(self, full_path):
        """Extract datastore-relative path from full path like [datastore] path"""
        if not full_path:
            return ""
        if "[" in full_path and "]" in full_path:
            parts = full_path.split("]", 1)
            if len(parts) > 1:
                return parts[1].strip()
        return full_path

    def _get_vi_sdk_info(self):
        """Extract VI SDK information"""
        return {
            "server": self.content.about.apiVersion or "",
            "uuid": self.content.about.instanceUuid or "",
        }
