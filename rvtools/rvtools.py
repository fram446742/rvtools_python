#!/usr/bin/env python
"""Main rvtools module"""

import sys
import os
import ssl
import argparse
import logging
import urllib3
from datetime import datetime
from pyVim import connect

from rvtools.corerv import CoreCode
from rvtools.logging_config import setup_logging
from rvtools.parallel_executor import ParallelCollectorExecutor
from rvtools.printrv.xlsx_export import XlsxExporter
from rvtools.printrv.json_print import json_print_unified
from rvtools.utils.retry import retry_with_backoff
from rvtools.vinfo.vinfo import VInfoCollector
from rvtools.vhealth.vhealth import VHealthCollector
from rvtools.vhealth.vhealth_test import VHealthTestCollector, set_test_script_mode
from rvtools.vpartition.vpartition import VPartitionCollector
from rvtools.vcpu.vcpu import VCPUCollector
from rvtools.vmemory.vmemory import VMemoryCollector
from rvtools.vdisk.vdisk import VDiskCollector
from rvtools.vnetwork.vnetwork import VNetworkCollector
from rvtools.vsnapshot.vsnapshot import VSnapshotCollector
from rvtools.vtools.vtools import VToolsCollector
from rvtools.vcd.vcd import VCDCollector
from rvtools.vusb.vusb import VUSBCollector
from rvtools.vrp.vrp import VRPCollector
from rvtools.vcluster.vcluster import VClusterCollector
from rvtools.vhost.vhost import VHostCollector
from rvtools.vdatastore.vdatastore import VDatastoreCollector
from rvtools.vmultipath.vmultipath import VMultiPathCollector
from rvtools.vhba.vhba import VHBACollector
from rvtools.vnic.vnic import VNICCollector
from rvtools.vswitch.vswitch import VSwitchCollector
from rvtools.vport.vport import VPortCollector
from rvtools.dvswitch.dvswitch import DVSwitchCollector
from rvtools.dvport.dvport import DVPortCollector
from rvtools.vsc_vmk.vsc_vmk import VSCVMKCollector
from rvtools.vsource.vsource import VSourceCollector
from rvtools.vlicense.vlicense import VLicenseCollector
from rvtools.vfileinfo.vfileinfo import VFileInfoCollector
from rvtools.vmetadata.vmetadata import VMetaDataCollector

urllib3.disable_warnings()
logger = logging.getLogger("rvtools")


def get_args():
    parser = argparse.ArgumentParser(description="RVTools Python parameters")

    parser.add_argument(
        "-s",
        "--host",
        required=False,
        action="store",
        help="vCenter server to connect to",
    )

    parser.add_argument(
        "-u", "--username", required=False, action="store", help="vCenter username"
    )

    parser.add_argument(
        "-p", "--password", required=False, action="store", help="vCenter user password"
    )

    parser.add_argument(
        "-d",
        "--directory",
        required=False,
        action="store",
        help="Directory where will be saved all export files",
    )

    parser.add_argument(
        "-f",
        "--format",
        required=False,
        action="store",
        default=None,
        choices=["xlsx", "csv", "json-separate", "json-unified"],
        help="Export format: xlsx (default), csv, json-separate, json-unified",
    )

    parser.add_argument(
        "--sheets",
        required=False,
        action="store",
        default=None,
        help="Comma-separated list of sheets to collect (default: all). Example: vInfo,vPartition,vHealth",
    )

    parser.add_argument(
        "--threads",
        required=False,
        action="store",
        default=None,
        help="Number of threads for parallel collection (default: auto = min(8, cpu_count))",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        required=False,
        action="store_true",
        default=None,
        help="Show additional info",
    )

    parser.add_argument(
        "-c",
        "--config",
        required=False,
        action="store",
        default=None,
        help="Path to configuration file (default: ~/.rvtools.toml)",
    )

    parser.add_argument(
        "--include-custom-fields",
        required=False,
        action="store_true",
        default=None,
        help="Include extra custom field columns (e.g., backup protection metadata). Default: hidden to match original RVTools format",
    )

    parser.add_argument(
        "--override",
        required=False,
        action="store_true",
        default=False,
        help="Allow terminal parameters to override config file values",
    )

    parser.add_argument(
        "--test-script",
        required=False,
        action="store_true",
        default=False,
        help="Use alternative zombie detection logic (vm.Layout.Disk instead of vm.config.hardware.device) for testing",
    )

    return parser.parse_args()


