
# HSA Reimbursement CLI

**HSA Reimbursement CLI** is a command-line tool designed to help users manage healthcare receipts of Health Savings Account. The app enables tracking reimbursements efficiently. It allows users to analyze receipts, request reimbursements, back up data, restore from backups, and generate reports, all through an intuitive command-line interface.

>All transactions are stored in a local SQLite database.

---

## Features

- **Receipt Management**:
  - Scan directories for healthcare receipts with automatic parsing of file metadata.
  - Validate receipt file naming conventions.
- **Reimbursement Tracking**:
  - Request optimal reimbursement amounts based on available receipts.
  - Track reimbursed and remaining amounts.
- **Backup and Restore**:
  - Backup reimbursement data to JSON files.
  - Restore data from backups.
- **Reporting**:
  - Generate detailed reimbursement reports.
  - Export reports to CSV or JSON formats.
- **User-Friendly Commands**:
  - Easy-to-use commands with a consistent interface.
  - Version tracking for updates and compatibility.

---

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)
- [File Naming Convention](#file-naming-convention)
- [Development Notes](#development-notes)
- [Local Testing](#local-testing)
- [Releasing to Pypi](#releasing-to-pypi)
- [License](#license)

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/radian21/hsa_reimburse.git
   cd hsa_reimburse
   ```

2. Install the package locally:
   ```bash
   pip install .
   ```

3. Verify installation:
   ```bash
   hsa --version
   ```

---

## Assumptions

This app assumes that the user is already saving their medical expense receipts. The app supports receipt files with any file extension because the app only parses the file names, not the file contents.

Filenames are assumed to meet the following condition:

`YYYYMMDD_#.##_anyDescription`

- `YYYYMMDD` is the date the receipt occurred on.
- `#.##` is a decimal number representing the value of the receipt in a currency.
- `anyDescription` is an optional string that can be included as desired.

Each of these parts are expected to be delimited by the `_` (underscore) character. By using the metadata from this format, the app can track reimbursement amounts and correlate files to those amounts.

---

## Usage

Run the `hsa` command with a subcommand:

```bash
hsa <command> [options]
```

### Examples:
- Scan receipts in a directory:
  ```bash
  hsa init --path "C:\Receipts"
  ```

  >The default path to the receipts will be used if no path is provided. Run `hsa config` to see file paths.

- Request a reimbursement:
  ```bash
  hsa request 1000
  ```

- Generate a summary:
  ```bash
  hsa summary
  ```

- Generate a report for tracability:
  ```bash
  hsa report
  ```

  Export a report to `json`:
  ```
  hsa report --export json
  ```

  Export a report to `csv`:

  ```
  hsa report --export csv
  ```

---

## Commands

### `init`
Scan a directory for receipts and add them to the database creating the database if necessary. It is safe to run this repeatedly as the database will not get re-created if it already exists and historical transactions will be preserved.

```bash
hsa init <path>

Example:

`hsa init --path "C:\HSA Receipts"`
```

- **Options**:
  - `<path>`: Path to the directory containing receipt files.

---

### `request`
Request a reimbursement for a specific amount. The tool will select optimal receipts that sum up to or just below the requested amount.

```bash
hsa request <amount>
```

- **Options**:
  - `<amount>`: The reimbursement amount requested.

---

### `reset`
Reset all reimbursement transactions after creating a backup. This does NOT rescan the receipts source directory. Run `hsa init` to rescan receipt files.

```bash
hsa reset
```

- Prompts for confirmation before proceeding.
- Saves a JSON backup of all reimbursement transactions before resetting the database. This backup is stored in `~/Documents/hsa-reimburse/backups` and can be used to restore the database as desired. 

---

### `restore`
Restore reimbursement data from a backup file.

```bash
hsa restore <backup_file>
```

- **Options**:
  - `<backup_file>`: Path to the JSON backup file.

> The default backup location is `~/Documents/hsa-reimburse/backups`

---

### `summary`
Show a summary of total reimbursed and available amounts.

```bash
hsa summary
```

---

### `config`
Display current application configuration. The `hsa_config.json` file is stored in the program directory.

```bash
hsa config
```

---

### `report`
Generate a detailed report of all reimbursements.

```bash
hsa report [--export <format>]
```

- **Options**:
  - `--export <format>`: Export report to `csv` or `json`.

---

> Exported report files are saved to: `~/Documents/hsa-reimburse/exports`

### `check-invalid`
Check for receipt files that do not match the expected naming convention.

```bash
hsa check-invalid [--path <path>]
```

- **Options**:
  - `--path <path>`: Directory to check. Defaults to the receipts directory.

---

## File Naming Convention

Receipt files must follow this format:

```plaintext
YYYYMMDD_DollarAmount_OptionalNote.extension
```

- **YYYYMMDD**: Date of the receipt.
- **DollarAmount**: Reimbursable amount in decimal format.
- **OptionalNote**: Additional details (optional).
- **Supported Extensions**:
  - .pdf
  - .jpg
  - .png
  - All other ignored

### Valid Examples:
- `20240101_150.00_PrescriptionReceipt.pdf`
- `20240215_200.50.png`
- `20240305_1056_CVS.jpg`

---

## Development Notes

### Global Variables
- **Database File**: `hsa_reimburse.db`
- **Backup Directory**: `~/Documents/.hsa_reimburse/backups`
- **Export Directory**: `~/Documents/.hsa_reimburse/exports`
- **Receipts Directory**: Configurable via `RECEIPTS_DIR`.

### Key Python Libraries
- `sqlite3`: Database for storing receipt and reimbursement data.
- `argparse`: Command-line argument parsing.
- `json`: Data serialization for backups and exports.
- `csv`: Exporting data to CSV format.
- `os`: File and path handling.

### Code Structure
- Commands are implemented as separate functions for modularity.
- SQL queries are used for database operations.
- Errors are handled gracefully with informative messages.

---

## Local Testing

### Uninstall, Rebuild, and Reinstall Locally

To test changes to the project locally, follow these steps to uninstall the current version, rebuild the package, and reinstall the updated version.

#### 1. Uninstall the Existing Package
Before installing a new version, uninstall the previous version to avoid conflicts.

```
pip uninstall hsa-reimburse -y
```

Verify that the package has been removed by running:

```
pip list | grep hsa-reimburse  # On Linux/MacOS
pip list | findstr hsa-reimburse  # On Windows
```

#### 2. Clean Previous Build Files
Remove any previously generated build artifacts to ensure a clean build.

Linux/MacOS:

```
rm -rf dist/ build/ *.egg-info
```

Windows PowerShell:
```
Remove-Item -Recurse -Force dist, build, *.egg-info
```

#### 3. Rebuild the Package
Rebuild the package using the build module:

```
python -m build
```

Upon successful build, check the dist/ folder for files like:

```
dist/
  hsa_reimburse-0.1.0-py3-none-any.whl
  hsa_reimburse-0.1.0.tar.gz
```

#### 4. Reinstall the Package Locally
Install the newly built package using pip:

```
pip install dist/hsa_reimburse-0.1.0-py3-none-any.whl
```

#### 5. Verify Installation
Check if the package was installed correctly:

```
hsa --version
```

Expected output:

```
hsa 0.2.0
```
---


## Releasing to Pypi

### Incrementing the Version Number and Preparing for a New Release
Before publishing a new version to PyPI, you need to update the version number across all relevant files.

#### 1. Update the Version Number
Update the following files:

`src/hsa_reimburse_package_radian21/__init__.py`

```
__version__ = "0.2.0"  # Update to the new version
```

`setup.py` (if not dynamically fetching version)

```
setup(
    name="hsa-reimburse",
    version="0.2.0",
    packages=find_packages(where="src"),
)
```

`pyproject.toml`
```
[project]
name = "hsa-reimburse"
version = "0.2.0"
```

`README.md` (if version is mentioned)
Update any references to the version number:

```
# HSA Reimburse CLI - Version 0.2.0
```

#### 2. Commit the Changes
After updating the version, commit the changes:

```
git add .
git commit -m "Bump version to 0.2.0"
git push origin main
```

#### 3. Build the New Release
Run the build process to package the updated version:

```
python -m build
```
Confirm that the new version files are in the dist/ directory.

#### 4. Upload to PyPI
Ensure you have the twine tool installed:

```
pip install twine
```

Upload the new package to PyPI:
```
twine upload dist/*
```

When prompted, enter your PyPI username and password.

#### 5. Verify on PyPI
After successful upload, verify that the new version is available on [PyPI](https://pypi.org/project/hsa-reimburse/).


#### 6. Install the Package from PyPI
To ensure the new version works correctly, install it from PyPI:

```
pip install hsa-reimburse --upgrade
```

Verify the installation:
```
hsa --version
```

#### 7. Prepare for the Next Development Cycle
Once the new version is published, increment the version number for development purposes (e.g., 0.3.0-dev).

Update __init__.py with a development version:
```
__version__ = "0.3.0-dev"
```
Commit the change:
```
git commit -am "Prepare for next development cycle 0.3.0-dev"
git push origin main
```

#### 8. Automate Version Bumping (Optional)
You can use tools like bumpver to automate versioning:

```
pip install bumpver
bumpver update --minor  # Increment minor version
```






---

## License

This project is licensed under the [MIT License](LICENSE).

---
