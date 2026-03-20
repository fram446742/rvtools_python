"""Module responsible for exporting data as JSON files"""
import json


def json_print_separate(filename, data, directory):
    """
    Export data as a separate JSON file with timestamp

    Args:
        filename: Output filename (already includes timestamp)
        data: List of dictionaries to export
        directory: Output directory path
    """
    full_file_path = f"{directory}/{filename}"

    print(f"## Creating {full_file_path} file.")

    with open(full_file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def json_print_unified(filename, unified_data, directory):
    """
    Export all sheets as a unified JSON file

    Args:
        filename: Output filename (already includes timestamp)
        unified_data: Dictionary with all sheets {sheet_name: [data]}
        directory: Output directory path
    """
    full_file_path = f"{directory}/{filename}"

    print(f"## Creating unified {full_file_path} file.")

    with open(full_file_path, 'w') as f:
        json.dump(unified_data, f, indent=2, default=str)