def get_all_collectors(service_instance, directory, test_script=False):
    """Get all available collectors
    
    Args:
        service_instance: vSphere connection
        directory: Output directory
        test_script: If True, use VHealthTestCollector instead of VHealthCollector
    """
    vhealth_collector = VHealthTestCollector(service_instance, directory) if test_script else VHealthCollector(service_instance, directory)
    
    return [
        VInfoCollector(service_instance, directory),
        vhealth_collector,
        VPartitionCollector(service_instance, directory),
        VCPUCollector(service_instance, directory),
        VMemoryCollector(service_instance, directory),
        VDiskCollector(service_instance, directory),
        VNetworkCollector(service_instance, directory),
        VSnapshotCollector(service_instance, directory),
        VToolsCollector(service_instance, directory),
        VCDCollector(service_instance, directory),
        VUSBCollector(service_instance, directory),
        VRPCollector(service_instance, directory),
        VClusterCollector(service_instance, directory),
        VHostCollector(service_instance, directory),
        VDatastoreCollector(service_instance, directory),
        VMultiPathCollector(service_instance, directory),
        VHBACollector(service_instance, directory),
        VNICCollector(service_instance, directory),
        VSwitchCollector(service_instance, directory),
        VPortCollector(service_instance, directory),
        DVSwitchCollector(service_instance, directory),
        DVPortCollector(service_instance, directory),
        VSCVMKCollector(service_instance, directory),
        VSourceCollector(service_instance, directory),
        VLicenseCollector(service_instance, directory),
        VFileInfoCollector(service_instance, directory),
        VMetaDataCollector(service_instance, directory),
    ]


def normalize_sheets_param(sheets_param):
    """Normalize sheets parameter to comma-separated string.
    
    Supports three formats:
    - None or empty: returns None (all sheets)
    - "all": returns None (all sheets)
    - "vHealth,vInfo": returns as-is (comma-separated string)
    - ["vHealth", "vInfo"]: converts list to comma-separated string
    
    Args:
        sheets_param: None, string ("all", "vHealth,vInfo"), or list ["vHealth", "vInfo"]
    
    Returns:
        Normalized string or None for all sheets
    """
    if sheets_param is None:
        return None
    
    if isinstance(sheets_param, list):
        sheets_param = ",".join(sheets_param)
    
    if isinstance(sheets_param, str):
        sheets_param = sheets_param.strip()
        if sheets_param.lower() == "all":
            return None
        if sheets_param:
            return sheets_param
    
    return None


def filter_collectors_by_sheets(collectors, sheet_names):
    """Filter collectors to only include specified sheets

    Args:
        collectors: List of collector instances
        sheet_names: Comma-separated sheet names, list of sheet names, "all", or None for all

    Returns:
        Filtered list of collectors
    """
    sheet_names = normalize_sheets_param(sheet_names)
    
    if not sheet_names:
        return collectors

    requested_sheets = set(s.strip() for s in sheet_names.split(","))
    return [c for c in collectors if c.sheet_name in requested_sheets]


@retry_with_backoff(retries=3, initial_delay=1, backoff_factor=2)
def connect_to_vcenter(server, username, password, ssl_context):
    """Connect to vCenter with exponential backoff retry

    Args:
        server: vCenter FQDN or IP
        username: vCenter username
        password: vCenter password
        ssl_context: SSL context for connection

    Returns:
        Service instance on success

    Raises:
        Exception on failure after retries
    """
    logger.debug(f"Attempting to connect to vCenter: {server}")
    return connect.SmartConnect(
        host=server, user=username, pwd=password, port=443, sslContext=ssl_context
    )


