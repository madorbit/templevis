"""
Test module for PDFProcessor class.

This module contains tests for the PDF processing functionality,
focusing on rectangle detection and text extraction capabilities.
"""

import os
import pytest
import cv2
import numpy as np
from templevis import PDFProcessor, PDFTableProcessor

# Fixtures are now provided by conftest.py

@pytest.mark.fast
def test_pdf_loading(pdf_processor):
    """Test PDF loading functionality with minimal PDF."""
    assert pdf_processor.load_pdf() is True, "Should successfully load PDF"
    assert pdf_processor.pages is not None, "Pages should be loaded"
    assert len(pdf_processor.pages) == 1, "Should have exactly one page"

@pytest.mark.slow
def test_full_pdf_loading(full_pdf_processor):
    """Test PDF loading functionality with full PDF."""
    assert full_pdf_processor.load_pdf() is True, "Should successfully load PDF"
    assert full_pdf_processor.pages is not None, "Pages should be loaded"
    assert len(full_pdf_processor.pages) > 1, "Should have multiple pages"

@pytest.mark.fast
def test_rectangle_detection(pdf_processor):
    """Test rectangle detection functionality with minimal PDF."""
    # Load PDF first
    pdf_processor.load_pdf()
    
    # Detect rectangles on first page
    rectangles = pdf_processor.detect_rectangles(0)
    
    # Basic validation of rectangle detection
    assert len(rectangles) > 0, "Should detect at least one rectangle"
    
    # Verify rectangle structure
    first_rect = rectangles[0]
    assert all(key in first_rect for key in ['x', 'y', 'width', 'height']), \
        "Rectangle should have x, y, width, and height"
    
    # Verify dimensions match known content
    assert 30 <= first_rect['width'] <= 55, "Rectangle width should be in valid range"
    assert 12 <= first_rect['height'] <= 18, "Rectangle height should be in valid range"

@pytest.mark.slow
def test_full_pdf_rectangle_detection(full_pdf_processor):
    """Test rectangle detection functionality with full PDF."""
    # Load PDF first
    full_pdf_processor.load_pdf()
    
    # Detect rectangles on first page
    rectangles = full_pdf_processor.detect_rectangles(0)
    
    # Basic validation of rectangle detection
    assert len(rectangles) > 10, "Should detect multiple rectangles"
    
    # Verify rectangle structure and dimensions
    for rect in rectangles:
        assert all(key in rect for key in ['x', 'y', 'width', 'height']), \
            "Rectangle should have x, y, width, and height"
        assert 30 <= rect['width'] <= 55, "Rectangle width should be in valid range"
        assert 12 <= rect['height'] <= 18, "Rectangle height should be in valid range"

def test_text_extraction(pdf_processor):
    """Test text extraction from detected regions."""
    # Load PDF and detect rectangles
    pdf_processor.load_pdf()
    rectangles = pdf_processor.detect_rectangles(0)
    
    # Test text extraction from first rectangle
    if rectangles:
        text = pdf_processor.extract_text(rectangles[0])
        assert isinstance(text, str), "Extracted text should be a string"

def test_debug_image_creation(pdf_processor):
    """Test debug image creation functionality."""
    # Load PDF and detect rectangles
    pdf_processor.load_pdf()
    rectangles = pdf_processor.detect_rectangles(0)
    
    # Create debug image
    debug_image = pdf_processor.create_debug_image(rectangles)
    
    # Verify debug image
    assert debug_image is not None, "Debug image should be created"
    assert isinstance(debug_image, np.ndarray), "Debug image should be a numpy array"
    assert len(debug_image.shape) == 3, "Debug image should be a color image"
    assert debug_image.shape[2] == 3, "Debug image should have 3 channels"

def test_invalid_pdf_handling():
    """Test handling of invalid PDF paths."""
    invalid_processor = PDFProcessor("nonexistent.pdf")
    assert invalid_processor.load_pdf() is False, "Should handle invalid PDF gracefully"

def test_invalid_page_number(pdf_processor):
    """Test handling of invalid page numbers."""
    # First ensure PDF is loaded
    assert pdf_processor.load_pdf() is True, "Should load PDF successfully"
    
    # Test with invalid page number
    rectangles = pdf_processor.detect_rectangles(999)
    assert rectangles == [], "Should return empty list for invalid page"
    
    # Test with negative page number
    rectangles = pdf_processor.detect_rectangles(-1)
    assert rectangles == [], "Should return empty list for negative page"
    
    # Test without loading PDF
    invalid_processor = PDFProcessor("nonexistent.pdf")
    rectangles = invalid_processor.detect_rectangles(0)
    assert rectangles == [], "Should return empty list when PDF not loaded"
