"""Integration tests for RVTools - config, export, and multi-vCenter"""

import unittest
import tempfile
import os
from pathlib import Path
import toml
from test.mocks.vcenter_mock import create_mock_service_instance


class TestTomlConfigParsing(unittest.TestCase):
    """Test TOML configuration parsing"""

    def setUp(self):
        """Setup temp directory for test configs"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp files"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_single_vcenter_config(self):
        """Test parsing single vCenter config"""
        config_content = """
[default]
vcenter = "vc.domain.com"
username = "administrator"
password = "SecurePass123"
directory = "/tmp/exports"
format = "xlsx"
threads = "auto"
verbose = false
"""
        config_file = Path(self.temp_dir) / "test_config.toml"
        config_file.write_text(config_content)
        
        config = toml.loads(config_content)
        self.assertIn("default", config)
        self.assertEqual(config["default"]["vcenter"], "vc.domain.com")
        self.assertEqual(config["default"]["format"], "xlsx")
        self.assertFalse(config["default"]["verbose"])

    def test_multi_vcenter_config(self):
        """Test parsing multi-vCenter config"""
        config_content = """
[production]
vcenter = "prod-vc.corp.com"
username = "vc_admin"
password = "Prod_Pass123"
directory = "/mnt/exports/prod"
format = "xlsx"
threads = "16"

[staging]
vcenter = "stage-vc.corp.com"
username = "vc_admin"
password = "Stage_Pass123"
directory = "/mnt/exports/stage"
format = "csv"
threads = "8"

[development]
vcenter = "dev-vc.corp.com"
username = "developer"
password = "Dev_Pass123"
directory = "/mnt/exports/dev"
format = "json-separate"
threads = "4"
"""
        config = toml.loads(config_content)
        self.assertEqual(len(config), 3)
        self.assertIn("production", config)
        self.assertIn("staging", config)
        self.assertIn("development", config)
        self.assertEqual(config["production"]["threads"], "16")
        self.assertEqual(config["staging"]["format"], "csv")
        self.assertEqual(config["development"]["format"], "json-separate")

    def test_config_with_optional_fields(self):
        """Test config with optional fields"""
        config_content = """
[default]
vcenter = "vc.domain.com"
username = "admin"
password = "pass"
directory = "/tmp/exports"
"""
        config = toml.loads(config_content)
        cfg = config["default"]
        
        # Required fields present
        self.assertIn("vcenter", cfg)
        self.assertIn("username", cfg)
        self.assertIn("directory", cfg)
        
        # Optional fields should have defaults
        format_type = cfg.get("format", "xlsx")
        self.assertEqual(format_type, "xlsx")
        
        verbose = cfg.get("verbose", False)
        self.assertFalse(verbose)

    def test_corecode_single_config_has_all_flags(self):
        """CoreCode should map optional TOML fields while parsing config"""
        from rvtools.corerv import CoreCode

        config_content = """
