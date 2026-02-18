"""
Test module for text extraction functionality.

This module tests the complete workflow of extracting and validating text
from various regions in the schedule PDF, including preprocessing and OCR steps.
"""

import os
import cv2
import numpy as np
import pytest
from templevis import PDFProcessor, PDFTableProcessor

# Fixtures are now provided by conftest.py

@pytest.mark.fast
def test_minimal_text_extraction(pdf_processor):
    """Test text extraction workflow with minimal PDF."""
    # 1. Detect rectangles
    rectangles = pdf_processor.detect_rectangles(0)
    assert len(rectangles) == 2, "Should detect exactly two rectangles"
    
    # 2. Extract and verify text from each rectangle
    ini1 = next(r for r in rectangles if pdf_processor.extract_text(r).strip() == 'INI-1')
    assert ini1 is not None, "Should find INI-1 text"
    
    ini2 = next(r for r in rectangles if pdf_processor.extract_text(r).strip() == 'INI-2')
    assert ini2 is not None, "Should find INI-2 text"

@pytest.mark.slow
def test_complete_text_extraction_workflow(full_pdf_processor):
    """Test text extraction workflow with full PDF."""
    # 1. Detect rectangles
    rectangles = full_pdf_processor.detect_rectangles(0)
    assert len(rectangles) > 10, "Should detect multiple rectangles"
    
    # 2. Extract and validate text from each rectangle
    extracted_texts = []
    for rect in rectangles:
        # Extract text
        text = full_pdf_processor.extract_text(rect)
        if text and text.strip():
            extracted_texts.append({
                'text': text.strip(),
                'rect': rect
            })
    
    assert len(extracted_texts) > 10, "Should extract text from multiple rectangles"
    
    # 3. Verify text properties
    for item in extracted_texts:
        text = item['text']
        rect = item['rect']
        
        # Text should be non-empty and properly formatted
        assert len(text) > 0, "Extracted text should not be empty"
        assert text == text.strip(), "Text should not have leading/trailing whitespace"
        assert "  " not in text, "Text should not have double spaces"
        
        # Text dimensions should match rectangle
        text_length = len(text)
        rect_width = rect['width']
        # Rough character width estimation (assuming monospace font)
        estimated_chars = rect_width / 8  # Approx 8 pixels per character
        assert text_length <= estimated_chars * 1.5, \
            f"Text length ({text_length}) should be reasonable for rectangle width ({rect_width})"

@pytest.mark.fast
def test_text_preprocessing(pdf_processor):
    """Test text extraction preprocessing steps."""
    # Get a rectangle known to contain text
    rectangles = pdf_processor.detect_rectangles(0)
    test_rect = next(r for r in rectangles 
                    if 30 <= r['width'] <= 55 and 12 <= r['height'] <= 18)
    
    # Extract region of interest (ROI)
    roi = pdf_processor.extract_roi(test_rect)
    assert roi is not None, "Should extract ROI"
    assert isinstance(roi, np.ndarray), "ROI should be numpy array"
    assert len(roi.shape) == 2, "ROI should be grayscale"
    
    # Verify preprocessing steps
    preprocessed = pdf_processor.preprocess_for_ocr(roi)
    assert preprocessed is not None, "Should preprocess ROI"
    assert isinstance(preprocessed, np.ndarray), "Preprocessed image should be numpy array"
    assert preprocessed.dtype == np.uint8, "Preprocessed image should be 8-bit"
    
    # Verify debug output
    debug_dir = os.path.join('data', 'debug')
    expected_files = ['roi_extracted.png', 'roi_preprocessed.png']
    for filename in expected_files:
        path = os.path.join(debug_dir, filename)
        assert os.path.exists(path), f"Debug image {filename} should be created"

@pytest.mark.fast
def test_error_handling(pdf_processor):
    """Test error handling in text extraction."""
    # Test invalid rectangle
    invalid_rect = {'x': -100, 'y': -100, 'width': 1000, 'height': 1000}
    text = pdf_processor.extract_text(invalid_rect)
    assert text is None or text.strip() == "", \
        "Should handle invalid rectangle dimensions"
    
    # Test invalid page number
    assert pdf_processor.detect_rectangles(999) == [], \
        "Should handle invalid page number"
    
    # Test missing PDF
    invalid_processor = PDFProcessor("nonexistent.pdf")
    assert not invalid_processor.load_pdf(), "Should handle missing PDF"
    assert invalid_processor.extract_text({'x': 0, 'y': 0, 'width': 100, 'height': 20}) is None, \
        "Should handle missing PDF in text extraction"
