"""
Test module for name extraction functionality.

This module tests the complete workflow of extracting names from the schedule PDF,
verifying both the extraction process and the accuracy of the results.
"""

import os
import pytest
from templevis import PDFProcessor, PDFTableProcessor

# Fixtures are now provided by conftest.py

@pytest.mark.fast
def test_minimal_name_extraction(pdf_processor):
    """Test name extraction workflow with minimal PDF."""
    # 1. Detect name column
    column = pdf_processor.detect_name_column(0)
    assert column is not None, "Should detect name column"
    
    # 2. Detect and extract names
    cells = pdf_processor.detect_name_cells(0)
    assert len(cells) == 2, "Should detect exactly two name cells"
    
    names = []
    for cell in cells:
        name = pdf_processor.extract_name(cell)
        if name and name.strip():
            names.append(name.strip())
    
    # 3. Verify names
    assert len(names) == 2, "Should extract exactly two names"
    assert "Smith, John" in names, "Should find first test name"
    assert "Doe, Jane" in names, "Should find second test name"

@pytest.mark.slow
def test_complete_name_extraction_workflow(full_table_processor):
    """Test name extraction workflow with full PDF."""
    # 1. Get names from table
    names = full_table_processor.get_names()
    assert len(names) > 10, "Should find multiple names"
    
    # 3. Verify name list properties
    assert len(names) > 10, "Should extract multiple names"
    assert len(names) == len(set(names)), "Names should be unique"
    
    # 4. Verify name format and content
    for name in names:
        # Names should be in "Last, First" format
        assert "," in name, f"Name '{name}' should be in 'Last, First' format"
        last_name, first_name = name.split(",", 1)
        
        # Verify name parts
        assert len(last_name.strip()) > 0, f"Last name missing in '{name}'"
        assert len(first_name.strip()) > 0, f"First name missing in '{name}'"
        
        # Verify proper formatting
        assert name == name.strip(), f"Name '{name}' has extra whitespace"
        assert "  " not in name, f"Name '{name}' has double spaces"
        # Allow periods and hyphens in names
        cleaned_name = name.replace(",", "").replace(" ", "").replace(".", "").replace("-", "")
        assert cleaned_name.isalpha(), \
            f"Name '{name}' contains invalid characters"

@pytest.mark.fast
def test_name_sorting(pdf_processor):
    """Test name sorting with minimal PDF."""
    # Get all names
    column = pdf_processor.detect_name_column(0)
    cells = pdf_processor.detect_name_cells(0)
    names = [pdf_processor.extract_name(cell).strip() 
             for cell in cells if pdf_processor.extract_name(cell)]
    
    # Verify sorting
    assert len(names) == 2, "Should find exactly two names"
    assert names[0] == "Doe, Jane", "First name should be Doe"
    assert names[1] == "Smith, John", "Second name should be Smith"

@pytest.mark.slow
def test_full_name_sorting(full_table_processor):
    """Test name sorting with full PDF."""
    # Get all names
    names = full_table_processor.get_names()
    
    # Verify sorting
    assert len(names) > 10, "Should find multiple names"
    sorted_names = sorted(names)
    assert names == sorted_names, "Names should be in alphabetical order"

def test_error_handling(pdf_processor):
    """Test error handling in name extraction workflow."""
    # Test invalid page number
    assert pdf_processor.detect_name_column(999) is None, \
        "Should handle invalid page number in column detection"
    assert pdf_processor.detect_name_cells(999) == [], \
        "Should handle invalid page number in cell detection"
    
    # Test invalid PDF
    invalid_processor = PDFProcessor("nonexistent.pdf")
    assert not invalid_processor.load_pdf(), "Should handle missing PDF"
    assert invalid_processor.detect_name_column(0) is None, \
        "Should handle missing PDF in column detection"
    assert invalid_processor.detect_name_cells(0) == [], \
        "Should handle missing PDF in cell detection"
    
    # Test invalid cell dimensions
    invalid_cell = {'x': 0, 'y': 0, 'width': 1000, 'height': 1000}
    name = pdf_processor.extract_name(invalid_cell)
    assert name is None or name.strip() == "", \
        "Should handle invalid cell dimensions"
