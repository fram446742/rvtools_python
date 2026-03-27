"""VHealth collector - vCenter health warnings (VM config, storage, security issues)

Implements comprehensive health checks matching RVTools vHealth output with proper
separation of message (warning text with placeholders) and message_type (category).

Uses vm.Layout.Disk (actual runtime state) instead of vm.config.hardware.device 
(desired configuration) for more accurate orphaned file detection.

Uses SearchDatastoreSubFolders_Task (built-in VMware recursion) for improved performance
and reliability in datastore scanning.
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
                        # VirtualUSB has direct 'connected' property
                        is_connected = hasattr(device, 'connected') and device.connected
                        if is_connected:
                            # Build USB ID from available properties
                            usb_id = "USB device"
                            try:
                                # Try to get vendor/product ID first
                                if hasattr(device, 'vendor') and hasattr(device, 'product'):
                                    vendor = device.vendor
                                    product = device.product
                                    if vendor and product:
                                        usb_id = f"USB {vendor:04x}:{product:04x}"
                                    elif hasattr(device, 'deviceInfo') and device.deviceInfo:
                                        usb_id = device.deviceInfo.label or usb_id
                                elif hasattr(device, 'deviceInfo') and device.deviceInfo:
                                    usb_id = device.deviceInfo.label or usb_id
                            except:
                                pass
                            
                            warning = {
                                "name": vm.name,
                                "message": f"VM has a USB device connected! [usb id: {usb_id}]",
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
            logger.debug(f"[ZOMBIE DEBUG] Total registered files: {len(registered_files)}")
            if registered_files:
                sample = list(registered_files)[:3]
                logger.debug(f"[ZOMBIE DEBUG] Sample registered paths: {sample}")
            
            # Build map of inactive VM disk paths for later lookup
            inactive_vm_disks = self._build_inactive_vm_disk_map()
            
            datastores = self.view_cache.get_list([vim.Datastore])

            for datastore in datastores:
                try:
                    zombie_list = self._scan_datastore_for_orphans(datastore, registered_files, inactive_vm_disks)
                    logger.debug(f"[ZOMBIE DEBUG] Datastore {datastore.name}: found {len(zombie_list)} zombies")
                    warnings.extend(zombie_list)
                except Exception as e:
                    logger.debug(f"Error scanning datastore {datastore.name}: {e}")
            
            logger.debug(f"[ZOMBIE DEBUG] Total zombie warnings: {len(warnings)}")

        except Exception as e:
            logger.debug(f"Error in orphaned file detection: {e}", exc_info=True)

        return warnings

    def _build_registered_file_set(self):
        """Build set of all registered VM file paths - uses vm.Layout.Disk (runtime state)
        
        Uses vm.Layout.Disk (actual runtime layout) instead of vm.config.hardware.device
        (desired configuration) to detect more accurate orphaned files.
        """
        registered_files = set()

        try:
            vms = self.view_cache.get_list([vim.VirtualMachine])
            logger.debug(f"Building registered files from {len(vms)} VMs using vm.Layout.Disk (runtime)")

            for vm in vms:
                try:
                    # Collect VM config file path (same in both modes)
                    if vm.config and vm.config.files and vm.config.files.vmPathName:
                        path = self._extract_datastore_path(vm.config.files.vmPathName).lower()
                        registered_files.add(path)
                        # logger.debug(f"VM {vm.name}: registered config file {path}")

                    # Use vm.Layout.Disk (runtime layout) for actual disk files
                    if hasattr(vm, 'layout') and vm.layout and hasattr(vm.layout, 'disk'):
                        try:
                            for disk in vm.layout.disk:
                                if hasattr(disk, 'diskFile'):
                                    for disk_file in disk.diskFile:
                                        path = self._extract_datastore_path(disk_file).lower()
                                        registered_files.add(path)
                                        # logger.debug(f"VM {vm.name}: layout disk {path}")
                        except Exception as e:
                            logger.debug(f"Error collecting vm.Layout.Disk for {vm.name}: {e}")
                            # Fall back to config-based collection
                            self._collect_config_disks(vm, registered_files)
                    else:
                        # Fall back if layout unavailable
                        self._collect_config_disks(vm, registered_files)
                    
                    # Collect snapshot disk files (same in both modes)
                    if vm.snapshot and vm.snapshot.rootSnapshotList:
                        self._collect_snapshot_files(vm, vm.snapshot.rootSnapshotList, registered_files)

                except Exception as e:
                    logger.debug(f"Error collecting VM files for {vm.name}: {e}")

            logger.debug(f"Total registered files: {len(registered_files)}")

        except Exception as e:
            logger.debug(f"Error building registered file set: {e}", exc_info=True)

        return registered_files

    def _build_inactive_vm_disk_map(self):
        """Build map of disk file paths to inactive (powered-off) VM names
        
        Returns dict mapping disk paths to VM info: {disk_path: {name, powerstate, config_path}}
        """
        inactive_vm_disks = {}

        try:
            vms = self.view_cache.get_list([vim.VirtualMachine])
            
            for vm in vms:
                try:
                    # Only track inactive (powered-off) VMs
                    if not vm.runtime or vm.runtime.powerState != vim.VirtualMachine.PowerState.poweredOff:
                        continue
                    
                    vm_info = {
                        'name': vm.name,
                        'powerstate': 'poweredOff',
                        'config_path': None
                    }
                    
                    # Get VM config path
                    if vm.config and vm.config.files and vm.config.files.vmPathName:
                        config_path = self._extract_datastore_path(vm.config.files.vmPathName).lower()
                        vm_info['config_path'] = config_path
                    
                    # Collect disk paths from layout (if available)
                    if hasattr(vm, 'layout') and vm.layout and hasattr(vm.layout, 'disk'):
                        try:
                            for disk in vm.layout.disk:
                                if hasattr(disk, 'diskFile'):
                                    for disk_file in disk.diskFile:
                                        path = self._extract_datastore_path(disk_file).lower()
                                        inactive_vm_disks[path] = vm_info
                        except Exception:
                            pass
                    
                    # Also collect from config as fallback
                    if vm.config and vm.config.hardware and vm.config.hardware.device:
                        try:
                            for device in vm.config.hardware.device:
                                if isinstance(device, vim.vm.device.VirtualDisk):
                                    if (hasattr(device, "backing") and device.backing and 
                                        hasattr(device.backing, "fileName")):
                                        path = self._extract_datastore_path(device.backing.fileName).lower()
                                        inactive_vm_disks[path] = vm_info
                        except Exception:
                            pass
                
                except Exception as e:
                    logger.debug(f"Error collecting inactive VM disks for {vm.name if hasattr(vm, 'name') else 'unknown'}: {e}")
            
            logger.debug(f"Found {len(inactive_vm_disks)} disk paths belonging to {len(set(v['name'] for v in inactive_vm_disks.values()))} inactive VMs")

        except Exception as e:
            logger.debug(f"Error building inactive VM disk map: {e}", exc_info=True)

        return inactive_vm_disks

    def _collect_config_disks(self, vm, registered_files):
        """Helper method to collect VM disk files from configuration"""
        try:
            if vm.config and vm.config.hardware and vm.config.hardware.device:
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualDisk):
                        if (hasattr(device, "backing") and device.backing and 
                            hasattr(device.backing, "fileName")):
                            path = self._extract_datastore_path(device.backing.fileName).lower()
                            registered_files.add(path)
                            logger.debug(f"VM {vm.name}: registered disk {path}")
        except Exception as e:
            logger.debug(f"Error collecting config disks for {vm.name}: {e}")

    def _scan_datastore_for_orphans(self, datastore, registered_files, inactive_vm_disks=None):
        """Scan a single datastore using SearchDatastoreSubFolders_Task for orphaned VM files
        
        Uses SearchDatastoreSubFolders_Task (built-in VMware recursion) instead of
        manual SearchDatastore_Task recursion for better performance and reliability.
        """
        warnings = []
        
        if inactive_vm_disks is None:
            inactive_vm_disks = {}

        try:
            if not datastore.browser:
                return warnings

            logger.debug(f"Searching datastore {datastore.name} for orphaned files using SearchDatastoreSubFolders_Task... (registered files: {len(registered_files)})")
            datastore_path = f"[{datastore.name}]"
            
            # Search using SearchDatastoreSubFolders_Task (built-in recursion)
            warnings.extend(
                self._search_datastore_subfolders(datastore, datastore_path, registered_files, inactive_vm_disks)
            )

        except Exception as e:
            logger.debug(f"Error scanning datastore {datastore.name}: {e}", exc_info=True)

        return warnings

    def _search_datastore_path(self, datastore, datastore_path, registered_files, inactive_vm_disks=None):
        """Search datastore using SearchDatastoreSubFolders_Task (built-in recursion)
        
        This method uses VMware's built-in recursive search API for better performance
        and reliability compared to manual recursion.
        """
        if inactive_vm_disks is None:
            inactive_vm_disks = {}
        
        warnings = []

        try:
            # Create search spec for VM-related files
            spec = vim.host.DatastoreBrowser.SearchSpec()
            spec.matchPattern = ["*.vmx", "*.vmdk", "*.vmtx"]
            spec.details = vim.host.DatastoreBrowser.FileInfo.Details()
            spec.details.fileSize = True
            spec.details.fileType = True
            spec.details.modification = True

            # Use built-in recursive search (handles recursion automatically)
            try:
                task = datastore.browser.SearchDatastoreSubFolders_Task(
                    datastorePath=datastore_path,
                    searchSpec=spec
                )
            except Exception as e:
                logger.debug(f"Error starting SearchDatastoreSubFolders: {datastore_path} - {e}")
                return warnings

            # Wait for task completion
            start_time = time.time()
            timeout = 120  # Longer timeout for recursive search
            
            while True:
                task_state = str(task.info.state)
                if task_state == "success":
                    break
                elif task_state == "error":
                    logger.debug(f"SearchDatastoreSubFolders error: {datastore_path}")
                    return warnings
                elif task_state in ["running", "queued"]:
                    if time.time() - start_time > timeout:
                        logger.debug(f"SearchDatastoreSubFolders timeout: {datastore_path}")
                        return warnings
                    time.sleep(0.5)
                else:
                    break

            # Process all results (includes all subdirectories recursively)
            if str(task.info.state) == "success" and task.info.result:
                # task.info.result is a list of HostDatastoreBrowserSearchResults
                all_results = task.info.result
                
                if not isinstance(all_results, list):
                    all_results = [all_results]
                
                logger.debug(f"SearchDatastoreSubFolders returned {len(all_results)} result sets")
                
                for result_set in all_results:
                    result_warnings = self._process_datastore_search_results(
                        result_set, datastore.name, registered_files, inactive_vm_disks
                    )
                    warnings.extend(result_warnings)

        except Exception as e:
            logger.debug(f"Error in SearchDatastoreSubFolders: {datastore_path} - {e}", exc_info=True)

        return warnings

    def _search_datastore_subfolders(self, datastore, datastore_path, registered_files, inactive_vm_disks=None):
        """Alias for backward compatibility - calls _search_datastore_path"""
        if inactive_vm_disks is None:
            inactive_vm_disks = {}
        return self._search_datastore_path(datastore, datastore_path, registered_files, inactive_vm_disks)

    def _process_datastore_search_results(self, search_results, datastore_name, registered_files, inactive_vm_disks=None):
        """Process files found in datastore search for orphaned entries with deduplication"""
        if inactive_vm_disks is None:
            inactive_vm_disks = {}
        
        warnings = []

        try:
            if not hasattr(search_results, "file") or not search_results.file:
                return warnings

            vi_sdk_info = self._get_vi_sdk_info()
            
            # Filter phase: remove -flat.vmdk and -ctk.vmdk files completely
            filtered_files = []
            for file_entry in search_results.file:
                try:
                    if not hasattr(file_entry, "path"):
                        continue
                    
                    file_path = file_entry.path.lower()
                    filename = file_path.split("/")[-1]
                    
                    # Skip -flat.vmdk and -ctk.vmdk companion files
                    if filename.endswith("-flat.vmdk") or filename.endswith("-ctk.vmdk"):
                        continue
                    
                    filtered_files.append((file_path, file_entry))
                except Exception:
                    continue
            
            # Grouping phase: group by basename to detect both .vmx and .vmdk with same name
            file_groups = {}  # basename -> list of (ext, file_path, file_entry)
            for file_path, file_entry in filtered_files:
                try:
                    filename = file_path.split("/")[-1]
                    
                    # Extract basename and extension
                    path_parts = filename.rsplit(".", 1)
                    basename = path_parts[0]
                    ext = path_parts[1] if len(path_parts) > 1 else ""
                    
                    if basename not in file_groups:
                        file_groups[basename] = []
                    file_groups[basename].append((ext, file_path, file_entry))
                except Exception:
                    continue
            
            # Deduplication phase: keep only one per basename
            # Important: If both .vmx and .vmdk exist with same name, skip BOTH
            # because the .vmx indicates this is a real VM (not a zombie VMDK)
            processed = set()
            
            for basename, files in file_groups.items():
                vmx_files = [f for f in files if f[0] == "vmx"]
                vmtx_files = [f for f in files if f[0] == "vmtx"]
                vmdk_files = [f for f in files if f[0] == "vmdk"]
                
                # If there's a .vmx with this basename, skip BOTH .vmx and .vmdk
                # (the .vmx means it's a registered VM, so the VMDK is not a zombie)
                if vmx_files:
                    # logger.debug(f"[ZOMBIE DEBUG] Skipping group '{basename}': has .vmx (registered VM)")
                    continue
                
                # If there's a .vmtx with this basename, report it as zombie template
                # (the .vmtx alone indicates a zombie template - its vmdk is not a zombie)
                if vmtx_files:
                    for ext, file_path, file_entry in vmtx_files:
                        if file_path not in processed:
                            # This is a zombie template file
                            full_path = f"[{datastore_name}] {file_entry.path}"
                            
                            # Extract file metadata
                            file_info_parts = []
                            file_age_days = None
                            
                            try:
                                if hasattr(file_entry, 'fileSize') and file_entry.fileSize:
                                    size_mb = file_entry.fileSize / (1024 * 1024)
                                    file_info_parts.append(f"size: {size_mb:.1f} MB")
                                
                                if hasattr(file_entry, 'modification') and file_entry.modification:
                                    mod_iso = file_entry.modification.isoformat()
                                    file_info_parts.append(f"modified: {mod_iso}")
                                    
                                    # Calculate age in days
                                    try:
                                        from datetime import datetime, timezone
                                        now = datetime.now(timezone.utc) if file_entry.modification.tzinfo else datetime.now()
                                        delta = now - file_entry.modification
                                        file_age_days = delta.days
                                        file_info_parts.append(f"age: {file_age_days} days")
                                    except:
                                        pass
                            except:
                                pass
                            
                            # Build file info string
                            file_info = ""
                            if file_info_parts:
                                file_info = f" ({', '.join(file_info_parts)})"
                            
                            msg = f"Possibly a Zombie template! Please check.{file_info}"

                            warning = {
                                "name": full_path,
                                "message": msg,
                                "message_type": "Zombie",
                                "age": file_age_days,
                                "vi_sdk_server": vi_sdk_info["server"],
                                "vi_sdk_uuid": vi_sdk_info["uuid"],
                            }
                            warnings.append(warning)
                            processed.add(file_path)
                    
                    # Skip processing VMDK files for this basename since template is already reported
                    continue
                
                # Only report orphaned .vmdk if there's NO .vmx or .vmtx with same name
                if vmdk_files:
                    files_to_report = [vmdk_files[0]]  # Keep only first .vmdk
                else:
                    continue
                
                # Check each file for orphaned status
                for ext, file_path, file_entry in files_to_report:
                    if file_path in processed:
                        continue
                    
                    file_path_normalized = file_path.replace("\\", "/")
                    
                    # Check if file is in registered files
                    is_registered = (file_path_normalized in registered_files)
                    
                    # Also check with backslash format
                    if not is_registered:
                        file_path_backslash = file_path.replace("/", "\\")
                        is_registered = (file_path_backslash in registered_files)
                    
                    # Log for debugging
                    if not is_registered:
                        # Build comprehensive debug info with all properties
                        debug_parts = [file_path]
                        
                        try:
                            if hasattr(file_entry, 'fileSize') and file_entry.fileSize:
                                size_bytes = file_entry.fileSize
                                size_mb = size_bytes / (1024 * 1024)
                                debug_parts.append(f"size: {size_bytes} bytes ({size_mb:.1f} MB)")
                            
                            if hasattr(file_entry, 'modification') and file_entry.modification:
                                mod_iso = file_entry.modification.isoformat()
                                debug_parts.append(f"modified: {mod_iso}")
                                
                                # Calculate age in days
                                try:
                                    from datetime import datetime, timezone
                                    now = datetime.now(timezone.utc) if file_entry.modification.tzinfo else datetime.now()
                                    delta = now - file_entry.modification
                                    age_days = delta.days
                                    debug_parts.append(f"age: {age_days} days")
                                except:
                                    pass
                        except:
                            pass
                        
                        # Check if this disk belongs to an inactive VM
                        disk_path_for_lookup = file_path_normalized.lower()
                        if disk_path_for_lookup in inactive_vm_disks:
                            vm_info = inactive_vm_disks[disk_path_for_lookup]
                            inactive_vm_name = vm_info.get('name', 'Unknown')
                            debug_parts.append(f"belongs to inactive VM: {inactive_vm_name}")
                        else:
                            debug_parts.append("belongs to: permanently orphaned (no inactive VM match)")
                        
                        debug_info = " | ".join(debug_parts)
                        logger.debug(f"[ZOMBIE DEBUG] File NOT in registered: {debug_info}")
                    else:
                        logger.debug(f"[ZOMBIE DEBUG] File IS registered: {file_path}")
                    
                    if not is_registered:
                        full_path = f"[{datastore_name}] {file_entry.path}"
                        
                        # Extract file metadata
                        file_info_parts = []
                        file_age_days = None
                        inactive_vm_name = None
                        
                        try:
                            if hasattr(file_entry, 'fileSize') and file_entry.fileSize:
                                size_mb = file_entry.fileSize / (1024 * 1024)
                                file_info_parts.append(f"size: {size_mb:.1f} MB")
                            
                            if hasattr(file_entry, 'modification') and file_entry.modification:
                                mod_iso = file_entry.modification.isoformat()
                                file_info_parts.append(f"modified: {mod_iso}")
                                
                                # Calculate age in days
                                try:
                                    from datetime import datetime, timezone
                                    now = datetime.now(timezone.utc) if file_entry.modification.tzinfo else datetime.now()
                                    delta = now - file_entry.modification
                                    file_age_days = delta.days
                                except:
                                    pass
                        except:
                            pass
                        
                        # Check if this disk belongs to an inactive VM
                        disk_path_for_lookup = file_path_normalized.lower()
                        if disk_path_for_lookup in inactive_vm_disks:
                            vm_info = inactive_vm_disks[disk_path_for_lookup]
                            inactive_vm_name = vm_info.get('name', 'Unknown')
                            file_info_parts.append(f"belongs to inactive VM: {inactive_vm_name}")
                        
                        # Build file info string
                        file_info = ""
                        if file_info_parts:
                            file_info = f" ({', '.join(file_info_parts)})"
                        
                        # Determine message based on file extension
                        if file_path.endswith(".vmdk"):
                            msg = f"Possibly a Zombie vmdk file! Please check.{file_info}"
                        elif file_path.endswith(".vmx"):
                            msg = f"Possibly a Zombie VM! Please check.{file_info}"
                        elif file_path.endswith(".vmtx"):
                            msg = f"Possibly a Zombie Template! Please check.{file_info}"
                        else:
                            msg = f"Possibly an orphaned file! Please check.{file_info}"

                        warning = {
                            "name": full_path,
                            "message": msg,
                            "message_type": "Zombie",
                            "vi_sdk_server": vi_sdk_info["server"],
                            "vi_sdk_uuid": vi_sdk_info["uuid"],
                        }
                        warnings.append(warning)
                        processed.add(file_path)

        except Exception as e:
            logger.debug(f"Error processing search results: {e}")

        return warnings

    def _collect_snapshot_files(self, vm, snapshots, registered_files):
        """Recursively collect snapshot disk file paths"""
        try:
            for snapshot in snapshots:
                try:
                    # SnapshotTree objects don't have config property
                    # Snapshots are tracked by their name and state, not separate config files
                    # The actual snapshot files are virtual disks referenced by the snapshot
                    
                    # For now, we skip collecting snapshot-specific files as they are
                    # typically managed by vCenter and not orphaned separately
                    # The snapshot disks are referenced through the VM's disk files
                    
                    # Recursively process child snapshots
                    if hasattr(snapshot, "childSnapshotList") and snapshot.childSnapshotList:
                        self._collect_snapshot_files(vm, snapshot.childSnapshotList, registered_files)
                
                except Exception as e:
                    logger.debug(f"Error collecting snapshot files: {e}")
        except Exception as e:
            logger.debug(f"Error in snapshot collection: {e}")

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
