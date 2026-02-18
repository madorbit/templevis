# Product Context

## Why This Project Exists
TempleVis was created to solve a specific operational challenge for LDS temple workers who need to quickly identify which workers are assigned to specific tasks during their shifts. The manual process of scanning PDF schedules to find workers assigned to "INI" (Initiatory) tasks was time-consuming and error-prone.

## Problems It Solves
1. **Manual Schedule Analysis**: Eliminates the need to manually scan through complex PDF tables to find specific task assignments
2. **Time-Critical Information Access**: Provides quick access to worker assignments for specific time periods (6:00 PM - 9:45 PM in 45-minute blocks)
3. **Data Format Conversion**: Transforms visual PDF schedules into structured, searchable data formats (CSV, ODS, Excel)
4. **Alphabetical Organization**: Automatically sorts worker names for easier reference and coordination
5. **Multi-Format Output**: Provides data in multiple formats to suit different workflow preferences

## How It Should Work
### User Experience Flow
1. **Simple Input**: User provides a PDF schedule file via command line
2. **Automatic Processing**: System extracts table data, identifies names and task assignments
3. **Structured Output**: Generates organized reports by time period with alphabetically sorted worker lists
4. **Multiple Formats**: Provides CSV files for data analysis and spreadsheet files (ODS/Excel) for manual annotation

### Key Functionality
- **Visual PDF Processing**: Reads complex table structures with merged cells and embedded text
- **Intelligent Name Extraction**: Identifies worker names from the second column of schedule tables
- **Task Code Recognition**: Detects and processes task codes (especially "INI" tasks) within time slot rectangles
- **Time Period Mapping**: Automatically assigns tasks to predefined time periods:
  - Period 1: 6:00-6:45 PM
  - Period 2: 6:45-7:30 PM  
  - Period 3: 7:30-8:15 PM
  - Period 4: 8:15-9:00 PM
  - Period 5: 9:00-9:45 PM
- **Multi-Page Support**: Handles schedules that span multiple PDF pages
- **Consistent Sorting**: Maintains alphabetical order across all output formats

## User Experience Goals
### Primary Users
- **Temple Coordinators**: Need quick access to worker assignments for operational planning
- **Area Supervisors**: Require organized lists of workers for specific time periods and tasks
- **Administrative Staff**: Need structured data for record-keeping and analysis

### Success Criteria
1. **Speed**: Process a typical schedule PDF in under 30 seconds
2. **Accuracy**: Correctly identify 95%+ of worker names and task assignments
3. **Usability**: Single command execution with clear, organized output
4. **Reliability**: Handle various PDF formats and layouts consistently
5. **Accessibility**: Provide multiple output formats to suit different user preferences

### User Workflow Integration
- **Before**: Manual scanning of PDF → handwritten notes → potential errors
- **After**: Single command → structured reports → immediate actionable information

## Value Proposition
TempleVis transforms a manual, error-prone process into an automated, reliable system that:
- Saves significant time for temple coordinators
- Reduces errors in worker assignment identification
- Provides consistent, professional output formats
- Enables better operational planning and coordination
- Supports both digital and print-based workflows

## Success Metrics
- **Time Savings**: Reduce schedule analysis time from 15-20 minutes to under 1 minute
- **Error Reduction**: Eliminate manual transcription errors
- **User Adoption**: Provide a tool that becomes essential for temple operations
- **Format Flexibility**: Support multiple output formats for different use cases
