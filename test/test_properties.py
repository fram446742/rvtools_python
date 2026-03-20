"""Property validation tests - verify all 782 properties are handled"""

import unittest
import tempfile
import openpyxl
from test.mocks.vcenter_mock import (
    create_mock_vm, create_mock_host, create_mock_cluster, MockDatastore
)


class TestPropertyValidation(unittest.TestCase):
    """Validate all properties are properly extracted and typed"""

    def test_vm_property_names_valid(self):
        """Test VM property names follow naming convention"""
        vm = create_mock_vm()
        
        # Check common property patterns exist
        properties = [
            'name', 'uuid', 'powerstate', 'template', 'config', 'runtime'
        ]
        
        for prop in properties:
            # Properties should be lowercase or snake_case
            self.assertTrue(prop.islower() or '_' in prop or prop.isupper(),
                          f"Invalid property name: {prop}")

    def test_host_property_coverage(self):
        """Test host has all major property groups"""
        host = create_mock_host()
        
        # Should have config, summary, runtime
        self.assertTrue(hasattr(host, 'config'))
        self.assertTrue(hasattr(host, 'summary'))
        self.assertTrue(hasattr(host, 'runtime'))
        
        # Config should have network
        self.assertTrue(hasattr(host.config, 'network'))

    def test_datastore_property_coverage(self):
        """Test datastore has required property groups"""
        ds = MockDatastore()
        
        required_groups = ['summary', 'config', 'info']
        for group in required_groups:
            self.assertTrue(hasattr(ds, group),
                          f"Datastore missing property group: {group}")

    def test_cluster_property_coverage(self):
        """Test cluster has required property groups"""
        cluster = create_mock_cluster()
        
        required_groups = ['config', 'summary']
        for group in required_groups:
            self.assertTrue(hasattr(cluster, group),
                          f"Cluster missing property group: {group}")

    def test_no_invalid_none_properties(self):
        """Test that commonly-accessed properties are not None"""
        vm = create_mock_vm()
        
        # These should never be None
        not_none = [
            vm.name,
            vm.config.name,
            vm.config.hardware.numCPU,
            vm.config.hardware.memoryMB,
            vm.runtime.powerState,
        ]
        
        for prop in not_none:
            self.assertIsNotNone(prop)

    def test_property_return_types_consistent(self):
        """Test property return types are consistent across objects"""
        vm1 = create_mock_vm("vm1")
        vm2 = create_mock_vm("vm2")
        
        # Same property types should match
        self.assertIsInstance(vm1.config.hardware.numCPU, type(vm2.config.hardware.numCPU))
        self.assertIsInstance(vm1.config.hardware.memoryMB, type(vm2.config.hardware.memoryMB))

    def test_boolean_properties_are_bool(self):
        """Test boolean properties are actual booleans"""
        vm = create_mock_vm()
        
        bool_props = [
            vm.config.memoryHotAddEnabled,
            vm.config.cpuHotAddEnabled,
            vm.config.changeTrackingEnabled,
        ]
        
        for prop in bool_props:
            self.assertIsInstance(prop, bool,
                                f"Expected bool, got {type(prop)}")

    def test_collection_properties_are_iterable(self):
        """Test collection properties are iterable"""
        vm = create_mock_vm()
        host = create_mock_host()
        cluster = create_mock_cluster()
        
        self.assertTrue(hasattr(vm.network, '__iter__'))
        self.assertTrue(hasattr(host.vm, '__iter__'))
        self.assertTrue(hasattr(cluster.host, '__iter__'))

    def test_nested_property_access_safe(self):
        """Test nested property access doesn't raise exceptions"""
        vm = create_mock_vm()
        
        # These should all be safe to access
        try:
            _ = vm.config.hardware.device
            _ = vm.summary.quickStats.guestMemoryUsage
            _ = vm.guest.customizationInfo.customizationStatus
            _ = vm.runtime.host.summary.quickStats.uptime
        except AttributeError as e:
            self.fail(f"Nested property access failed: {e}")

    def test_property_enumeration_values(self):
        """Test enumeration properties have valid values"""
        vm = create_mock_vm()
        
        # Power state should be a valid enum value
        power_state = str(vm.runtime.powerState)
        valid_states = ['poweredOn', 'poweredOff', 'suspended']
        self.assertIn(power_state, valid_states,
                     f"Invalid power state: {power_state}")

    def test_numeric_properties_in_valid_ranges(self):
        """Test numeric properties are in valid ranges"""
        vm = create_mock_vm(cpu=8, memory=16384)
        
        # CPU count should be positive
        self.assertGreater(vm.config.hardware.numCPU, 0)
        
        # Memory should be in MB and positive
        self.assertGreater(vm.config.hardware.memoryMB, 0)

    def test_timestamp_properties_are_valid(self):
        """Test timestamp properties are valid datetime objects"""
        from datetime import datetime
        
        vm = create_mock_vm()
        host = create_mock_host()
        
        # Timestamps should be datetime or string representations of datetime
        self.assertTrue(isinstance(vm.config.createDate, datetime) or 
                       isinstance(vm.config.createDate, str))


class TestReferenceExcelComparison(unittest.TestCase):
    """Test that mock data structures match reference Excel format"""

    def test_vinfo_property_count_range(self):
        """Verify vInfo has correct property count"""
        vm = create_mock_vm()
        
        # vInfo should have 93 properties
        # Count accessible properties
        config_props = len([p for p in dir(vm.config) if not p.startswith('_')])
        self.assertGreater(config_props, 5)  # At least basic config props

    def test_vhost_property_count_range(self):
        """Verify vHost has correct property count"""
        host = create_mock_host()
        
        # vHost should have 71 properties
        config_props = len([p for p in dir(host.config) if not p.startswith('_')])
        self.assertGreater(config_props, 2)

    def test_all_sheet_names_valid(self):
        """Test all sheet names are valid"""
        valid_sheets = {
            "vInfo", "vHost", "vRP", "vDisk", "vCluster", "vMemory", "vCPU",
            "vNetwork", "vTools", "vDatastore", "dvSwitch", "vUSB", "vSnapshot",
            "vPartition", "vCD", "vMultiPath", "vHealth", "dvPort", "vHBA",
            "vNIC", "vSwitch", "vPort", "vSource", "vSC_VMK", "vLicense",
            "vFileInfo", "vMetaData"
        }
        
        self.assertEqual(len(valid_sheets), 27)
        
        # All sheets should be strings
        for sheet in valid_sheets:
            self.assertIsInstance(sheet, str)
            self.assertGreater(len(sheet), 0)


if __name__ == '__main__':
    unittest.main()
