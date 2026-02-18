# Technical Context

## Technologies
Current technology stack:
- Python as the main programming language
  - Strong PDF processing libraries
  - Excellent data manipulation capabilities
  - Rich ecosystem for CSV, ODS, and Excel handling
- Key Libraries (✓ All Installed and Verified):
  - pdf2image: Convert PDF to images for visual processing
  - opencv-python: Image processing and rectangle detection
  - pytesseract: OCR for text extraction
  - pandas: Data manipulation and CSV generation
  - numpy: Numerical operations and grid management
  - pytest: Testing framework
  - odfpy: ODS spreadsheet generation
  - openpyxl: Excel spreadsheet generation

## Development Setup
Required components (✓ All Installed and Verified):
1. Python 3.x environment
2. Tesseract OCR engine
   - Installation path: C:\Program Files\Tesseract-OCR
   - Added to system PATH
   - Verified with pytesseract.get_tesseract_version()
   - Custom configuration implemented:
     - LSTM OCR Engine
     - Single line text mode
     - Character whitelist
     - High DPI setting
3. PDF processing dependencies
   - Poppler for PDF to image conversion
     - Installation path: C:\Program Files\poppler-24.08.0
     - Added C:\Program Files\poppler-24.08.0\Library\bin to system PATH
     - Verified with pdf2image.convert_from_path()
4. Development tools:
   - VSCode with Python extensions
   - Git for version control
   - Virtual environment for dependency management

## Technical Constraints
1. PDF Format:
   - Multi-page schedule support needed
   - Complex table structure with merged cells
   - Text within rectangles
   - 5-minute time slot granularity

2. Processing Requirements:
   - Rectangle Detection:
     - Size: 30-55px width, 12-18px height
     - Aspect ratio: 1.8-3.5
     - Contrast: std_dev > 70
   - Text Extraction:
     - OCR preprocessing
     - Custom configuration
   - Time Slot Mapping:
     - Grid position tracking
     - Time period calculation

## Dependencies
Core dependencies (✓ All Installed and Verified):
```
pdf2image>=1.16.3
opencv-python>=4.8.1.78
pytesseract>=0.3.10
pandas>=2.1.0
numpy>=1.26.0
pytest>=7.4.0
odfpy>=1.4.1
openpyxl>=3.1.2
```

Additional tools (✓ All Installed and Verified):
- Tesseract OCR engine
- Poppler for PDF processing
- Testing frameworks

## Build & Deployment
Development workflow:
1. Local development (Current phase)
   - Sample PDF processing
   - Rectangle detection refinement
   - Text extraction improvement
2. Testing (In Progress)
   - Unit tests for core functionality
   - Integration tests pending
3. Packaging (Planned)
   - Distribution preparation
   - Documentation completion

## Development Tools
Current setup (✓ All Configured):
- VSCode as primary IDE
  - Python extensions installed
  - Debugging tools configured
- Git for version control
- Python virtual environment
  - Dependencies isolated
  - Requirements tracked
- Testing frameworks
  - pytest configured
  - Test discovery working
- Debug visualization system
  - Output directory structure
  - Image saving functionality

## Installation Steps
1. Tesseract OCR (✓ Completed):
   - Installation path verified
   - System PATH updated
   - OCR functionality tested

2. Poppler Installation (✓ Completed):
   - Installation path verified
   - System PATH updated
   - PDF conversion tested

3. Environment Configuration (✓ Completed):
   - Python environment active
   - Dependencies installed
   - Paths configured
   - Tests passing

## Debug System
Implemented functionality:
1. Visual Processing:
   - Threshold visualization
   - Morphological operations
   - Contour detection
   - Rectangle filtering

2. Text Extraction:
   - ROI extraction
   - Preprocessing steps
   - OCR results

3. Output Directory:
   - Organized debug images
   - Step-by-step visualization
   - Processing validation

Note: Development environment is fully configured and verified. Core functionality is implemented with debug capabilities. Ready for feature enhancement and refinement.
