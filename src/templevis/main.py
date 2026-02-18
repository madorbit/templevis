"""
Main Module

This module demonstrates the usage of the table processor
for extracting schedule information from PDF files.
"""

import os
from .table_processor import PDFTableProcessor

def main():
    """Main function demonstrating table processing capabilities."""
    import sys
    if len(sys.argv) < 3 or sys.argv[1] != "process":
        print("Usage: templevis process <pdf_file>")
        sys.exit(1)
        
    # Get PDF path from command line argument
    pdf_path = sys.argv[2]
    processor = PDFTableProcessor(pdf_path)

    # Extract table data
    print(f"Processing PDF: {pdf_path}")
    df = processor.extract_table_data()
    if df is not None:
        print("\nTable structure detected")
        print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Extract names
        print("\nExtracting names...")
        names = processor.get_names()
        print(f"Found {len(names)} names:")
        for i, name in enumerate(names[:5], 1):
            print(f"{i}. {name}")
        if len(names) > 5:
            print(f"... and {len(names) - 5} more")
        
        # Find INI tasks
        print("\nFinding INI tasks...")
        tasks = processor.get_ini_tasks()
        print(f"Found {len(tasks)} INI tasks:")
        for i, task in enumerate(tasks[:5], 1):
            print(f"{i}. {task['name']}: {task['task']} at {task['start_time']}")
        if len(tasks) > 5:
            print(f"... and {len(tasks) - 5} more")
        
        # Generate reports
        print("\nGenerating reports...")
        output_dir = 'output'
        
        # Generate CSV reports
        if processor.generate_reports(output_dir, format='csv'):
            print(f"\nCSV reports generated in '{output_dir}' directory:")
            print("- complete_schedule.csv")
            for period in range(1, 6):
                filename = f"period_{period}_tasks.csv"
                if os.path.exists(os.path.join(output_dir, filename)):
                    print(f"- {filename}")
        else:
            print("Failed to generate CSV reports")
            
        # Generate Excel report
        if processor.generate_reports(output_dir, format='xlsx'):
            print(f"\nExcel report generated in '{output_dir}' directory:")
            print("- schedule.xlsx")
        else:
            print("Failed to generate Excel report")
    else:
        print("Failed to extract table data from PDF")

if __name__ == "__main__":
    main()
