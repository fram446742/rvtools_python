"""VHealth collector - vCenter health and alarms"""

from pyVmomi import vim
from rvtools.collectors.base_collector import BaseCollector


class VHealthCollector(BaseCollector):
    """Collector for vHealth sheet - vCenter health and alarm messages"""

    @property
    def sheet_name(self):
        return "vHealth"

    def collect(self):
        """Collect health and alarm information from vCenter"""
        health_list = []

        try:
            alarm_manager = self.content.alarmManager
            if alarm_manager:
                alarms = alarm_manager.GetAlarm(self.content.rootFolder)
                for alarm_def in alarms:
                    health_data = self._collect_alarm(alarm_def)
                    health_list.append(health_data)
        except Exception as e:
            print(f"Warning: Could not retrieve alarms: {e}")

        return health_list

    def _collect_alarm(self, alarm):
        """Collect information for a single alarm"""
        health_data = {}

        health_data["name"] = alarm.info.name or ""
        health_data["message"] = alarm.info.description or ""

        # Extract alarm type from alarm object
        alarm_type = "Unknown"
        try:
            # Try to get from trigger (which contains the event/metric being monitored)
            if hasattr(alarm.info, "trigger"):
                trigger = alarm.info.trigger
                # For event-based alarms
                if hasattr(trigger, "eventType"):
                    event_type = trigger.eventType
                    # Extract last part of event type (e.g., "vim.event.VmCreatedEvent" -> "VmCreatedEvent")
                    if isinstance(event_type, str) and "." in event_type:
                        alarm_type = event_type.split(".")[-1]
                    else:
                        alarm_type = str(event_type)
                # For metric-based alarms
                elif hasattr(trigger, "metricId"):
                    metric = trigger.metricId
                    if hasattr(metric, "key"):
                        alarm_type = str(metric.key)
                    elif hasattr(metric, "counterId"):
                        alarm_type = f"metric_{metric.counterId}"

            # Fallback: use alarm key
            if alarm_type == "Unknown" and hasattr(alarm.info, "key"):
                key = alarm.info.key
                if key:
                    # Extract meaningful part from key
                    if "." in key:
                        parts = key.split(".")
                        alarm_type = parts[-1]
                    else:
                        alarm_type = key
        except Exception:
            pass

        health_data["message_type"] = alarm_type

        vi_sdk_info = self._get_vi_sdk_info()
        health_data["vi_sdk_server"] = vi_sdk_info["server"]
        health_data["vi_sdk_uuid"] = vi_sdk_info["uuid"]

        return health_data

    def _get_vi_sdk_info(self):
        """Extract VI SDK information"""
        return {
            "server": self.content.about.apiVersion or "",
            "uuid": self.content.about.instanceUuid or "",
        }
