#!/usr/bin/env python3
import os
import sqlite3
import json
from datetime import datetime
import argparse
from hashlib import sha256
import re
from datetime import datetime
import csv
from . import __version__

CONFIG_FILE = "hsa_config.json"

# Default parameter values
DB_FILE = os.path.expanduser("~/Documents/hsa-reimburse/hsa_reimburse.db")
BACKUP_DIR = os.path.expanduser("~/Documents/hsa-reimburse/backups")
EXPORT_DIR = os.path.expanduser("~/Documents/hsa-reimburse/exports")
RECEIPTS_DIR = os.path.expanduser("~/Documents/hsa-reimburse/receipts")

def connect_db():
    """Connect to the SQLite database with explicit date/time handling."""
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    # Register adapters and converters for datetime
    sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
    sqlite3.register_converter("DATETIME", lambda s: datetime.fromisoformat(s.decode("utf-8")))

    return conn


def initialize_database():
    """Initialize the database tables if not already created."""
    conn = connect_db()
    cursor = conn.cursor()

    # Create receipts table with added path column
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            path TEXT,
            date TEXT,
            amount REAL,
            note TEXT,
            is_reimbursed BOOLEAN DEFAULT 0,
            file_hash TEXT UNIQUE
        )
    """)

    # Create reimbursements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reimbursements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            amount REAL,
            receipts_used TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()



def update_config(key, value):
    """Update the configuration file with the given key-value pair."""
    config = load_config()
    config[key] = os.path.abspath(value)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)




def load_config():
    """Load the configuration file if it exists, otherwise return defaults."""
    default_config = {
        "database_path": os.path.abspath(DB_FILE),
        "receipts_dir": os.path.abspath(RECEIPTS_DIR),
        "backup_dir": os.path.abspath(BACKUP_DIR),
        "export_dir": os.path.abspath(EXPORT_DIR),
    }

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            stored_config = json.load(f)
            default_config.update(stored_config)

    return default_config



def print_config():
    """Print the current application configuration."""
    config = load_config()

    config_data = {
        "Database Path": config["database_path"],
        "Receipts Directory": config["receipts_dir"],
        "Backup Directory": config["backup_dir"],
        "Export Directory": config["export_dir"]
    }

    print("\nCurrent Application Configuration:")
    print("=" * 40)
    for key, value in config_data.items():
        print(f"{key}: {value}")
    print("=" * 40)


    

def scan_receipts(path=None):
    """Scan the folder for new receipts and add them to the database."""
    config = load_config()

    if path:
        path = os.path.abspath(os.path.normpath(path))  # Convert UNC path to absolute path
        update_config("receipts_dir", path)
    else:
        path = config["receipts_dir"]

    # Debugging: Check the path being used
    print(f"Using receipts directory: {path}")

    if not os.path.exists(path):
        print(f"Error: Directory not found: {path}")
        return

    initialize_database()

    conn = connect_db()
    cursor = conn.cursor()

    # Track changes for logging
    new_count, updated_count, unchanged_count = 0, 0, 0

    scanned_files = set()

    try:
        files = os.listdir(path)
        if not files:
            print(f"Warning: No files found in directory {path}")
        
        for file in files:
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                print(f"Processing: {file_path}")  # Debugging output

                # Parse metadata from filename
                file_base, file_ext = os.path.splitext(file)
                if file_ext.lower() not in [".pdf", ".png", ".jpg"]:  # Skip unsupported files
                    continue

                parts = file_base.split("_") if "_" in file_base else file_base.split(".")
                date = parts[0]
                amount = float(parts[1])
                note = "_".join(parts[2:]) if len(parts) > 2 else "No note"

                # Compute file hash to detect changes
                file_hash = sha256(open(file_path, 'rb').read()).hexdigest()

                # Check if the file already exists in the database
                cursor.execute("SELECT filename, file_hash FROM receipts WHERE file_hash = ?", (file_hash,))
                existing_record = cursor.fetchone()

                if existing_record:
                    existing_filename = existing_record[0]
                    if existing_filename != file:
                        # Update the record if the filename has changed
                        cursor.execute("""
                            UPDATE receipts SET filename=?, path=?, date=?, amount=?, note=?
                            WHERE file_hash=?
                        """, (file, path, date, amount, note, file_hash))
                        updated_count += 1
                    else:
                        unchanged_count += 1
                else:
                    cursor.execute("""
                        INSERT INTO receipts (filename, path, date, amount, note, file_hash)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (file, path, date, amount, note, file_hash))
                    new_count += 1

                scanned_files.add(file)

    except Exception as e:
        print(f"Error accessing directory: {e}")

    # Find orphaned records (files no longer in the scanned directory)
    cursor.execute("SELECT filename FROM receipts")
    stored_files = {row[0] for row in cursor.fetchall()}
    orphaned_files = stored_files - scanned_files

    if orphaned_files:
        print("Warning: Some files are no longer present in the directory:")
        for orphan in orphaned_files:
            print(f"  - {orphan}")

    conn.commit()
    conn.close()

    # Summary report
    print("Receipts scanned and database updated.")
    print(f"New receipts added: {new_count}")
    print(f"Receipts updated: {updated_count}")
    print(f"Receipts unchanged: {unchanged_count}")
    if orphaned_files:
        print(f"Receipts missing from the scanned directory: {len(orphaned_files)}")






