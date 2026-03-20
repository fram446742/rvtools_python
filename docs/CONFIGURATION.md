# RVTools Configuration Guide

Complete guide to configuring RVTools with TOML configuration files.

## Quick Start

Create `~/.rvtools.toml`:

```toml
[default]
vcenter = "vc.domain.com"
username = "administrator@vsphere.local"
password = "SecurePassword123"
directory = "/mnt/rvtools/exports"
format = "xlsx"
threads = "auto"
verbose = false
```

Run:
```bash
rvtools
```

## Configuration File Location

By default, RVTools looks for configuration at:
- `~/.rvtools.toml` (Linux/macOS)
- `%USERPROFILE%\.rvtools.toml` (Windows)

Override with `-c` or `--config`:
```bash
rvtools --config /etc/rvtools/prod.toml
```

## Configuration Structure

### Required Fields

Every section must include:

```toml
[section_name]
vcenter = "vc.domain.com"           # FQDN or IP of vCenter
username = "administrator"           # vCenter username
password = "SecurePassword123"       # vCenter password (consider env vars)
directory = "/mnt/exports"          # Output directory (must exist)
```

### Optional Fields

```toml
format = "xlsx"                     # Default: "xlsx"
threads = "auto"                    # Default: "auto"
verbose = false                     # Default: false
```

## Configuration Examples

### Example 1: Single vCenter (Default)

```toml
[default]
vcenter = "vc.corp.com"
username = "svc_rvtools"
password = "MySecurePass@123"
directory = "/mnt/exports/default"
format = "xlsx"
threads = "auto"
verbose = false
```

### Example 2: Multi-vCenter Production Setup

```toml
[production]
vcenter = "prod-vc01.corp.com"
username = "svc_rvtools_prod"
password = "ProdSecure@456"
directory = "/mnt/exports/production"
format = "xlsx"
threads = "16"
verbose = false

[production-backup]
vcenter = "prod-vc02.backup.corp.com"
username = "svc_rvtools_prod"
password = "ProdSecure@456"
directory = "/mnt/exports/production-backup"
format = "xlsx"
threads = "16"

[staging]
vcenter = "stage-vc.corp.com"
username = "svc_rvtools_stage"
password = "StagePass@789"
directory = "/mnt/exports/staging"
format = "csv"
threads = "8"
verbose = true

[development]
vcenter = "dev-vc.corp.com"
username = "developer"
password = "DevPass@012"
directory = "/mnt/exports/development"
format = "json-separate"
threads = "4"
verbose = true
```

Run against specific config:
```bash
rvtools --config ~/.rvtools.toml
```

All sections processed sequentially. Each generates separate export files.

### Example 3: Geo-Distributed vCenters

```toml
[us-east]
vcenter = "vc-us-east.datacenter.com"
username = "rvtools_us_east"
password = "${RVTOOLS_PASS_US_EAST}"
directory = "/mnt/exports/us-east"
format = "xlsx"

[eu-west]
vcenter = "vc-eu-west.datacenter.eu"
username = "rvtools_eu_west"
password = "${RVTOOLS_PASS_EU_WEST}"
directory = "/mnt/exports/eu-west"
format = "xlsx"

[apac]
vcenter = "vc-apac.datacenter.sg"
username = "rvtools_apac"
password = "${RVTOOLS_PASS_APAC}"
directory = "/mnt/exports/apac"
format = "xlsx"
```

## Field Reference

### vcenter
- **Type**: String
- **Required**: Yes
- **Format**: FQDN or IPv4 address
- **Examples**: `vc.domain.com`, `192.168.1.100`, `vcenter.internal`

### username
- **Type**: String
- **Required**: Yes
- **Format**: vCenter username (may include domain)
- **Examples**: `administrator`, `administrator@vsphere.local`, `DOMAIN\user`

### password
- **Type**: String
- **Required**: Yes
- **Format**: Plain text or environment variable
- **Security**: Use env vars for production
- **Examples**: `MyPass@123`, `${VCENTER_PASS}`

### directory
- **Type**: String
- **Required**: Yes
- **Format**: Absolute file path
- **Must exist**: Yes (create with `mkdir -p`)
- **Permissions**: Must be writable
- **Examples**: `/mnt/exports`, `/var/rvtools`, `C:\rvtools\exports`

### format
- **Type**: String
- **Default**: `"xlsx"`
- **Valid values**:
  - `"xlsx"`: Single Excel file with all sheets (recommended)
  - `"csv"`: Individual CSV files per sheet
  - `"json-separate"`: Individual JSON files per sheet
  - `"json-unified"`: Single JSON file with all sheets
- **Examples**: `format = "xlsx"`, `format = "csv"`

### threads
- **Type**: String or Integer
- **Default**: `"auto"`
- **Valid values**:
  - `"auto"`: CPU count (auto-detected, min 8, max 32)
  - Integer: `4`, `8`, `16`, `32`
- **Use case**: Reduce for small labs, increase for large environments
- **Examples**: `threads = "auto"`, `threads = "16"`

### verbose
- **Type**: Boolean
- **Default**: `false`
- **Valid values**: `true` or `false`
- **Effect**: Enables debug logging to console and log file
- **Examples**: `verbose = false`, `verbose = true`

