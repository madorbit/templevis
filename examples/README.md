# TempleVis Examples

This directory contains example scripts demonstrating various features of TempleVis.

## Available Examples

1. `basic_usage.py`
   - Basic initialization and usage
   - Table data extraction
   - Name list retrieval
   - INI task identification
   - CSV report generation

2. `custom_periods.py`
   - Custom time period definition
   - Period-specific report generation
   - Task filtering by time period
   - Custom output directory structure

3. `task_filtering.py`
   - INI task filtering
   - Time-based task filtering
   - Worker-specific task retrieval
   - Task code filtering
   - Task statistics generation

## Running the Examples

1. Install TempleVis:
   ```bash
   pip install templevis
   ```

2. Run any example using the following format:
   ```bash
   python -m templevis process <path_to_pdf_file>
   ```

   For instance:
   ```bash
   python -m templevis process memory-bank/b&w_wed_4th_shift_20Aug2025.pdf
   ```

3. The examples in this directory demonstrate how to use TempleVis programmatically. To run them, use:
   ```bash
   python examples/basic_usage.py
   python examples/custom_periods.py
   python examples/task_filtering.py
   ```

Note: The new usage method processes PDF files directly. The examples in this directory show how to use TempleVis as a Python module for more advanced use cases.

## Example Output

Each example will generate different CSV reports in the `output` directory:

- `basic_usage.py`: Creates standard period-based reports
- `custom_periods.py`: Creates reports with custom time intervals
- `task_filtering.py`: Creates filtered reports focusing on INI tasks

## Notes

- Make sure Tesseract OCR and Poppler are installed on your system
- The examples assume a schedule PDF with the standard temple worker format
- Debug output can be found in the `data/debug` directory when enabled
- All examples include error handling and informative output
- The main usage method is now `python -m templevis process <path_to_pdf_file>`
- The examples in this directory demonstrate programmatic usage of TempleVis as a Python module

For more detailed information, refer to the main README.md in the project root.
