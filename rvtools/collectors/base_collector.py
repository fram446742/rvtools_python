"""Base class for all data collectors"""
from abc import ABC, abstractmethod
from datetime import datetime
import logging

logger = logging.getLogger('rvtools')


class BaseCollector(ABC):
    """Abstract base class for collecting vCenter data"""

    def __init__(self, service_instance, directory):
        """
        Initialize collector with vCenter connection and output directory

        Args:
            service_instance: pyVmomi service instance connected to vCenter
            directory: Output directory for exports
        """
        self.service_instance = service_instance
        self.directory = directory
        try:
            self.content = service_instance.RetrieveContent()
        except Exception as e:
            logger.error(f"Failed to retrieve content: {e}")
            self.content = None

    @property
    @abstractmethod
    def sheet_name(self):
        """Name of the sheet (e.g., 'vInfo', 'vHealth')"""
        pass

    @abstractmethod
    def collect(self):
        """
        Collect data from vCenter

        Returns:
            list: List of dictionaries containing collected data
        """
        pass

    def export_csv(self, data):
        """Export data as CSV file with timestamp"""
        from rvtools.printrv.csv_print import csv_print

        filename = self._get_filename('csv')
        csv_print(filename, data, self.directory)

    def export_json_separate(self, data):
        """Export data as separate JSON file with timestamp"""
        from rvtools.printrv.json_print import json_print_separate

        filename = self._get_filename('json')
        json_print_separate(filename, data, self.directory)

    def export_json_unified(self, data, unified_data):
        """
        Add data to unified JSON export

        Args:
            data: Current sheet data
            unified_data: Dictionary to accumulate all sheets
        """
        unified_data[self.sheet_name] = data

    def _get_filename(self, extension):
        """
        Generate filename with timestamp

        Format: SHEET_YYYY-MM-DD_HH.MM.ext

        Args:
            extension: File extension (csv, json)

        Returns:
            str: Formatted filename
        """
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d_%H.%M')
        return f"{self.sheet_name}_{timestamp}.{extension}"

    def run(self, format_type='xlsx', unified_data=None):
        """
        Run collector and export data

        Args:
            format_type: Export format ('xlsx', 'csv', 'json-separate', 'json-unified')
            unified_data: Dictionary for unified JSON export
        """
        try:
            logger.debug(f"## Processing {self.sheet_name} module")
            data = self.collect()

            if not data:
                logger.warning(f"No data collected for {self.sheet_name}")
                return

            if format_type == 'xlsx':
                return data
            elif format_type == 'csv':
                self.export_csv(data)
            elif format_type == 'json-separate':
                self.export_json_separate(data)
            elif format_type == 'json-unified':
                self.export_json_unified(data, unified_data)
        except Exception as e:
            logger.error(f"Error processing {self.sheet_name}: {e}", exc_info=True)
            return []
