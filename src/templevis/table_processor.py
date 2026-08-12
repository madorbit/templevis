"""
Table Processor Module

This module handles the processing of PDF files using pdfplumber to extract table data.
"""

import os
import re
import pdfplumber
import pandas as pd
from datetime import datetime, timedelta
from .ods_generator import ODSGenerator
from .excel_generator import ExcelGenerator

class PDFTableProcessor:
    """Handles processing of PDF files and extraction of schedule information using table parsing."""

    def __init__(self, pdf_path):
        """Initialize the PDF processor with a PDF file path."""
        self.pdf_path = pdf_path
        self.debug_dir = os.path.join('data', 'debug')
        os.makedirs(self.debug_dir, exist_ok=True)
        self.table_data = None
        self.names = []
        self.tasks = []

    @staticmethod
    def _normalize_name_text(value):
        """Normalize whitespace/newlines and canonicalize 'Last, First' formatting."""
        name = str(value)
        name = re.sub(r'\s+', ' ', name).strip()
        if ',' in name:
            last_name, first_name = name.split(',', 1)
            name = f"{last_name.strip()}, {first_name.strip()}"
        return name

    def find_task_codes(self, page_num=None):
        """
        Find all task codes in the specified page.
        
        Args:
            page_num: Optional page number to process (default: None, process all pages)
            
        Returns:
            List of dictionaries containing task code information:
            {
                'text': str,      # Task code text
                'x': int,         # X coordinate
                'y': int,         # Y coordinate
                'width': int,     # Width of task code box
                'height': int     # Height of task code box
            }
        """
        if self.table_data is None:
            self.extract_table_data(page_num)
            
        if self.table_data is None:
            return []
            
        try:
            task_codes = []
            task_code_patterns = ['CH', 'EO', 'V-', 'LAU', 'BCR', 'TRG', 'STU', 'RDA', 'PM', 'INI']
            
            # Process each row
            for idx, row in self.table_data.iterrows():
                # Look for task codes in each cell
                for col_idx, cell in enumerate(row):
                    cell_str = str(cell).strip()
                    if any(cell_str.startswith(pattern) for pattern in task_code_patterns):
                        # Get column name (time) for position calculation
                        time_col = self.table_data.columns[col_idx]
                        
                        # Calculate approximate position
                        # These are rough estimates since we don't have actual PDF coordinates
                        x = 100 + (col_idx * 50)  # Start at x=100, each column ~50px wide
                        y = 750 - (idx * 20)      # Start at y=750, each row ~20px high
                        
                        task_codes.append({
                            'text': cell_str,
                            'x': x,
                            'y': y,
                            'width': 40,  # Standard width for task codes
                            'height': 15   # Standard height for task codes
                        })
            
            return task_codes
            
        except Exception as e:
            print(f"Error finding task codes: {e}")
            return []

    def extract_names_from_text(self, pdf):
        """
        Extract names from the PDF text layer.
        Each line in format: "# LastName, FirstName TASKS... AlphabeticalName"
        We need the Name part (column 1).

        Returns:
            List of names in row order
        """
        names = []

        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')
            for line in lines:
                # Skip empty or header lines
                if not line.strip():
                    continue

                # Lines with data start with a number
                parts = line.strip().split(None, 1)  # Split into row_num and rest
                if len(parts) < 2 or not parts[0].isdigit():
                    continue

                # parts[0] = row number
                # parts[1] = "LastName, FirstName TASKS... AlphabeticalName"
                remaining = parts[1]

                # Find the comma that separates last and first name
                comma_idx = remaining.find(',')
                if comma_idx == -1:
                    continue

                last_name = remaining[:comma_idx].strip()

                # After the comma, get everything before the first task code
                after_comma = remaining[comma_idx + 1:].strip()

                task_codes = ['CH', 'EO', 'V-', 'V�', 'LAU', 'BCR', 'TRG', 'STU', 'RDA', 'RDB', 'PM', 'INI', 'BFR', 'DRA', 'CON', 'RRA', 'NI', 'IAC', 'VC', 'VAC', 'PRE', 'MED']

                # Find where the first task code starts
                first_name_parts = []
                words = after_comma.split()
                for word in words:
                    # Check if this word is a task code
                    if any(word.startswith(code) for code in task_codes):
                        break
                    first_name_parts.append(word)

                if not first_name_parts:
                    continue

                first_name = ' '.join(first_name_parts)

                # Combine last name and first name
                full_name = f"{last_name}, {first_name}"
                names.append(full_name)

        return names

    def extract_table_data(self, page_num=None):
        """
        Extract table data from PDF pages.

        Args:
            page_num: Optional page number to process (default: None, process all pages)

        Returns:
            DataFrame containing the table data
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # First, extract names from text layer
                names_from_text = self.extract_names_from_text(pdf)
                print(f"\nExtracted {len(names_from_text)} names from text layer:")
                for i, name in enumerate(names_from_text[:10]):
                    print(f"  {i+1}. {name}")
                if len(names_from_text) > 10:
                    print(f"  ... and {len(names_from_text) - 10} more")

                # Handle single page or all pages
                pages = [pdf.pages[page_num]] if page_num is not None else pdf.pages
                if page_num is not None and page_num >= len(pdf.pages):
                    return None

                # Process selected pages
                all_tables = []
                for i, page in enumerate(pages):
                    page_num_str = f"{page_num + 1}" if page_num is not None else f"{i + 1}"
                    print(f"\nProcessing page {page_num_str}")
                    
                    # Extract tables from the page
                    tables = page.extract_tables()
                    
                    if not tables:
                        print("No tables found on this page")
                        continue
                    
                    print(f"Found {len(tables)} tables")
                    
                    # Get the main schedule table (usually the largest one)
                    table = max(tables, key=len)
                    print(f"Main table size: {len(table)} rows")
                    
                    # Store table for later processing
                    all_tables.append(table)
                
                if not all_tables:
                    print("No tables found in the PDF")
                    return None
                
                # Process each table to get structure
                all_data_rows = []
                columns = None
                current_row = 0
                
                for table_num, table in enumerate(all_tables):
                    print(f"\nProcessing table {table_num + 1}")
                    
                    # Print first few rows to understand structure
                    print("\nRaw table structure (first 5 rows):")
                    for i, row in enumerate(table[:5]):
                        print(f"Row {i}: {[str(cell) for cell in row]}")
                    
                    # First row has time headers
                    # Second row has column names
                    # Third row onwards is data
                    if len(table) >= 3:
                        time_row = table[0]
                        header_row = table[1]
                        data_rows = table[2:]
                        
                        # Only process column headers from first table
                        if columns is None:
                            print("\nTime headers (first 5):")
                            print(time_row[:5])
                            print("\nColumn names (first 5):")
                            print(header_row[:5])
                            
                            # Create column names using both rows
                            columns = []
                            current_hour = None
                            
                            # First two columns are # and Name
                            columns.append('#')  # Always use '#' for first column
                            columns.append('Name')  # Always use 'Name' for second column
                            print("Header column 0: #")
                            print("Header column 1: Name")
                            
                            # Process time slots
                            i = 2
                            slots_since_hour = 0  # Track slots since last hour marker
                            while i < len(header_row):
                                time = str(time_row[i] or '').strip()
                                
                                if time:
                                    # Check if this is an hour marker (e.g., "6:00 PM")
                                    if ':00' in time:
                                        current_hour = int(time.split(':')[0])
                                        print(f"Found hour marker: {time}")
                                        columns.append(time)  # Include hour marker in columns
                                        i += 1
                                        # Skip PM marker if it exists
                                        if i < len(time_row) and str(time_row[i]).strip() == 'PM':
                                            i += 1
                                        slots_since_hour = 1  # Start counting after hour marker
                                        continue
                                    else:
                                        print(f"Time column {i}: {time}")
                                        columns.append(time)
                                        slots_since_hour += 1
                                else:
                                    # Generate time based on current hour
                                    if current_hour is not None:
                                        minutes = slots_since_hour * 5
                                        time = f"{current_hour}:{minutes:02d} PM"
                                        print(f"Generated time: {time} (hour: {current_hour}, minutes: {minutes})")
                                        columns.append(time)
                                        slots_since_hour += 1
                                    else:
                                        columns.append('')
                                i += 1
                            
                            print(f"\nGenerated {len(columns)} columns")
                            print("\nFinal column names (first 10):")
                            print(columns[:10])
                        
                        # Add non-empty data rows to combined list
                        for row in data_rows:
                            # Check if row has any content
                            if len(row) > 1:
                                # Clean row data
                                cleaned_row = []
                                for cell in row:
                                    cell_str = str(cell).strip()
                                    cleaned_row.append('' if cell_str == 'None' else cell_str)
                                
                                # Check if row has any non-empty cells
                                if any(cell for cell in cleaned_row):
                                    # Ensure row has enough columns
                                    while len(cleaned_row) < len(columns):
                                        cleaned_row.append('')
                                    # Trim row to match columns
                                    cleaned_row = cleaned_row[:len(columns)]
                                    all_data_rows.append(cleaned_row)
                                    current_row += 1
                    else:
                        print("Table structure not as expected")
                        continue
                
                if not columns or not all_data_rows:
                    print("No valid data found in tables")
                    return None
                
                # Convert to DataFrame with all data rows
                df = pd.DataFrame(all_data_rows, columns=columns)

                # Inject names from text layer into column 1
                if len(names_from_text) > 0:
                    print(f"\nInjecting {len(names_from_text)} names into column 1...")
                    for idx in range(min(len(names_from_text), len(df))):
                        df.iloc[idx, 1] = names_from_text[idx]

                # Print raw data
                print("\nRaw data sample (first 5 rows):")
                print(df.head())

                # Store raw data before cleaning
                self.raw_data = df.copy()
                self.table_data = df.copy()  # Also store as table_data initially

                # Clean up the data but keep task codes and names
                task_codes = ['CH', 'EO', 'V-', 'LAU', 'BCR', 'TRG', 'STU', 'RDA', 'PM', 'INI']

                # ALWAYS use column 1 for names (it has names aligned with task assignments)
                # Column 67 (last column) has alphabetically sorted names but NOT aligned with tasks
                name_col_idx = 1
                print(f"Using column 1 (Name column) for name extraction")

                # Create a new DataFrame with cleaned data
                cleaned_data = []
                for idx, row in df.iterrows():
                    cleaned_row = {}
                    # Keep # column as is
                    cleaned_row['#'] = str(row['#']).strip()

                    # Get name from the identified name column
                    name = self._normalize_name_text(row.iloc[name_col_idx])

                    # Remove trailing numbers from names (like "Altamirano, Ethan 23")
                    if name and name != 'None':
                        name_parts = name.rsplit(' ', 1)
                        if len(name_parts) == 2 and name_parts[1].isdigit():
                            name = name_parts[0]

                    # Split on first task code if present
                    if any(code in name for code in task_codes):
                        name = name.split(' CH')[0].split(' EO')[0].split(' V-')[0].split(' LAU')[0].split(' BCR')[0].split(' TRG')[0].split(' STU')[0].split(' RDA')[0].split(' PM')[0].split(' INI')[0]
                    cleaned_row['Name'] = name if name != 'None' else ''
                    
                    # Clean task columns
                    for col in df.columns[2:]:
                        cell = str(row[col]).strip()
                        if cell == 'None':
                            cleaned_row[col] = ''
                        elif any(cell.startswith(code) for code in task_codes):
                            # Fix encoding for en-dash and normalize task codes
                            cell = cell.replace('–', '-').replace('—', '-')
                            cleaned_row[col] = cell.strip()
                        else:
                            cleaned_row[col] = ''
                    cleaned_data.append(cleaned_row)
                
                # Create new DataFrame with cleaned data
                df = pd.DataFrame(cleaned_data)
                
                # Print name column after cleaning
                print("\nName column after cleaning:")
                print(df.iloc[:, 1].tolist())
                
                # Store cleaned data
                self.table_data = df
                
                # Return raw data for tests that expect unprocessed data
                return df
                
        except Exception as e:
            print(f"Error extracting table data: {e}")
            return None

    def get_names(self):
        """
        Extract names from the second column of the table.
        
        Returns:
            List of names found in the table
        """
        if self.table_data is None:
            self.extract_table_data()
            
        if self.table_data is None:
            return []
            
        try:
            print("\nAvailable columns:")
            print(self.table_data.columns.tolist()[:5])
            
            # Get the name column (second column)
            name_col = self.table_data.iloc[:, 1]
            
            # Filter out empty/NaN values and clean names
            names = []
            print("\nProcessing names:")
            
            # Process all names
            for idx, name in enumerate(name_col):
                # Clean up the name
                name = self._normalize_name_text(name)
                
                # Skip obvious non-name entries
                if not name or name.lower() in ['name', '#', 'none']:
                    print(f"Skipping non-name entry at index {idx}: {name}")
                    continue
                    
                # Skip section headers
                if name.lower() in ['coordinator positions', 'on leave / no longer on shift', 'requested a sub']:
                    print(f"Skipping section header at index {idx}: {name}")
                    continue
                    
                # Skip if name doesn't contain a comma (likely not in Last, First format)
                if ',' not in name:
                    print(f"Skipping entry without comma at index {idx}: {name}")
                    continue
                    
                # Verify name format (Last, First)
                try:
                    last_name, first_name = name.split(',', 1)
                    if not last_name.strip() or not first_name.strip():
                        print(f"Skipping invalid name format at index {idx}: {name}")
                        continue
                except ValueError:
                    print(f"Skipping malformed name at index {idx}: {name}")
                    continue
                
                # Clean up name
                name = f"{last_name.strip()}, {first_name.strip()}"
                print(f"{idx + 1}. {name}")
                names.append(name)
                
                # Update the DataFrame with the cleaned name
                self.table_data.iloc[idx, 1] = name
            
            # Store for later use
            self.names = names
            
            return names
            
        except Exception as e:
            print(f"Error extracting names: {e}")
            return []

    def detect_next_assignment(self, row, ini_end_col_idx):
        """
        Detect if a worker has a real assignment immediately after their INI task.
        
        Args:
            row: DataFrame row for the worker
            ini_end_col_idx: Column index where the INI task ends
            
        Returns:
            str: Next task code if found, None otherwise
        """
        # Look ahead 4 time slots (20 minutes)
        lookahead_slots = 4
        
        for i in range(1, lookahead_slots + 1):
            col_idx = ini_end_col_idx + i
            
            # Check if we're within bounds
            if col_idx >= len(row):
                break
                
            cell_str = str(row.iloc[col_idx]).strip()
            
            # Skip empty cells
            if not cell_str or cell_str == '':
                continue
                
            # Skip STU (Study) and STU-SE* variants (free periods)
            if cell_str == 'STU' or cell_str.startswith('STU-SE'):
                continue
                
            # Found a real assignment
            return cell_str
            
        # No real assignment found in lookahead window
        return None

    def get_ini_tasks(self):
        """
        Find all INI task codes and their time slots.
        
        Returns:
            List of dictionaries containing task information:
            {
                'name': str,      # Worker name
                'task': str,      # Task code (INI*)
                'start_time': str,# Start time
                'end_time': str,  # End time
                'time_period': int, # 1-5 based on time range
                'next_task': str  # Next assignment after INI, or None
            }
        """
        if self.table_data is None:
            self.extract_table_data()
            
        if self.table_data is None:
            return []
            
        try:
            tasks = []
            
            print("\nProcessing rows for INI tasks...")
            
            # Process each row
            for idx, row in self.table_data.iterrows():
                name = self._normalize_name_text(row.iloc[1])  # Second column contains names
                
                # Skip empty names or header rows
                if not name or name.lower() in ['name', 'worker', '#'] or name.startswith('Page'):
                    print(f"Skipping row with name: {name}")
                    continue
                    
                print(f"\nChecking row for {name}:")
                print(f"First few cells: {[str(cell) for cell in row[:5]]}")
                
                # Look for INI tasks in the row
                ini_start_col = None
                ini_end_col = None
                ini_task_code = None
                in_ini_block = False
                
                for col_idx, cell in enumerate(row):
                    cell_str = str(cell).strip()
                    # Handle both 'INI' and 'INI-#' formats
                    if cell_str == 'INI' or cell_str.startswith('INI-'):
                        # Normalize task code (add -1 if just INI)
                        if cell_str == 'INI':
                            cell_str = 'INI-1'
                        
                        # Track the start and end of INI assignment
                        if not in_ini_block:
                            # Starting a new INI block
                            ini_start_col = col_idx
                            ini_task_code = cell_str
                            in_ini_block = True
                            print(f"Found INI task: {cell_str} at column {col_idx}")
                        # Update end column as we continue through the block
                        ini_end_col = col_idx
                    elif in_ini_block:
                        # We've found the end of the INI block, process it
                        time_col = self.table_data.columns[ini_start_col]
                        print(f"INI block ended. Start time column: {time_col}")
                        
                        # Detect next assignment after INI task
                        next_task = self.detect_next_assignment(row, ini_end_col)
                        if next_task:
                            print(f"Next assignment detected: {next_task}")
                        
                        # Parse time and calculate period
                        try:
                            # Clean up time string
                            time_str = str(time_col).strip()
                            if not time_str:
                                in_ini_block = False
                                ini_start_col = None
                                ini_end_col = None
                                continue
                                
                            # Parse and convert to 24-hour format
                            try:
                                # Try 12-hour format first
                                time = datetime.strptime(time_str, '%I:%M %p')
                                print(f"Parsed time (12-hour): {time}")
                            except ValueError:
                                try:
                                    # Try 24-hour format
                                    time = datetime.strptime(time_str, '%H:%M')
                                    print(f"Parsed time (24-hour): {time}")
                                except ValueError:
                                    print(f"Failed to parse time: {time_str}")
                                    in_ini_block = False
                                    ini_start_col = None
                                    ini_end_col = None
                                    continue
                            
                            # Calculate decimal hour (time is already in 24-hour format)
                            decimal_hour = time.hour + (time.minute / 60.0)
                            print(f"Hour: {time.hour}, Minutes: {time.minute}")
                            print(f"Decimal hour: {decimal_hour}")
                            
                            # Determine time period (1-5)
                            if 18 <= decimal_hour < 18.75:  # 6:00-6:45
                                period = 1
                            elif 18.75 <= decimal_hour < 19.5:  # 6:45-7:30
                                period = 2
                            elif 19.5 <= decimal_hour < 20.25:  # 7:30-8:15
                                period = 3
                            elif 20.25 <= decimal_hour < 21:  # 8:15-9:00
                                period = 4
                            elif 21 <= decimal_hour < 21.75:  # 9:00-9:45
                                period = 5
                            else:
                                period = None
                            print(f"Time period: {period}")
                                
                            tasks.append({
                                'name': name,
                                'task': ini_task_code,  # Use normalized task code
                                'start_time': time_col,
                                'end_time': (time + timedelta(minutes=5)).strftime('%I:%M %p'),
                                'time_period': period,
                                'next_task': next_task
                            })
                            print(f"Added task for {name} in period {period}")
                            
                        except ValueError:
                            pass
                        
                        # Reset for next INI block
                        in_ini_block = False
                        ini_start_col = None
                        ini_end_col = None
                        ini_task_code = None
                
                # Handle case where INI block extends to end of row
                if in_ini_block and ini_start_col is not None:
                    time_col = self.table_data.columns[ini_start_col]
                    next_task = self.detect_next_assignment(row, ini_end_col)
                    print(f"INI block extends to end of row. Start time column: {time_col}")
                    
                    try:
                        time_str = str(time_col).strip()
                        if time_str:
                            try:
                                time = datetime.strptime(time_str, '%I:%M %p')
                            except ValueError:
                                try:
                                    time = datetime.strptime(time_str, '%H:%M')
                                except ValueError:
                                    continue
                            
                            decimal_hour = time.hour + (time.minute / 60.0)
                            
                            if 18 <= decimal_hour < 18.75:
                                period = 1
                            elif 18.75 <= decimal_hour < 19.5:
                                period = 2
                            elif 19.5 <= decimal_hour < 20.25:
                                period = 3
                            elif 20.25 <= decimal_hour < 21:
                                period = 4
                            elif 21 <= decimal_hour < 21.75:
                                period = 5
                            else:
                                period = None
                            
                            tasks.append({
                                'name': name,
                                'task': ini_task_code,
                                'start_time': time_col,
                                'end_time': (time + timedelta(minutes=5)).strftime('%I:%M %p'),
                                'time_period': period,
                                'next_task': next_task
                            })
                            print(f"Added task for {name} in period {period} (end of row)")
                    except ValueError:
                        pass
            
            # Store for later use
            self.tasks = tasks
            
            return tasks
            
        except Exception as e:
            print(f"Error finding INI tasks: {e}")
            return []

    def generate_reports(self, output_dir='output', periods=None, format='csv'):
        """
        Generate CSV reports for different time periods.
        
        Args:
            output_dir: Directory to save CSV files (default: 'output')
            periods: Optional list of custom time periods, each a dict with:
                    - name: Period name
                    - start: Start time (HH:MM format)
                    - end: End time (HH:MM format)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.tasks:
            self.get_ini_tasks()
            
        if not self.tasks:
            return False
            
        try:
            # Create output directory
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                print(f"Error creating output directory: {e}")
                return False

            # Use default periods if none provided
            if periods is None:
                periods = [
                    {'name': 'Period 1', 'start': '18:00', 'end': '18:45'},
                    {'name': 'Period 2', 'start': '18:45', 'end': '19:30'},
                    {'name': 'Period 3', 'start': '19:30', 'end': '20:15'},
                    {'name': 'Period 4', 'start': '20:15', 'end': '21:00'},
                    {'name': 'Period 5', 'start': '21:00', 'end': '21:45'}
                ]

            # Validate period format
            for period in periods:
                if not all(key in period for key in ['name', 'start', 'end']):
                    print("Invalid period format")
                    return False

            # Create DataFrames for each period
            period_dfs = {i+1: [] for i in range(len(periods))}
            
            # Sort tasks by start time
            sorted_tasks = sorted(self.tasks, key=lambda x: x['start_time'])
            
            # Assign tasks to periods
            for task in sorted_tasks:
                task_time = datetime.strptime(task['start_time'], '%I:%M %p')
                task_hour = task_time.hour + (task_time.minute / 60.0)
                
                # Find matching period
                for i, period in enumerate(periods, 1):
                    start_time = datetime.strptime(period['start'], '%H:%M')
                    end_time = datetime.strptime(period['end'], '%H:%M')
                    start_hour = start_time.hour + (start_time.minute / 60.0)
                    end_hour = end_time.hour + (end_time.minute / 60.0)
                    
                    if start_hour <= task_hour < end_hour:
                        period_dfs[i].append({
                            'Name': self._normalize_name_text(task['name']),
                            'Task': task['task'],
                            'Start Time': task['start_time'],
                            'End Time': task['end_time']
                        })
                        break
            
            # Generate reports based on format
            if format == 'csv':
                # Save period reports as CSV
                for i, period in enumerate(periods, 1):
                    data = sorted(period_dfs[i], key=lambda x: x['Name'])
                    df = pd.DataFrame(data)
                    
                    # Create empty DataFrame with correct columns if no data
                    if df.empty:
                        df = pd.DataFrame(columns=['Name', 'Task', 'Start Time', 'End Time'])
                        
                    # Use period name if provided, otherwise use period number
                    period_name = period.get('name', f'Period {i}').replace(' ', '_').lower()
                    filename = f'{period_name}_tasks.csv'
                    df.to_csv(os.path.join(output_dir, filename), index=False)
                
                # Create complete schedule CSV
                complete_df = pd.DataFrame(sorted_tasks)
                if complete_df.empty:
                    complete_df = pd.DataFrame(columns=['name', 'task', 'start_time', 'end_time', 'time_period'])
                complete_df.to_csv(os.path.join(output_dir, 'complete_schedule.csv'), index=False)
                
            elif format in ['ods', 'xlsx']:
                try:
                    # Create workbook with all periods
                    generator = ODSGenerator() if format == 'ods' else ExcelGenerator()
                    
                    # Only call create_workbook for ODS format
                    if format == 'ods':
                        generator.create_workbook()
                    
                    for i, period in enumerate(periods, 1):
                        # Get period data
                        data = sorted(period_dfs.get(i, []), key=lambda x: x['Name'])
                        
                        # Extract names and start time
                        names = [row['Name'] for row in data]
                        
                        # Build next_tasks dictionary for this period (Excel only)
                        next_tasks = None
                        if format == 'xlsx':
                            next_tasks = {}
                            for task in sorted_tasks:
                                # Only include tasks in this period
                                task_time = datetime.strptime(task['start_time'], '%I:%M %p')
                                task_hour = task_time.hour + (task_time.minute / 60.0)
                                
                                start_time_obj = datetime.strptime(period.get('start', '18:00'), '%H:%M')
                                end_time_obj = datetime.strptime(period.get('end', '18:45'), '%H:%M')
                                start_hour = start_time_obj.hour + (start_time_obj.minute / 60.0)
                                end_hour = end_time_obj.hour + (end_time_obj.minute / 60.0)
                                
                                if start_hour <= task_hour < end_hour:
                                    if task.get('next_task'):
                                        next_tasks[task['name']] = task['next_task']
                        
                        # Convert start time to 24-hour format for Excel generator
                        start_time = period.get('start', '18:00')  # Default to 18:00 if not specified
                        
                        # Add sheet for this period
                        period_name = period.get('name', f'Period {i}')
                        if format == 'xlsx':
                            generator.add_period_sheet(period_name, start_time, names, next_tasks)
                        else:
                            generator.add_period_sheet(period_name, start_time, names)
                    
                    # Save the file
                    filename = 'schedule.ods' if format == 'ods' else 'schedule.xlsx'
                    generator.save(os.path.join(output_dir, filename))
                except Exception as e:
                    print(f"Error generating {format.upper()} file: {e}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error generating reports: {e}")
            return False
