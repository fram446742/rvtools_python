"""VMetaData collector - Metadata information"""

from datetime import datetime
from rvtools.collectors.base_collector import BaseCollector


class VMetaDataCollector(BaseCollector):
    """Collector for vMetaData sheet - Backup metadata"""

    @property
    def sheet_name(self):
        return "vMetaData"

    def collect(self):
        """Collect metadata information"""
        metadata_list = []

        now = datetime.now()

        metadata_data = {
            "rvtools_major_version": "1",
            "rvtools_version": "1.0.0",
            "xlsx_creation_datetime": now.isoformat(),
            "server": self.content.about.name if self.content.about else "",
        }
        metadata_list.append(metadata_data)

        return metadata_list
