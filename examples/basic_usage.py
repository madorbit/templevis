"""
Basic Usage Example

This example demonstrates the programmatic usage of TempleVis for processing
a temple worker schedule PDF and generating CSV reports.

Note: For command-line usage, use:
python -m templevis process <path_to_pdf_file>

This example shows how to use TempleVis as a Python module for more advanced use cases.
"""

from templevis import PDFTableProcessor

def main():
    # Initialize the processor with a PDF file
    processor = PDFTableProcessor('schedule.pdf')

    # Extract all table data
    print("Extracting table data...")
    df = processor.extract_table_data()
    if df is not None:
        print(f"Found {df.shape[0]} rows and {df.shape[1]} columns")

        # Get list of worker names
        names = processor.get_names()
        print(f"\nFound {len(names)} workers:")
        for name in names[:5]:
            print(f"- {name}")
        if len(names) > 5:
            print("...")

        # Find INI tasks
        ini_tasks = processor.get_ini_tasks()
        print(f"\nFound {len(ini_tasks)} INI tasks:")
        for task in ini_tasks[:5]:
            print(f"- {task['name']}: {task['task']} ({task['start_time']} - {task['end_time']})")
        if len(ini_tasks) > 5:
            print("...")

        # Generate CSV reports
        print("\nGenerating CSV reports...")
        output_dir = 'output'
        if processor.generate_csv_reports(output_dir):
            print(f"\nReports generated in '{output_dir}':")
            print("1. complete_schedule.csv - Full schedule")
            print("2. period_1_tasks.csv - Tasks 6:00-6:45 PM")
            print("3. period_2_tasks.csv - Tasks 6:45-7:30 PM")
            print("4. period_3_tasks.csv - Tasks 7:30-8:15 PM")
            print("5. period_4_tasks.csv - Tasks 8:15-9:00 PM")
            print("6. period_5_tasks.csv - Tasks 9:00-9:45 PM")
        else:
            print("Failed to generate reports")
    else:
        print("Failed to extract table data")

if __name__ == "__main__":
    main()
