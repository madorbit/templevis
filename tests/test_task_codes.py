"""
Test module for task code extraction and validation.

This module tests the complete workflow of finding and validating task codes
in the schedule PDF, with particular focus on INI tasks.
"""

import os
import pytest
from templevis import PDFTableProcessor

# Fixtures are now provided by conftest.py

@pytest.mark.fast
def test_minimal_task_code_workflow(table_processor):
    """Test the complete task code extraction and validation workflow."""
    # 1. Find all task codes
    task_codes = table_processor.find_task_codes(0)  # Process first page
    assert len(task_codes) == 1, "Should find exactly one task code"
    
    # 2. Verify task code found
    ini1 = task_codes[0]
    assert ini1['text'] == 'INI-1', "Should find INI-1 task"
    
    # 2. Verify task code properties
    for code in task_codes:
        # Verify structure
        assert isinstance(code, dict), "Task code should be a dictionary"
        assert all(key in code for key in ['text', 'x', 'y', 'width', 'height']), \
            "Task code should have all required fields"
        
        # Verify text format
        text = code['text']
        assert len(text) >= 3, f"Task code '{text}' should be at least 3 characters"
        assert all(c.isupper() or c.isdigit() or c == '-' for c in text), \
            f"Task code '{text}' should only contain uppercase letters, numbers, and hyphens"
        
        # Verify dimensions
        assert 30 <= code['width'] <= 55, \
            f"Task code width {code['width']} should be in valid range"
        assert 12 <= code['height'] <= 18, \
            f"Task code height {code['height']} should be in valid range"
        
        # Verify aspect ratio
        aspect_ratio = code['width'] / code['height']
        assert 1.8 <= aspect_ratio <= 3.5, \
            f"Task code aspect ratio {aspect_ratio:.2f} should be in valid range"

@pytest.mark.fast
def test_minimal_ini_task_validation(table_processor):
    """Test INI task validation with minimal PDF."""
    # Find all task codes
    task_codes = table_processor.find_task_codes(0)
    
    # Filter INI tasks
    ini_tasks = [code for code in task_codes if code['text'].startswith('INI')]
    assert len(ini_tasks) == 1, "Should find exactly one INI task"
    
    # Verify INI task
    task = ini_tasks[0]
    assert task['text'] == 'INI-1', "Should find INI-1 task"

@pytest.mark.slow
def test_full_ini_task_validation(full_table_processor):
    """Test INI task validation with full PDF."""
    # Find all task codes
    task_codes = full_table_processor.find_task_codes(0)
    
    # Filter INI tasks
    ini_tasks = [code for code in task_codes if code['text'].startswith('INI')]
    assert len(ini_tasks) > 2, "Should find multiple INI tasks"
    
    # Verify INI task format
    for task in ini_tasks:
        text = task['text']
        # Should be INI followed by a number or hyphen
        assert text.startswith('INI'), f"Task '{text}' should start with INI"
        remainder = text[3:]
        assert remainder == '' or remainder[0] in '-123456789', \
            f"Task '{text}' should have valid suffix"
        
        # If there's a number, it should be 1-9
        if remainder and remainder[0] != '-':
            assert 1 <= int(remainder) <= 9, \
                f"Task '{text}' should have valid number suffix"

@pytest.mark.fast
def test_minimal_task_code_positioning(table_processor):
    """Test task code positioning with minimal PDF."""
    task_codes = table_processor.find_task_codes(0)
    assert len(task_codes) == 1, "Should find exactly one task code"
    
    # Get INI-1 task
    ini1 = task_codes[0]
    assert ini1['text'] == 'INI-1', "Should find INI-1 task"
    
    # Verify task position
    assert 100 <= ini1['x'] <= 500, "Task should be within reasonable x range"
    assert 600 <= ini1['y'] <= 800, "Task should be within reasonable y range"

@pytest.mark.slow
def test_full_task_code_positioning(full_table_processor):
    """Test task code positioning with full PDF."""
    task_codes = full_table_processor.find_task_codes(0)
    assert len(task_codes) > 2, "Should find multiple task codes"
    
    # Task codes should not overlap
    for i, code1 in enumerate(task_codes):
        for code2 in task_codes[i+1:]:
            # Check for horizontal overlap
            x1_range = range(code1['x'], code1['x'] + code1['width'])
            x2_range = range(code2['x'], code2['x'] + code2['width'])
            x_overlap = set(x1_range) & set(x2_range)
            
            # Check for vertical overlap
            y1_range = range(code1['y'], code1['y'] + code1['height'])
            y2_range = range(code2['y'], code2['y'] + code2['height'])
            y_overlap = set(y1_range) & set(y2_range)
            
            # If there's both horizontal and vertical overlap, codes are overlapping
            assert not (x_overlap and y_overlap), \
                f"Task codes should not overlap: {code1['text']} and {code2['text']}"

@pytest.mark.fast
def test_error_handling(table_processor):
    """Test error handling in task code extraction."""
    # Test invalid page number
    invalid_page_codes = table_processor.find_task_codes(999)
    assert invalid_page_codes == [], "Should handle invalid page number"
