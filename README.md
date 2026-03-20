# rvtools python
Application to be executed on Linux and collect all information from vCenter

The idea is to be a similar application as RVTools [1] the main difference is, the application from website was designed to be executed only on MS platform, this version will be written in python 3 so will be possible execute on Linux environment.

About the final result, the idea is generate similar output as RVTools in multiple formats: **CSV files, JSON (separate files), or JSON (unified file)**.

The point here is not about COPY but just improve the Python skill and use the project [1] as reference once this one is a fantastic product!!!

Thank you and feel free to request Features / Enhancements.

Ps.: Necessary python 3.9 or greater.

## Features

✅ **All 27 RVTools sheets implemented:**
- VMs: vInfo, vCPU, vMemory, vDisk, vPartition, vNetwork, vCD, vSnapshot, vUSB, vTools
- Infrastructure: vRP, vCluster, vHost, vDatastore, vMultiPath
- Networking: vHBA, vNIC, vSwitch, vPort, dvSwitch, dvPort, vSC_VMK
- Metadata: vSource, vLicense, vFileInfo, vHealth, vMetaData

✅ **Multiple export formats:**
- **XLSX (default)** - All sheets in single workbook with styling
- CSV (individual files)
- JSON (individual files per sheet)
- JSON (unified file with all sheets)

✅ **Parallel processing** - Multi-threaded data collection (auto-detected, min 8 threads)

✅ **Comprehensive logging** - Dual output to console and file with timestamps

✅ **Error resilience** - Missing properties/sheets don't break collection

✅ **Timestamp-based filenames** (e.g., rvtools_2026-03-20_10.37.xlsx)

# How to use

## Option 1: Run without installing (from repository)

```bash
cd /path/to/rvtools_python
uv venv
. .venv/bin/activate
uv pip install -r requirements.txt
python -m rvtools
```

## Option 2: Install as editable package with uv

```bash
cd /path/to/rvtools_python
uv venv
. .venv/bin/activate
uv pip install -e .
rvtools
```

## Configuration

On the first run, create `~/.rvtools.conf`:
```
vcenter=<fqdn>
username=<vcenter username>
password=<password>
directory=<directory>
```
The directory is where all exported files will be saved.

## Command-line options

```bash
rvtools --help
```

Options:
- `-s, --host` - vCenter FQDN
- `-u, --username` - vCenter username
- `-p, --password` - vCenter password
- `-d, --directory` - Output directory for exports
- `-f, --format` - Export format (default: xlsx)
  - `xlsx` - All sheets in single Excel workbook
  - `csv` - Individual CSV files per sheet
  - `json-separate` - Individual JSON files per sheet
  - `json-unified` - All sheets in single JSON file
- `--threads` - Number of parallel threads (default: auto = min(8, cpu_count))
- `-v, --verbose` - Show additional info

## Examples

Export as XLSX (default):
```bash
rvtools --host vcenter.example.com --username admin --password pass --directory /export
```

Export as CSV with 4 threads:
```bash
rvtools -s vcenter.example.com -u admin -p pass -d /export -f csv --threads 4
```

Export as JSON unified format:
```bash
rvtools -s vcenter.example.com -u admin -p pass -d /export -f json-unified
```

## Output files

Default XLSX output:
- `rvtools_2026-03-20_10.37.xlsx` (contains all 27 sheets with styling)

CSV format:
- `vInfo_2026-03-20_10.37.csv`
- `vHealth_2026-03-20_10.37.csv`
- ... (one per sheet)

JSON unified format:
- `rvtools_2026-03-20_10.37.json` (all sheets in single file)

Logs are saved to:
- `rvtools_2026-03-20_10.37.log` (in export directory)


You can just update the information on the file to be seamless and generate all reports without asking for the password again, or you are able to pass the information all the time as parameter

```
$ rvtools --help
usage: rvtools [-h] [-s HOST] [-u USERNAME] [-p PASSWORD] [-d DIRECTORY]
               [-f {csv,json-separate,json-unified}] [-v VERBOSE]

               [-v VERBOSE]

RVTools Python parameters

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --host HOST  vCenter server to connect to
  -u USERNAME, --username USERNAME
                        vCenter username
  -p PASSWORD, --password PASSWORD
                        vCenter user password
  -d DIRECTORY, --directory DIRECTORY
                        Directory where will be saved all export files.
                        Should be empty or not exist yet
  -f {csv,json-separate,json-unified}, --format {csv,json-separate,json-unified}
                        Export format: csv (default), json-separate (individual
                        JSON files), or json-unified (all sheets in one file)
  -v VERBOSE, --verbose VERBOSE
                        Show additional info
```

**Examples:**

Export all sheets as CSV files (default):
```
$ rvtools -s vcenter.example.com -u admin@vsphere.local -p password -d /tmp/export
```

Export as individual JSON files:
```
$ rvtools -s vcenter.example.com -u admin@vsphere.local -p password -d /tmp/export -f json-separate
```

Export all sheets in a single unified JSON file:
```
$ rvtools -s vcenter.example.com -u admin@vsphere.local -p password -d /tmp/export -f json-unified
```

The result will be the exported files created on the directory defined on the conf file by `directory=<directory>` or via CLI by `-d DIRECTORY`.
```
vInfo_2026-03-20_10.37.csv
vHealth_2026-03-20_10.37.csv
vPartition_2026-03-20_10.37.csv
... (all 27 sheets)
```

Or if using JSON unified format:
```
rvtools_2026-03-20_10.37.json
```

Hope you enjoy it. Still working to improve/add all features. Feel free to send your feedback or just submit a new Issue [here](https://github.com/waldirio/rvtools_python/issues).

Best
Waldirio

[1]. https://www.robware.net/rvtools/