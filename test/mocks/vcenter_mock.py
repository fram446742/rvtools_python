"""Realistic mock objects for vCenter components - enables testing without live vCenter connection"""

from datetime import datetime, timedelta
from pyVmomi import vim


class MockConfig:
    """Mock config object"""
    def __init__(self):
        self.name = "test-vm-1"
        self.uuid = "550e8400-e29b-41d4-a716-446655440000"
        self.annotation = "Test VM annotation"
        self.guestFullName = "Ubuntu Linux 22.04 (64-bit)"
        self.version = "vmx-19"
        self.firmware = "bios"
        self.changeVersion = "2026-03-20T12:00:00Z"
        self.createDate = datetime.now()
        self.bootOptions = MockBootOptions()
        self.files = MockFiles()
        self.hardware = MockHardware()
        self.latencySensitivity = MockLatencySensitivity()
        self.memoryHotAddEnabled = True
        self.cpuHotAddEnabled = True
        self.cpuHotRemoveEnabled = False
        self.changeTrackingEnabled = True
        self.ftInfo = None
        self.dasVmProtection = MockDasVmProtection()


class MockBootOptions:
    """Mock boot options"""
    def __init__(self):
        self.bootDelay = 0
        self.bootRetryDelay = 1000
        self.bootRetryEnabled = False
        self.rebootPowerOff = False
        self.efiSecureBootEnabled = False


class MockFiles:
    """Mock VM files"""
    def __init__(self):
        self.vmPathName = "[datastore1] test-vm-1/test-vm-1.vmx"
        self.logDirectory = "[datastore1] test-vm-1"
        self.snapshotDirectory = "[datastore1] test-vm-1"
        self.suspendDirectory = "[datastore1] test-vm-1"


class MockHardware:
    """Mock hardware config"""
    def __init__(self):
        self.numCPU = 4
        self.numCoresPerSocket = 2
        self.memoryMB = 8192
        self.device = [MockVirtualDisk(), MockVirtualDisk()]
        self.version = "vmx-19"


class MockVirtualDisk:
    """Mock virtual disk"""
    def __init__(self, capacity_kb=104857600):
        self.capacityInKB = capacity_kb
        self.key = 2000
        self.controllerKey = 1000
        self.unitNumber = 0


class MockLatencySensitivity:
    """Mock latency sensitivity"""
    def __init__(self):
        self.level = "normal"


class MockDasVmProtection:
    """Mock DAS VM protection"""
    def __init__(self):
        self.vmToolsMonitoringSettings = MockVMToolsMonitoringSettings()
        self.restartPriority = "medium"


class MockVMToolsMonitoringSettings:
    """Mock VM tools monitoring"""
    def __init__(self):
        self.enabled = True
        self.vmMonitoring = "vmMonitoringOnly"


class MockRuntime:
    """Mock runtime info"""
    def __init__(self):
        self.powerState = vim.VirtualMachine.PowerState.poweredOn
        self.connectionState = vim.VirtualMachine.ConnectionState.connected
        self.consolidationNeeded = False
        self.host = MockHostSystem()
        self.suspendTime = datetime.now() - timedelta(days=30)
        self.faultToleranceState = "notConfigured"


class MockSummary:
    """Mock summary"""
    def __init__(self):
        self.config = MockSummaryConfig()
        self.quickStats = MockQuickStats()
        self.runtime = MockSummaryRuntime()


class MockSummaryConfig:
    """Mock summary config"""
    def __init__(self):
        self.name = "test-vm-1"
        self.vmPathName = "[datastore1] test-vm-1/test-vm-1.vmx"


class MockQuickStats:
    """Mock quick stats"""
    def __init__(self):
        self.hostMemoryUsage = 1024
        self.guestMemoryUsage = 2048
        self.overallCpuUsage = 250
        self.overallMemoryUsage = 2048
        self.uncommittedStorage = 1073741824


class MockSummaryRuntime:
    """Mock summary runtime"""
    def __init__(self):
        self.powerState = vim.VirtualMachine.PowerState.poweredOn
        self.connectionState = vim.VirtualMachine.ConnectionState.connected


