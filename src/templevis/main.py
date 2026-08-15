"""
Main Module

This module demonstrates the usage of the table processor
for extracting schedule information from PDF files.
"""

import os
from .table_processor import PDFTableProcessor
from .staffing_generator import StaffingAssignmentsGenerator

def veil(argv):
    """Generate the veil staffing assignments workbook from schedule PDFs."""
    import argparse
    parser = argparse.ArgumentParser(prog='templevis veil')
    parser.add_argument('--brothers', help='Brother volunteer schedule PDF')
    parser.add_argument('--sisters', help='Sister volunteer schedule PDF')
    parser.add_argument('--template', default='StaffingAssignments.xlsx',
                        help='Staffing assignments template workbook')
    parser.add_argument('--output', help='Explicit output workbook path')
    parser.add_argument('--output-dir', default='output',
                        help='Directory for the generated workbook')
    args = parser.parse_args(argv)

    if not args.brothers and not args.sisters:
        parser.error('at least one of --brothers or --sisters is required')

    generator = StaffingAssignmentsGenerator(args.template)
    output_path = generator.generate(
        brothers_pdf=args.brothers,
        sisters_pdf=args.sisters,
        output_path=args.output,
        output_dir=args.output_dir,
    )
    print(f"Veil staffing assignments written to {output_path}")

def main():
    """Main function demonstrating table processing capabilities."""
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "veil":
        veil(sys.argv[2:])
        return

    if len(sys.argv) < 3 or sys.argv[1] != "process":
        print("Usage: templevis process <pdf_file>")
        print("       templevis veil --brothers <pdf> [--sisters <pdf>]")
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