def process_single_vcenter(
    server, username, password, directory, export_format, max_workers, sheets_filter, include_custom_fields=False, test_script=False
):
    """Process data collection and export for a single vCenter"""
    from rvtools.collectors.base_collector import set_include_custom_fields
    
    # Set the custom fields flag for this vCenter
    set_include_custom_fields(include_custom_fields)
    
    # Set test script mode if enabled
    if test_script:
        set_test_script_mode(True)
        logger.info("Test script mode enabled: using vm.Layout.Disk and SearchDatastoreSubFolders for zombie detection")
    
    ssl_context = ssl._create_unverified_context()

    logger.info(f"Connecting to vCenter: {server}")
    logger.info(f"Export format: {export_format}")

    try:
        service_instance = connect_to_vcenter(server, username, password, ssl_context)
    except Exception as e:
        logger.error(f"Failed to connect to vCenter {server}: {e}")
        return False

    try:
        # Get all collectors and filter by requested sheets
        all_collectors = get_all_collectors(service_instance, directory, test_script=test_script)
        collectors = filter_collectors_by_sheets(all_collectors, sheets_filter)

        if sheets_filter:
            logger.info(
                f"Collecting from {len(collectors)} selected sheets: {sheets_filter}"
            )
        else:
            logger.info(f"Collecting from all {len(collectors)} sheets")

        # Execute collectors
        executor = ParallelCollectorExecutor(max_workers=max_workers)
        results = executor.execute_collectors(collectors, format_type="xlsx")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M")
        vcenter_suffix = f"_{server.replace('.', '_')}" if server != "localhost" else ""

        # Handle different export formats
        if export_format == "xlsx":
            xlsx_filename = f"rvtools{vcenter_suffix}_{timestamp}.xlsx"
            exporter = XlsxExporter(xlsx_filename, directory)

            for sheet_name, data in results.items():
                if data:
                    try:
                        exporter.add_sheet(sheet_name, data)
                    except Exception as e:
                        logger.error(
                            f"Failed to add sheet {sheet_name}: {e}", exc_info=True
                        )
                        continue

            exporter.save()
            logger.info(f"✓ XLSX export completed: {xlsx_filename}")

        elif export_format == "json-unified":
            unified_data = {
                sheet_name: data for sheet_name, data in results.items() if data
            }
            json_print_unified(
                f"rvtools{vcenter_suffix}_{timestamp}.json", unified_data, directory
            )
            logger.info(f"✓ JSON unified export completed")

        elif export_format == "json-separate":
            from rvtools.printrv.json_print import json_print_separate

            for sheet_name, data in results.items():
                if data:
                    try:
                        json_print_separate(
                            f"{sheet_name}{vcenter_suffix}_{timestamp}.json",
                            data,
                            directory,
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to export JSON for {sheet_name}: {e}",
                            exc_info=True,
                        )
                        continue
            logger.info(f"✓ JSON separate export completed")

        elif export_format == "csv":
            from rvtools.printrv.csv_print import csv_print

            for sheet_name, data in results.items():
                if data:
                    try:
                        csv_print(
                            f"{sheet_name}{vcenter_suffix}_{timestamp}.csv",
                            data,
                            directory,
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to export CSV for {sheet_name}: {e}", exc_info=True
                        )
                        continue
            logger.info(f"✓ CSV export completed")

        return True

    except Exception as e:
        logger.error(f"Fatal error during export for {server}: {e}", exc_info=True)
        return False
    finally:
        for handler in logger.handlers:
            handler.flush() if hasattr(handler, "flush") else None


def _resolve_setting(cli_value, config_value, default=None, override=False):
    """
    Resolve a setting based on CLI and config values.
    
    Args:
        cli_value: Value from CLI arguments
        config_value: Value from config file
        default: Default value if both are None
        override: If True, CLI values override config values
                 If False, config values take precedence, CLI only used if required
    
    Returns:
        Resolved setting value
    """
    if override:
        # Override mode: CLI values take precedence
        if cli_value is not None:
            return cli_value
    # Normal mode: config takes precedence
    if config_value is not None:
        return config_value
    if cli_value is not None:
        return cli_value
    return default


