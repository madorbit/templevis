"""
Test Configuration Module

This module provides pytest fixtures and configuration for all test modules.
It centralizes common test data and setup procedures.
"""

import os
import pytest
from templevis import PDFTableProcessor

# Global test configuration
TEST_DATA_DIR = os.path.join('memory-bank')
DEBUG_OUTPUT_DIR = os.path.join('data', 'debug')
TEST_OUTPUT_DIR = os.path.join('output', 'test')


@pytest.fixture(scope="session")
def test_pdf_path():
    """Fixture providing path to test PDF file."""
    pdf_path = os.path.join(TEST_DATA_DIR, 'b&w_wed_4th_shift_23Jul2025.pdf')
    if not os.path.exists(pdf_path):
        pytest.skip(f"Test PDF not found: {pdf_path}")
    return pdf_path

@pytest.fixture(scope="session")
def table_processor(test_pdf_path):
    """Fixture providing initialized PDFTableProcessor."""
    return PDFTableProcessor(test_pdf_path)

@pytest.fixture(scope="session")
def full_table_processor(test_pdf_path):
    """Fixture providing initialized PDFTableProcessor with full PDF."""
    return PDFTableProcessor(test_pdf_path)

@pytest.fixture(scope="function")
def temp_output_dir(tmpdir):
    """Fixture providing temporary output directory."""
    output_dir = tmpdir.mkdir("test_output")
    return str(output_dir)

@pytest.fixture(scope="session")
def sample_task_data():
    """Fixture providing sample task data for testing."""
    return {
        'name': 'Smith, John',
        'task': 'INI-1',
        'start_time': '18:00',
        'end_time': '18:45'
    }

@pytest.fixture(scope="session")
def sample_period_data():
    """Fixture providing sample time period data."""
    return {
        'name': 'Period 1',
        'start': '18:00',
        'end': '18:45'
    }

def pytest_configure(config):
    """Configure test environment before running tests."""
    # Create necessary directories if they don't exist
    os.makedirs(DEBUG_OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    
    # Register custom markers
    config.addinivalue_line("markers", "fast: mark test as fast (quick execution)")
    config.addinivalue_line("markers", "slow: mark test as slow (long execution)")
    config.addinivalue_line("markers", "environment: environment setup tests")
    config.addinivalue_line("markers", "pdf: PDF processing tests")
    config.addinivalue_line("markers", "table: table processing tests")
    config.addinivalue_line("markers", "names: name extraction tests")
    config.addinivalue_line("markers", "tasks: task code tests")

def pytest_collection_modifyitems(items):
    """Add markers to tests based on their categories."""
    for item in items:
        # Add category markers
        if "environment" in item.nodeid:
            item.add_marker(pytest.mark.environment)
        elif "table_processor" in item.nodeid:
            item.add_marker(pytest.mark.table)
        elif "name_extraction" in item.nodeid:
            item.add_marker(pytest.mark.names)
        elif "task_codes" in item.nodeid:
            item.add_marker(pytest.mark.tasks)
        
        # Add speed markers
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        elif any(x in item.nodeid for x in ['full_pdf', 'complete_workflow']):
            item.add_marker(pytest.mark.slow)
        else:
            item.add_marker(pytest.mark.fast)