class MockGuest:
    """Mock guest info"""
    def __init__(self):
        self.guestState = "running"
        self.hostName = "test-vm-1.domain.com"
        self.ipAddress = "192.168.1.100"
        self.customizationInfo = MockCustomizationInfo()


class MockCustomizationInfo:
    """Mock customization info"""
    def __init__(self):
        self.customizationStatus = "DONE"


class MockVirtualMachine:
    """Realistic mock VM object matching pyVmomi VirtualMachine structure"""

    def __init__(self, name="test-vm-1", moId="vm-1", powered_on=True, custom_values=None):
        self._moId = moId
        self.name = name
        self.config = MockConfig()
        self.config.name = name
        self.runtime = MockRuntime()
        if not powered_on:
            self.runtime.powerState = vim.VirtualMachine.PowerState.poweredOff
        self.summary = MockSummary()
        self.summary.config.name = name
        self.guest = MockGuest()
        self.guest.hostName = f"{name}.domain.com"
        self.guestHeartbeatStatus = "green"
        self.configStatus = "green"
        self.resourcePool = None
        self.parent = MockFolder()
        self.parentVApp = None
        self.network = [MockNetwork()]
        self.layout = MockLayout()
        self.customValue = custom_values or []

    @property
    def _GetMoId(self):
        """Property for backward compatibility"""
        return self._moId


class MockHostSystem:
    """Realistic mock ESXi host object"""

    def __init__(self, name="esxi.corp.com", moId="host-1"):
        self._moId = moId
        self.name = name
        self.config = MockHostConfig()
        self.summary = MockHostSummary()
        self.runtime = MockHostRuntime()
        self.vm = []
        self.datastore = []
        self.network = [MockNetwork()]
        self.configManager = MockConfigManager()
        self.capability = MockCapability()

    @property
    def _GetMoId(self):
        return self._moId


class MockHostConfig:
    """Mock host config"""
    def __init__(self):
        self.network = MockHostNetworkConfig()
        self.storageDevice = MockStorageDevice()
        self.vmotionEnabled = True


class MockHostNetworkConfig:
    """Mock host network config"""
    def __init__(self):
        self.vnic = [MockVirtualNic()]
        self.vswitch = [MockVirtualSwitch()]
        self.portgroup = [MockPortGroup()]


class MockVirtualNic:
    """Mock virtual NIC"""
    def __init__(self):
        self.device = "vmk0"
        self.spec = MockVirtualNicSpec()


class MockVirtualNicSpec:
    """Mock virtual NIC spec"""
    def __init__(self):
        self.ip = MockIpConfig()
        self.mac = "00:50:56:a0:00:01"


class MockIpConfig:
    """Mock IP config"""
    def __init__(self):
        self.address = "192.168.1.10"
        self.netmask = "255.255.255.0"


class MockVirtualSwitch:
    """Mock virtual switch"""
    def __init__(self):
        self.name = "vSwitch0"
        self.pnic = ["vmnic0", "vmnic1"]
        self.portgroup = ["Management Network"]


class MockPortGroup:
    """Mock port group"""
    def __init__(self):
        self.spec = MockPortGroupSpec()
        self.key = "pg-1"


class MockPortGroupSpec:
    """Mock port group spec"""
    def __init__(self):
        self.name = "VM Network"
        self.vlanId = 0


class MockHostSummary:
    """Mock host summary"""
    def __init__(self):
        self.config = MockHostSummaryConfig()
        self.runtime = MockHostSummaryRuntime()
        self.quickStats = MockHostQuickStats()


class MockHostSummaryConfig:
    """Mock host summary config"""
    def __init__(self):
        self.name = "esxi.corp.com"


class MockHostSummaryRuntime:
    """Mock host summary runtime"""
    def __init__(self):
        self.connectionState = vim.HostSystem.ConnectionState.connected
        self.powerState = vim.HostSystem.PowerState.poweredOn
        self.bootTime = datetime.now() - timedelta(days=30)


class MockHostQuickStats:
    """Mock host quick stats"""
    def __init__(self):
        self.uptime = 2592000  # 30 days in seconds
        self.overallCpuUsage = 5000
        self.overallMemoryUsage = 65536


