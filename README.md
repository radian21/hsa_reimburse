
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

### Example:
- Scan receipts in a directory:
  ```bash
  hsa init ~/path/to/receipts
  ```

  >The default path to the receipts will be used if no path is provided. The default path is: `~/Documents/hsa-reimburse/receipts`

- Request a reimbursement:
  ```bash
  hsa request 1000
  ```

- Generate a summary:
  ```bash
  hsa summary
  ```

---

## Commands

### `init`
Scan a directory for receipts and add them to the database.

```bash
hsa init <path>
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
Reset all reimbursement transactions after creating a backup.

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
- **Supported Extensions**: Any. It doesn't matter. These are your file and this app only reads data from the file names.

### Example:
- `20240101_150.00_PrescriptionReceipt.pdf`
- `20240215_200.50.png`

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

## License

This project is licensed under the [MIT License](LICENSE).

---
