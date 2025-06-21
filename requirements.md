# Job Posting Curation Assistant - Requirements

## Project Overview
A command-line tool that search and filters tech industry job postings based on user-defined criteria, initially focusing on Greenhouse.io hosted positions.

## Core Functionality

### Input Methods
- **Phase 1 (MVP):** Structured command format
  - Example: `--title "data scientist" --location "NYC" --keywords "dbt"`
- **Phase 2 (Future):** Natural language parsing
  - Example: `"Find data scientists job in NYC. Job postings mention dbt"`

### Data Source
- Primary: Greenhouse.io hosted job postings
- Target: Tech industry positions only

### Search Criteria
- Job title (partial matching)
- Location (city/state/remote)
- Keywords in job description
- Company name (optional)

### Output Format
- Table view displayed in terminal
- Columns: Job Title, Company, URL, Time Created, Location, Compensation (when available)
- Export option to CSV file

## Technical Requirements

### Architecture
- Command-line interface (no web frontend initially)
- Python-based (recommended for web scraping libraries)
- Modular design for easy extension to other job sites

### Key Components
1. Web scraper module for Greenhouse.io
2. Search/filter engine
3. CLI argument parser
4. Data formatter/table renderer
5. Optional: CSV export functionality

### Data Handling
- Temporary storage during session (no persistent database required for MVP)
- Handle missing compensation data gracefully
- Basic error handling for failed requests

### Performance
- Rate limiting to respect Greenhouse.io servers
- Reasonable response time for searches (under 30 seconds for typical queries)

## Example Usage
```bash
# Structured input (MVP)
python job_curator.py --title "software engineer" --location "San Francisco" --keywords "python,django"

# Future natural language input
python job_curator.py "Find senior frontend developer jobs in Austin that mention React"
```

## Success Criteria
- Successfully scrapes and parses Greenhouse.io job postings
- Filters results accurately based on provided criteria
- Displays results in clean, readable table format
- Handles edge cases (no results, connection errors) gracefully