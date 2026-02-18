# Integration Tests

This directory contains integration tests that verify the complete workflow of TempleVis. Unlike unit tests that focus on individual components, these tests ensure that all components work together correctly.

## Test Coverage

### Complete Workflow Test
Tests the entire pipeline from PDF processing to CSV generation:
1. PDF loading and table extraction
2. Name identification and extraction
3. INI task detection and processing
4. CSV report generation and verification
5. Data validation across all outputs

### Custom Period Workflow
Tests the system's ability to handle custom time periods:
1. Custom period definition
2. Report generation with custom periods
3. Output validation for custom periods

### Error Handling
Tests system robustness with invalid inputs:
1. Missing PDF files
2. Invalid output directories
3. Malformed period configurations
4. Edge cases in data processing

## Running Integration Tests

### Run All Integration Tests
```bash
pytest tests/integration/
```

### Run Specific Test
```bash
pytest tests/integration/test_complete_workflow.py -k test_complete_workflow
```

### Run with Debug Output
```bash
pytest tests/integration/ -v --capture=no
```

## Test Data Requirements

Integration tests require:
1. Sample PDF file in memory-bank directory
2. Write access to temp directory
3. All dependencies installed:
   - Tesseract OCR
   - Poppler
   - Python packages from requirements.txt

## Common Issues

1. **Missing Test Data**
   ```
   FileNotFoundError: [Errno 2] No such file or directory: 'memory-bank/wed_4th_shift_23Jul2025.pdf'
   ```
   Solution: Ensure test PDF is present in memory-bank directory

2. **Permission Issues**
   ```
   PermissionError: [Errno 13] Permission denied: '/nonexistent/dir'
   ```
   Solution: Check write permissions for output directories

3. **Dependency Issues**
   ```
   ModuleNotFoundError: No module named 'pdf2image'
   ```
   Solution: Install all required packages from requirements.txt

## Adding New Integration Tests

1. Create new test file in this directory
2. Use fixtures from conftest.py
3. Follow existing patterns for workflow testing
4. Include appropriate error handling tests
5. Document any new test data requirements

## Best Practices

1. Test complete workflows, not individual components
2. Verify all output files and their contents
3. Include error handling scenarios
4. Use temporary directories for outputs
5. Clean up test artifacts after completion
6. Document any special setup requirements