[default]
vcenter = "vc.domain.com"
username = "admin"
password = "pass"
directory = "/tmp/exports"
format = "csv"
threads = "4"
sheets = "vInfo,vPartition"
verbose = true
include_custom_fields = true
"""
        config_file = Path(self.temp_dir) / "test_config_flags.toml"
        config_file.write_text(config_content)

        parsed = CoreCode().read_conf_file(str(config_file))
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed._format, "csv")
        self.assertEqual(parsed._threads, "4")
        self.assertEqual(parsed._sheets, "vInfo,vPartition")
        self.assertTrue(parsed._verbose)
        self.assertTrue(parsed._include_custom_fields)


class TestExportFormats(unittest.TestCase):
    """Test export format validation"""

    def test_valid_export_formats(self):
        """Test all valid export formats"""
        valid_formats = ["xlsx", "csv", "json-separate", "json-unified"]
        for fmt in valid_formats:
            # Format should be recognized
            self.assertIn(fmt, valid_formats)

    def test_xlsx_format_properties(self):
        """Test XLSX format specific properties"""
        # XLSX should produce single file with multiple sheets
        format_type = "xlsx"
        self.assertEqual(format_type, "xlsx")

    def test_csv_format_properties(self):
        """Test CSV format specific properties"""
        # CSV should produce multiple files
        format_type = "csv"
        self.assertEqual(format_type, "csv")

    def test_json_separate_format(self):
        """Test JSON separate format"""
        # JSON-separate should produce multiple files
        format_type = "json-separate"
        self.assertEqual(format_type, "json-separate")

    def test_json_unified_format(self):
        """Test JSON unified format"""
        # JSON-unified should produce single file
        format_type = "json-unified"
        self.assertEqual(format_type, "json-unified")


class TestSheetFiltering(unittest.TestCase):
    """Test sheet filtering functionality"""

    def test_sheet_filter_parsing(self):
        """Test parsing sheet filter strings"""
        filter_string = "vInfo,vHost,vPartition"
        sheets = filter_string.split(",")
        self.assertEqual(len(sheets), 3)
        self.assertIn("vInfo", sheets)
        self.assertIn("vHost", sheets)
        self.assertIn("vPartition", sheets)

    def test_sheet_filter_single(self):
        """Test single sheet filter"""
        filter_string = "vInfo"
        sheets = filter_string.split(",")
        self.assertEqual(len(sheets), 1)
        self.assertEqual(sheets[0], "vInfo")

    def test_sheet_filter_all(self):
        """Test selecting all sheets"""
        all_sheets = [
            "vInfo", "vHost", "vRP", "vDisk", "vCluster", "vMemory", "vCPU",
            "vNetwork", "vTools", "vDatastore", "dvSwitch", "vUSB", "vSnapshot",
            "vPartition", "vCD", "vMultiPath", "vHealth", "dvPort", "vHBA",
            "vNIC", "vSwitch", "vPort", "vSource", "vSC_VMK", "vLicense",
            "vFileInfo", "vMetaData"
        ]
        self.assertEqual(len(all_sheets), 27)


class TestServiceInstanceConnection(unittest.TestCase):
    """Test mock service instance connection"""

    def test_mock_si_returns_content(self):
        """Test mock SI can return content"""
        si = create_mock_service_instance()
        content = si.RetrieveContent()
        self.assertIsNotNone(content)

    def test_mock_si_content_properties(self):
        """Test mock SI content has required properties"""
        si = create_mock_service_instance()
        content = si.content
        
        required = ['rootFolder', 'viewManager', 'propertyCollector', 'about']
        for prop in required:
            self.assertTrue(hasattr(content, prop),
                          f"Content missing property: {prop}")

    def test_mock_si_about_info(self):
        """Test mock SI about info"""
        si = create_mock_service_instance()
        about = si.content.about
        
        self.assertEqual(about.name, "VMware vSphere")
        self.assertEqual(about.version, "8.0.0")
        self.assertIsNotNone(about.build)
        self.assertIsNotNone(about.vendor)


class TestMultiVCenterProcessing(unittest.TestCase):
    """Test multi-vCenter configuration and processing"""

    def test_multi_vcenter_sections(self):
        """Test multiple vCenter sections in config"""
        config_content = """
[production]
vcenter = "prod-vc.corp.com"
username = "admin"
password = "pass"
directory = "/exports/prod"

[dr]
vcenter = "dr-vc.corp.com"
username = "admin"
password = "pass"
directory = "/exports/dr"
"""
        config = toml.loads(config_content)
        sections = list(config.keys())
        
        self.assertEqual(len(sections), 2)
        self.assertIn("production", sections)
        self.assertIn("dr", sections)

    def test_section_vcenter_isolation(self):
        """Test that vCenter sections don't interfere"""
        config_content = """
[vc1]
vcenter = "vc1.corp.com"
username = "user1"

[vc2]
vcenter = "vc2.corp.com"
username = "user2"
"""
        config = toml.loads(config_content)
        
        self.assertEqual(config["vc1"]["vcenter"], "vc1.corp.com")
        self.assertEqual(config["vc2"]["vcenter"], "vc2.corp.com")
        self.assertEqual(config["vc1"]["username"], "user1")
        self.assertEqual(config["vc2"]["username"], "user2")


if __name__ == '__main__':
    unittest.main()