def check_invalid_files(path=None):
    """Check for files that do not match the expected naming convention."""
    path = path or RECEIPTS_DIR  # Use default path if none is provided

    if not os.path.exists(path):
        print(f"Directory not found: {path}")
        return

    print(f"Checking for invalid files in: {path}")
    invalid_files = []

    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            file_base, file_ext = os.path.splitext(file)
            if file_ext.lower() in [".db"]:  # Ignore .db extension
                continue

            # Expected format: YYYYMMDD_DollarAmount_OptionalNote.pdf
            parts = file_base.split("_")
            if len(parts) < 2:
                invalid_files.append(file)
                continue

            # Validate date (first part)
            date_str = parts[0]
            try:
                datetime.strptime(date_str, "%Y%m%d")
            except ValueError:
                invalid_files.append(file)
                continue

            # Validate dollar amount (second part)
            amount_str = parts[1]
            if not re.match(r"^\d+(\.\d{1,2})?$", amount_str):
                invalid_files.append(file)
                continue

            # The third part (note) is optional and doesn't require validation

    # Report invalid files
    if invalid_files:
        print("Invalid Files:")
        for invalid_file in invalid_files:
            print(f"  - {invalid_file}")
    else:
        print("All files match the expected naming convention.")



def request_reimbursement(amount):
    """Find the optimal receipts for reimbursement."""
    initialize_database()

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, filename, amount FROM receipts WHERE is_reimbursed = 0")
    receipts = cursor.fetchall()

    receipts.sort(key=lambda x: x[2], reverse=True)  # Sort by amount, descending

    selected_receipts = []
    total = 0.0
    for receipt in receipts:
        if total + receipt[2] <= amount:
            selected_receipts.append(receipt)
            total += receipt[2]

    print(f"Requested Amount: ${amount:.2f}")
    print("Selected Receipts:")
    for receipt in selected_receipts:
        print(f"  - {receipt[1]} (${receipt[2]:.2f})")
    print(f"Total: ${total:.2f}")

    confirm = input("Confirm this reimbursement? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Reimbursement cancelled.")
        conn.close()
        return

    # Mark receipts as reimbursed
    receipt_ids = [r[0] for r in selected_receipts]
    current_date = datetime.now().date().isoformat()  # Explicit conversion
    timestamp = datetime.now().isoformat()           # Explicit conversion

    cursor.execute("INSERT INTO reimbursements (date, amount, receipts_used, timestamp) VALUES (?, ?, ?, ?)", (
        current_date, total, json.dumps(receipt_ids), timestamp
    ))
    cursor.executemany("UPDATE receipts SET is_reimbursed = 1 WHERE id = ?", [(rid,) for rid in receipt_ids])

    conn.commit()
    conn.close()
    print(f"Reimbursement of ${total:.2f} recorded.")


def reset_reimbursements():
    """Reset reimbursement transactions."""
    print("WARNING: This action will delete all reimbursement transactions.")
    confirmation = input("Type 'YES' to confirm, or anything else to cancel: ")
    if confirmation != "YES":
        print("Reset cancelled.")
        return

    backup_reimbursements()

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reimbursements")
    cursor.execute("UPDATE receipts SET is_reimbursed = 0")
    conn.commit()
    conn.close()

    print("Reimbursement records have been reset.")



def backup_reimbursements(backup_path=None):
    """Backup reimbursement data to a JSON file."""
    config = load_config()
    backup_dir = backup_path or config["backup_dir"]
    update_config("backup_dir", backup_dir)

    os.makedirs(backup_dir, exist_ok=True)
    
    backup_file = os.path.join(
        backup_dir, f"backup_reimbursements_{datetime.now().isoformat().replace(':', '-')}.json"
    )

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, amount, receipts_used, timestamp FROM reimbursements")
    reimbursements = cursor.fetchall()
    conn.close()

    if reimbursements:
        with open(backup_file, "w", encoding="utf-8") as f:
            # Convert rows (tuples) into dictionaries
            column_names = ["id", "date", "amount", "receipts_used", "timestamp"]
            reimbursement_dicts = [dict(zip(column_names, row)) for row in reimbursements]
            json.dump(reimbursement_dicts, f, indent=4)
        print(f"Backup created: {backup_file}")
    else:
        print("No reimbursements to back up.")



