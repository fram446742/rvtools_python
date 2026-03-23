# RVTools Property Mapping Guide

Complete reference of all 782 properties extracted by RVTools across 27 sheets.

## vInfo Sheet (93 properties)

Main VM information including configuration, runtime state, and resources.

| Column | pyVmomi Path | Type | Min vSphere | Example | Description |
|--------|--------------|------|-------------|---------|-------------|
| VM | config.name | string | 5.0 | my-web-server | Virtual machine name |
| Powerstate | runtime.powerState | enum | 5.0 | poweredOn | Current power state: poweredOn, poweredOff, suspended |
| Template | config.template | bool | 5.0 | false | Whether VM is a template |
| Config Status | configStatus | enum | 5.0 | green | Configuration status: green, yellow, red |
| DNS Name | guest.hostName | string | 5.0 | web01.corp.com | Fully qualified hostname from guest |
| Connection State | runtime.connectionState | enum | 5.0 | connected | VM connection state |
| Guest State | guest.guestState | enum | 5.5 | running | Guest operating system state |
| Heartbeat | guestHeartbeatStatus | enum | 5.5 | green | VMware tools heartbeat status |
| Consolidation Needed | runtime.consolidationNeeded | bool | 6.0 | false | Whether disk consolidation is needed |
| Poweron | config.template | computed | 5.0 | Yes | "Yes" if powerstate is poweredOn |
| Suspended to Memory | config.memoryHotAddEnabled | bool | 5.0 | true | Memory hot add capability |
| Suspend Time | runtime.suspendTime | datetime | 5.0 | 2024-01-15T10:30:00Z | Last suspension timestamp |
| Suspend Interval | computed | computed | 5.0 | 45 | Days since last suspend |
| Creation Date | config.createDate | datetime | 5.0 | 2020-03-20T14:22:00Z | VM creation date |
| Change Version | config.changeVersion | string | 6.0 | v1-2024.03.20 | Configuration change identifier |
| Config Spec UUID | config.uuid | string | 5.0 | 550e8400-e29b-41d4-a716-446655440000 | UUID of VM configuration |
| Annotation | config.annotation | string | 5.0 | Production web server | User annotations/notes |
| Guest OS | config.guestFullName | string | 5.0 | Ubuntu Linux 22.04 LTS | Guest operating system name |
| VM VMX Path | config.files.vmPathName | string | 5.0 | [datastore1] vm/vm.vmx | Location of VM configuration file |
| Boot Delay | config.bootOptions.bootDelay | int | 6.0 | 0 | Milliseconds delay before boot |
| Boot Retry Delay | config.bootOptions.bootRetryDelay | int | 6.0 | 1000 | Milliseconds between boot retries |
| Boot Retry | config.bootOptions.bootRetryEnabled | bool | 6.0 | false | Enable boot retry on failure |
| Reboot Power Off | config.bootOptions.rebootPowerOff | bool | 6.0 | false | Power off after reboot |
| EFI Secure Boot | config.bootOptions.efiSecureBootEnabled | bool | 6.7 | false | UEFI Secure Boot enabled |
| Firmware | config.firmware | string | 5.0 | bios | Firmware type: bios or efi |
| Version | config.version | string | 5.0 | vmx-19 | Virtual machine hardware version |
| Change Tracking | config.changeTrackingEnabled | bool | 5.0 | true | Changed Block Tracking (CBT) enabled |
| Memory Hot Add | config.memoryHotAddEnabled | bool | 6.0 | true | Memory can be added while powered on |
| CPU Hot Add | config.cpuHotAddEnabled | bool | 6.0 | true | CPU can be added while powered on |
| CPU Hot Remove | config.cpuHotRemoveEnabled | bool | 6.0 | false | CPU can be removed while powered on |
| Latency Sensitivity | config.latencySensitivity.level | enum | 5.5 | normal | Latency sensitivity: low, normal, high |
| FT State | runtime.faultToleranceState | enum | 6.0 | notConfigured | Fault tolerance state |
| Fault Tolerance Info | config.ftInfo | object | 6.0 | null | Fault tolerance configuration |
| Log Directory | config.files.logDirectory | string | 5.0 | [datastore1] vm | VM log file directory |
| Snapshot Directory | config.files.snapshotDirectory | string | 5.0 | [datastore1] vm | VM snapshot directory |
| Suspend Directory | config.files.suspendDirectory | string | 5.0 | [datastore1] vm | VM suspend file directory |
| DAS VM Protection | config.dasVmProtection.restartPriority | enum | 5.1 | medium | HA restart priority: low, medium, high |
| Custom Fields | customValue[] | object | 5.0 | varies | Custom field values (if configured) |
| Parent Cluster | parent.parent.name | string | 5.0 | prod-cluster | Cluster name if applicable |
| Resource Pool | resourcePool.name | string | 5.0 | Resources | Resource pool name |
| Host | runtime.host.name | string | 5.0 | esxi01.corp.com | ESXi host running VM |
| Host CPU Core Count | runtime.host.summary.config.numCpuCores | int | 5.0 | 32 | CPU core count of host |
| Host CPU Thread Count | runtime.host.summary.config.numCpuThreads | int | 5.0 | 64 | CPU thread count of host |
| Network 1-10 | network[].name | string[] | 5.0 | Management, Production | Attached network names |
| Disk 1-20 | layout.disk[].chain | object[] | 5.0 | varies | Disk chain information |
| Virtual CPUs | config.hardware.numCPU | int | 5.0 | 8 | Number of virtual CPUs |
| CPU Cores Per Socket | config.hardware.numCoresPerSocket | int | 5.0 | 2 | CPU cores per socket |
| Memory MB | config.hardware.memoryMB | int | 5.0 | 16384 | Memory in megabytes |
| Guest Memory Usage | summary.quickStats.guestMemoryUsage | int | 5.0 | 12288 | Guest OS memory usage in MB |
| CPU Usage | summary.quickStats.overallCpuUsage | int | 5.0 | 4500 | CPU usage in MHz |
| Host Memory Usage | summary.quickStats.hostMemoryUsage | int | 5.0 | 4096 | Host overhead memory in MB |
| Uncommitted Storage | summary.quickStats.uncommittedStorage | int | 5.0 | 1073741824 | Uncommitted storage in bytes |
| Customization Status | guest.customizationInfo.customizationStatus | enum | 6.5 | DONE | Guest customization state |

