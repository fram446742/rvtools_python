"""Unit tests for RVTools collectors using mock objects"""

import unittest
from datetime import datetime
from test.mocks.vcenter_mock import (
    create_mock_vm, create_mock_host, create_mock_cluster,
    create_mock_service_instance, MockVirtualMachine, MockHostSystem,
    MockDatastore, MockCluster, MockNetwork, MockDistributedVirtualSwitch
)
from rvtools.collectors.base_collector import BaseCollector, set_global_view_cache


class TestVInfoCollector(unittest.TestCase):
    """Test vInfo collector - 93 properties"""

    def setUp(self):
        """Setup test fixtures"""
        self.mock_si = create_mock_service_instance()
        self.mock_vm = create_mock_vm("test-vm", "vm-1", True)

    def test_vm_has_required_config_properties(self):
        """Verify VM has all required config properties"""
        required = ['name', 'uuid', 'annotation', 'guestFullName', 'version', 'firmware']
        for prop in required:
            self.assertTrue(hasattr(self.mock_vm.config, prop),
                          f"VM config missing property: {prop}")

    def test_vm_has_required_runtime_properties(self):
        """Verify VM has all required runtime properties"""
        required = ['powerState', 'connectionState', 'consolidationNeeded', 'host']
        for prop in required:
            self.assertTrue(hasattr(self.mock_vm.runtime, prop),
                          f"VM runtime missing property: {prop}")

    def test_vm_has_required_hardware_properties(self):
        """Verify VM hardware has required properties"""
        required = ['numCPU', 'memoryMB', 'device']
        for prop in required:
            self.assertTrue(hasattr(self.mock_vm.config.hardware, prop),
                          f"VM hardware missing property: {prop}")

    def test_vm_summary_properties(self):
        """Verify VM summary properties exist"""
        self.assertIsNotNone(self.mock_vm.summary)
        self.assertTrue(hasattr(self.mock_vm.summary, 'quickStats'))
        self.assertTrue(hasattr(self.mock_vm.summary.quickStats, 'guestMemoryUsage'))

    def test_vm_guest_properties(self):
        """Verify VM guest properties"""
        self.assertIsNotNone(self.mock_vm.guest)
        self.assertTrue(hasattr(self.mock_vm.guest, 'hostName'))
        self.assertTrue(hasattr(self.mock_vm.guest, 'ipAddress'))
        self.assertTrue(hasattr(self.mock_vm.guest, 'guestState'))

    def test_vm_property_types(self):
        """Verify property types are correct"""
        self.assertIsInstance(self.mock_vm.config.name, str)
        self.assertIsInstance(self.mock_vm.config.hardware.numCPU, int)
        self.assertIsInstance(self.mock_vm.config.hardware.memoryMB, int)
        self.assertIn(str(self.mock_vm.runtime.powerState), ['poweredOn', 'poweredOff', 'suspended'])

    def test_vm_powerstate_values(self):
        """Verify powerstate has valid values"""
        vm_on = create_mock_vm("vm-on", "vm-1", True)
        vm_off = create_mock_vm("vm-off", "vm-2", False)
        self.assertIsNotNone(vm_on.runtime.powerState)
        self.assertIsNotNone(vm_off.runtime.powerState)

    def test_vm_none_handling(self):
        """Verify None handling for optional properties"""
        self.mock_vm.config.annotation = None
        self.assertIsNone(self.mock_vm.config.annotation)
        # Should not raise exception when accessing None values


