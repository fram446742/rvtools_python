"""VSource collector - vCenter source information"""

from rvtools.collectors.base_collector import BaseCollector


class VSourceCollector(BaseCollector):
    """Collector for vSource sheet - vCenter metadata"""

    @property
    def sheet_name(self):
        return "vSource"

    def collect(self):
        """Collect vCenter source information"""
        source_list = []

        about = self.content.about if self.content else None
        if about:
            source_data = {
                "name": getattr(about, "name", "") or "",
                "os_type": getattr(about, "osType", "") or "",
                "api_type": getattr(about, "apiType", "") or "",
                "api_version": getattr(about, "apiVersion", "") or "",
                "version": getattr(about, "version", "") or "",
                "patch_level": getattr(about, "patchLevel", "") or "",
                "build": getattr(about, "build", "") or "",
                "fullname": getattr(about, "fullName", "") or "",
                "product_name": getattr(about, "productName", "") or "",
                "product_version": getattr(about, "productLineId", "") or "",
                "product_line": getattr(about, "productLineId", "") or "",
                "vendor": getattr(about, "vendor", "") or "",
                "vi_sdk_server": getattr(about, "apiVersion", "") or "",
                "vi_sdk_uuid": getattr(about, "instanceUuid", "") or "",
            }
            source_list.append(source_data)

        return source_list
