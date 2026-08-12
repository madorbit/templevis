"""
Test module for PDFTableProcessor class.

This module contains tests for the table processing functionality,
focusing on table extraction and data parsing capabilities.
"""

import os
import pytest
import pandas as pd
from templevis import PDFTableProcessor

# Fixtures are now provided by conftest.py

@pytest.mark.fast
def test_table_extraction(table_processor):
    """Test table extraction functionality with minimal PDF."""
    df = table_processor.extract_table_data()
    assert df is not None, "Should extract table data"
    assert isinstance(df, pd.DataFrame), "Should return DataFrame"
    assert len(df) >= 1, "Should have at least one row"
    assert len(df.columns) >= 5, "Should have at least 5 columns"
    assert list(df.columns[:2]) == ['#', 'Name'], "First two columns should be # and Name"
    assert any(row['Name'].strip() == 'Smith, John' for _, row in df.iterrows()), \
        "Should find Smith, John in table"

@pytest.mark.slow
def test_full_table_extraction(full_table_processor):
    """Test table extraction functionality with full PDF."""
    df = full_table_processor.extract_table_data()
    assert df is not None, "Should extract table data"
    assert isinstance(df, pd.DataFrame), "Should return DataFrame"
    assert len(df) > 10, "Should have multiple rows"
    assert len(df.columns) > 10, "Should have multiple columns"

@pytest.mark.fast
def test_name_extraction(table_processor):
    """Test name extraction functionality with minimal PDF."""
    names = table_processor.get_names()
    assert isinstance(names, list), "Should return list of names"
    assert len(names) == 1, "Should find exactly one name"
    assert "Smith, John" in names, "Should find test name"

@pytest.mark.slow
def test_full_name_extraction(full_table_processor):
    """Test name extraction functionality with full PDF."""
    names = full_table_processor.get_names()
    assert isinstance(names, list), "Should return list of names"
    assert len(names) > 10, "Should find multiple names"
    assert all(isinstance(name, str) and name.strip() for name in names), \
        "All names should be non-empty strings"
    assert all(',' in name for name in names), \
        "All names should be in Last, First format"

@pytest.mark.fast
def test_ini_task_detection(table_processor):
    """Test INI task detection functionality with minimal PDF."""
    tasks = table_processor.get_ini_tasks()
    assert isinstance(tasks, list), "Should return list of tasks"
    assert len(tasks) == 1, "Should find exactly one INI task"
    
    # Check task
    task = tasks[0]
    assert task['name'] == "Smith, John", "Task should be assigned to Smith, John"
    assert task['task'] == 'INI-1', "Task should be INI-1"
    assert task['start_time'] == '6:00 PM', "Task should start at 6:00 PM"

@pytest.mark.slow
def test_full_ini_task_detection(full_table_processor):
    """Test INI task detection functionality with full PDF."""
    tasks = full_table_processor.get_ini_tasks()
    assert isinstance(tasks, list), "Should return list of tasks"
    assert len(tasks) > 2, "Should find multiple INI tasks"
    
    # Check task structure
    for task in tasks:
        assert isinstance(task, dict), "Task should be a dictionary"
        assert all(key in task for key in ['name', 'task', 'start_time', 'end_time', 'time_period']), \
            "Task should have all required fields"
        assert task['task'].startswith('INI'), "Task code should start with INI"
        assert isinstance(task['time_period'], (int, type(None))), \
            "Time period should be integer or None"
        if task['time_period']:
            assert 1 <= task['time_period'] <= 5, "Time period should be between 1 and 5"

@pytest.mark.fast
def test_csv_report_generation(table_processor, temp_output_dir):
    """Test CSV report generation functionality."""
    success = table_processor.generate_reports(temp_output_dir, format='csv')
    assert success, "Should generate CSV reports"
    
    # Check if files were created
    assert os.path.exists(os.path.join(temp_output_dir, 'complete_schedule.csv')), \
        "Should create complete schedule CSV"
    
    # Check period files
    period_files = [f for f in os.listdir(temp_output_dir) if f.startswith('period_')]
    assert len(period_files) == 5, "Should create 5 period-specific CSV files"

def test_invalid_pdf_handling():
    """Test handling of invalid PDF paths."""
    processor = PDFTableProcessor("nonexistent.pdf")
    assert processor.extract_table_data() is None, "Should handle invalid PDF gracefully"
    assert processor.get_names() == [], "Should return empty list for invalid PDF"
    assert processor.get_ini_tasks() == [], "Should return empty list for invalid PDF"

def test_empty_table_handling(tmp_path):
    """Test handling of PDFs without tables."""
    # Create empty PDF for testing
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"%PDF-1.7\n%\x80\x80\x80\x80\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
    
    processor = PDFTableProcessor(str(empty_pdf))
    assert processor.extract_table_data() is None, "Should handle PDF without tables"
    assert processor.get_names() == [], "Should return empty list for PDF without tables"
    assert processor.get_ini_tasks() == [], "Should return empty list for PDF without tables"

@pytest.mark.fast
def test_invalid_page_number(table_processor):
    """Test handling of invalid page numbers."""
    assert table_processor.extract_table_data(999) is None, "Should handle invalid page number"

@pytest.mark.fast
def test_csv_report_content(table_processor, temp_output_dir):
    """Test content of generated CSV reports."""
    output_dir = temp_output_dir
    table_processor.generate_reports(output_dir, format='csv')
    
    # Check complete schedule CSV
    complete_csv = os.path.join(output_dir, 'complete_schedule.csv')
    if os.path.exists(complete_csv):
        df = pd.read_csv(complete_csv)
        assert all(col in df.columns for col in ['name', 'task', 'start_time', 'end_time']), \
            "Complete schedule should have required columns"
    
    # Check period CSVs
    for period in range(1, 6):
        period_csv = os.path.join(output_dir, f'period_{period}_tasks.csv')
        if os.path.exists(period_csv):
            df = pd.read_csv(period_csv)
            assert all(col in df.columns for col in ['Name', 'Task', 'Start Time', 'End Time']), \
                f"Period {period} CSV should have required columns"
            assert all(task.startswith('INI') for task in df['Task']), \
                f"Period {period} CSV should only contain INI tasks"