def restore_reimbursements(backup_file):
    """Restore reimbursement data from a backup file."""
    if not os.path.exists(backup_file):
        print(f"Backup file not found: {backup_file}")
        return

    # Load the backup file
    with open(backup_file, "r", encoding="utf-8") as f:
        reimbursements = json.load(f)

    conn = connect_db()
    cursor = conn.cursor()

    # Iterate through the list of reimbursement dictionaries
    for reimbursement in reimbursements:
        cursor.execute("""
            INSERT INTO reimbursements (id, date, amount, receipts_used, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            reimbursement["id"],  # Unique identifier
            reimbursement["date"],  # Date of the reimbursement
            reimbursement["amount"],  # Total reimbursed amount
            reimbursement["receipts_used"],  # Receipt IDs as JSON string
            reimbursement["timestamp"],  # Timestamp of the transaction
        ))

    conn.commit()
    conn.close()

    print(f"Restored {len(reimbursements)} reimbursement transactions from backup.")




def summary():
    """Show summary of total reimbursed and available amounts."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM receipts WHERE is_reimbursed = 0")
    available = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(amount) FROM reimbursements")
    reimbursed = cursor.fetchone()[0] or 0.0

    conn.close()

    print(f"Total Available for Reimbursement: ${available:.2f}")
    print(f"Total Reimbursed: ${reimbursed:.2f}")


def generate_report(export_format=None):
    """Generate a report of all reimbursements, with options to export to CSV or JSON."""
    initialize_database()

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, amount, receipts_used, timestamp
        FROM reimbursements
        ORDER BY timestamp ASC
    """)
    reimbursements = cursor.fetchall()
    conn.close()

    if not reimbursements:
        print("No reimbursements found.")
        return

    # Prepare data for export
    export_data = []

    # Display report
    print(f"{'Date':<15}{'Amount':<10}Files")
    print("=" * 50)

    for reimbursement in reimbursements:
        date = reimbursement[0]
        amount = reimbursement[1]
        receipt_ids = json.loads(reimbursement[2])

        # Fetch filenames for these receipt IDs
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT filename FROM receipts WHERE id IN ({','.join(['?']*len(receipt_ids))})", receipt_ids)
        filenames = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Print to console
        print(f"{date:<15}${amount:<9.2f}")
        for filename in filenames:
            print(f"  - {filename}")
        print()  # Blank line between transactions

        # Add to export data
        export_data.append({
            "date": date,
            "amount": amount,
            "files": filenames
        })

    # Export to file if format is specified
    if export_format:
        if export_format == "csv":
            export_to_csv(export_data)
        elif export_format == "json":
            export_to_json(export_data)



def export_to_csv(data, export_path=None):
    """Export reimbursement data to a CSV file."""
    config = load_config()
    export_dir = export_path or config["export_dir"]
    update_config("export_dir", export_dir)

    os.makedirs(export_dir, exist_ok=True)

    export_file = os.path.join(
        export_dir, f"reimbursements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    with open(export_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Amount", "Files"])
        for record in data:
            writer.writerow([record["date"], record["amount"], "; ".join(record["files"])])
    
    print(f"Report exported to CSV: {export_file}")



def export_to_json(data, export_path=None):
    """Export reimbursement data to a JSON file."""
    config = load_config()
    export_dir = export_path or config["export_dir"]
    update_config("export_dir", export_dir)

    os.makedirs(export_dir, exist_ok=True)

    export_file = os.path.join(
        export_dir, f"reimbursements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"Report exported to JSON: {export_file}")



def main():
    parser = argparse.ArgumentParser(description="HSA Reimbursement CLI")
    parser.add_argument("--version", action="version", version=f"hsa-reimburse {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Scan a directory for receipts").add_argument("--path", help="Path to the directory containing the receipts. Defaults to RECEIPTS_DIR.")
    subparsers.add_parser("request", help="Request reimbursement").add_argument("amount", type=float)
    subparsers.add_parser("reset", help="Reset reimbursements with backup")
    subparsers.add_parser("restore", help="Restore reimbursements from backup").add_argument("backup_file")
    subparsers.add_parser("summary", help="Show summary of reimbursements")
    subparsers.add_parser("config", help="Display current application configuration")
    #subparsers.add_parser("backup", help="Backup reimbursements").add_argument("--path", help="Path to store backups")
    #subparsers.add_parser("export", help="Export reports").add_argument("--path", help="Path to export reports")

    report_parser = subparsers.add_parser("report", help="Generate a report of all reimbursements")
    report_parser.add_argument("--export", choices=["csv", "json"], help="Export the report to CSV or JSON")

    invalid_files_parser = subparsers.add_parser("check-invalid", help="Check for files with invalid naming convention")
    invalid_files_parser.add_argument("--path", help="Path to the directory to check. Defaults to RECEIPTS_DIR.")


    args = parser.parse_args()

    if args.command == "init":
        scan_receipts(args.path)
    elif args.command == "request":
        request_reimbursement(args.amount)
    elif args.command == "reset":
        reset_reimbursements()
    elif args.command == "restore":
        restore_reimbursements(args.backup_file)
    elif args.command == "summary":
        summary()
    elif args.command == "report":
        generate_report(export_format=args.export)
    elif args.command == "check-invalid":
        check_invalid_files(args.path)
    elif args.command == "config":
        print_config()

if __name__ == "__main__":
    main()