class MockHostRuntime:
    """Mock host runtime"""
    def __init__(self):
        self.connectionState = vim.HostSystem.ConnectionState.connected
        self.powerState = vim.HostSystem.PowerState.poweredOn
        self.inMaintenanceMode = False
        self.bootTime = datetime.now() - timedelta(days=30)


class MockConfigManager:
    """Mock config manager"""
    def __init__(self):
        self.storageManager = MockStorageManager()


class MockStorageManager:
    """Mock storage manager"""
    pass


class MockCapability:
    """Mock capability"""
    def __init__(self):
        self.cpuFeature = [MockCpuFeature()]


class MockCpuFeature:
    """Mock CPU feature"""
    def __init__(self):
        self.key = "lbr"


class MockStorageDevice:
    """Mock storage device"""
    def __init__(self):
        self.hostBusAdapter = []
        self.scsiLun = []


class MockDatastore:
    """Realistic mock datastore object"""

    def __init__(self, name="datastore1", moId="datastore-1"):
        self._moId = moId
        self.name = name
        self.summary = MockDatastoreSummary()
        self.config = MockDatastoreConfig()
        self.info = MockDatastoreInfo()

    @property
    def _GetMoId(self):
        return self._moId


class MockDatastoreSummary:
    """Mock datastore summary"""
    def __init__(self):
        self.name = "datastore1"
        self.capacity = 1099511627776  # 1TB
        self.freeSpace = 549755813888  # 500GB
        self.uncommittedSpace = 0
        self.url = "/vmfs/volumes/datastore1"
        self.type = "VMFS"


class MockDatastoreConfig:
    """Mock datastore config"""
    def __init__(self):
        self.vmfs = MockVmfsConfig()


class MockVmfsConfig:
    """Mock VMFS config"""
    def __init__(self):
        self.blockSize = 1048576
        self.maxFileSize = 562949953421312
        self.version = "6"


class MockDatastoreInfo:
    """Mock datastore info"""
    def __init__(self):
        self.vmfs = MockVmfsInfo()


class MockVmfsInfo:
    """Mock VMFS info"""
    def __init__(self):
        self.uuid = "550e8400-e29b-41d4-a716-446655440000"
        self.extent = [MockVmfsExtent()]


class MockVmfsExtent:
    """Mock VMFS extent"""
    def __init__(self):
        self.diskName = "naa.6001405abcdef1234567890abcdef"
        self.partition = 3


class MockCluster:
    """Realistic mock cluster object"""

    def __init__(self, name="cluster1", moId="domain-c1"):
        self._moId = moId
        self.name = name
        self.config = MockClusterConfig()
        self.summary = MockClusterSummary()
        self.host = []
        self.resourcePool = None

    @property
    def _GetMoId(self):
        return self._moId


class MockClusterConfig:
    """Mock cluster config"""
    def __init__(self):
        self.drsConfig = MockDrsConfig()
        self.dasConfig = MockDasConfig()


class MockDrsConfig:
    """Mock DRS config"""
    def __init__(self):
        self.enabled = True
        self.defaultVmBehavior = "asSpecified"


class MockDasConfig:
    """Mock DAS config"""
    def __init__(self):
        self.enabled = True
        self.vmMonitoring = "vmMonitoringOnly"


class MockClusterSummary:
    """Mock cluster summary"""
    def __init__(self):
        self.name = "cluster1"
        self.numHosts = 3
        self.numVms = 50
        self.totalCpu = 96  # cores
        self.totalMemory = 393216  # MB = 384GB
        self.effectiveCpu = 96
        self.effectiveMemory = 393216
        self.numEffectiveHosts = 3


class MockNetwork:
    """Realistic mock network object"""

    def __init__(self, name="VM Network", moId="network-1"):
        self._moId = moId
        self.name = name
        self.summary = MockNetworkSummary()

    @property
    def _GetMoId(self):
        return self._moId


class MockNetworkSummary:
    """Mock network summary"""
    def __init__(self):
        self.name = "VM Network"
        self.network = None