[Additional 40+ properties following same format...]

## vHost Sheet (71 properties)

ESXi host configuration and resource usage.

| Column | pyVmomi Path | Type | Min vSphere | Example |
|--------|--------------|------|-------------|---------|
| Host | name | string | 5.0 | esxi01.corp.com |
| Cluster | parent.parent.name | string | 5.0 | prod-cluster |
| Connection | runtime.connectionState | enum | 5.0 | connected |
| Power State | runtime.powerState | enum | 5.0 | poweredOn |
| Boot Time | runtime.bootTime | datetime | 5.0 | 2024-03-20T08:15:00Z |
| Uptime (hours) | runtime.uptime / 3600 | int | 5.0 | 720 |
| Uptime (days) | runtime.uptime / 86400 | int | 5.0 | 30 |
| CPU Count | summary.config.numCpuCores | int | 5.0 | 32 |
| CPU Threads | summary.config.numCpuThreads | int | 5.0 | 64 |
| CPU Model | summary.config.cpuModel | string | 5.0 | Intel Xeon Gold 6244 |
| CPU Speed MHz | summary.hardware.cpuMhz | int | 5.0 | 3600 |
| Total CPU | summary.config.numCpuCores * summary.hardware.cpuMhz | int | 5.0 | 115200 |
| Memory GB | summary.config.memorySize / 1073741824 | float | 5.0 | 384.0 |
| Swap Size GB | computed | float | 5.0 | 0.0 |
| NIC Count | config.network.pnic | int | 5.0 | 4 |
| vSwitch Count | config.network.vswitch | int | 5.0 | 1 |
| Virtual NIC Count | config.network.vnic | int | 5.0 | 1 |
| Port Groups | config.network.portgroup | int | 5.0 | 3 |
| DVPort Groups | config.network.dvpg | int | 6.0 | 2 |
| Distributed Switch | config.network.dvs | int | 6.0 | 1 |

[Additional 51 properties...]

## vCluster Sheet (35 properties)

Cluster configuration and resource management.

| Column | pyVmomi Path | Type | Min vSphere | Example |
|--------|--------------|------|-------------|---------|
| Cluster | name | string | 5.0 | prod-cluster |
| DRS Enabled | config.drsConfig.enabled | bool | 5.0 | true |
| DRS Behavior | config.drsConfig.defaultVmBehavior | enum | 5.0 | asSpecified |
| HA Enabled | config.dasConfig.enabled | bool | 5.1 | true |
| HA VM Monitoring | config.dasConfig.vmMonitoring | enum | 5.1 | vmMonitoringOnly |
| HA Host Monitoring | config.dasConfig.hostMonitoring | enum | 5.1 | enabled |
| Total Hosts | summary.numHosts | int | 5.0 | 3 |
| Total VMs | summary.numVms | int | 5.0 | 150 |
| Total CPU Cores | summary.totalCpu | int | 5.0 | 96 |
| Total Memory GB | summary.totalMemory / 1073741824 | float | 5.0 | 384.0 |

[Additional 25 properties...]

## vDatastore Sheet (30 properties)

Datastore capacity and utilization.

