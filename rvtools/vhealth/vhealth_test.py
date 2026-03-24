"""VHealth test collector - Alternative implementations using vm.Layout.Disk and SearchDatastoreSubFolders

This module provides test-script mode implementations of the vHealth collector.
When --test-script flag is used, these alternative APIs are tested instead of production methods:

1. vm.Layout.Disk (runtime state) instead of vm.config.hardware.device (desired config)
2. SearchDatastoreSubFolders_Task (built-in recursion) instead of SearchDatastore_Task (manual recursion)

Usage:
    from rvtools.vhealth.vhealth_test import VHealthTestCollector
    collector = VHealthTestCollector(service_instance, directory)
    data = collector.collect()
"""

from pyVmomi import vim
from rvtools.vhealth.vhealth import VHealthCollector
import logging
import time

logger = logging.getLogger("rvtools")


# Global flag for test script mode (shared across module)
_test_script_mode = False


def set_test_script_mode(enabled):
    """Enable/disable test script mode for zombie detection"""
    global _test_script_mode
    _test_script_mode = enabled


def get_test_script_mode():
    """Check if test script mode is enabled"""
    return _test_script_mode


class VHealthTestCollector(VHealthCollector):
    """Test script mode collector - uses alternative APIs for testing
    
    Inherits from VHealthCollector and overrides key methods to test alternative
    implementations. All shared methods are inherited to avoid code duplication.
    """

    def _build_registered_file_set(self):
        """Build set of all registered VM file paths - test script mode using vm.Layout.Disk
        
        Uses vm.Layout.Disk (actual runtime layout) instead of vm.config.hardware.device
        (desired configuration) to test if runtime state provides more accurate results.
        """
        registered_files = set()

        try:
            vms = self.view_cache.get_list([vim.VirtualMachine])
            logger.debug(f"[TEST-SCRIPT] Building registered files from {len(vms)} VMs")
            logger.debug(f"[TEST-SCRIPT] Using vm.Layout.Disk (runtime) instead of vm.config.hardware.device")

            for vm in vms:
                try:
                    # Collect VM config file path (same in both modes)
                    if vm.config and vm.config.files and vm.config.files.vmPathName:
                        path = self._extract_datastore_path(vm.config.files.vmPathName).lower()
                        registered_files.add(path)
                        logger.debug(f"VM {vm.name}: registered config file {path}")

                    # Test script mode: use vm.Layout.Disk (runtime layout)
                    if hasattr(vm, 'layout') and vm.layout and hasattr(vm.layout, 'disk'):
                        try:
                            for disk in vm.layout.disk:
                                if hasattr(disk, 'diskFile'):
                                    for disk_file in disk.diskFile:
                                        path = self._extract_datastore_path(disk_file).lower()
                                        registered_files.add(path)
                                        logger.debug(f"VM {vm.name}: layout disk {path}")
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

    def _scan_datastore_for_orphans(self, datastore, registered_files):
        """Scan a single datastore using SearchDatastoreSubFolders_Task - test script mode
        
        Uses SearchDatastoreSubFolders_Task (built-in VMware recursion) instead of
        manual SearchDatastore_Task recursion to test if built-in API provides
        better performance or accuracy.
        """
        warnings = []

        try:
            if not datastore.browser:
                return warnings

            logger.debug(f"[TEST-SCRIPT] Searching datastore {datastore.name} for orphaned files... (registered files: {len(registered_files)})")
            datastore_path = f"[{datastore.name}]"
            
            # Search using SearchDatastoreSubFolders_Task (test method)
            logger.debug(f"[TEST-SCRIPT] Using SearchDatastoreSubFolders_Task (built-in recursion)")
            warnings.extend(
                self._search_datastore_subfolders(datastore, datastore_path, registered_files)
            )

        except Exception as e:
            logger.debug(f"[TEST-SCRIPT] Error scanning datastore {datastore.name}: {e}", exc_info=True)

        return warnings

    def _search_datastore_subfolders(self, datastore, datastore_path, registered_files):
        """Search datastore using SearchDatastoreSubFolders_Task (built-in recursion)
        
        This is an alternative method to manual recursion, using VMware's built-in
        recursive search API. Used when --test-script flag is enabled.
        """
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
                logger.debug(f"[TEST-SCRIPT] Error starting SearchDatastoreSubFolders: {datastore_path} - {e}")
                return warnings

            # Wait for task completion
            start_time = time.time()
            timeout = 120  # Longer timeout for recursive search
            
            while True:
                task_state = str(task.info.state)
                if task_state == "success":
                    break
                elif task_state == "error":
                    logger.debug(f"[TEST-SCRIPT] SearchDatastoreSubFolders error: {datastore_path}")
                    return warnings
                elif task_state in ["running", "queued"]:
                    if time.time() - start_time > timeout:
                        logger.debug(f"[TEST-SCRIPT] SearchDatastoreSubFolders timeout: {datastore_path}")
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
                
                logger.debug(f"[TEST-SCRIPT] SearchDatastoreSubFolders returned {len(all_results)} result sets")
                
                for result_set in all_results:
                    result_warnings = self._process_datastore_search_results(
                        result_set, datastore.name, registered_files
                    )
                    warnings.extend(result_warnings)

        except Exception as e:
            logger.debug(f"[TEST-SCRIPT] Error in SearchDatastoreSubFolders: {datastore_path} - {e}", exc_info=True)

        return warnings
