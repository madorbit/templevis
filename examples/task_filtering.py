"""
Task Filtering Example

This example demonstrates various ways to programmatically filter and analyze tasks
in the temple worker schedule, with a focus on INI tasks.

Note: For command-line usage, use:
python -m templevis process <path_to_pdf_file>

This example shows how to use TempleVis as a Python module for more advanced use cases.
"""

from templevis import PDFTableProcessor

def main():
    # Initialize processor
    processor = PDFTableProcessor('schedule.pdf')

    # Extract table data
    print("Analyzing schedule tasks...")
    df = processor.extract_table_data()
    if df is not None:
        # Get all INI tasks
        ini_tasks = processor.get_ini_tasks()
        print("\nAll INI Tasks:")
        for task in ini_tasks[:5]:
            print(f"- {task['name']}: {task['task']} "
                  f"({task['start_time']} - {task['end_time']})")
        if len(ini_tasks) > 5:
            print("...")

        # Get INI tasks for a specific time period
        evening_ini = processor.get_ini_tasks(
            start_time='19:00',  # 7:00 PM
            end_time='20:00'     # 8:00 PM
        )
        print("\nINI Tasks between 7:00 PM and 8:00 PM:")
        for task in evening_ini:
            print(f"- {task['name']}: {task['task']} "
                  f"({task['start_time']} - {task['end_time']})")

        # Get tasks by specific code
        specific_tasks = processor.get_tasks_by_code('INI-1')
        print("\nTasks with code 'INI-1':")
        for task in specific_tasks:
            print(f"- {task['name']}: {task['start_time']} - {task['end_time']}")

        # Get all tasks for a specific worker
        worker_name = ini_tasks[0]['name']  # Use first INI worker as example
        worker_tasks = processor.get_worker_tasks(worker_name)
        print(f"\nAll tasks for {worker_name}:")
        for task in worker_tasks:
            print(f"- {task['task']}: {task['start_time']} - {task['end_time']}")

        # Generate filtered CSV report
        output_dir = 'output/filtered'
        if processor.generate_filtered_report(
            output_dir,
            task_prefix='INI',
            filename='ini_tasks.csv'
        ):
            print(f"\nFiltered report generated: {output_dir}/ini_tasks.csv")

        # Get task statistics
        task_stats = processor.get_task_statistics(task_prefix='INI')
        print("\nINI Task Statistics:")
        print(f"Total INI tasks: {task_stats['total_tasks']}")
        print(f"Unique workers: {task_stats['unique_workers']}")
        print(f"Most common time: {task_stats['peak_time']}")
        print("\nTasks per period:")
        for period, count in task_stats['tasks_per_period'].items():
            print(f"- {period}: {count} tasks")

if __name__ == "__main__":
    main()
