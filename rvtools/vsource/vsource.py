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
                "name": about.name or "",
                "os_type": about.osType or "",
                "api_type": about.apiType or "",
                "api_version": about.apiVersion or "",
                "version": about.version or "",
                "patch_level": getattr(about, "patchLevel", "") or "",
                "build": about.build or "",
                "fullname": about.fullName or "",
                "product_name": about.productName or "",
                "product_version": about.productLineId or "",
                "product_line": about.productLineId or "",
                "vendor": about.vendor or "",
                "vi_sdk_server": about.apiVersion or "",
                "vi_sdk_uuid": about.instanceUuid or "",
            }
            source_list.append(source_data)

        return source_list