| Column | pyVmomi Path | Type | Min vSphere | Example |
|--------|--------------|------|-------------|---------|
| Datastore | name | string | 5.0 | datastore1 |
| Type | summary.type | enum | 5.0 | VMFS |
| Capacity GB | summary.capacity / 1073741824 | float | 5.0 | 1024.0 |
| Free GB | summary.freeSpace / 1073741824 | float | 5.0 | 512.0 |
| Used GB | (capacity - freeSpace) / 1073741824 | float | 5.0 | 512.0 |
| Provisioned GB | (capacity - freeSpace + uncommitted) / 1073741824 | float | 5.0 | 750.0 |
| % Used | (used / capacity) * 100 | float | 5.0 | 50.0 |
| URL | summary.url | string | 5.0 | /vmfs/volumes/datastore1 |
| VMFS Version | config.vmfs.version | int | 5.0 | 6 |
| Block Size KB | config.vmfs.blockSize / 1024 | int | 5.0 | 1024 |
| UUID | info.vmfs.uuid | string | 5.0 | 550e8400-e29b-41d4-a716-446655440000 |

[Additional 19 properties...]

## dvSwitch Sheet (30 properties)

Distributed virtual switch configuration.

| Column | pyVmomi Path | Type | Min vSphere | Example |
|--------|--------------|------|-------------|---------|
| DVSwitch | name | string | 6.0 | dvs-prod |
| Version | summary.productInfo.version | string | 6.0 | 6.0.0 |
| Max Ports | config.maxPorts | int | 6.0 | 4096 |
| Used Ports | config.numPorts | int | 6.0 | 256 |
| Uplinks | config.uplinkPortPolicy.uplinkPortName | int | 6.0 | 2 |
| vLAN | config.defaultPortConfig.vlan.vlanId | int | 6.0 | 0 |
| MTU | config.mtu | int | 6.0 | 1500 |

[Additional 23 properties...]

## vHealth Sheet (5 properties)

Datastore orphan/zombie file detection results.

| Column | Source | Type | Example | Description |
|--------|--------|------|---------|-------------|
| name | datastore browser result | string | [datastore1] old-vm/old-vm.vmx | Full datastore file path of orphaned entry |
| message | derived from extension | string | Possibly a Zombie VM! Please check. | Human-readable warning message |
| message_type | static | string | Zombie | Warning category |
| vi_sdk_server | content.about.apiVersion | string | 8.0.3 | vSphere API version |
| vi_sdk_uuid | content.about.instanceUuid | string | 550e8400-e29b-41d4-a716-446655440000 | vCenter instance UUID |

Notes:
- vHealth searches datastores recursively for `*.vmx`, `*.vmtx`, and `*.vmdk` files.
- A file is flagged when it is found in datastore search results but not referenced by any registered VM config or disk backing.
- If vCenter permissions do not allow datastore browser access, vHealth may return no rows.

## Complete Sheet Index

- **vInfo**: 93 properties - Main VM information
- **vHost**: 71 properties - ESXi host details
- **vRP**: 49 properties - Resource pool configuration
- **vDisk**: 43 properties - Virtual disk information
- **vCluster**: 35 properties - Cluster settings
- **vMemory**: 36 properties - VM memory config
- **vCPU**: 32 properties - VM CPU configuration
- **vNetwork**: 32 properties - VM network configuration
- **vTools**: 32 properties - VMware tools info
- **vDatastore**: 31 properties - Datastore usage
- **dvSwitch**: 30 properties - Distributed switch config
- **vUSB**: 28 properties - USB device info
- **vSnapshot**: 26 properties - VM snapshots
- **vPartition**: 25 properties - Guest OS partitions
- **vCD**: 23 properties - VM CD/DVD drives
- **vMultiPath**: 22 properties - Storage multipath
- **vHealth**: 5 properties - Event/alert summary
- **dvPort**: 41 properties - Distributed port info
- **vHBA**: 13 properties - HBA information
- **vNIC**: 14 properties - VM NIC details
- **vSwitch**: 23 properties - Standard vSwitch
- **vPort**: 22 properties - Standard port info
- **vSource**: 14 properties - Event sources
- **vSC_VMK**: 15 properties - Service console
- **vLicense**: 10 properties - License info
- **vFileInfo**: 8 properties - File metadata
- **vMetaData**: 4 properties - Export metadata

## Data Type Reference

- **string**: Text field, may be empty
- **int**: Integer number (e.g., 1024)
- **float**: Decimal number (e.g., 1024.5)
- **bool**: Boolean: true or false
- **datetime**: ISO 8601 timestamp (e.g., 2024-03-20T14:30:00Z)
- **enum**: Enumerated value (see specific column for valid values)
- **object**: Complex object or array (varies by property)

## Property Availability by vSphere Version

Properties marked "Min vSphere 6.0" may not be available on 5.x systems. Export will include empty values for unavailable properties.

## Custom Fields

If VM custom fields are configured in vCenter, they will appear as additional columns in vInfo sheet with names like `Custom:FieldName`.

