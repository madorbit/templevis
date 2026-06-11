# TempleVis

A Python tool for processing LDS temple worker schedule PDFs and generating CSV reports of task assignments organized by time periods.

## Overview

TempleVis processes PDF schedules containing temple worker assignments and extracts:

- Worker names
- Task assignments (particularly INI tasks)
- Time period information
- Schedule details

The tool generates CSV reports for different time periods and provides a complete schedule overview.

## Features

- ✨ Multi-page PDF processing
- 📊 Table data extraction
- 👥 Name extraction and sorting
- ⏰ Time period assignment
- 📄 Multiple output formats (CSV, ODS, Excel)
- 🔍 INI task tracking
- 📋 Template-based spreadsheet generation
- 🎯 Debug visualization system
- 🎨 Professional Excel formatting with alternating row colors

## Installation

### Prerequisites

1. Python 3.8 or higher
2. Tesseract OCR engine

   ```bash
   # Windows (using chocolatey)
   choco install tesseract

   # Linux
   sudo apt-get install tesseract-ocr

   # macOS
   brew install tesseract
   ```

3. Poppler for PDF processing

   ```bash
   # Windows (using chocolatey)
   choco install poppler

   # Linux
   sudo apt-get install poppler-utils

   # macOS
   brew install poppler
   ```

### Installing TempleVis

```bash
pip install templevis
```

## Usage

### Command Line Interface

```bash
# Process a schedule PDF and generate all reports
python -m templevis process path/to/schedule.pdf

# Example
python -m templevis process memory-bank/b&w_wed_4th_shift_20Aug2025.pdf
```

### Python API

```python
from templevis import PDFTableProcessor

# Initialize processor
processor = PDFTableProcessor('path/to/schedule.pdf')

# Extract table data
df = processor.extract_table_data()

# Get worker names
names = processor.get_names()

# Find INI tasks
ini_tasks = processor.get_ini_tasks()

# Generate all reports (CSV, ODS, Excel)
processor.generate_reports('output_directory')
```

## Time Periods

The system processes schedules into five distinct time periods:

1. Period 1: 6:00 PM - 6:45 PM
2. Period 2: 6:45 PM - 7:30 PM
3. Period 3: 7:30 PM - 8:15 PM
4. Period 4: 8:15 PM - 9:00 PM
5. Period 5: 9:00 PM - 9:45 PM

## Output Files

The tool generates multiple output formats:

### CSV Files

1. `complete_schedule.csv` - Full schedule with all assignments
2. `period_1_tasks.csv` through `period_5_tasks.csv` - Tasks for each time period

### Spreadsheet Files

1. `schedule.ods` - OpenDocument Spreadsheet with template formatting
2. `schedule.xlsx` - Excel workbook with professional formatting

Each output contains:

- **Name** - Worker name (alphabetically sorted)
- **Task** - Task assignment code
- **Start Time** - Assignment start time
- **End Time** - Assignment end time

### Spreadsheet Features

- **Template-based formatting** with consistent styling
- **Multiple sheets** - one per time period
- **Room and Task columns** for manual annotation
- **Professional Excel formatting**:
  - Font size 14 for improved readability
  - Alternating row colors (white and light gray)
  - Center-justified headers
  - Consistent cell borders and styling

## Development Setup

1. Clone the repository

   ```bash
   git clone https://github.com/username/templevis.git
   cd templevis
   ```

2. Create a virtual environment

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. Install development dependencies

   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests
   ```bash
   pytest
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
