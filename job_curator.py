#!/usr/bin/env python3

from src.job_curator.cli.parser import parse_arguments
from src.job_curator.scraper.greenhouse import GreenhouseScraper
from src.job_curator.filters.job_filter import JobFilter
from src.job_curator.formatter.table_formatter import TableFormatter

def main():
    args = parse_arguments()
    
    scraper = GreenhouseScraper()
    job_filter = JobFilter()
    formatter = TableFormatter()
    
    print("Searching for jobs...")
    
    try:
        jobs = scraper.scrape_jobs(company_filter=args.company)
        filtered_jobs = job_filter.filter_jobs(jobs, args)
        formatter.display_table(filtered_jobs)
        
        if args.export:
            formatter.export_csv(filtered_jobs, args.export)
            print(f"\nResults exported to {args.export}")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    main()