"""VHealth collector - vCenter health warnings (zombie/orphaned file detection)"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector
from rvtools.cache_utils import ViewCache
import logging

logger = logging.getLogger("rvtools")


class VHealthCollector(BaseCollector):
    """Collector for vHealth sheet - Detects zombie VMs, templates, and orphaned files"""

    def __init__(self, service_instance, directory):
        """Initialize with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vHealth"

    def collect(self):
        """Collect health information - primarily zombie/orphaned file detection"""
        health_list = []

        # Detect orphaned/zombie VM files in datastores
        try:
            zombie_warnings = self._detect_orphaned_files()
            health_list.extend(zombie_warnings)
        except Exception as e:
            logger.warning(f"Error detecting orphaned files: {e}")

        return health_list

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
            logger.warning(f"Error in orphaned file detection: {e}")

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
                            logger.debug(f"VM {vm.name}: registered {path}")

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
            import time

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