def main():
    """Main entry point"""
    args = get_args()

    # CLI-level options take precedence only if --override is set, otherwise config takes precedence
    override = args.override
    cli_format = args.format
    cli_threads = args.threads
    cli_sheets = args.sheets
    cli_verbose = args.verbose
    cli_include_custom_fields = args.include_custom_fields
    test_script = args.test_script

    # Get configuration
    # Load config file if needed (when any required field is missing)
    config_from_file = None
    if (
        args.host is None
        or args.username is None
        or args.password is None
        or args.directory is None
    ):
        config_file = args.config or os.path.expanduser("~/.rvtools.toml")
        logger.info(f"Reading TOML configuration file from {config_file}")
        obj = CoreCode()

        # Determine which required fields are being provided via CLI
        optional_fields = []
        if args.host is not None:
            optional_fields.append("vcenter")
        if args.username is not None:
            optional_fields.append("username")
        if args.password is not None:
            optional_fields.append("password")
        if args.directory is not None:
            optional_fields.append("directory")

        # Try to read multi-vCenter config first
        multi_configs = obj.read_conf_file_multi(args.config, optional_fields=optional_fields)

        if multi_configs:
            logger.info(
                f"Found {len(multi_configs)} vCenter configuration(s): {', '.join(c.get('_section_name', 'unknown') for c in multi_configs)}"
            )
            config_from_file = multi_configs
        else:
            # Fallback to single config
            conn = obj.read_conf_file(args.config, optional_fields=optional_fields)
            if conn is None:
                sys.exit(1)

            if conn._vcenter == "<fqdn>":
                logger.error(
                    f"You are using default values. Please update {config_file}"
                )
                sys.exit(1)

            config_from_file = [
                {
                    "vcenter": conn._vcenter,
                    "username": conn._username,
                    "password": conn._password,
                    "directory": conn._directory,
                    "format": conn._format,
                    "threads": conn._threads,
                    "sheets": getattr(conn, '_sheets', None),
                    "verbose": getattr(conn, '_verbose', False),
                    "include_custom_fields": conn._include_custom_fields,
                    "_section_name": "default",
                }
            ]

    # Build configs_to_process with proper override handling
    configs_to_process = []
    
    if config_from_file:
        # We have config from file
        for config in config_from_file:
            # Apply CLI overrides if enabled
            if override:
                # Override mode: CLI values replace config values
                if args.host is not None:
                    config["vcenter"] = args.host
                if args.username is not None:
                    config["username"] = args.username
                if args.password is not None:
                    config["password"] = args.password
                if args.directory is not None:
                    config["directory"] = args.directory
            else:
                # Normal mode: CLI values only fill in missing required fields
                if args.host is not None and config.get("vcenter") is None:
                    config["vcenter"] = args.host
                if args.username is not None and config.get("username") is None:
                    config["username"] = args.username
                if args.password is not None and config.get("password") is None:
                    config["password"] = args.password
                if args.directory is not None and config.get("directory") is None:
                    config["directory"] = args.directory
            
            configs_to_process.append(config)
    else:
        # CLI arguments provided and no config needed
        configs_to_process = [
            {
                "vcenter": args.host,
                "username": args.username,
                "password": args.password,
                "directory": args.directory,
                "format": None,
                "threads": None,
                "sheets": None,
                "verbose": None,
                "include_custom_fields": None,
                "_section_name": "cli-args",
            }
        ]

    # Choose global verbose based on CLI or any config value
    global_verbose = cli_verbose if cli_verbose is not None else any(
        bool(config.get("verbose", False)) for config in configs_to_process
    )

    # Setup logging (use directory from first config)
    directory = configs_to_process[0].get("directory")
    logger_instance, log_file = setup_logging(directory, verbose=global_verbose)

    if not os.path.isdir(directory):
        logger.error(f"Directory does not exist: {directory}")
        sys.exit(1)

    # Log override mode status
    if override:
        logger.info("Override mode enabled: terminal parameters will override config values")
    else:
        logger.info("Override mode disabled: config values will take precedence over optional terminal parameters")

    # Process each vCenter configuration
    success_count = 0
    for config in configs_to_process:
        try:
            # Per-vCenter effective settings - apply override logic
            export_format = _resolve_setting(cli_format, config.get("format"), "xlsx", override=override)
            threads = _resolve_setting(cli_threads, config.get("threads"), "auto", override=override)
            sheets_filter = _resolve_setting(cli_sheets, config.get("sheets"), None, override=override)
            sheets_filter = normalize_sheets_param(sheets_filter)
            verbose = _resolve_setting(cli_verbose, config.get("verbose"), False, override=override)
            include_custom_fields = _resolve_setting(
                cli_include_custom_fields,
                config.get("include_custom_fields"),
                False,
                override=override,
            )

            # Evolve threads setting to max_workers
            if isinstance(threads, str) and threads.lower() == "auto":
                max_workers = None
            else:
                try:
                    max_workers = int(threads)
                except Exception:
                    logger.error("threads must be a number or 'auto'")
                    sys.exit(1)

            # Reflect verbose per config
            if verbose:
                logger.info("Verbose output enabled")

            # Set custom fields per vCenter directly before collection
            from rvtools.collectors.base_collector import set_include_custom_fields
            set_include_custom_fields(include_custom_fields)
            if include_custom_fields:
                logger.info("Including extra custom field columns (backup metadata, etc.)")
            else:
                logger.info("Hiding extra custom field columns (use --include-custom-fields to show)")

            section_name = config.get("_section_name", config.get("vcenter", "unknown"))
            logger.info(f"{'=' * 60}")
            logger.info(f"Processing vCenter: {section_name}")
            logger.info(f"{'=' * 60}")

            success = process_single_vcenter(
                server=config.get("vcenter"),
                username=config.get("username"),
                password=config.get("password"),
                directory=config.get("directory"),
                export_format=export_format,
                max_workers=max_workers,
                sheets_filter=sheets_filter,
                include_custom_fields=include_custom_fields,
                test_script=test_script,
            )

            if success:
                success_count += 1
        except Exception as e:
            logger.error(f"Error processing vCenter config: {e}", exc_info=True)
            continue

    # Summary
    logger.info(f"{'=' * 60}")
    logger.info(
        f"Processing complete: {success_count}/{len(configs_to_process)} vCenters processed"
    )
    logger.info(f"{'=' * 60}")

    if success_count == 0:
        sys.exit(1)

    logger.info(f"Log file: {log_file}")
    logger.info("Collection completed successfully")

    # Ensure all logs are written before exit
    for handler in logger.handlers:
        handler.flush() if hasattr(handler, "flush") else None
        handler.close() if hasattr(handler, "close") else None

if __name__ == "__main__":
    main()
