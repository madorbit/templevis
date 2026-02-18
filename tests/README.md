# TempleVis Test Suite

This directory contains the test suite for TempleVis. The tests are organized by functionality and use pytest as the testing framework.

## Test Categories

1. **Environment Tests** (`test_environment.py`)
   - Basic environment setup verification
   - Tesseract OCR installation check
   - PDF processing capabilities
   - OpenCV functionality

2. **PDF Processing Tests** (`test_pdf_processor.py`)
   - PDF loading and conversion
   - Page handling
   - Image preprocessing
   - Debug output generation

3. **Table Processing Tests** (`test_table_processor.py`)
   - Table structure detection
   - Cell extraction
   - Data parsing
   - Time period handling

4. **Name Extraction Tests** (`test_name_extraction.py`)
   - Worker name detection
   - Name column processing
   - Name sorting and validation

5. **Task Code Tests** (`test_task_codes.py`, `test_ini_codes.py`)
   - Task code identification
   - INI task filtering
   - Time slot mapping
   - Task duration calculation

6. **Text Extraction Tests** (`test_text_extraction.py`)
   - OCR preprocessing
   - Text recognition
   - Character validation
   - Special character handling

## Running Tests

### Basic Usage

Run all tests:
```bash
pytest
```

Run specific test categories:
```bash
pytest tests/test_environment.py    # Environment tests only
pytest tests/test_pdf_processor.py  # PDF processing tests only
```

### Test Markers

Tests are organized using markers for easier filtering:

```bash
pytest -m environment  # Run environment tests
pytest -m pdf         # Run PDF processing tests
pytest -m table       # Run table processing tests
pytest -m names       # Run name extraction tests
pytest -m tasks       # Run task code tests
```

### Test Configuration

Test configuration is centralized in `conftest.py`, which provides:
- Common fixtures
- Path configurations
- Test data
- Environment setup

### Debug Output

Test runs generate debug output in:
- `data/debug/`: Visual processing debug files
- `output/test/`: Test-specific CSV outputs

## Adding New Tests

1. Choose the appropriate test module based on functionality
2. Use fixtures from `conftest.py` where possible
3. Follow the existing test structure:
   ```python
   def test_new_feature():
       """Clear description of what is being tested."""
       # Arrange
       # Act
       # Assert
   ```
4. Add appropriate markers in `conftest.py`

## Test Data

Test data is stored in the `memory-bank` directory:
- Sample PDF schedules
- Expected output files
- Test configurations

## Common Fixtures

Available fixtures (defined in `conftest.py`):
- `test_pdf_path`: Path to test PDF file
- `pdf_processor`: Initialized PDFTableProcessor
- `test_image`: Basic test image with text
- `test_rectangle_image`: Test image with rectangle
- `pdf_pages`: Converted PDF pages
- `temp_output_dir`: Temporary output directory
- `sample_task_data`: Sample task data
- `sample_period_data`: Sample period data

## Best Practices

1. Use descriptive test names that indicate:
   - What is being tested
   - Expected behavior
   - Conditions/context if relevant

2. Structure tests using AAA pattern:
   - Arrange: Set up test data and conditions
   - Act: Execute the code being tested
   - Assert: Verify the results

3. Use fixtures for common setup
4. Include debug output when relevant
5. Add comments for complex test logic
6. Keep tests focused and atomic

## Troubleshooting

Common issues and solutions:

1. **Tesseract Path Issues**
   - Verify TESSERACT_PATH in conftest.py
   - Check Tesseract installation

2. **PDF Processing Errors**
   - Verify POPPLER_PATH in conftest.py
   - Check PDF file accessibility

3. **Debug Output Issues**
   - Ensure debug directories exist
   - Check write permissions

4. **Test Data Missing**
   - Verify test PDF files in memory-bank
   - Check file paths in conftest.py
