"""VFileInfo collector - File information"""

from rvtools.collectors.base_collector import BaseCollector


class VFileInfoCollector(BaseCollector):
    """Collector for vFileInfo sheet - File information"""

    @property
    def sheet_name(self):
        return "vFileInfo"

    def collect(self):
        """Collect file information"""
        file_list = []

        file_data = {
            "friendly_path_name": "",
            "file_name": "",
            "file_type": "",
            "file_size_in_bytes": "",
            "path": "",
            "internal_sort_column": "",
            "vi_sdk_server": self.content.about.apiVersion or "",
            "vi_sdk_uuid": self.content.about.instanceUuid or "",
        }
        file_list.append(file_data)

        return file_list
