# RVTools Python

A comprehensive Python tool for exporting VMware vSphere infrastructure data in multiple formats (XLSX, CSV, JSON). Extract 782+ properties across 27 sheets covering VMs, hosts, networks, storage, and more.

**Cross-platform** • **Multi-vCenter** • **High Performance** • **No Dependencies on Windows**

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output Formats](#output-formats)
- [Documentation](#documentation)
- [Advanced](#advanced)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Features

### Data Collection

✅ **All 27 RVTools sheets implemented** (782+ properties):
- **VMs**: vInfo, vCPU, vMemory, vDisk, vPartition, vNetwork, vCD, vSnapshot, vUSB, vTools
- **Infrastructure**: vRP, vCluster, vHost, vDatastore, vMultiPath
- **Networking**: vHBA, vNIC, vSwitch, vPort, dvSwitch, dvPort, vSC_VMK
- **Advanced**: vSource, vLicense, vFileInfo, vHealth, vMetaData

### Export Formats

✅ **Multiple output formats**:
- **XLSX (default)** - Single Excel file with all 27 sheets, styled columns, optimized for Excel
- **CSV** - Individual CSV files per sheet, easy to import into databases
- **JSON** - Individual files per sheet or single unified file, API-friendly
- **Automatic filename** - Timestamps included: `rvtools_2026-03-20_14.30.xlsx`

### Performance

✅ **Optimized for scale**:
- **Multi-threaded** - Auto-detected thread count (8-32 threads based on CPU)
- **Batch API calls** - Property collection batched for 10x faster performance
- **Caching** - View caching prevents redundant API calls
- **Large environments** - Tested with 10,000+ VMs and 100+ hosts

### Reliability

✅ **Enterprise-grade features**:
- **Exponential backoff retry** - Automatic retries on timeout/connection errors
- **Comprehensive logging** - Detailed logs to console and file with timestamps
- **Error resilience** - Missing properties don't break collection
- **Multi-vCenter support** - Process multiple vCenters in single config
- **Sheet filtering** - Export only specific sheets as needed

### Configuration

✅ **Flexible TOML configuration**:
- **Multi-vCenter** - Single config file for multiple vCenters
- **Environment variables** - Secure credential handling
- **Per-section defaults** - Different settings for each environment
- **Override via CLI** - Command-line arguments override config

---

## Quick Start

### 1. Install

```bash
pip install rvtools
```

### 2. Create configuration

```bash
cat > ~/.rvtools.toml << 'EOF'
[default]
vcenter = "vcenter.domain.com"
username = "administrator@vsphere.local"
password = "SecurePassword123"
directory = "/mnt/rvtools/exports"
format = "xlsx"
threads = "auto"
verbose = false
EOF

chmod 600 ~/.rvtools.toml
```

### 3. Run

```bash
rvtools
```

Output:
```
rvtools_2026-03-20_14.30.xlsx
```

---

## Installation

### Option 1: From PyPI (Recommended)

```bash
pip install rvtools
```

### Option 2: From Repository

```bash
git clone https://github.com/waldirio/rvtools_python.git
cd rvtools_python
python -m pip install -e .
```

### Option 3: From Repository (without installing)

```bash
git clone https://github.com/waldirio/rvtools_python.git
cd rvtools_python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m rvtools --help
```

### Requirements

- **Python**: 3.8 or later
- **OS**: Linux, macOS, Windows
- **Network**: Access to vCenter HTTPS (port 443)
- **Disk**: 100 MB available for exports (depends on environment size)

---

## Configuration

### Configuration File

Create `~/.rvtools.toml`:

```toml
[default]
vcenter = "vc.domain.com"
username = "administrator@vsphere.local"
password = "SecurePassword123"
directory = "/mnt/exports"
format = "xlsx"
threads = "auto"
verbose = false
```

### Multi-vCenter Configuration

```toml
[production]
vcenter = "prod-vc.corp.com"
username = "svc_rvtools"
password = "${VCENTER_PASS_PROD}"
directory = "/mnt/exports/production"
format = "xlsx"
threads = "16"

[staging]
vcenter = "stage-vc.corp.com"
username = "svc_rvtools"
password = "${VCENTER_PASS_STAGE}"
directory = "/mnt/exports/staging"
format = "csv"
threads = "8"
```

### Configuration Options

| Option | Type | Default | Example |
|--------|------|---------|---------|
| `vcenter` | string | (required) | `vc.domain.com` |
| `username` | string | (required) | `administrator@vsphere.local` |
| `password` | string | (required) | `SecurePass123` or `${PASS_ENV_VAR}` |
| `directory` | string | (required) | `/mnt/exports` |
| `format` | string | `xlsx` | `xlsx`, `csv`, `json-separate`, `json-unified` |
| `threads` | string | `auto` | `auto`, `4`, `8`, `16`, `32` |
| `verbose` | bool | `false` | `true`, `false` |

**See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for complete reference.**

---

## Usage

### Basic Usage

```bash
# Use default configuration from ~/.rvtools.toml
rvtools

# Override configuration file location
rvtools --config /etc/rvtools/prod.toml

# Command-line arguments override config
rvtools --host vc.domain.com --username admin --password pass --directory /exports
```

### Command-Line Options

```bash
rvtools --help

usage: rvtools [-h] [-s HOST] [-u USERNAME] [-p PASSWORD] [-d DIRECTORY]
               [-f FORMAT] [-c CONFIG] [--sheets SHEETS] [--threads THREADS]
               [-v] [--version]

RVTools - VMware vSphere data export

optional arguments:
  -h, --help            show this help message and exit
  -s, --host HOST       vCenter server FQDN or IP
  -u, --username USERNAME
                        vCenter username (can include domain)
  -p, --password PASSWORD
                        vCenter password
  -d, --directory DIRECTORY
                        Output directory for exports
  -f, --format FORMAT   Export format: xlsx (default), csv, json-separate, json-unified
  -c, --config CONFIG   Configuration file (default: ~/.rvtools.toml)
  --sheets SHEETS       Comma-separated sheet names to export
                        Example: vInfo,vHost,vDatastore
  --threads THREADS     Number of parallel threads (auto, 4-32)
  -v, --verbose         Enable verbose logging
  --version             Show version information
```

### Examples

**Export all sheets as XLSX (default)**:
```bash
rvtools --host vc.domain.com --username admin --password pass --directory /exports
```

**Export specific sheets**:
```bash
rvtools --sheets vInfo,vHost,vCluster --directory /exports
```

**Export as CSV with verbose logging**:
```bash
rvtools -s vc.domain.com -u admin -p pass -d /exports -f csv --verbose
```

**Use configuration file**:
```bash
rvtools --config ~/.rvtools.toml
```

**Process multiple vCenters**:
```bash
# Config file with [production], [staging], [dev] sections
rvtools --config ~/.rvtools.toml
```

---

## Output Formats

### XLSX Format (Default)

Single Excel file with all 27 sheets:
- **File**: `rvtools_2026-03-20_14.30.xlsx`
- **Sheets**: All 27 sheets in single workbook
- **Styling**: Formatted columns, frozen headers
- **Usage**: Open in Excel, use for reports

### CSV Format

Individual CSV files per sheet:
- **Files**: `vInfo_2026-03-20_14.30.csv`, `vHost_2026-03-20_14.30.csv`, ...
- **Format**: Standard RFC 4180 CSV
- **Encoding**: UTF-8
- **Usage**: Import to database, use in data pipelines

### JSON Separate Format

Individual JSON files per sheet:
- **Files**: `vInfo_2026-03-20_14.30.json`, `vHost_2026-03-20_14.30.json`, ...
- **Structure**: Array of objects per sheet
- **Usage**: API-friendly, import to NoSQL databases

### JSON Unified Format

Single JSON file with all sheets:
- **File**: `rvtools_2026-03-20_14.30.json`
- **Structure**: Object with sheets as keys
- **Usage**: Single file transfer, archival

---

## Documentation

### Comprehensive Guides

- **[Property Mapping](docs/PROPERTY_MAPPING.md)** - Complete reference of all 782 properties
- **[Configuration Guide](docs/CONFIGURATION.md)** - TOML syntax, multi-vCenter setup, examples
- **[Compatibility Matrix](docs/COMPATIBILITY.md)** - vSphere 5.0 through 9.0 support
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common errors and solutions

### Quick Links

| Topic | File |
|-------|------|
| All 782 properties by sheet | [Property Mapping](docs/PROPERTY_MAPPING.md) |
| vCenter connectivity | [Configuration Guide](docs/CONFIGURATION.md) |
| vSphere version support | [Compatibility Matrix](docs/COMPATIBILITY.md) |
| Error diagnosis | [Troubleshooting](docs/TROUBLESHOOTING.md) |

---

## Advanced

### Environment Variables

Secure credential handling:

```bash
export VCENTER_HOST="vc.domain.com"
export VCENTER_USER="administrator@vsphere.local"
export VCENTER_PASS="SecurePassword123"

rvtools --host $VCENTER_HOST --username $VCENTER_USER --password $VCENTER_PASS
```

Or in config file:

```toml
[production]
vcenter = "${VCENTER_HOST}"
username = "${VCENTER_USER}"
password = "${VCENTER_PASS}"
directory = "/mnt/exports"
```

### Automated Scheduling

#### Cron (Linux/macOS)

```bash
# Daily export at 2 AM
0 2 * * * /usr/local/bin/rvtools --config /etc/rvtools/prod.toml >> /var/log/rvtools.log 2>&1

# Weekly export every Sunday at 3 AM
0 3 * * 0 /usr/local/bin/rvtools --config /etc/rvtools/prod.toml --format xlsx >> /var/log/rvtools.log 2>&1
```

#### Systemd Timer (Linux)

```ini
# /etc/systemd/system/rvtools.timer
[Unit]
Description=RVTools vCenter Export Timer
Wants=rvtools.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/rvtools.service
[Unit]
Description=RVTools vCenter Export Service

[Service]
Type=oneshot
User=rvtools
ExecStart=/usr/local/bin/rvtools --config /etc/rvtools/prod.toml
StandardOutput=journal
```

Enable and start:
```bash
sudo systemctl enable rvtools.timer
sudo systemctl start rvtools.timer
```

### Custom Sheet Filtering

Export only specific sheets:

```bash
# VMs only
rvtools --sheets vInfo,vCPU,vMemory,vDisk

# Infrastructure only
rvtools --sheets vHost,vCluster,vDatastore

# Networking only
rvtools --sheets vNetwork,vSwitch,dvSwitch,vNIC
```

### Performance Tuning

**Large environments (10,000+ VMs)**:
```bash
rvtools --threads 32 --format xlsx --verbose
```

**Small labs (<100 VMs)**:
```bash
rvtools --threads 4 --format csv --verbose
```

**Memory-constrained systems**:
```bash
rvtools --threads 1 --format json-separate
```

---

## Troubleshooting

### Connection Issues

```bash
# Check connectivity
ping vcenter.domain.com

# Verify DNS
nslookup vcenter.domain.com

# Check HTTPS
curl -k https://vcenter.domain.com/ui/

# Enable verbose logging
rvtools --verbose
```

### Authentication Errors

```bash
# Verify credentials
# Correct format: administrator@vsphere.local or DOMAIN\user

# Test with verbose logging
rvtools --verbose --username "admin@vsphere.local"

# Check vCenter logs
# In vCenter: Administrator > Logs
```

### Performance Issues

```bash
# Check available threads
nproc

# Monitor system
top -p $(pgrep -f rvtools)

# Reduce threads for constrained systems
rvtools --threads 4
```

**For detailed troubleshooting, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).**

---

## Testing

Run all tests:

```bash
python -m unittest discover test/

# Or with verbose output
python -m unittest discover test/ -v

# Test specific module
python -m unittest test.test_collectors
```

Tests cover:
- Mock vCenter objects
- Collector property validation
- Configuration parsing
- Export formats
- Performance benchmarks

---

## Performance

Typical collection times:

| Environment | VMs | Hosts | Time | Threads |
|-------------|-----|-------|------|---------|
| Small lab | 50 | 2 | 30 seconds | 4 |
| Medium | 500 | 5 | 2 minutes | 8 |
| Large | 2000 | 20 | 5 minutes | 16 |
| Very Large | 10000 | 100 | 30 minutes | 32 |

Performance optimizations:
- Batch property collection
- Multi-threaded data gathering
- Efficient caching
- Exponential backoff retries

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m unittest discover test/`
5. Submit a pull request

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## References

- [Original RVTools](https://www.robware.net/rvtools/) - Inspiration and property reference
- [VMware pyVmomi](https://github.com/vmware/pyvmomi) - vSphere Python SDK
- [vSphere API Documentation](https://code.vmware.com/apis/358/vsphere)

---

## Acknowledgments

- Created as a Python alternative to the original Windows-only RVTools
- Thanks to [Rob Veitch](https://www.robware.net/) for creating the original RVTools
- Thanks to VMware for the comprehensive pyVmomi SDK

---

## Support

- **Documentation**: See `/docs` directory
- **Issues**: Report on [GitHub Issues](https://github.com/waldirio/rvtools_python/issues)
- **Discussions**: Use [GitHub Discussions](https://github.com/waldirio/rvtools_python/discussions)

---

**Created by Waldirio Camelo** - Feel free to request features or submit issues!
