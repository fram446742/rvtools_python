"""Performance benchmark tests for RVTools collectors"""

import unittest
import time
from test.mocks.vcenter_mock import (
    create_mock_vm, create_mock_host, create_mock_cluster, MockDatastore
)


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks for collector operations"""

    def test_vm_creation_performance(self):
        """Test VM object creation performance"""
        start = time.time()
        vms = [create_mock_vm(f"vm-{i}", f"vm-{i}") for i in range(100)]
        duration = time.time() - start
        
        # Should create 100 VMs in reasonable time
        self.assertLess(duration, 1.0, f"VM creation too slow: {duration}s")
        self.assertEqual(len(vms), 100)

    def test_host_creation_with_vms_performance(self):
        """Test host creation with VMs performance"""
        start = time.time()
        hosts = [create_mock_host(f"esxi-{i}", f"host-{i}", 20) for i in range(5)]
        duration = time.time() - start
        
        # Should create 5 hosts with 20 VMs each in reasonable time
        self.assertLess(duration, 1.0, f"Host creation too slow: {duration}s")
        self.assertEqual(len(hosts), 5)
        self.assertEqual(len(hosts[0].vm), 20)

    def test_cluster_creation_performance(self):
        """Test cluster creation with hosts and VMs"""
        start = time.time()
        cluster = create_mock_cluster("cluster1", 5, 20)
        duration = time.time() - start
        
        # Should create cluster with 5 hosts and 100 VMs in reasonable time
        self.assertLess(duration, 1.0, f"Cluster creation too slow: {duration}s")
        self.assertEqual(cluster.summary.numHosts, 5)
        self.assertEqual(cluster.summary.numVms, 100)

    def test_property_access_performance_single_vm(self):
        """Test property access performance"""
        vm = create_mock_vm()
        
        start = time.time()
        for _ in range(1000):
            _ = vm.name
            _ = vm.config.hardware.numCPU
            _ = vm.runtime.powerState
            _ = vm.summary.quickStats.guestMemoryUsage
        duration = time.time() - start
        
        # 1000 property accesses should be very fast
        self.assertLess(duration, 0.1, f"Property access too slow: {duration}s")

    def test_host_property_access_performance(self):
        """Test host property access performance"""
        host = create_mock_host(num_vms=50)
        
        start = time.time()
        for _ in range(100):
            _ = host.name
            _ = host.summary.quickStats.uptime
            _ = len(host.vm)
            for vm in host.vm:
                _ = vm.name
        duration = time.time() - start
        
        # Should complete quickly
        self.assertLess(duration, 0.5, f"Host iteration too slow: {duration}s")

    def test_cluster_iteration_performance(self):
        """Test cluster member iteration performance"""
        cluster = create_mock_cluster("cluster1", 5, 20)
        
        start = time.time()
        for _ in range(10):
            for host in cluster.host:
                for vm in host.vm:
                    _ = vm.name
        duration = time.time() - start
        
        # Should iterate through 5 hosts and 100 VMs in reasonable time
        self.assertLess(duration, 0.5, f"Cluster iteration too slow: {duration}s")

    def test_large_scale_vm_operations(self):
        """Test operations with large number of VMs"""
        vms = [create_mock_vm(f"vm-{i}", f"vm-{i}") for i in range(500)]
        
        start = time.time()
        cpu_total = sum(vm.config.hardware.numCPU for vm in vms)
        mem_total = sum(vm.config.hardware.memoryMB for vm in vms)
        duration = time.time() - start
        
        # Should process 500 VMs quickly
        self.assertLess(duration, 0.2, f"Large scale operation too slow: {duration}s")
        self.assertGreater(cpu_total, 0)
        self.assertGreater(mem_total, 0)

    def test_nested_property_access_performance(self):
        """Test nested property access performance"""
        vms = [create_mock_vm() for _ in range(10)]
        hosts = [create_mock_host(num_vms=len(vms)) for _ in range(3)]
        cluster = create_mock_cluster()
        cluster.host = hosts
        
        start = time.time()
        for _ in range(100):
            for host in cluster.host:
                _ = host.summary.quickStats.uptime
                for vm in host.vm:
                    _ = vm.summary.quickStats.guestMemoryUsage
        duration = time.time() - start
        
        # Should handle nested iteration quickly
        self.assertLess(duration, 1.0, f"Nested access too slow: {duration}s")

    def test_mock_datastore_operations(self):
        """Test datastore mock operations"""
        datastores = [MockDatastore(f"ds-{i}", f"ds-{i}") for i in range(50)]
        
        start = time.time()
        for ds in datastores:
            _ = ds.summary.capacity
            _ = ds.summary.freeSpace
            _ = ds.summary.type
        duration = time.time() - start
        
        # Should process 50 datastores quickly
        self.assertLess(duration, 0.1, f"Datastore operations too slow: {duration}s")


class TestMockCreationThroughput(unittest.TestCase):
    """Test mock object creation throughput"""

    def test_vm_creation_throughput_per_second(self):
        """Test VMs created per second"""
        start = time.time()
        vms = [create_mock_vm(f"vm-{i}") for i in range(1000)]
        duration = time.time() - start
        
        throughput = 1000 / duration
        self.assertGreater(throughput, 100, f"Too slow: {throughput} VMs/sec")

    def test_host_creation_throughput_per_second(self):
        """Test hosts with VMs created per second"""
        start = time.time()
        hosts = [create_mock_host(f"h-{i}", num_vms=10) for i in range(100)]
        duration = time.time() - start
        
        throughput = 100 / duration
        self.assertGreater(throughput, 10, f"Too slow: {throughput} hosts/sec")

    def test_property_retrieval_throughput(self):
        """Test property retrievals per second"""
        vm = create_mock_vm()
        
        start = time.time()
        count = 0
        for _ in range(100):
            for _ in range(100):
                _ = vm.config.hardware.numCPU
                _ = vm.runtime.powerState
                _ = vm.guest.hostName
                count += 3
        duration = time.time() - start
        
        throughput = count / duration
        self.assertGreater(throughput, 10000, f"Too slow: {throughput} properties/sec")


if __name__ == '__main__':
    unittest.main()
