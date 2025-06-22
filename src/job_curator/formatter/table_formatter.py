from typing import List
from tabulate import tabulate
import csv
from src.job_curator.scraper.greenhouse import JobPosting

class TableFormatter:
    def display_table(self, jobs: List[JobPosting]):
        if not jobs:
            print("No jobs found matching your criteria.")
            return
        
        headers = ["Job Title", "Company", "Location", "Technical Skills", "Compensation", "URL"]
        rows = []
        
        for job in jobs:
            compensation = job.compensation if job.compensation else "Not specified"
            url = job.url[:50] + "..." if len(job.url) > 50 else job.url
            technical_skills = job.technical_skills[:40] + "..." if len(job.technical_skills) > 40 else job.technical_skills
            
            rows.append([
                job.title,
                job.company,
                job.location,
                technical_skills,
                compensation,
                url
            ])
        
        print(f"\nFound {len(jobs)} job(s):")
        print(tabulate(rows, headers=headers, tablefmt="grid", maxcolwidths=[30, 20, 25, 20, 50]))
    
    def export_csv(self, jobs: List[JobPosting], filename: str):
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Job Title", "Company", "Location", "Technical Skills", "Compensation", "URL"])
            
            for job in jobs:
                writer.writerow([
                    job.title,
                    job.company,
                    job.location,
                    job.technical_skills,
                    job.compensation or "Not specified",
                    job.url
                ])