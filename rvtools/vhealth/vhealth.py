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
            datastore_path = f"[{datastore.name}]"

            logger.debug(f"Searching datastore {datastore.name} for orphaned files...")
            task = self._start_datastore_search_task(
                datastore.browser, datastore_path, spec
            )
            if task is None:
                logger.debug(
                    f"Datastore {datastore.name} browser does not support search APIs"
                )
                return warnings

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

    def _start_datastore_search_task(self, browser, datastore_path, search_spec):
        """Start datastore browser task using the best supported search API."""
        search_methods = [
            ("SearchDatastoreSubFolders", {"datastorePath": datastore_path, "searchSpec": search_spec}),
            ("SearchDatastoreSubFolders_Task", {"datastorePath": datastore_path, "searchSpec": search_spec}),
            ("SearchDatastore", {"datastorePath": datastore_path, "spec": search_spec}),
            ("SearchDatastore_Task", {"datastorePath": datastore_path, "searchSpec": search_spec}),
        ]

        for method_name, kwargs in search_methods:
            method = getattr(browser, method_name, None)
            if method is None:
                continue

            try:
                return method(**kwargs)
            except TypeError:
                # Different pyVmomi versions expose slightly different signatures.
                continue
            except Exception as exc:
                logger.debug(f"Datastore search call failed using {method_name}: {exc}")
                continue

        return None

    def _iter_search_result_entries(self, search_results):
        """Yield (folder_path, file_path) from both single-folder and recursive search results."""
        if isinstance(search_results, list):
            for folder_result in search_results:
                folder_path = getattr(folder_result, "folderPath", "")
                for file_entry in getattr(folder_result, "file", []) or []:
                    file_path = getattr(file_entry, "path", None)
                    if file_path:
                        yield folder_path, file_path
            return

        folder_path = getattr(search_results, "folderPath", "")
        for file_entry in getattr(search_results, "file", []) or []:
            file_path = getattr(file_entry, "path", None)
            if file_path:
                yield folder_path, file_path

    def _process_datastore_search_results(self, search_results, datastore_name, registered_files):
        """Process files found in datastore search for orphaned entries"""
        warnings = []

        try:
            vi_sdk_info = self._get_vi_sdk_info()

            for folder_path, file_path in self._iter_search_result_entries(search_results):
                try:
                    relative_path = self._search_result_to_relative_path(
                        folder_path, file_path
                    )
                    file_path_lower = relative_path.lower()

                    # Check if this file is registered
                    if file_path_lower not in registered_files:
                        # This is an orphaned/zombie file
                        message = self._get_zombie_message(file_path)
                        full_path = f"[{datastore_name}] {relative_path}"

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

    def _search_result_to_relative_path(self, folder_path, file_path):
        """Build normalized datastore-relative path from folder and file values."""
        file_part = self._normalize_relative_path(file_path)
        folder_part = self._extract_datastore_path(folder_path)
        folder_part = self._normalize_relative_path(folder_part)

        if not folder_part:
            return file_part
        if not file_part:
            return folder_part
        if file_part.startswith(folder_part + "/"):
            return file_part
        return f"{folder_part}/{file_part}".strip("/")

    def _normalize_relative_path(self, path):
        """Normalize paths so datastore paths compare reliably."""
        if not path:
            return ""

        normalized = str(path).strip()
        normalized = normalized.replace("\\", "/")
        return normalized.lstrip("/")

    def _extract_datastore_path(self, full_path):
        """Extract path relative to datastore from full path like [datastore] path"""
        if not full_path:
            return ""

        # Format: "[datastore_name] /path/to/file"
        if "[" in full_path and "]" in full_path:
            # Extract part after "]"
            parts = full_path.split("]", 1)
            if len(parts) > 1:
                return self._normalize_relative_path(parts[1])

        return self._normalize_relative_path(full_path)

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