## Environment Variables

Use environment variables for sensitive data:

```toml
[production]
vcenter = "vc.corp.com"
username = "${VCENTER_USER}"
password = "${VCENTER_PASS}"
directory = "/mnt/exports/prod"
```

Set environment variables before running:

```bash
export VCENTER_USER="administrator@vsphere.local"
export VCENTER_PASS="SecurePassword123"
rvtools
```

Or in shell script:
```bash
#!/bin/bash
export VCENTER_USER="administrator@vsphere.local"
export VCENTER_PASS="SecurePassword123"
rvtools --config ~/.rvtools.toml
```

## vCenter Connection Strings

### IPv4 Address
```toml
vcenter = "192.168.1.100"
```

### FQDN
```toml
vcenter = "vcenter.internal.company.com"
```

### Short Hostname with Domain
```toml
vcenter = "vc.corp.local"
```

### IPv6 Address
```toml
vcenter = "[2001:db8::1]"
```

## Output Directory Setup

Create export directories before running:

```bash
# Single vCenter
mkdir -p /mnt/exports/default

# Multi-vCenter
mkdir -p /mnt/exports/{prod,stage,dev}

# Geo-distributed
mkdir -p /mnt/exports/{us-east,eu-west,apac}

# Set permissions
chmod 755 /mnt/exports
chown rvtools:rvtools /mnt/exports
```

## Common Configuration Patterns

### Production Export (Daily)

```toml
[prod-daily]
vcenter = "prod-vc.corp.com"
username = "svc_rvtools"
password = "${VCENTER_PASS}"
directory = "/mnt/rvtools/exports/production"
format = "xlsx"
threads = "auto"
verbose = false
```

Cron job:
```bash
0 2 * * * /usr/local/bin/rvtools --config /etc/rvtools/prod.toml
```

### Development/Lab (On-Demand)

```toml
[lab]
vcenter = "lab-vc.internal"
username = "developer"
password = "${LAB_PASS}"
directory = "/tmp/rvtools-lab"
format = "csv"
threads = "4"
verbose = true
```

### Archive Export (Monthly, All Formats)

```toml
[archive-xlsx]
vcenter = "vc.corp.com"
username = "svc_rvtools"
password = "${VCENTER_PASS}"
directory = "/archive/rvtools/2026-03/xlsx"
format = "xlsx"
threads = "auto"

[archive-csv]
vcenter = "vc.corp.com"
username = "svc_rvtools"
password = "${VCENTER_PASS}"
directory = "/archive/rvtools/2026-03/csv"
format = "csv"
threads = "auto"

[archive-json]
vcenter = "vc.corp.com"
username = "svc_rvtools"
password = "${VCENTER_PASS}"
directory = "/archive/rvtools/2026-03/json"
format = "json-separate"
threads = "auto"
```

## Sheet Filtering

To export only specific sheets, use `--sheets` argument:

```bash
# Export only vInfo and vHost
rvtools --sheets vInfo,vHost

# Export only storage-related sheets
rvtools --sheets vDisk,vDatastore,vMultiPath
```

Sheets can also be filtered in CLI, not in config file.

## Troubleshooting Configuration

### Config File Not Found
```bash
# Verify file exists
ls -la ~/.rvtools.toml

# Check permissions (must be readable)
chmod 644 ~/.rvtools.toml
```

### TOML Syntax Error
```bash
# Validate TOML syntax
python3 -m toml ~/.rvtools.toml

# Common issues:
# - Missing quotes: username = administrator  ❌ (should be "administrator")
# - Unescaped characters: password = pass@word ❌ (should be "pass@word")
# - Wrong type: threads = "16"  ✓ (string is correct)
```

### Environment Variable Not Substituted
```bash
# Wrong (shell variable, not env var)
password = "$VCENTER_PASS"

# Correct (must export before running)
export VCENTER_PASS="MyPassword"
rvtools
```

### Connection Issues
```bash
# Enable verbose logging
verbose = true

# Check connectivity
ping vcenter.domain.com

# Verify DNS resolution
nslookup vcenter.domain.com

# Test with correct credentials
rvtools --host vcenter.domain.com --username admin --password pass
```

## Best Practices

1. **Use environment variables** for passwords in production
2. **Create dedicated service account** with read-only vCenter permissions
3. **Store config file** with restricted permissions (600 or 644)
4. **Use HTTPS** for vCenter connections (automatic)
5. **Test config** with verbose logging before scheduling
6. **Rotate passwords** regularly (update env vars)
7. **Monitor exports** for completeness and data quality
8. **Archive exports** for compliance and auditing

## Performance Tuning

### Large Environments (10,000+ VMs)
```toml
[production]
threads = "32"    # Use more threads
format = "xlsx"   # Single large file faster than CSV
verbose = false   # Disable debug logging
```

### Small Labs (<100 VMs)
```toml
[lab]
threads = "4"     # Fewer threads for small data
format = "csv"    # Useful for analysis
verbose = true    # Enable debugging
```

### Memory-Constrained Systems
```toml
[constrained]
threads = "1"     # Single thread = less memory
format = "json-separate"  # Smaller individual files
```

