# TempleVis Test Suite

This directory contains the test suite for TempleVis. The tests are organized by functionality and use pytest as the testing framework.

## Test Categories

1. **Table Processing Tests** (`test_table_processor.py`)
   - Table structure detection
   - Cell extraction
   - Data parsing
   - Time period handling

2. **Task Code Tests** (`test_task_codes.py`)
   - Task code identification
   - INI task filtering
   - Time slot mapping
   - Task duration calculation

3. **ODS Output Tests** (`test_ods_output.py`)
   - ODS workbook generation
   - Template structure
   - Sheet and data validation

4. **Integration Tests** (`integration/test_complete_workflow.py`)
   - End-to-end table parsing workflow
   - Custom period report generation
   - Error handling behavior

## Running Tests

### Basic Usage

Run all tests:
```bash
pytest
```

Run specific test categories:
```bash
pytest tests/test_table_processor.py
pytest tests/test_task_codes.py
```

### Test Markers

Tests are organized using markers for easier filtering:

```bash
pytest -m environment  # Run environment tests
pytest -m table       # Run table processing tests
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
- `table_processor`: Initialized PDFTableProcessor
- `full_table_processor`: Initialized PDFTableProcessor for full test workflows
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

1. **PDF Processing Errors**
   - Check PDF file accessibility

2. **Debug Output Issues**
   - Ensure debug directories exist
   - Check write permissions

3. **Test Data Missing**
   - Verify test PDF files in memory-bank
   - Check file paths in conftest.py
