#!/usr/bin/env python3

from src.job_curator.cli.parser import parse_arguments
from src.job_curator.scraper.greenhouse import GreenhouseScraper
from src.job_curator.filters.job_filter import JobFilter
from src.job_curator.formatter.table_formatter import TableFormatter
from datetime import datetime
import os

def main():
    args = parse_arguments()
    
    # Use cached URLs if available for testing
    use_cached = os.path.exists('test_urls.json')
    scraper = GreenhouseScraper(use_cached_urls=use_cached)
    job_filter = JobFilter()
    formatter = TableFormatter()
    
    print("Searching for jobs...")
    
    try:
        # Scrape jobs using job title (required parameter)
        jobs = scraper.scrape_jobs(job_title=args.title)
        
        # Apply local filtering for location, company, and keywords
        filtered_jobs = job_filter.filter_jobs(jobs, args)
        formatter.display_table(filtered_jobs)
        
        # Always save results to CSV with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_title_clean = args.title.replace(" ", "_").replace("/", "_")
        csv_filename = f"jobs_{job_title_clean}_{timestamp}.csv"
        formatter.export_csv(filtered_jobs, csv_filename)
        print(f"\nResults saved to {csv_filename}")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    main()