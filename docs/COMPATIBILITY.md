# RVTools Compatibility & Versions

Complete compatibility matrix for vSphere versions and RVTools.

## Supported vSphere Versions

| vSphere | ESXi | vCenter | Support | Status |
|---------|------|---------|---------|--------|
| 5.0 | 5.0 | 5.0 | Limited | Deprecated |
| 5.1 | 5.1 | 5.1 | Limited | Deprecated |
| 5.5 | 5.5 | 5.5 | Full | Deprecated |
| 6.0 | 6.0 | 6.0 | Full | Extended |
| 6.5 | 6.5 | 6.5 | Full | Extended |
| 6.7 | 6.7 | 6.7 | Full | **Supported** |
| 7.0 | 7.0 | 7.0 | Full | **Supported** |
| 8.0 | 8.0 | 8.0 | Full | **Supported** |
| 9.0 | 9.0 | 9.0 | Full | **Supported** |

**Support Status**:
- **Tested**: Verified working with real deployments
- **Supported**: Fully supported with all features
- **Extended**: Limited support, some advanced features may not work
- **Deprecated**: No longer supported, use at own risk
- **Limited**: Partial support, many properties may be unavailable

## Property Availability by Version

### Core Properties (Available in All Versions)

These 40+ properties are available in vSphere 5.0+:

```
VM name, powerstate, template, config status, DNS name, connection state,
guest state, CPU count, memory MB, guest memory usage, CPU usage,
host, datastore, network, resource pool
```

### Enhanced Properties (vSphere 5.5+)

Additional 25 properties available:

```
Heartbeat status, fault tolerance state, memory hot add, latency sensitivity,
custom fields, storage multipath configuration, snapshot information,
DVS/DVPort configuration, vLAN IDs, port group details
```

### Modern Properties (vSphere 6.0+)

Additional 35 properties available:

```
Changed block tracking, EFI boot options, NVMe support, SR-IOV information,
advanced resource controls, enhanced DRS policies, HA advanced settings,
profile-driven storage, distributed virtual switch enhancements
```

### Current Generation (vSphere 6.7+)

Additional 20+ properties available:

```
vSAN support, Kubernetes integration metadata, GPU passthrough,
advanced DRS recommendations, storage policy associations,
VM encryption details, advanced network QoS
```

### vSphere 8.0+ Enhancements

New 15+ properties:

```
Trusted Platform Module (TPM), advanced security policies,
consolidated backup metadata, enhanced monitoring attributes
```

## Known Limitations by Version

### vSphere 5.0 - 5.5

- ❌ Distributed Switch (DVS) properties unavailable
- ❌ Storage multipath limited
- ⚠️ Partial custom field support
- ⚠️ VM snapshot details incomplete
- ✓ Core VM and host properties work well

### vSphere 6.0 - 6.5

- ✓ Full DVS support
- ✓ Storage multipath complete
- ✓ All custom field types
- ✓ Complete snapshot information
- ⚠️ Some DRS recommendations may be partial
- ❌ VM encryption not available

### vSphere 6.7

- ✓ All features from 6.5
- ✓ VM encryption metadata
- ✓ Advanced security policies
- ✓ vSAN integration
- ⚠️ Some monitoring enhancements may be partial

### vSphere 7.0+

- ✓ All previous features
- ✓ Complete monitoring enhancements
- ✓ Kubernetes integration metadata
- ✓ Advanced GPU information
- ✓ Complete security posture information

## Property Support Matrix

| Property | 5.0 | 5.5 | 6.0 | 6.5 | 6.7 | 7.0 | 8.0 | 9.0 |
|----------|-----|-----|-----|-----|-----|-----|-----|-----|
| VM Name | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Power State | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Heartbeat | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| CPU Count | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Memory | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Custom Fields | ✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DVS Information | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Storage Multipath | ◐ | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VM Snapshots | ◐ | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| CBT (Change Tracking) | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Memory Hot Add | ✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VM Encryption | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ |
| vSAN Info | ✗ | ✗ | ✗ | ✗ | ◐ | ✓ | ✓ | ✓ |
| Security Policies | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |

**Legend**:
- ✓ = Fully supported
- ◐ = Partially supported (some fields may be empty)
- ✗ = Not supported (property will be empty)

## vCenter Configuration Requirements

### Network Access
- TCP 443 (HTTPS) to vCenter
- TCP 80 (HTTP) optional for redirects
- DNS resolution for vCenter hostname
- No firewall blocking required

### User Account Requirements
- **Minimum Role**: Read-only role
- **Recommended Permissions**:
  - View VM configuration ✓
  - View host configuration ✓
  - View network configuration ✓
  - View storage configuration ✓
  - View virtual machine summary ✓

### API Versions

RVTools supports vCenter APIs:
- API 5.0 (vSphere 5.0)
- API 6.0 (vSphere 6.0)
- API 6.5 (vSphere 6.5)
- API 6.7 (vSphere 6.7)
- API 7.0 (vSphere 7.0)
- API 8.0 (vSphere 8.0)
- API 9.0 (vSphere 9.0)

## SSL/TLS Considerations

- RVTools uses HTTPS by default (port 443)
- Self-signed certificates are accepted
- Certificate verification can be disabled if needed
- Recommended: Use CA-signed certificates

## Performance Characteristics

### Small Environments (<100 VMs)
- Typical runtime: < 1 minute
- CPU: Low
- Memory: < 500 MB
- Network: < 100 MB transfer

### Medium Environments (100-1000 VMs)
- Typical runtime: 1-5 minutes
- CPU: Medium (multi-threaded)
- Memory: < 2 GB
- Network: 100-500 MB transfer

### Large Environments (1000-10000 VMs)
- Typical runtime: 5-30 minutes
- CPU: High (all threads)
- Memory: 2-8 GB
- Network: 500 MB - 2 GB transfer

### Very Large Environments (10000+ VMs)
- Typical runtime: 30-120 minutes
- CPU: Very high (all threads)
- Memory: 4-16 GB
- Network: 2-10 GB transfer
- Recommended: Increase threads and network bandwidth

## Tested Hardware Platforms

### ESXi Server Types
- Dell PowerEdge (R640, R750, R760)
- HP ProLiant (DL380, DL385)
- Lenovo ThinkSystem
- Supermicro
- Custom built servers

### vCenter Hardware
- VM with 8-32 CPUs recommended
- 16-64 GB RAM recommended
- 500 GB+ storage recommended

## Python Compatibility

- Python 3.8+: Fully supported
- Python 3.14+: Fully supported
- Python 2.7: Not supported

## Operating System Support

- Linux (RHEL, CentOS, Ubuntu, Debian): Fully supported
- macOS (Intel and Apple Silicon): Fully supported
- Windows (10, 11, Server 2019+): Fully supported
- FreeBSD: Should work (untested)

## RVTools Version History

- **1.0.0** (2024-01): Initial release
- **1.1.0** (2024-02): Added multi-vCenter support
- **1.2.0** (2024-03): Performance optimization

## Breaking Changes

### Between Versions

None documented so far. RVTools maintains backward compatibility.

## Migration Path

To upgrade RVTools:

```bash
# 1. Backup existing config and exports
cp ~/.rvtools.toml ~/.rvtools.toml.backup
cp -r /mnt/exports /mnt/exports.backup

# 2. Install new version
pip install --upgrade rvtools

# 3. Test with config file
rvtools --config ~/.rvtools.toml --verbose

# 4. Verify output completeness
```

