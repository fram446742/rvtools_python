# RVTools Troubleshooting Guide

Comprehensive guide to diagnosing and resolving common RVTools issues.

## Common Errors and Solutions

### Connection Errors

#### Error: "Connection refused" or "Connection timeout"

**Symptoms**:
```
Error: Connection refused to vcenter.domain.com:443
Timeout waiting for vCenter response
```

**Causes**:
1. vCenter is unreachable
2. Network firewall blocking
3. DNS resolution failure
4. vCenter service stopped

**Solutions**:

```bash
# 1. Check connectivity
ping vcenter.domain.com
nslookup vcenter.domain.com

# 2. Verify vCenter is running
# (In vCenter: Administration > System Configuration > Shutdown/Restart)

# 3. Check network access
telnet vcenter.domain.com 443
curl -k https://vcenter.domain.com/ui/

# 4. Enable verbose logging
rvtools --verbose --config ~/.rvtools.toml
```

**Config check**:
```toml
# Verify config has correct vCenter
[default]
vcenter = "vcenter.domain.com"     # Check spelling
username = "admin"
password = "pass"
directory = "/exports"
```

#### Error: "SSL certificate verification failed"

**Symptoms**:
```
SSL: CERTIFICATE_VERIFY_FAILED
SSL certificate problem: self signed certificate
```

**Causes**:
1. vCenter using self-signed certificate
2. CA certificate not in trust store
3. Certificate expired
4. Hostname mismatch

**Solutions**:

```bash
# 1. Check certificate validity
openssl s_client -connect vcenter.domain.com:443

# 2. Get certificate expiry
echo | openssl s_client -servername vcenter.domain.com \
    -connect vcenter.domain.com:443 2>/dev/null | \
    openssl x509 -noout -dates

# 3. Ignore certificate verification (use with caution)
# (Environment variable support needed in config)

# 4. Trust certificate in system store
# Copy vCenter SSL cert to local trust store
```

**Workaround**:
- Self-signed certificates are typically acceptable for internal use
- RVTools should accept them automatically
- If still failing, verify certificate chain is complete

### Authentication Errors

#### Error: "Invalid credentials"

**Symptoms**:
```
Authentication failed
Invalid username or password
```

**Solutions**:

```bash
# 1. Verify credentials
# Test manually
ssh -l administrator@vsphere.local vcenter.domain.com

# 2. Check username format
# Should be one of:
#   - administrator@vsphere.local
#   - DOMAIN\username
#   - username (if SSO configured)

# 3. Verify password
# Check for special characters needing escaping
# Use environment variables for complex passwords

# 4. Check account lockout
# (In vCenter: Administration > Users and Groups)
```

**Config verification**:
```toml
[default]
username = "administrator@vsphere.local"  # Correct format
password = "${VCENTER_PASS}"              # Use env var
```

Set environment variable:
```bash
export VCENTER_PASS="MyPassword@123"
rvtools
```

#### Error: "Access denied" or "Permission denied"

**Symptoms**:
```
Access denied: You do not have permission to perform this operation
Insufficient permissions for operation
```

**Solutions**:

```bash
# 1. Verify user has read-only role
# (In vCenter: Administration > Users and Groups)

# 2. Check permissions on affected objects
# (In vCenter: Navigator > Hosts > Clusters > Permissions)

# 3. Ensure minimal permissions:
#    - View vSphere objects
#    - View virtual machine summary
#    - View host configuration
#    - View network configuration
#    - View storage configuration

# 4. Run with verbose logging to see which object fails
rvtools --verbose
```

**vCenter permission setup**:
```
Role: Read-Only
Assigned to: rvtools_service_account
Applied to: Root folder (propagate)
```

### Data Collection Errors

#### Error: "No data collected" or "Empty results"

**Symptoms**:
```
Warning: No data collected for vInfo
Output file is empty or has headers only
```

**Causes**:
1. No VMs in vCenter
2. Objects are not accessible
3. Collection failed silently

**Solutions**:

```bash
# 1. Verify objects exist in vCenter
# (In vCenter: Navigator > VMs and Templates)

# 2. Check object count
# Run with verbose logging
rvtools --verbose

# 3. Check log file
# Look at the most recent log file
tail -f rvtools_YYYY-MM-DD_HH.MM.log

# 4. Verify data retrieval
# Enable debugging
rvtools --verbose --config ~/.rvtools.toml > debug.log 2>&1
```

**What to check in log**:
```
# Should see lines like:
## Processing vInfo module
Retrieved 150 virtual machines
Retrieved 5 ESXi hosts
Retrieved 2 clusters
```

