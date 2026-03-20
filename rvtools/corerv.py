"""Module to read the conf file / vcenter, username and password"""

import re
import os


class CoreCode(object):
    """Main Class *CoreCode* responsible for read the conf file feature"""

    def read_conf_file(self):
        """Definition to read the conf file rvtools.conf (single config)"""
        home_area = os.path.expanduser("~")

        try:
            fp_conf_file = open(home_area + "/.rvtools.conf", "r")
            for line in fp_conf_file:
                if re.search("^vcenter", line):
                    self._vcenter = re.split("=", re.search("^vcenter", line).string)[
                        1
                    ].strip()
                if re.search("^username", line):
                    self._username = re.split("=", re.search("^username", line).string)[
                        1
                    ].strip()
                if re.search("^password", line):
                    self._password = re.split("=", re.search("^password", line).string)[
                        1
                    ].strip()
                if re.search("^directory", line):
                    self._directory = re.split(
                        "=", re.search("^directory", line).string
                    )[1].strip()
                if re.search("^format", line):
                    self._format = re.split("=", re.search("^format", line).string)[
                        1
                    ].strip()
                if re.search("^threads", line):
                    self._threads = re.split("=", re.search("^threads", line).string)[
                        1
                    ].strip()
                if re.search("^verbose", line):
                    self._verbose = re.split("=", re.search("^verbose", line).string)[
                        1
                    ].strip()

            return self
        except FileNotFoundError:
            print(
                "There isn't the conf file on ~/.rvtools.conf, creating a new one now"
            )
            print("according to the example below:")
            print("-----------------------")
            print("vcenter=<fqdn>")
            print("username=<vcenter username>")
            print("password=<password>")
            print("directory=<directory>")
            print("-----------------------")
            print("")
            print("Please update the info if you would like to persist the credentials")

            template_conf_file = open(home_area + "/.rvtools.conf", "w+")
            print("vcenter=<fqdn>", file=template_conf_file)
            print("username=<vcenter username>", file=template_conf_file)
            print("password=<password>", file=template_conf_file)
            print("directory=<directory>", file=template_conf_file)
            print("format=xlsx", file=template_conf_file)
            print("threads=auto", file=template_conf_file)
            print("verbose=false", file=template_conf_file)
            template_conf_file.close()

    def read_conf_file_multi(self):
        """Read multi-vCenter config file with TOML-like sections
        
        Supports format:
        [vcenter1]
        vcenter=host1.domain.com
        username=user1
        password=pass1
        directory=/tmp
        
        [vcenter2]
        vcenter=host2.domain.com
        username=user2
        password=pass2
        directory=/tmp
        
        Lines starting with # are treated as comments
        """
        home_area = os.path.expanduser("~")
        configs = []
        current_section = {}

        try:
            with open(home_area + "/.rvtools.conf", "r") as fp_conf_file:
                for line in fp_conf_file:
                    # Strip whitespace and skip empty lines
                    line = line.strip()
                    
                    # Skip comments
                    if line.startswith("#") or line == "":
                        continue
                    
                    # Detect section headers [name]
                    section_match = re.match(r"^\[([^\]]+)\]$", line)
                    if section_match:
                        # Save previous section if it has required fields
                        if current_section and self._validate_config(current_section):
                            configs.append(current_section)
                        current_section = {"_section_name": section_match.group(1)}
                        continue
                    
                    # Parse key=value pairs
                    kv_match = re.match(r"^([^=]+)=(.*)$", line)
                    if kv_match and current_section is not None:
                        key = kv_match.group(1).strip()
                        value = kv_match.group(2).strip()
                        current_section[key] = value
                
                # Don't forget last section
                if current_section and self._validate_config(current_section):
                    configs.append(current_section)
            
            return configs if configs else None
        except FileNotFoundError:
            return None

    def _validate_config(self, config):
        """Check if config has minimum required fields"""
        return all(k in config for k in ["vcenter", "username", "password", "directory"])

    def config_to_object(self, config_dict):
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