class MockDistributedVirtualSwitch:
    """Realistic mock DVS object"""

    def __init__(self, name="dvs-1", moId="dvs-1"):
        self._moId = moId
        self.name = name
        self.config = MockDVSConfig()
        self.summary = MockDVSSummary()
        self.portgroup = []

    @property
    def _GetMoId(self):
        return self._moId


class MockDVSConfig:
    """Mock DVS config"""
    def __init__(self):
        self.numPorts = 256
        self.maxPorts = 4096
        self.uplinkPortgroup = [MockDistributedVirtualPortgroup()]
        self.defaultPortConfig = MockVmwareDistributedVirtualSwitchVlanIdSpec()


class MockVmwareDistributedVirtualSwitchVlanIdSpec:
    """Mock VLAN spec"""
    def __init__(self):
        self.vlanId = 0


class MockDVSSummary:
    """Mock DVS summary"""
    def __init__(self):
        self.name = "dvs-1"
        self.numPorts = 256
        self.productInfo = MockProductInfo()


class MockProductInfo:
    """Mock product info"""
    def __init__(self):
        self.version = "8.0.0"


class MockDistributedVirtualPortgroup:
    """Realistic mock DVPort group object"""

    def __init__(self, name="pg-1", moId="dvportgroup-1"):
        self._moId = moId
        self.name = name
        self.config = MockDVPortgroupConfig()
        self.summary = MockDVPortgroupSummary()

    @property
    def _GetMoId(self):
        return self._moId


class MockDVPortgroupConfig:
    """Mock DVPort group config"""
    def __init__(self):
        self.name = "pg-1"
        self.numPorts = 128
        self.defaultPortConfig = MockDefaultPortConfig()


class MockDefaultPortConfig:
    """Mock default port config"""
    def __init__(self):
        self.vlan = MockVmwareDistributedVirtualSwitchVlanIdSpec()
        self.blocked = MockBoolPolicy()


class MockBoolPolicy:
    """Mock bool policy"""
    def __init__(self):
        self.inherited = False
        self.value = False


class MockDVPortgroupSummary:
    """Mock DVPort group summary"""
    def __init__(self):
        self.name = "pg-1"
        self.numPorts = 128
        self.portConnectCount = 64


class MockFolder:
    """Realistic mock folder object"""

    def __init__(self, name="vm", moId="group-v1"):
        self._moId = moId
        self.name = name
        self.parent = None
        self.childEntity = []

    @property
    def _GetMoId(self):
        return self._moId


class MockResourcePool:
    """Realistic mock resource pool"""

    def __init__(self, name="Resources", moId="resgroup-1"):
        self._moId = moId
        self.name = name
        self.config = MockResourcePoolConfig()
        self.summary = MockResourcePoolSummary()
        self.vm = []

    @property
    def _GetMoId(self):
        return self._moId


class MockResourcePoolConfig:
    """Mock resource pool config"""
    def __init__(self):
        self.cpuAllocation = MockResourceAllocationInfo()
        self.memoryAllocation = MockResourceAllocationInfo()


class MockResourceAllocationInfo:
    """Mock resource allocation"""
    def __init__(self):
        self.reservation = 0
        self.limit = -1
        self.shares = MockSharesInfo()


class MockSharesInfo:
    """Mock shares info"""
    def __init__(self):
        self.shares = 1024
        self.level = "normal"


class MockResourcePoolSummary:
    """Mock resource pool summary"""
    def __init__(self):
        self.name = "Resources"
        self.config = MockResourcePoolConfig()
        self.runtime = MockResourcePoolRuntime()


class MockResourcePoolRuntime:
    """Mock resource pool runtime"""
    def __init__(self):
        self.cpu = MockResourcePoolResourceUsage()
        self.memory = MockResourcePoolResourceUsage()


class MockResourcePoolResourceUsage:
    """Mock resource usage"""
    def __init__(self):
        self.reservationUsed = 4096
        self.reservationUsedForVm = 2048
        self.unreservedForPool = 0
        self.unreservedForVm = 393216
        self.overallUsage = 8192


class MockLayout:
    """Mock VM layout"""
    def __init__(self):
        self.disk = [MockDiskLayout()]


class MockDiskLayout:
    """Mock disk layout"""
    def __init__(self):
        self.key = 2000
        self.chain = [MockDiskChain()]