#### Error: "Partial data collection" or "Some properties empty"

**Symptoms**:
```
Output file has many empty columns
Some VMs missing expected properties
```

**Causes**:
1. Properties not available in vSphere version
2. Object doesn't have property (normal)
3. Insufficient permissions for property
4. Performance collector timeout

**Solutions**:

```bash
# 1. Check vSphere version compatibility
rvtools --verbose | grep "vSphere version"

# 2. Verify properties for your version
# See: COMPATIBILITY.md

# 3. Check permissions on properties:
# (In vCenter: Administration > Roles)

# 4. If timeouts occur, increase thread timeout
# (Modify config or check log)

# 5. Increase timeout for large environments
# Reduce thread count if resource constrained
```

### Export Format Errors

#### Error: "XLSX file is corrupted"

**Symptoms**:
```
File cannot be opened in Excel
"The file is corrupted and cannot be opened"
```

**Causes**:
1. Disk space exhausted during export
2. Special characters in data
3. Very large file size
4. File write error

**Solutions**:

```bash
# 1. Check disk space
df -h /mnt/exports

# 2. Free up space
du -sh /mnt/exports/*
rm -rf /mnt/exports/old_*

# 3. Try different format (more stable)
rvtools --format csv

# 4. Check file size (XLSX has limits)
ls -lh rvtools_*.xlsx

# 5. Split export into smaller exports
# Use sheet filtering:
rvtools --sheets vInfo,vHost,vDatastore
rvtools --sheets vNetwork,vDisk,vPartition
```

#### Error: "CSV encoding issues"

**Symptoms**:
```
Special characters garbled
Non-ASCII characters not readable
```

**Solutions**:

```bash
# CSV is always UTF-8 encoded
# Open in Excel with UTF-8 setting:
# File > Open > CSV > Text Import Wizard > UTF-8

# Or convert with iconv
iconv -f UTF-8 -t ISO-8859-1 input.csv > output.csv
```

#### Error: "JSON parsing error"

**Symptoms**:
```
Unexpected token in JSON
JSON is invalid
```

**Solutions**:

```bash
# Validate JSON syntax
python3 -m json.tool rvtools_export.json

# Pretty print and check
python3 -c "import json; json.load(open('rvtools_export.json'))"

# Check for special characters
head -n 100 rvtools_export.json
```

### Performance Issues

#### Issue: "Very slow collection" or "Takes too long"

**Symptoms**:
```
vInfo collection taking > 5 minutes
Each sheet taking 30+ seconds
```

**Causes**:
1. Too many VMs (>5000)
2. Thread count too low
3. Network latency
4. vCenter performance issues
5. Batch operation timeouts

**Solutions**:

```bash
# 1. Increase thread count
[production]
threads = "32"    # From "auto"
format = "xlsx"   # Faster than CSV

# 2. Use batch collection where available
# (Automatic in vInfo - uses BatchPropertyCollector)

# 3. Check vCenter performance
# (In vCenter: Administration > System Configuration)

# 4. Monitor network
# Check for dropped packets, high latency
iperf3 -c vcenter.domain.com

# 5. Reduce data collection scope
# Use sheet filtering to collect less data
rvtools --sheets vInfo,vHost
```

#### Issue: "High memory usage"

**Symptoms**:
```
RVTools uses > 4 GB RAM
System starts swapping
Out of memory error
```

**Causes**:
1. Collecting too much data at once
2. Large number of objects
3. Inefficient collection method
4. Memory leak (possible bug)

**Solutions**:

```bash
# 1. Reduce thread count
[default]
threads = "4"     # From "auto" or "16"

# 2. Monitor memory usage
top -p $(pgrep -f rvtools)

# 3. Split collection
# Collect fewer sheets at a time
rvtools --sheets vInfo
rvtools --sheets vHost

# 4. Increase system memory
# If possible, add more RAM to collection system

# 5. Use smaller batch size
# (May require code modification)
```

### Log File Analysis

#### Finding Log Files

```bash
# Log files in current directory
ls -la rvtools_*.log

# Check most recent
tail -f rvtools_2026-03-20_14.30.log

# Search for errors
grep ERROR rvtools_*.log
grep WARNING rvtools_*.log
```

#### Interpreting Log Messages

**Normal startup**:
```
2026-03-20 14:30:00,123 - rvtools - INFO - Starting RVTools collection
2026-03-20 14:30:00,234 - rvtools - DEBUG - Connecting to vcenter.domain.com
2026-03-20 14:30:02,456 - rvtools - DEBUG - Connection successful
```

