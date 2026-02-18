# Project Brief

## Project Overview
This is a project to implement a tool that can visually read a PDF, extract names and assignments from a table, and create a CSV version of the PDF.  The PDF contains a table of assignments for LDS temple workers for their shifts.  Each row represents a single worker and the various tasks they need to accomplish during their shift.  The columns represent times, each representing 5 minutes in duration with an overarching label that encompasses an entire hour's worth of time.  In each row, the assignements are created by a rectangle covering certain time slots.  In each rectangle is a text code representing the specific task.  

The specific task I'm trying to accomplish is extract the list of workers assigned to tasks that start with `INI` so that I can expect who will show up for my area at any given time.

An example PDF table is included in the @memory_bank directory.

## Core Requirements
- Visually read a PDF and extract information
- Identify the list of names available for this week's schedule (in the second column of the table)
- Identify the list of assignements for each worker during the shift
- For a given worker and a specific task, assign that task to each time column for which that task duration covers.
- Produce output in multiple formats:
  - CSV files:
    - One has a representation of the table in CSV format. For row, when there is a task assigned, the task code shows up on each time column.
    - One CSV has the list of workers assigned to a task in the time between 6pm and 6:45pm 
    - One CSV has the list of workers assigned to a task in the time between 6:45pm and 7:30pm 
    - One CSV has the list of workers assigned to a task in the time between 7:30pm and 8:15pm 
    - One CSV has the list of workers assigned to a task in the time between 8:15pm and 9pm 
    - One CSV has the list of workers assigned to a task in the time between 9pm and 9:45pm 
  - ODS spreadsheet:
    - Template-based workbook with standard formatting
    - One sheet per time period with worker assignments
    - Room and task columns for manual entry
    - Assignment time and title headers

## Project Goals
*To be defined based on project direction*

## Scope
*To be defined based on project requirements*

Note: This is a foundation document that will be updated as the project requirements and goals are established.