class MockDiskChain:
    """Mock disk chain"""
    def __init__(self):
        self.fileKey = [MockFileInfo()]


class MockFileInfo:
    """Mock file info"""
    def __init__(self):
        self.fileKey = 0
        self.fileName = "[datastore1] test-vm-1/test-vm-1.vmdk"


class MockServiceInstance:
    """Realistic mock ServiceInstance object for testing"""

    def __init__(self):
        self.content = MockServiceContent()

    def RetrieveContent(self):
        """Return content"""
        return self.content


class MockServiceContent:
    """Mock service content"""

    def __init__(self):
        self.rootFolder = MockFolder("root", "group-d1")
        self.viewManager = MockViewManager()
        self.propertyCollector = MockPropertyCollector()
        self.about = MockAbout()
        self.sessionManager = MockSessionManager()
        self.userSession = MockUserSession()

    def RetrievePropertiesEx(self, *args, **kwargs):
        """Mock retrieve properties"""
        return MockRetrieveResult()


class MockAbout:
    """Mock about"""
    def __init__(self):
        self.name = "VMware vSphere"
        self.version = "8.0.0"
        self.build = "12345678"
        self.osType = "linux-x86"
        self.vendor = "VMware, Inc."
        self.apiVersion = "8.0.0"


class MockSessionManager:
    """Mock session manager"""
    def __init__(self):
        self.sessionList = [MockUserSession()]


class MockUserSession:
    """Mock user session"""
    def __init__(self):
        self.key = "52186d2c-e70f-9b2f-7c4d-a819fa78e3ba"
        self.userName = "VSPHERE.LOCAL\\Administrator"
        self.fullName = "Administrator"
        self.loginTime = datetime.now()
        self.lastActiveTime = datetime.now()
        self.locale = "en_US"
        self.messageLocale = "en_US"
        self.ipAddress = "192.168.1.100"
        self.userAgent = "Mozilla/5.0"
        self.callCount = 5


class MockViewManager:
    """Mock view manager"""

    def CreateContainerView(self, container, type, recursive):
        """Create container view"""
        return MockContainerView()


class MockContainerView:
    """Mock container view"""

    def __init__(self):
        self.view = []

    def Destroy(self):
        """Destroy view"""
        pass


class MockPropertyCollector:
    """Mock property collector"""

    def CreatePropertyCollector(self):
        """Create collector"""
        return MockPropertyCollector()

    def RetrievePropertiesEx(self, *args, **kwargs):
        """Retrieve properties"""
        return MockRetrieveResult()


class MockRetrieveResult:
    """Mock retrieve result"""

    def __init__(self):
        self.objects = []
        self.token = None


class MockPropertyFilterSpec:
    """Mock property filter spec"""

    def __init__(self):
        self.propSet = []
        self.objectSet = []


# Factory functions for creating test data

def create_mock_vm(name="test-vm", moId="vm-1", powered_on=True, cpu=4, memory=8192):
    """Create a realistic mock VM with customizable properties"""
    vm = MockVirtualMachine(name, moId, powered_on)
    vm.config.hardware.numCPU = cpu
    vm.config.hardware.memoryMB = memory
    return vm


def create_mock_host(name="esxi-1", moId="host-1", num_vms=10):
    """Create a realistic mock host with VMs"""
    host = MockHostSystem(name, moId)
    host.vm = [create_mock_vm(f"vm-{i}", f"vm-{i}", True) for i in range(num_vms)]
    return host


def create_mock_cluster(name="cluster1", num_hosts=3, vms_per_host=10):
    """Create a realistic mock cluster"""
    cluster = MockCluster(name)
    cluster.host = [create_mock_host(f"esxi-{i}", f"host-{i}", vms_per_host) for i in range(num_hosts)]
    cluster.summary.numHosts = num_hosts
    cluster.summary.numVms = num_hosts * vms_per_host
    return cluster


def create_mock_service_instance():
    """Create a complete mock vCenter service instance for testing"""
    si = MockServiceInstance()
    si.content.rootFolder.childEntity = [
        MockFolder("Datacenters", "group-1")
    ]
    return si