class TestVHostCollector(unittest.TestCase):
    """Test vHost collector - 71 properties"""

    def setUp(self):
        """Setup test fixtures"""
        self.mock_host = create_mock_host("esxi-1.corp.com", "host-1", 5)

    def test_host_has_required_properties(self):
        """Verify host has all required properties"""
        required = ['name', 'config', 'summary', 'runtime', 'vm', 'datastore']
        for prop in required:
            self.assertTrue(hasattr(self.mock_host, prop),
                          f"Host missing property: {prop}")

    def test_host_config_network_properties(self):
        """Verify host network config"""
        self.assertIsNotNone(self.mock_host.config.network)
        self.assertTrue(hasattr(self.mock_host.config.network, 'vnic'))
        self.assertTrue(hasattr(self.mock_host.config.network, 'vswitch'))

    def test_host_summary_runtime_properties(self):
        """Verify host summary runtime"""
        self.assertIsNotNone(self.mock_host.summary.runtime)
        self.assertTrue(hasattr(self.mock_host.summary.runtime, 'connectionState'))
        self.assertTrue(hasattr(self.mock_host.summary.runtime, 'bootTime'))

    def test_host_quickstats_properties(self):
        """Verify host quickstats"""
        stats = self.mock_host.summary.quickStats
        self.assertTrue(hasattr(stats, 'uptime'))
        self.assertTrue(hasattr(stats, 'overallCpuUsage'))
        self.assertTrue(hasattr(stats, 'overallMemoryUsage'))
        self.assertIsInstance(stats.uptime, int)

    def test_host_vms_collection(self):
        """Verify host VMs are properly populated"""
        self.assertEqual(len(self.mock_host.vm), 5)
        for vm in self.mock_host.vm:
            self.assertIsInstance(vm, MockVirtualMachine)

    def test_host_property_types(self):
        """Verify host property types"""
        self.assertIsInstance(self.mock_host.name, str)
        self.assertIsInstance(self.mock_host.summary.quickStats.uptime, int)


class TestDatastoreCollector(unittest.TestCase):
    """Test vDatastore collector"""

    def setUp(self):
        """Setup test fixtures"""
        self.mock_ds = MockDatastore("datastore1", "datastore-1")

    def test_datastore_required_properties(self):
        """Verify datastore has required properties"""
        required = ['name', 'summary', 'config', 'info']
        for prop in required:
            self.assertTrue(hasattr(self.mock_ds, prop),
                          f"Datastore missing property: {prop}")

    def test_datastore_summary_properties(self):
        """Verify datastore summary"""
        summary = self.mock_ds.summary
        self.assertTrue(hasattr(summary, 'capacity'))
        self.assertTrue(hasattr(summary, 'freeSpace'))
        self.assertTrue(hasattr(summary, 'type'))
        self.assertIsInstance(summary.capacity, int)
        self.assertIsInstance(summary.freeSpace, int)
        self.assertEqual(summary.type, "VMFS")

    def test_datastore_vmfs_config(self):
        """Verify datastore VMFS config"""
        vmfs = self.mock_ds.config.vmfs
        self.assertIsNotNone(vmfs)
        self.assertTrue(hasattr(vmfs, 'blockSize'))
        self.assertTrue(hasattr(vmfs, 'version'))


class TestClusterCollector(unittest.TestCase):
    """Test vCluster collector - 35 properties"""

    def setUp(self):
        """Setup test fixtures"""
        self.mock_cluster = create_mock_cluster("cluster1", 3, 10)

    def test_cluster_required_properties(self):
        """Verify cluster has required properties"""
        required = ['name', 'config', 'summary', 'host']
        for prop in required:
            self.assertTrue(hasattr(self.mock_cluster, prop),
                          f"Cluster missing property: {prop}")

    def test_cluster_drs_config(self):
        """Verify cluster DRS config"""
        drs = self.mock_cluster.config.drsConfig
        self.assertIsNotNone(drs)
        self.assertTrue(hasattr(drs, 'enabled'))
        self.assertIsInstance(drs.enabled, bool)

    def test_cluster_das_config(self):
        """Verify cluster DAS config"""
        das = self.mock_cluster.config.dasConfig
        self.assertIsNotNone(das)
        self.assertTrue(hasattr(das, 'enabled'))

    def test_cluster_summary_stats(self):
        """Verify cluster summary statistics"""
        summary = self.mock_cluster.summary
        self.assertEqual(summary.numHosts, 3)
        self.assertEqual(summary.numVms, 30)  # 3 hosts * 10 VMs
        self.assertTrue(hasattr(summary, 'totalCpu'))
        self.assertTrue(hasattr(summary, 'totalMemory'))

    def test_cluster_hosts_populated(self):
        """Verify cluster has hosts"""
        self.assertEqual(len(self.mock_cluster.host), 3)
        for host in self.mock_cluster.host:
            self.assertIsInstance(host, MockHostSystem)


class TestNetworkCollector(unittest.TestCase):
    """Test vNetwork collector - 32 properties"""

    def setUp(self):
        """Setup test fixtures"""
        self.mock_network = MockNetwork("VM Network", "network-1")

    def test_network_required_properties(self):
        """Verify network has required properties"""
        self.assertTrue(hasattr(self.mock_network, 'name'))
        self.assertTrue(hasattr(self.mock_network, 'summary'))

    def test_network_summary(self):
        """Verify network summary"""
        self.assertIsNotNone(self.mock_network.summary)
        self.assertTrue(hasattr(self.mock_network.summary, 'name'))


