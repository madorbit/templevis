"""
PDF Processor Module

This module handles the processing of PDF files to extract schedule information.
"""

import os
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Constants for name column detection
NAME_COLUMN_MIN_HEIGHT = 500  # Minimum height for name column
NAME_CELL_MIN_WIDTH = 80      # Minimum width for name cells (reduced)
NAME_CELL_MAX_WIDTH = 250     # Maximum width for name cells (increased)
NAME_CELL_MIN_HEIGHT = 10     # Minimum height for name cells (reduced)
NAME_CELL_MAX_HEIGHT = 20     # Maximum height for name cells (increased)
NAME_CELL_MIN_CONTRAST = 50   # Minimum contrast for name cells

class PDFProcessor:
    """Handles processing of PDF files and extraction of schedule information."""

    def __init__(self, pdf_path):
        """Initialize the PDF processor with a PDF file path."""
        self.pdf_path = pdf_path
        self.pages = []
        self.debug_dir = os.path.join('data', 'debug')
        os.makedirs(self.debug_dir, exist_ok=True)
        self.name_column = None  # Store name column bounds once detected

    def load_pdf(self):
        """Load the PDF file and convert pages to images."""
        try:
            poppler_path = r'C:\Program Files\poppler-24.08.0\Library\bin'
            self.pages = convert_from_path(self.pdf_path, poppler_path=poppler_path)
            return True
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return False

    def validate_page_num(self, page_num):
        """Validate page number and return True if valid."""
        if not self.pages:
            return False
        return 0 <= page_num < len(self.pages)

    def get_page_image(self, page_num):
        """Get OpenCV image for the specified page."""
        if not self.validate_page_num(page_num):
            return None
        page = self.pages[page_num]
        return cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)

    def extract_roi(self, rectangle, page_num=0):
        """Extract region of interest from an image."""
        img = self.get_page_image(page_num)
        if img is None:
            return None

        try:
            x, y = max(0, rectangle['x']), max(0, rectangle['y'])
            w = min(rectangle['width'], img.shape[1] - x)
            h = min(rectangle['height'], img.shape[0] - y)
            
            if w <= 0 or h <= 0:
                return None
                
            roi = img[y:y+h, x:x+w]
            if roi.size == 0:
                return None
                
            # Convert to grayscale
            return cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            print(f"ROI extraction error: {e}")
            return None

    def preprocess_for_ocr(self, roi):
        """Preprocess image for OCR."""
        if roi is None or roi.size == 0:
            return None

        try:
            # Scale up image
            scale_factor = 4
            scaled = cv2.resize(roi, None, 
                              fx=scale_factor, fy=scale_factor, 
                              interpolation=cv2.INTER_CUBIC)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(scaled, (3, 3), 0)
            
            # Increase contrast
            alpha = 1.5  # Contrast control
            beta = 0     # Brightness control
            contrasted = cv2.convertScaleAbs(blurred, alpha=alpha, beta=beta)
            
            # Apply Otsu's thresholding
            _, thresh = cv2.threshold(contrasted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return thresh
        except Exception as e:
            print(f"Preprocessing error: {e}")
            return None

    def create_debug_image(self, rectangles, page_num=0):
        """Create debug visualization of detected rectangles."""
        img = self.get_page_image(page_num)
        if img is None or not rectangles:
            return None

        try:
            debug_img = img.copy()
            for rect in rectangles:
                x, y = rect['x'], rect['y']
                w, h = rect['width'], rect['height']
                cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Add text info if available
                if 'text' in rect:
                    cv2.putText(debug_img, rect['text'], 
                              (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 
                              0.5, (0, 0, 255), 1)
            
            # Save debug image
            cv2.imwrite(os.path.join(self.debug_dir, 'debug_visualization.png'), debug_img)
            return debug_img
        except Exception as e:
            print(f"Debug image creation error: {e}")
            return None

    def detect_name_column(self, page_num):
        """
        Detect the name column (second column) in the specified page.
        Returns a dictionary with x1, x2, y1, y2 coordinates of the column bounds.
        """
        if not self.validate_page_num(page_num):
            return None

        # Convert PIL Image to OpenCV format
        img = self.get_page_image(page_num)
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding for better text detection
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 2
        )
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
        
        # Find contours of vertical lines
        contours, _ = cv2.findContours(vertical_lines, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort contours by x-coordinate
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])
        
        # Find the second column (should be between first two long vertical lines)
        column_bounds = None
        vertical_lines = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h > NAME_COLUMN_MIN_HEIGHT:  # Filter for long vertical lines
                vertical_lines.append(x)
                if len(vertical_lines) == 2:  # Found the second column
                    column_bounds = {
                        'x1': vertical_lines[0],
                        'x2': vertical_lines[1],
                        'y1': y,
                        'y2': y + h
                    }
                    break
        
        # Save debug visualization
        if column_bounds:
            debug_img = img.copy()
            cv2.rectangle(debug_img, 
                         (column_bounds['x1'], column_bounds['y1']),
                         (column_bounds['x2'], column_bounds['y2']),
                         (0, 255, 0), 2)
            cv2.imwrite(os.path.join(self.debug_dir, 'name_column.png'), debug_img)
            
            # Store column bounds for later use
            self.name_column = column_bounds
        
        return column_bounds

    def detect_name_cells(self, page_num):
        """
        Detect name cells within the name column.
        Returns a list of dictionaries containing cell information.
        """
        if not self.validate_page_num(page_num):
            return []

        if not self.name_column:
            self.detect_name_column(page_num)
        
        if not self.name_column:
            return []
        
        # Convert PIL Image to OpenCV format
        img = self.get_page_image(page_num)
        if img is None:
            return []

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Extract name column ROI
        roi = gray[self.name_column['y1']:self.name_column['y2'],
                  self.name_column['x1']:self.name_column['x2']]
        
        # Save original ROI for debugging
        cv2.imwrite(os.path.join(self.debug_dir, 'name_column_roi.png'), roi)
        
        # Apply preprocessing steps
        # 1. Apply bilateral filter to reduce noise while preserving edges
        bilateral = cv2.bilateralFilter(roi, 9, 75, 75)
        cv2.imwrite(os.path.join(self.debug_dir, 'name_column_bilateral.png'), bilateral)
        
        # 2. Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 2
        )
        cv2.imwrite(os.path.join(self.debug_dir, 'name_column_thresh.png'), thresh)
        
        # 3. Apply morphological operations to connect text components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))  # Wider kernel to connect letters
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cv2.imwrite(os.path.join(self.debug_dir, 'name_column_morph.png'), morph)
        
        # 4. Use connected components to find text regions
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(morph, connectivity=8)
        
        # 5. Filter and process components
        name_cells = []
        for i in range(1, num_labels):  # Skip background (label 0)
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            area = stats[i, cv2.CC_STAT_AREA]
            
            # Save component for debugging
            component = np.zeros_like(morph)
            component[labels == i] = 255
            cv2.imwrite(os.path.join(self.debug_dir, f'component_{i}.png'), component)
            
            # Filter based on size and aspect ratio
            if (NAME_CELL_MIN_WIDTH < w < NAME_CELL_MAX_WIDTH and 
                NAME_CELL_MIN_HEIGHT < h < NAME_CELL_MAX_HEIGHT and
                area > 200):  # Increased minimum area
                
                # Extract ROI and analyze content
                component_roi = bilateral[y:y+h, x:x+w]
                std_dev = cv2.meanStdDev(component_roi)[1][0][0]
                
                # Save ROI for debugging
                cv2.imwrite(os.path.join(self.debug_dir, f'component_roi_{x}_{y}.png'), component_roi)
                
                # Only include components with sufficient contrast
                if std_dev > NAME_CELL_MIN_CONTRAST:
                    # Adjust coordinates to full page context
                    x_global = x + self.name_column['x1']
                    y_global = y + self.name_column['y1']
                    
                    name_cells.append({
                        'x': x_global,
                        'y': y_global,
                        'width': w,
                        'height': h
                    })
        
        # Create visualization of detected regions
        vis = cv2.cvtColor(bilateral, cv2.COLOR_GRAY2BGR)
        
        # Draw connected components
        component_vis = np.zeros_like(morph)
        for i in range(1, num_labels):
            component_vis[labels == i] = 255
        cv2.imwrite(os.path.join(self.debug_dir, 'all_components.png'), component_vis)
        
        # Draw detected cells
        for cell in name_cells:
            x = cell['x'] - self.name_column['x1']
            y = cell['y'] - self.name_column['y1']
            cv2.rectangle(vis, (x, y), (x + cell['width'], y + cell['height']), (0, 0, 255), 1)
            # Add text with dimensions
            cv2.putText(vis, f"{cell['width']}x{cell['height']}", 
                       (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imwrite(os.path.join(self.debug_dir, 'name_column_regions.png'), vis)
        
        # Save debug visualization
        debug_img = img.copy()
        for cell in name_cells:
            cv2.rectangle(debug_img,
                         (cell['x'], cell['y']),
                         (cell['x'] + cell['width'], cell['y'] + cell['height']),
                         (0, 0, 255), 2)
        cv2.imwrite(os.path.join(self.debug_dir, 'detected_names.png'), debug_img)
        
        return name_cells

    def extract_name(self, cell):
        """
        Extract and clean name text from a cell.
        Uses specialized OCR configuration for name text.
        """
        if not self.pages:
            return None
            
        # Get the first page
        page = self.pages[0]
        img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
        
        # Extract region of interest (ROI)
        x, y, w, h = cell['x'], cell['y'], cell['width'], cell['height']
        roi = img[y:y+h, x:x+w]
        
        # Save extracted ROI
        cv2.imwrite(os.path.join(self.debug_dir, f'name_roi_extracted_{x}_{y}.png'), roi)
        
        # Preprocess ROI for better OCR
        # 1. Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 2. Scale up image
        scale_factor = 4
        scaled = cv2.resize(gray, None, 
                          fx=scale_factor, fy=scale_factor, 
                          interpolation=cv2.INTER_CUBIC)
        
        # 3. Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(scaled, (3, 3), 0)
        
        # 4. Increase contrast
        alpha = 1.5  # Contrast control
        beta = 0     # Brightness control
        contrasted = cv2.convertScaleAbs(blurred, alpha=alpha, beta=beta)
        
        # 5. Apply Otsu's thresholding
        _, thresh = cv2.threshold(contrasted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Configure Tesseract for name extraction
        custom_config = (
            r'--oem 3 '           # Use LSTM OCR Engine
            r'--psm 7 '           # Treat image as single line of text
            r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz,.- '
            r'--dpi 300'          # High DPI for better accuracy
        )
        
        try:
            # Perform OCR
            text = pytesseract.image_to_string(thresh, config=custom_config)
            
            # Clean up the text
            text = text.strip()
            text = ' '.join(text.split())  # Normalize whitespace
            
            return text
        except Exception as e:
            print(f"Name OCR Error: {e}")
            return None

    def detect_rectangles(self, page_num):
        """Detect rectangles in the specified page."""
        if not self.validate_page_num(page_num):
            return []

        # Convert PIL Image to OpenCV format
        img = self.get_page_image(page_num)
        if img is None:
            return []
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            15,  # Block size
            2    # C constant
        )
        
        # Save thresholded image for debugging
        cv2.imwrite(os.path.join(self.debug_dir, 'page_thresh.png'), thresh)
        
        # Perform morphological operations to clean up the image
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Save morphological result for debugging
        cv2.imwrite(os.path.join(self.debug_dir, 'morph.png'), morph)
        
        # Find contours
        contours, _ = cv2.findContours(morph, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Save all contours for debugging
        debug_img = img.copy()
        cv2.drawContours(debug_img, contours, -1, (0, 255, 0), 1)
        cv2.imwrite(os.path.join(self.debug_dir, 'all_contours.png'), debug_img)
        
        print(f"\nFound {len(contours)} total contours")
        
        # Filter and process rectangles
        rectangles = []
        for contour in contours:
            # Get the rectangle bounding the contour
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate aspect ratio and area
            aspect_ratio = float(w)/h
            area = w * h
            
            # Filter rectangles based on size and aspect ratio
            # Task codes can vary in width based on number of characters:
            # - 3 chars (like CIR): ~36px wide
            # - 4 chars (like INI1): ~45px wide
            # Height is typically around 14-15px
            if (25 < w < 60 and 10 < h < 20):  # Even more relaxed size constraints
                # Print debug info for each potential rectangle
                print(f"\nPotential rectangle at ({x}, {y}):")
                print(f"Size: {w}x{h}, Aspect ratio: {aspect_ratio:.2f}, Area: {area}")
                
                # Extract ROI and analyze its content
                roi = gray[y:y+h, x:x+w]
                mean_value = cv2.mean(roi)[0]
                std_dev = cv2.meanStdDev(roi)[1][0][0]
                print(f"Mean value: {mean_value:.2f}, Std dev: {std_dev:.2f}")
                
                # Save ROI for debugging
                cv2.imwrite(os.path.join(self.debug_dir, f'roi_{x}_{y}.png'), roi)
                
                # Accept rectangles with reasonable characteristics
                if (1.4 < aspect_ratio < 4.5 and  # Very relaxed aspect ratio
                    std_dev > 40 and             # More relaxed contrast requirement
                    area > 200):                 # Minimum area requirement
                        rectangles.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'contour': contour
                    })
                    
                # Save debug visualization
                debug_img = img.copy()
                cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.imwrite(os.path.join(self.debug_dir, 'detected_rectangles.png'), debug_img)
        
        return rectangles

    def find_task_codes(self, page_num=0, prefix=None):
        """
        Find task codes in the specified page.
        
        Args:
            page_num: Page number to process (default: 0)
            prefix: Optional prefix to filter task codes (e.g., 'INI')
        
        Returns:
            List of dictionaries containing task code information
        """
        if not self.validate_page_num(page_num):
            return []

        rectangles = self.detect_rectangles(page_num)
        task_codes = []
        
        for rect in rectangles:
            text = self.extract_text(rect)
            if text and len(text) >= 3:  # Task codes are typically 3+ characters
                # If prefix is specified, only include matching codes
                if prefix is None or text.startswith(prefix):
                    task_codes.append({
                        'text': text,
                        'x': rect['x'],
                        'y': rect['y'],
                        'width': rect['width'],
                        'height': rect['height'],
                        'contour': rect['contour']
                    })
        
        return task_codes

    def find_ini_codes(self, page_num=0):
        """Find all INI task codes in the specified page."""
        return self.find_task_codes(page_num, prefix='INI')

    def extract_text(self, rectangle):
        """Extract text from a rectangle region using OCR."""
        if not self.pages:
            return None

        try:
            # Extract ROI
            roi = self.extract_roi(rectangle)
            if roi is None:
                return ""

            # Preprocess for OCR
            processed = self.preprocess_for_ocr(roi)
            if processed is None:
                return ""

            # Configure Tesseract parameters
            custom_config = (
                r'--oem 3 '           # Use LSTM OCR Engine
                r'--psm 7 '           # Treat image as single line of text
                r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- '
                r'--dpi 300 '         # Specify higher DPI for better accuracy
                r'-c tessedit_do_invert=0'  # Don't let Tesseract invert the image
            )
            
            # Perform OCR
            text = pytesseract.image_to_string(processed, config=custom_config)
            return text.strip()

        except Exception as e:
            print(f"Text extraction error: {e}")
            return ""
