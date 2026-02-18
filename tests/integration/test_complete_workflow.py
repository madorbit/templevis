"""
Integration Test Module

This module tests the complete workflow of TempleVis,
from PDF processing through to CSV generation.
"""

import os
import pytest
import pandas as pd
from templevis import PDFTableProcessor

def test_complete_workflow(test_pdf_path, temp_output_dir):
    """Test the complete workflow from PDF processing to CSV generation."""
    # Initialize processor
    processor = PDFTableProcessor(test_pdf_path)

    # 1. Extract table data
    df = processor.extract_table_data()
    assert df is not None, "Should extract table data"
    assert isinstance(df, pd.DataFrame), "Should return DataFrame"

    # 2. Extract and verify names
    names = processor.get_names()
    assert len(names) > 0, "Should find worker names"
    assert all(isinstance(name, str) and name.strip() for name in names), \
        "All names should be valid strings"

    # 3. Find INI tasks
    ini_tasks = processor.get_ini_tasks()
    assert len(ini_tasks) > 0, "Should find INI tasks"
    for task in ini_tasks:
        assert task['task'].startswith('INI'), "Tasks should start with INI"
        assert all(key in task for key in ['name', 'start_time', 'end_time']), \
            "Tasks should have all required fields"

    # 4. Generate CSV reports
    assert processor.generate_csv_reports(temp_output_dir), \
        "Should generate CSV reports"

    # 5. Verify CSV outputs
    # Check complete schedule
    complete_schedule = pd.read_csv(os.path.join(temp_output_dir, 'complete_schedule.csv'))
    assert len(complete_schedule) > 0, "Complete schedule should have entries"
    assert all(col in complete_schedule.columns 
              for col in ['name', 'task', 'start_time', 'end_time']), \
        "Complete schedule should have required columns"

    # Check period files
    for period in range(1, 6):
        period_file = os.path.join(temp_output_dir, f'period_{period}_tasks.csv')
        assert os.path.exists(period_file), f"Period {period} file should exist"
        
        period_data = pd.read_csv(period_file)
        assert len(period_data) > 0, f"Period {period} should have entries"
        assert all(col in period_data.columns 
                  for col in ['Name', 'Task', 'Start Time', 'End Time']), \
            f"Period {period} should have required columns"
        
        # Verify INI tasks in period files
        assert all(task.startswith('INI') for task in period_data['Task']), \
            f"Period {period} should only contain INI tasks"

def test_workflow_with_custom_periods(test_pdf_path, temp_output_dir, sample_period_data):
    """Test workflow with custom time periods."""
    processor = PDFTableProcessor(test_pdf_path)
    
    # Define custom periods
    custom_periods = [
        {
            'name': 'Early',
            'start': '18:00',
            'end': '19:00'
        },
        {
            'name': 'Late',
            'start': '19:00',
            'end': '20:00'
        }
    ]

    # Generate reports with custom periods
    assert processor.generate_csv_reports(
        temp_output_dir, 
        periods=custom_periods
    ), "Should generate custom period reports"

    # Verify custom period outputs
    for period in custom_periods:
        period_name = period['name'].replace(' ', '_').lower()
        period_file = os.path.join(temp_output_dir, f'{period_name}_tasks.csv')
        assert os.path.exists(period_file), \
            f"Custom period {period['name']} file should exist"
        
        period_data = pd.read_csv(period_file)
        assert len(period_data) > 0, \
            f"Custom period {period['name']} should have entries"

def test_workflow_error_handling(test_pdf_path, temp_output_dir):
    """Test workflow error handling with invalid inputs."""
    # Test with nonexistent PDF
    processor = PDFTableProcessor("nonexistent.pdf")
    assert processor.extract_table_data() is None, \
        "Should handle missing PDF gracefully"
    assert not processor.generate_csv_reports(temp_output_dir), \
        "Should handle CSV generation failure gracefully"

    # Test with invalid output directory
    processor = PDFTableProcessor(test_pdf_path)
    assert not processor.generate_csv_reports("/nonexistent/dir"), \
        "Should handle invalid output directory gracefully"

    # Test with invalid period configuration
    invalid_periods = [{'name': 'Invalid'}]  # Missing start/end times
    assert not processor.generate_csv_reports(
        temp_output_dir, 
        periods=invalid_periods
    ), "Should handle invalid period configuration gracefully"
