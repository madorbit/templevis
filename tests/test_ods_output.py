"""
ODS Output Test Module

This module tests the generation of ODS spreadsheet files.
"""

import os
import pytest
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P
from templevis import PDFTableProcessor
from templevis.ods_generator import ODSGenerator


def _cell_text(cell):
    """Return concatenated paragraph text content from an ODS cell."""
    parts = []
    for paragraph in cell.getElementsByType(P):
        if paragraph.firstChild and hasattr(paragraph.firstChild, "data"):
            parts.append(paragraph.firstChild.data)
    return " ".join(parts).strip()

@pytest.fixture
def test_names():
    """Fixture providing test names."""
    return [
        "Smith, John",
        "Johnson, Mary",
        "Williams, Robert",
        "Brown, Patricia"
    ]

def test_ods_generator_creation():
    """Test basic ODS generator creation."""
    generator = ODSGenerator()
    generator.create_workbook()
    assert generator.doc is not None

def test_template_sheet_creation():
    """Test template sheet structure."""
    generator = ODSGenerator()
    generator.create_workbook()
    table = generator.create_template_sheet("Test Period", "6:00 PM")
    
    # Verify table structure
    rows = table.getElementsByType(TableRow)
    assert len(rows) > 0
    
    # Check title
    title_cell = rows[0].getElementsByType(TableCell)[0]
    assert "Wednesday 4th Shift Initiatory" in _cell_text(title_cell)
    
    # Check assignment time
    time_cells = rows[2].getElementsByType(TableCell)
    assert "Assignment Time:" in _cell_text(time_cells[0])
    assert "6:00 PM" in _cell_text(time_cells[1])

def test_ods_output_generation(test_pdf_path, temp_output_dir):
    """Test complete ODS file generation."""
    processor = PDFTableProcessor(test_pdf_path)
    
    # Define test periods
    periods = [
        {'name': 'Early', 'start': '18:00', 'end': '19:00'},
        {'name': 'Late', 'start': '19:00', 'end': '20:00'}
    ]
    
    # Generate ODS output
    assert processor.generate_reports(temp_output_dir, periods, format='ods')
    
    # Verify file creation
    ods_path = os.path.join(temp_output_dir, 'schedule.ods')
    assert os.path.exists(ods_path)
    
    # Load and verify ODS content
    doc = load(ods_path)
    sheets = doc.spreadsheet.getElementsByType(Table)
    
    # Should have one sheet per period
    assert len(sheets) == len(periods)
    
    # Verify sheet names
    sheet_names = [sheet.getAttribute('name') for sheet in sheets]
    assert 'Early' in sheet_names
    assert 'Late' in sheet_names

def test_ods_template_structure(test_names):
    """Test ODS template structure with sample names."""
    generator = ODSGenerator()
    generator.create_workbook()
    generator.add_period_sheet("Test Period", "6:00 PM", test_names)
    
    # Save to temporary file
    temp_path = "temp_test.ods"
    try:
        generator.save(temp_path)
        
        # Load and verify
        doc = load(temp_path)
        sheet = doc.spreadsheet.getElementsByType(Table)[0]
        
        # Verify column headers
        rows = sheet.getElementsByType(TableRow)
        header_row = rows[4]  # Fifth row has headers
        cells = header_row.getElementsByType(TableCell)
        headers = [_cell_text(cell) for cell in cells]
        
        assert "Names" in headers
        assert "Room" in headers
        assert "Washing" in headers
        assert "Anointing" in headers
        assert "Clothing" in headers
        
        # Verify names are present
        for i, name in enumerate(test_names, start=5):
            name_cell = rows[i].getElementsByType(TableCell)[1]
            assert name in _cell_text(name_cell)
            
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_ods_error_handling():
    """Test error handling in ODS generation."""
    generator = ODSGenerator()
    
    # Test saving without creating workbook
    with pytest.raises(ValueError):
        generator.save("test.ods")

    # Test invalid sheet name
    generator.create_workbook()
    with pytest.raises(ValueError, match="Sheet name cannot be empty"):
        generator.add_period_sheet("", "6:00 PM", [])
