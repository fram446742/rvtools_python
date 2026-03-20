"""VLicense collector - License information"""

from rvtools.collectors.base_collector import BaseCollector


class VLicenseCollector(BaseCollector):
    """Collector for vLicense sheet - License information"""

    @property
    def sheet_name(self):
        return "vLicense"

    def collect(self):
        """Collect license information from vCenter"""
        license_list = []

        try:
            license_manager = self.content.licenseManager
            if license_manager and license_manager.licenses:
                for license_info in license_manager.licenses:
                    lic_data = {
                        "name": license_info.name or "",
                        "key": license_info.licenseKey or "",
                        "labels": self._get_labels(license_info),
                        "cost_unit": license_info.costUnit or "",
                        "total": str(license_info.total) if license_info.total else "",
                        "used": str(license_info.used) if license_info.used else "",
                        "expiration_date": str(license_info.expireDate)
                        if license_info.expireDate
                        else "",
                        "features": self._get_features(license_info),
                        "vi_sdk_server": self.content.about.apiVersion or "",
                        "vi_sdk_uuid": self.content.about.instanceUuid or "",
                    }
                    license_list.append(lic_data)
        except Exception:
            pass

        return license_list

    def _get_labels(self, license_info):
        """Get comma-separated labels"""
        try:
            if hasattr(license_info, "labels") and license_info.labels:
                return ", ".join(license_info.labels)
            return ""
        except Exception:
            return ""

    def _get_features(self, license_info):
        """Get comma-separated features"""
        try:
            if hasattr(license_info, "properties") and license_info.properties:
                return ", ".join([str(p) for p in license_info.properties])
            return ""
        except Exception:
            return ""
