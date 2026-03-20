"""Module to read the conf file / vcenter, username and password"""

import os
import sys
import logging

try:
    import tomllib
except ImportError:
    import tomli as tomllib

logger = logging.getLogger("rvtools")


class CoreCode(object):
    """Main Class *CoreCode* responsible for read the conf file feature"""

    def read_conf_file(self):
        """Read single vCenter config from TOML file (legacy support)"""
        home_area = os.path.expanduser("~")
        toml_path = os.path.join(home_area, ".rvtools.toml")

        try:
            with open(toml_path, "rb") as f:
                config = tomllib.load(f)
            
            # Try to get default section or first available
            if "default" in config:
                section = config["default"]
            elif "vcenter" in config and isinstance(config["vcenter"], str):
                # Legacy format: top-level keys
                section = config
            else:
                # Get first section
                sections = [v for v in config.values() if isinstance(v, dict)]
                if not sections:
                    logger.error("No valid configuration found in ~/.rvtools.toml")
                    return None
                section = sections[0]
            
            # Validate required fields
            if not all(k in section for k in ["vcenter", "username", "password", "directory"]):
                logger.error("Missing required fields in config: vcenter, username, password, directory")
                return None
            
            # Create object from config
            return self._config_to_object(section)
        
        except FileNotFoundError:
            return self._create_default_config()
        except Exception as e:
            logger.error(f"Error reading TOML config: {e}")
            return None

    def read_conf_file_multi(self):
        """Read multi-vCenter config file (TOML format)
        
        Supports format:
        [vcenter1]
        vcenter = "host1.domain.com"
        username = "user1"
        password = "pass1"
        directory = "/tmp"
        format = "xlsx"
        threads = "8"
        
        [vcenter2]
        vcenter = "host2.domain.com"
        username = "user2"
        password = "pass2"
        directory = "/tmp"
        
        Returns: List of config dicts, or None if file not found or invalid
        """
        home_area = os.path.expanduser("~")
        toml_path = os.path.join(home_area, ".rvtools.toml")

        try:
            with open(toml_path, "rb") as f:
                config = tomllib.load(f)
            
            configs = []
            
            # Check if this is a multi-vcenter config or legacy format
            if "default" in config and isinstance(config["default"], dict):
                # Multi-vCenter format with [default] and other [name] sections
                for section_name, section_config in config.items():
                    if isinstance(section_config, dict) and self._validate_config(section_config):
                        section_config["_section_name"] = section_name
                        configs.append(section_config)
            elif "vcenter" in config and isinstance(config["vcenter"], str):
                # Legacy single-vCenter format
                if self._validate_config(config):
                    config["_section_name"] = "default"
                    configs.append(config)
            else:
                # All top-level items should be sections
                for section_name, section_config in config.items():
                    if isinstance(section_config, dict) and self._validate_config(section_config):
                        section_config["_section_name"] = section_name
                        configs.append(section_config)
            
            return configs if configs else None
        
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error reading multi-vCenter TOML config: {e}")
            return None

    def _validate_config(self, config):
        """Check if config has minimum required fields"""
        return all(k in config for k in ["vcenter", "username", "password", "directory"])

    def _config_to_object(self, config_dict):
        """Convert config dict to CoreCode object"""
        obj = CoreCode()
        obj._vcenter = config_dict.get("vcenter", "<fqdn>")
        obj._username = config_dict.get("username", "")
        obj._password = config_dict.get("password", "")
        obj._directory = config_dict.get("directory", "")
        obj._format = config_dict.get("format", "xlsx")
        obj._threads = config_dict.get("threads", "auto")
        obj._verbose = config_dict.get("verbose", "false")
        return obj

    def _create_default_config(self):
        """Create default config file"""
        home_area = os.path.expanduser("~")
        toml_path = os.path.join(home_area, ".rvtools.toml")
        
        default_template = '''# RVTools Configuration File (TOML format)

# Default vCenter configuration
[default]
vcenter = "<fqdn>"
username = "<vcenter username>"
password = "<password>"
directory = "<directory>"
format = "xlsx"
threads = "auto"
verbose = false

# Additional vCenter examples (uncomment to use):
# [production]
# vcenter = "prod-vc.domain.com"
# username = "admin"
# password = "password"
# directory = "/tmp/prod"
# format = "xlsx"
# threads = "16"

# [development]
# vcenter = "dev-vc.domain.com"
# username = "admin"
# password = "password"
# directory = "/tmp/dev"
# format = "csv"
# threads = "4"
'''
        
        try:
            with open(toml_path, "w") as f:
                f.write(default_template)
            
            print("RVTools configuration file created at ~/.rvtools.toml")
            print("Please update with your vCenter details:")
            print("-" * 50)
            print(default_template)
            print("-" * 50)
            logger.info("Default config created at ~/.rvtools.toml")
            return None
        
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
            return None

