"""VHealth collector - vCenter health and alarms"""

from rvtools.collectors.base_collector import BaseCollector
from rvtools.cache_utils import ViewCache
import logging

logger = logging.getLogger("rvtools")


class VHealthCollector(BaseCollector):
    """Collector for vHealth sheet - vCenter health and alarm status"""

    def __init__(self, service_instance, directory):
        """Initialize with cache"""
        super().__init__(service_instance, directory)
        self.view_cache = ViewCache(self.content)

    @property
    def sheet_name(self):
        return "vHealth"

    def collect(self):
        """Collect health and alarm information from vCenter"""
        health_list = []

        try:
            # Get triggered/active alarms from alarm manager
            content = self.content
            if not content:
                return health_list

            alarm_manager = getattr(content, "alarmManager", None)
            if alarm_manager:
                # Get all triggered alarms (not just alarm definitions)
                try:
                    # GetTriggeredAlarms gives us active alarm states
                    root_folder = getattr(content, "rootFolder", None)
                    if root_folder is None:
                        return health_list

                    triggered_alarms = alarm_manager.GetTriggeredAlarms(entity=root_folder)
                    for triggered_alarm in triggered_alarms:
                        health_data = self._collect_triggered_alarm(triggered_alarm)
                        if health_data:
                            health_list.append(health_data)
                except Exception as e:
                    logger.debug(f"Could not get triggered alarms: {e}")

                # Fallback: Get alarm definitions and check their status
                if not health_list:
                    try:
                        alarms = alarm_manager.GetAlarm(root_folder)
                        for alarm_def in alarms:
                            health_data = self._collect_alarm(alarm_def)
                            if health_data:
                                health_list.append(health_data)
                    except Exception as e:
                        logger.debug(f"Could not get alarm definitions: {e}")

        except Exception as e:
            logger.warning(f"Error collecting vHealth alarms: {e}")

        return health_list

    def _collect_triggered_alarm(self, triggered_alarm):
        """Collect information for a triggered alarm instance"""
        try:
            health_data = {}

            # Get alarm definition
            alarm = triggered_alarm.alarm
            if not alarm:
                return None

            health_data["name"] = alarm.info.name or ""
            health_data["message"] = alarm.info.description or ""

            # Extract alarm type from alarm name or description
            alarm_type = self._extract_alarm_type(alarm)
            health_data["message_type"] = alarm_type

            vi_sdk_info = self._get_vi_sdk_info()
            health_data["vi_sdk_server"] = vi_sdk_info["server"]
            health_data["vi_sdk_uuid"] = vi_sdk_info["uuid"]

            return health_data
        except Exception as e:
            logger.debug(f"Error processing triggered alarm: {e}")
            return None

    def _collect_alarm(self, alarm):
        """Collect information for a single alarm definition"""
        try:
            health_data = {}

            health_data["name"] = alarm.info.name or ""
            health_data["message"] = alarm.info.description or ""

            # Extract alarm type from alarm name or description
            alarm_type = self._extract_alarm_type(alarm)
            health_data["message_type"] = alarm_type

            vi_sdk_info = self._get_vi_sdk_info()
            health_data["vi_sdk_server"] = vi_sdk_info["server"]
            health_data["vi_sdk_uuid"] = vi_sdk_info["uuid"]

            return health_data
        except Exception as e:
            logger.debug(f"Error processing alarm: {e}")
            return None

    def _get_vi_sdk_info(self):
        """Extract VI SDK information"""
        about = getattr(self.content, "about", None)
        return {
            "server": getattr(about, "apiVersion", "") or "",
            "uuid": getattr(about, "instanceUuid", "") or "",
        }

    def _extract_alarm_type(self, alarm):
        """
        Extract alarm type from alarm name/description.

        Looks for known alarm type keywords in the alarm name or description.
        Returns the alarm type (e.g., "Zombie", "Snapshots", "CDROM", etc.)
        or the alarm key if no keywords found.
        """
        # Keywords to look for in alarm name/description
        keywords = {
            "zombie": "Zombie",
            "snapshot": "Snapshots",
            "cdrom": "CDROM",
            "consolidation": "Consolidation",
            "iscsi": "iSCSI",
            "nfs": "NFS",
            "datastore": "Datastore",
            "cpu": "CPU",
            "memory": "Memory",
            "disk": "Disk",
            "network": "Network",
            "vmware": "VMware",
            "vsan": "vSAN",
            "vcenter": "vCenter",
            "host": "Host",
            "cluster": "Cluster",
            "storage": "Storage",
        }

        alarm_type = ""

        # Try to extract from alarm name
        alarm_name = (alarm.info.name or "").lower()
        alarm_desc = (alarm.info.description or "").lower()

        # Check each keyword
        for keyword, alarm_type_name in keywords.items():
            if keyword in alarm_name or keyword in alarm_desc:
                alarm_type = alarm_type_name
                break

        # If no keyword found, try to extract from alarm key
        if not alarm_type:
            try:
                if hasattr(alarm.info, "key") and alarm.info.key:
                    key = alarm.info.key
                    # Extract meaningful part from key (e.g., "alarm-2814" stays as is)
                    alarm_type = key
            except Exception:
                pass

        return alarm_type or "Unknown"