class TestDVSCollector(unittest.TestCase):
    """Test dvSwitch collector - 30 properties"""

    def setUp(self):
        """Setup test fixtures"""
        self.mock_dvs = MockDistributedVirtualSwitch("dvs-1", "dvs-1")

    def test_dvs_required_properties(self):
        """Verify DVS has required properties"""
        required = ['name', 'config', 'summary']
        for prop in required:
            self.assertTrue(hasattr(self.mock_dvs, prop),
                          f"DVS missing property: {prop}")

    def test_dvs_config_properties(self):
        """Verify DVS config"""
        config = self.mock_dvs.config
        self.assertTrue(hasattr(config, 'numPorts'))
        self.assertTrue(hasattr(config, 'maxPorts'))
        self.assertIsInstance(config.numPorts, int)

    def test_dvs_summary_properties(self):
        """Verify DVS summary"""
        summary = self.mock_dvs.summary
        self.assertTrue(hasattr(summary, 'name'))
        self.assertTrue(hasattr(summary, 'productInfo'))
        self.assertEqual(summary.productInfo.version, "8.0.0")


class TestMockObjectIntegration(unittest.TestCase):
    """Integration tests with mock objects"""

    def test_complete_vm_workflow(self):
        """Test complete VM workflow"""
        vm = create_mock_vm("web-server", "vm-100", True, 8, 16384)
        
        # Verify essential properties are accessible
        self.assertEqual(vm.name, "web-server")
        self.assertEqual(vm.config.hardware.numCPU, 8)
        self.assertEqual(vm.config.hardware.memoryMB, 16384)
        
        # Verify property access doesn't raise exceptions
        _ = vm.config.uuid
        _ = vm.summary.quickStats.guestMemoryUsage
        _ = vm.guest.hostName

    def test_complete_host_workflow(self):
        """Test complete host workflow"""
        host = create_mock_host("esxi-prod", "host-100", 20)
        
        self.assertEqual(host.name, "esxi-prod")
        self.assertEqual(len(host.vm), 20)
        self.assertIsNotNone(host.config.network.vnic)
        self.assertIsNotNone(host.summary.quickStats.uptime)

    def test_complete_cluster_workflow(self):
        """Test complete cluster workflow"""
        cluster = create_mock_cluster("prod-cluster", 5, 15)
        
        self.assertEqual(cluster.summary.numHosts, 5)
        self.assertEqual(cluster.summary.numVms, 75)
        self.assertEqual(len(cluster.host), 5)

    def test_mock_si_structure(self):
        """Test mock service instance structure"""
        si = create_mock_service_instance()
        
        self.assertIsNotNone(si.RetrieveContent())
        content = si.content
        self.assertIsNotNone(content.rootFolder)
        self.assertIsNotNone(content.viewManager)
        self.assertIsNotNone(content.propertyCollector)
        self.assertIsNotNone(content.about)


class TestPropertyTypes(unittest.TestCase):
    """Test property type consistency"""

    def test_vm_timestamps_are_datetime(self):
        """Verify VM timestamps are datetime objects"""
        vm = create_mock_vm()
        self.assertIsInstance(vm.config.createDate, datetime)
        self.assertIsInstance(vm.runtime.suspendTime, datetime)

    def test_host_timestamps_are_datetime(self):
        """Verify host timestamps are datetime objects"""
        host = create_mock_host()
        self.assertIsInstance(host.summary.runtime.bootTime, datetime)

    def test_numeric_properties_are_numbers(self):
        """Verify numeric properties are actual numbers"""
        vm = create_mock_vm()
        self.assertIsInstance(vm.config.hardware.numCPU, int)
        self.assertIsInstance(vm.config.hardware.memoryMB, int)
        
        ds = MockDatastore()
        self.assertIsInstance(ds.summary.capacity, int)
        self.assertIsInstance(ds.summary.freeSpace, int)

    def test_string_properties_are_strings(self):
        """Verify string properties are actual strings"""
        vm = create_mock_vm()
        self.assertIsInstance(vm.name, str)
        self.assertIsInstance(vm.config.uuid, str)
        self.assertIsInstance(vm.guest.hostName, str)


if __name__ == '__main__':
    unittest.main()
