"""
Environment Test Module

This module verifies the basic setup and functionality of our development environment,
including PDF processing and OCR capabilities.
"""

import os
import pytest
import cv2
import numpy as np
from pdf2image import convert_from_path
import pytesseract

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_tesseract_installation():
    """Verify Tesseract OCR is properly installed and accessible."""
    try:
        version = pytesseract.get_tesseract_version()
        # Version is returned as a Version object, convert to string and check it's not empty
        assert str(version), "Tesseract version should not be empty"
    except Exception as e:
        pytest.fail(f"Failed to get Tesseract version: {e}")

def test_pdf_loading():
    """Verify we can load and convert a PDF to images."""
    pdf_path = os.path.join('memory-bank', 'wed_4th_shift_23Jul2025.pdf')
    try:
        # Need to set poppler path
        poppler_path = r'C:\Program Files\poppler-24.08.0\Library\bin'
        pages = convert_from_path(pdf_path, poppler_path=poppler_path)
        assert len(pages) > 0, "Should convert at least one page"
        
        # Convert first page to numpy array for OpenCV
        first_page = np.array(pages[0])
        assert first_page.shape[2] == 3, "Should be a color image with 3 channels"
        
        # Basic image processing test
        gray = cv2.cvtColor(first_page, cv2.COLOR_RGB2GRAY)
        assert len(gray.shape) == 2, "Grayscale image should have 2 dimensions"
        
    except Exception as e:
        pytest.fail(f"Failed to process PDF: {e}")

def test_basic_ocr():
    """Verify OCR functionality with actual schedule content."""
    # Load a real PDF page
    pdf_path = os.path.join('memory-bank', 'wed_4th_shift_23Jul2025.pdf')
    poppler_path = r'C:\Program Files\poppler-24.08.0\Library\bin'
    pages = convert_from_path(pdf_path, poppler_path=poppler_path)
    first_page = np.array(pages[0])
    
    # Convert to grayscale
    gray = cv2.cvtColor(first_page, cv2.COLOR_RGB2GRAY)
    
    # Extract a region known to contain text (name column)
    name_region = gray[100:200, 100:300]  # Adjust coordinates based on actual content
    
    # Perform OCR
    try:
        text = pytesseract.image_to_string(name_region)
        assert len(text.strip()) > 0, "Should detect text in name region"
        assert any(c.isalpha() for c in text), "Should contain alphabetic characters"
    except Exception as e:
        pytest.fail(f"OCR failed: {e}")

def test_opencv_rectangle_detection():
    """Verify rectangle detection with actual schedule content."""
    # Load a real PDF page
    pdf_path = os.path.join('memory-bank', 'wed_4th_shift_23Jul2025.pdf')
    poppler_path = r'C:\Program Files\poppler-24.08.0\Library\bin'
    pages = convert_from_path(pdf_path, poppler_path=poppler_path)
    first_page = np.array(pages[0])
    
    # Convert to grayscale
    gray = cv2.cvtColor(first_page, cv2.COLOR_RGB2GRAY)
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find rectangular contours
    rectangles = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h
        # Task rectangles typically have aspect ratio between 1.5 and 4.0
        if 1.5 <= aspect_ratio <= 4.0 and 25 <= w <= 60 and 10 <= h <= 20:
            rectangles.append((x, y, w, h))
    
    assert len(rectangles) > 0, "Should detect task rectangles in schedule"
    
    # Verify dimensions of first rectangle
    x, y, w, h = rectangles[0]
    assert 25 <= w <= 60, "Rectangle width should be in valid range"
    assert 10 <= h <= 20, "Rectangle height should be in valid range"
