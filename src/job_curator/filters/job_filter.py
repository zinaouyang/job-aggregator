from typing import List
from src.job_curator.scraper.greenhouse import JobPosting

class JobFilter:
    def filter_jobs(self, jobs: List[JobPosting], args) -> List[JobPosting]:
        filtered_jobs = jobs
        
        if args.title:
            filtered_jobs = self._filter_by_title(filtered_jobs, args.title)
        
        if args.location:
            filtered_jobs = self._filter_by_location(filtered_jobs, args.location)
        
        if args.company:
            filtered_jobs = self._filter_by_company(filtered_jobs, args.company)
        
        if args.keywords:
            keywords = [k.strip() for k in args.keywords.split(',')]
            filtered_jobs = self._filter_by_keywords(filtered_jobs, keywords)
        
        return filtered_jobs
    
    def _filter_by_title(self, jobs: List[JobPosting], title: str) -> List[JobPosting]:
        return [job for job in jobs if title.lower() in job.title.lower()]
    
    def _filter_by_location(self, jobs: List[JobPosting], location: str) -> List[JobPosting]:
        return [job for job in jobs if location.lower() in job.location.lower()]
    
    def _filter_by_company(self, jobs: List[JobPosting], company: str) -> List[JobPosting]:
        return [job for job in jobs if company.lower() in job.company.lower()]
    
    def _filter_by_keywords(self, jobs: List[JobPosting], keywords: List[str]) -> List[JobPosting]:
        filtered_jobs = []
        for job in jobs:
            description_lower = job.description.lower()
            if any(keyword.lower() in description_lower for keyword in keywords):
                filtered_jobs.append(job)
        return filtered_jobs