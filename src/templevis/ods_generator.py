"""
ODS Generator Module

This module handles the generation of ODS spreadsheet files using templates
for temple worker schedule output.
"""

import os
from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style, TextProperties, TableColumnProperties, TableRowProperties, TableCellProperties, ParagraphProperties
from odf.text import P
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.table import CoveredTableCell

class ODSGenerator:
    """Handles generation of ODS spreadsheet files from schedule data."""

    def __init__(self):
        """Initialize the ODS generator."""
        self.doc = None
        self.styles = {}

    def _create_styles(self):
        """Create and store common styles for the document."""
        # Title style with gray background
        title_style = Style(name="Title", family="table-cell")
        title_style.addElement(TextProperties(fontsize="14pt", fontweight="bold"))
        title_style.addElement(TableCellProperties(backgroundcolor="#f0f0f0", border="1pt solid #000000"))
        title_style.addElement(ParagraphProperties(textalign="center"))
        self.styles['title'] = title_style
        self.doc.styles.addElement(title_style)

        # Header style with bold text
        header_style = Style(name="Header", family="table-cell")
        header_style.addElement(TextProperties(fontsize="12pt", fontweight="bold"))
        header_style.addElement(TableCellProperties(border="1pt solid #000000"))
        self.styles['header'] = header_style
        self.doc.styles.addElement(header_style)

        # Number column style
        number_style = Style(name="NumberCol", family="table-column")
        number_style.addElement(TableColumnProperties(columnwidth="0.5in"))
        self.styles['number_column'] = number_style
        self.doc.automaticstyles.addElement(number_style)

        # Name column style
        name_style = Style(name="NameCol", family="table-column")
        name_style.addElement(TableColumnProperties(columnwidth="2in"))
        self.styles['name_column'] = name_style
        self.doc.automaticstyles.addElement(name_style)

        # Data column style
        data_style = Style(name="DataCol", family="table-column")
        data_style.addElement(TableColumnProperties(columnwidth="1.5in"))
        self.styles['data_column'] = data_style
        self.doc.automaticstyles.addElement(data_style)

        # Row styles
        row_style = Style(name="RowHeight", family="table-row")
        row_style.addElement(TableRowProperties(rowheight="0.25in"))
        self.styles['row'] = row_style
        self.doc.automaticstyles.addElement(row_style)

        # Title row style
        title_row_style = Style(name="TitleRow", family="table-row")
        title_row_style.addElement(TableRowProperties(rowheight="0.2in"))
        self.styles['title_row'] = title_row_style
        self.doc.automaticstyles.addElement(title_row_style)

        # Cell style with borders
        cell_style = Style(name="Cell", family="table-cell")
        cell_style.addElement(TableCellProperties(border="1pt solid #000000"))
        self.styles['cell'] = cell_style
        self.doc.styles.addElement(cell_style)

        # Merged cell style with borders
        merged_cell_style = Style(name="MergedCell", family="table-cell")
        merged_cell_style.addElement(TableCellProperties(border="1pt solid #000000"))
        merged_cell_style.addElement(ParagraphProperties(textalign="center"))
        self.styles['merged_cell'] = merged_cell_style
        self.doc.styles.addElement(merged_cell_style)

    def create_template_sheet(self, table_name, assignment_time):
        """Create a new sheet with the standard template structure."""
        table = Table(name=table_name)

        # Add column styles
        table.addElement(TableColumn(stylename=self.styles['number_column']))  # Number column
        table.addElement(TableColumn(stylename=self.styles['name_column']))    # Name column
        table.addElement(TableColumn(stylename=self.styles['data_column']))    # Room
        table.addElement(TableColumn(stylename=self.styles['data_column']))    # Washing
        table.addElement(TableColumn(stylename=self.styles['data_column']))    # Anointing
        table.addElement(TableColumn(stylename=self.styles['data_column']))    # Clothing

        # Add title row with merged cells
        title_row = TableRow(stylename=self.styles['title_row'])
        title_cell = TableCell(stylename=self.styles['title'], numbercolumnsspanned=6)
        title_cell.addElement(P(text="Wednesday 4th Shift Initiatory"))
        title_row.addElement(title_cell)
        
        # Add covered cells for merged title
        for _ in range(5):  # 5 covered cells for 6-column span
            title_row.addElement(CoveredTableCell())
        table.addElement(title_row)

        # Add empty row after title
        empty_row1 = TableRow(stylename=self.styles['row'])
        for _ in range(6):  # Add empty cells for all columns
            cell = TableCell(stylename=self.styles['cell'])
            empty_row1.addElement(cell)
        table.addElement(empty_row1)

        # Add assignment time row with merged cells
        time_row = TableRow(stylename=self.styles['row'])
        time_label = TableCell(stylename=self.styles['cell'], numbercolumnsspanned=2)
        time_label.addElement(P(text="Assignment Time:", stylename=self.styles['header']))
        time_value = TableCell(stylename=self.styles['cell'], numbercolumnsspanned=4)
        time_value.addElement(P(text=assignment_time, stylename=self.styles['header']))
        
        # Add cells for assignment time row
        time_row.addElement(time_label)
        time_row.addElement(CoveredTableCell())  # Cover merged label cell
        time_row.addElement(time_value)
        for _ in range(3):  # Cover merged value cells
            time_row.addElement(CoveredTableCell())
        table.addElement(time_row)

        # Add empty row after assignment time
        empty_row2 = TableRow(stylename=self.styles['row'])
        for _ in range(6):  # Add empty cells for all columns
            cell = TableCell(stylename=self.styles['cell'])
            empty_row2.addElement(cell)
        table.addElement(empty_row2)

        # Add column headers
        header_row = TableRow()
        headers = ["#", "Names", "Room", "Washing", "Anointing", "Clothing"]
        for header in headers:
            cell = TableCell(stylename=self.styles['header'])
            cell.addElement(P(text=header))
            header_row.addElement(cell)
        table.addElement(header_row)

        # Add numbered rows (1-24) with merged cells for room assignments
        current_room = 1
        rows_per_room = 4
        rows_added = 0

        for i in range(1, 25):
            row = TableRow(stylename=self.styles['row'])
            
            # Add row number
            number_cell = TableCell(stylename=self.styles['cell'])
            number_cell.addElement(P(text=str(i)))
            row.addElement(number_cell)
            
            # Add name cell (empty)
            name_cell = TableCell(stylename=self.styles['cell'])
            name_cell.addElement(P(text=""))
            row.addElement(name_cell)
            
            # Add room assignment cells
            if rows_added % rows_per_room == 0:
                # First row of a new room group - add merged cells
                for _ in range(4):  # Room, Washing, Anointing, Clothing
                    cell = TableCell(stylename=self.styles['merged_cell'], numberrowsspanned=rows_per_room)
                    cell.addElement(P(text=str(current_room)))
                    row.addElement(cell)
                current_room += 1
            else:
                # Add covered cells for the merged room assignments
                for _ in range(4):
                    row.addElement(CoveredTableCell())
            
            table.addElement(row)
            rows_added += 1

        return table

    def create_workbook(self):
        """Create a new ODS workbook."""
        self.doc = OpenDocumentSpreadsheet()
        self._create_styles()

    def add_period_sheet(self, period_name, assignment_time, names):
        """Add a new sheet for a period with the given names."""
        if not self.doc:
            self.create_workbook()

        if not period_name:
            raise ValueError("Sheet name cannot be empty")

        table = self.create_template_sheet(period_name, assignment_time)

        # Fill in names
        rows = table.getElementsByType(TableRow)
        for i, name in enumerate(names, start=3):  # Start at row 3 (after headers)
            if i < len(rows):  # Check if row exists
                name_cell = rows[i].getElementsByType(TableCell)[1]  # Second column for names
                name_cell.addElement(P(text=name))

        self.doc.spreadsheet.addElement(table)

    def save(self, filepath):
        """Save the workbook to the specified path."""
        if not self.doc:
            raise ValueError("No document created yet")
        
        self.doc.save(filepath)