**Normal data collection**:
```
2026-03-20 14:30:10,123 - rvtools - DEBUG - ## Processing vInfo module
2026-03-20 14:30:12,456 - rvtools - DEBUG - Retrieved 150 virtual machines
2026-03-20 14:30:15,789 - rvtools - DEBUG - ## Processing vHost module
```

**Warnings (non-fatal)**:
```
2026-03-20 14:30:20,111 - rvtools - WARNING - Property 'customValue' not available
2026-03-20 14:30:21,222 - rvtools - WARNING - No data collected for vHealth
```

**Errors (may halt collection)**:
```
2026-03-20 14:30:30,111 - rvtools - ERROR - Failed to retrieve vInfo: timeout
2026-03-20 14:30:31,222 - rvtools - ERROR - Connection lost during vHost collection
```

## Testing and Validation

### Health Check Script

```bash
#!/bin/bash
# Test vCenter connectivity
echo "Testing RVTools health..."

# 1. Config file
if [ ! -f ~/.rvtools.toml ]; then
    echo "❌ Config file not found"
    exit 1
fi
echo "✓ Config file exists"

# 2. vCenter connectivity
VCENTER=$(grep "^vcenter" ~/.rvtools.toml | cut -d'"' -f2)
if ping -c 1 "$VCENTER" > /dev/null; then
    echo "✓ vCenter reachable: $VCENTER"
else
    echo "❌ vCenter unreachable: $VCENTER"
    exit 1
fi

# 3. HTTPS connectivity
if timeout 5 bash -c "echo >/dev/tcp/$VCENTER/443"; then
    echo "✓ HTTPS port 443 open"
else
    echo "❌ HTTPS port 443 not accessible"
    exit 1
fi

# 4. Disk space
EXPORT_DIR=$(grep "^directory" ~/.rvtools.toml | cut -d'"' -f2)
DISK_FREE=$(df "$EXPORT_DIR" | tail -1 | awk '{print $4}')
if [ "$DISK_FREE" -gt 1000000 ]; then
    echo "✓ Sufficient disk space: ${DISK_FREE}KB"
else
    echo "❌ Low disk space: ${DISK_FREE}KB"
    exit 1
fi

# 5. Permissions
if [ -w "$EXPORT_DIR" ]; then
    echo "✓ Export directory writable: $EXPORT_DIR"
else
    echo "❌ Export directory not writable: $EXPORT_DIR"
    exit 1
fi

echo ""
echo "All health checks passed! Ready to run RVTools."
```

Run health check:
```bash
chmod +x health_check.sh
./health_check.sh
```

### Verification After Export

```bash
#!/bin/bash
# Verify export completeness

EXPORT_FILE="rvtools_export.xlsx"

echo "Verifying $EXPORT_FILE..."

# 1. File exists
if [ ! -f "$EXPORT_FILE" ]; then
    echo "❌ Export file not found"
    exit 1
fi
echo "✓ Export file exists"

# 2. File size reasonable
SIZE=$(stat -f%z "$EXPORT_FILE" 2>/dev/null || stat -c%s "$EXPORT_FILE")
if [ "$SIZE" -gt 1000000 ]; then
    echo "✓ File size: $(numfmt --to=iec-i --suffix=B $SIZE 2>/dev/null || echo $SIZE)"
else
    echo "⚠ File may be incomplete: $SIZE bytes"
fi

# 3. File is valid Excel (if unzip available)
if unzip -t "$EXPORT_FILE" > /dev/null 2>&1; then
    echo "✓ XLSX file integrity verified"
else
    echo "❌ XLSX file is corrupted"
    exit 1
fi

echo "✓ Export verification complete"
```

## Support and Debugging

### Generating Debug Information

```bash
# Run with maximum verbosity
rvtools --verbose --config ~/.rvtools.toml > debug_full.log 2>&1

# Include system info
echo "=== System Information ===" >> debug_full.log
python3 --version >> debug_full.log
uname -a >> debug_full.log
df -h >> debug_full.log
free -h >> debug_full.log

# Include config (without passwords)
echo "=== Configuration ===" >> debug_full.log
grep -v password ~/.rvtools.toml >> debug_full.log

# Share debug log for troubleshooting
# (Remove any sensitive data first)
```

### Getting Help

If issues persist:

1. **Check logs**: `tail -f rvtools_*.log`
2. **Enable verbose**: `--verbose` flag
3. **Verify config**: Review ~/.rvtools.toml
4. **Test connectivity**: `ping vcenter.domain.com`
5. **Check permissions**: Verify vCenter user role
6. **Try default settings**: Use minimal config first
7. **Collect debug logs**: Use health check script

