#!/usr/bin/env python
""" Main rvtools module """

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
from rvtools.vinfo.vinfo import VInfoCollector
from rvtools.vhealth.vhealth import VHealthCollector
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
logger = logging.getLogger('rvtools')


def get_args():
    parser = argparse.ArgumentParser(description="RVTools Python parameters")

    parser.add_argument('-s', '--host',
                        required=False,
                        action='store',
                        help='vCenter server to connect to')

    parser.add_argument('-u', '--username',
                        required=False,
                        action='store',
                        help='vCenter username')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='vCenter user password')

    parser.add_argument('-d', '--directory',
                        required=False,
                        action='store',
                        help='Directory where will be saved all export files')

    parser.add_argument('-f', '--format',
                        required=False,
                        action='store',
                        default='xlsx',
                        choices=['xlsx', 'csv', 'json-separate', 'json-unified'],
                        help='Export format: xlsx (default), csv, json-separate, json-unified')

    parser.add_argument('--threads',
                        required=False,
                        action='store',
                        default='auto',
                        help='Number of threads for parallel collection (default: auto = min(8, cpu_count))')

    parser.add_argument('-v', '--verbose',
                        required=False,
                        action='store_true',
                        help='Show additional info')

    return parser.parse_args()


def main():
    """ Main entry point """
    args = get_args()

    # Get configuration
    if (args.host is None or args.username is None or args.password is None or args.directory is None):
        logger.info("Reading Conf File")
        obj = CoreCode()
        conn = obj.read_conf_file()
        if conn is None:
            sys.exit(1)
        else:
            server = conn._vcenter
            username = conn._username
            password = conn._password
            directory = conn._directory
            if server == '<fqdn>':
                logger.error("You are using default values. Please update ~/.rvtools.conf")
                sys.exit(1)
    else:
        server = args.host
        username = args.username
        password = args.password
        directory = args.directory

    export_format = args.format or 'xlsx'
    
    # Parse threads
    if args.threads.lower() == 'auto':
        max_workers = None
    else:
        try:
            max_workers = int(args.threads)
        except ValueError:
            logger.error("--threads must be a number or 'auto'")
            sys.exit(1)

    # Setup logging
    logger_instance, log_file = setup_logging(directory)

    if not os.path.isdir(directory):
        logger.error(f"Directory does not exist: {directory}")
        sys.exit(1)

    ssl_context = ssl._create_unverified_context()

    logger.info(f"Connecting to vCenter: {server}")
    logger.info(f"Export format: {export_format}")

    try:
        service_instance = connect.SmartConnect(
            host=server,
            user=username,
            pwd=password,
            port=443,
            sslContext=ssl_context
        )
    except Exception as e:
        logger.error(f"Failed to connect to vCenter: {e}")
        sys.exit(1)

    # Create collectors
    collectors = [
        VInfoCollector(service_instance, directory),
        VHealthCollector(service_instance, directory),
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

    # Execute collectors - always collect data, format handles export
    executor = ParallelCollectorExecutor(max_workers=max_workers)
    results = executor.execute_collectors(collectors, format_type='xlsx')

    timestamp = datetime.now().strftime('%Y-%m-%d_%H.%M')

    # Handle different export formats
    if export_format == 'xlsx':
        xlsx_filename = f"rvtools_{timestamp}.xlsx"
        exporter = XlsxExporter(xlsx_filename, directory)
        
        for sheet_name, data in results.items():
            if data:
                exporter.add_sheet(sheet_name, data)
        
        exporter.save()
        logger.info(f"✓ XLSX export completed: {xlsx_filename}")

    elif export_format == 'json-unified':
        unified_data = {sheet_name: data for sheet_name, data in results.items() if data}
        json_print_unified(f"rvtools_{timestamp}.json", unified_data, directory)
        logger.info(f"✓ JSON unified export completed: rvtools_{timestamp}.json")

    elif export_format == 'json-separate':
        from rvtools.printrv.json_print import json_print_separate
        for sheet_name, data in results.items():
            if data:
                json_print_separate(f"{sheet_name}_{timestamp}.json", data, directory)
        logger.info(f"✓ JSON separate export completed ({len([d for d in results.values() if d])} sheets)")

    elif export_format == 'csv':
        from rvtools.printrv.csv_print import csv_print
        for sheet_name, data in results.items():
            if data:
                csv_print(f"{sheet_name}_{timestamp}.csv", data, directory)
        logger.info(f"✓ CSV export completed ({len([d for d in results.values() if d])} sheets)")

    logger.info(f"Log file: {log_file}")
    logger.info("Collection completed successfully")


if __name__ == "__main__":
    main()
