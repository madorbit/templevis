"""
Custom Time Periods Example

This example demonstrates how to programmatically process a schedule PDF with custom time periods
instead of using the default 45-minute periods.

Note: For command-line usage, use:
python -m templevis process <path_to_pdf_file>

This example shows how to use TempleVis as a Python module for more advanced use cases.
"""

from templevis import PDFTableProcessor
from datetime import datetime, timedelta

def main():
    # Initialize processor
    processor = PDFTableProcessor('schedule.pdf')

    # Define custom time periods (30-minute intervals)
    custom_periods = [
        {
            'name': 'Early Evening',
            'start': '18:00',  # 6:00 PM
            'end': '18:30'     # 6:30 PM
        },
        {
            'name': 'Mid Evening 1',
            'start': '18:30',  # 6:30 PM
            'end': '19:00'     # 7:00 PM
        },
        {
            'name': 'Mid Evening 2',
            'start': '19:00',  # 7:00 PM
            'end': '19:30'     # 7:30 PM
        },
        {
            'name': 'Late Evening',
            'start': '19:30',  # 7:30 PM
            'end': '20:00'     # 8:00 PM
        }
    ]

    # Extract table data
    print("Processing schedule with custom time periods...")
    df = processor.extract_table_data()
    if df is not None:
        # Generate reports with custom periods
        output_dir = 'output/custom_periods'
        if processor.generate_csv_reports(output_dir, periods=custom_periods):
            print(f"\nReports generated in '{output_dir}':")
            print("1. complete_schedule.csv")
            for i, period in enumerate(custom_periods, 1):
                print(f"{i+1}. period_{i}_tasks.csv - {period['name']} "
                      f"({period['start']} - {period['end']})")
        
        # Get tasks for a specific period
        early_tasks = processor.get_tasks_for_period(
            start_time='18:00',
            end_time='18:30'
        )
        print("\nEarly Evening Tasks:")
        for task in early_tasks[:5]:
            print(f"- {task['name']}: {task['task']}")
        if len(early_tasks) > 5:
            print("...")

if __name__ == "__main__":
    main()
