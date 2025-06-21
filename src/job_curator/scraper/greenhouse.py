import requests
from bs4 import BeautifulSoup
import time
from dataclasses import dataclass
from typing import List, Optional
import re
import json
from datetime import datetime, timedelta

@dataclass
class JobPosting:
    title: str
    company: str
    url: str
    location: str
    description: str
    compensation: Optional[str] = None
    posted_date: Optional[str] = None

class GreenhouseScraper:
    def __init__(self):
        self.base_url = "https://boards.greenhouse.io"
        self.api_base_url = "https://boards-api.greenhouse.io/v1/boards"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.rate_limit_delay = 1
        self.days_back = 7  # Default to jobs from past week
    
    def scrape_jobs(self, company_filter: Optional[str] = None) -> List[JobPosting]:
        """Scrape jobs from Greenhouse boards
        
        Args:
            company_filter: If provided, only search this specific company
        """
        jobs = []
        
        if company_filter:
            # Search only the specified company
            companies_to_search = [company_filter.lower()]
        else:
            # Use web scraping to discover companies with recent job postings
            companies_to_search = self._discover_active_companies()
        
        for company in companies_to_search:
            try:
                company_jobs = self._scrape_company_jobs_api(company)
                if not company_jobs:
                    company_jobs = self._scrape_company_jobs_html(company)
                
                # Filter jobs by date
                recent_jobs = self._filter_recent_jobs(company_jobs)
                jobs.extend(recent_jobs)
                
                time.sleep(self.rate_limit_delay)
            except Exception as e:
                print(f"Error scraping {company}: {e}")
                continue
        
        return jobs
    
    def _scrape_company_jobs_api(self, company: str) -> List[JobPosting]:
        """Try to scrape jobs using Greenhouse API first"""
        api_url = f"{self.api_base_url}/{company}/jobs"
        
        try:
            response = self.session.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for job_data in data.get('jobs', []):
                    job = self._parse_api_job(job_data, company)
                    if job:
                        jobs.append(job)
                return jobs
        except Exception:
            pass
        
        return []
    
    def _discover_active_companies(self) -> List[str]:
        """Discover companies with active job postings using common patterns"""
        # Start with well-known tech companies that use Greenhouse
        base_companies = [
            'stripe', 'shopify', 'atlassian', 'mongodb', 'datadog',
            'twilio', 'gitlab', 'hashicorp', 'snowflake', 'databricks',
            'github', 'figma', 'notion', 'linear', 'vercel', 'openai',
            'anthropic', 'discord', 'slack', 'zoom', 'dropbox', 'canva',
            'coinbase', 'robinhood', 'plaid', 'airtable', 'retool', 'segment'
        ]
        
        active_companies = []
        for company in base_companies:
            try:
                # Quick check if company has active job board
                test_url = f"{self.api_base_url}/{company}/jobs"
                response = self.session.get(test_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('jobs') and len(data['jobs']) > 0:
                        active_companies.append(company)
                time.sleep(0.5)  # Light rate limiting
            except Exception:
                continue
        
        return active_companies[:20]  # Limit to 20 companies to avoid overwhelming requests
    
    def _parse_api_job(self, job_data: dict, company: str) -> Optional[JobPosting]:
        """Parse job data from Greenhouse API response"""
        try:
            title = job_data.get('title', 'Unknown Title')
            job_id = job_data.get('id')
            absolute_url = job_data.get('absolute_url', '')
            
            location = 'Unknown Location'
            if job_data.get('location'):
                location = job_data['location'].get('name', 'Unknown Location')
            
            content = job_data.get('content', '')
            description = BeautifulSoup(content, 'html.parser').get_text(strip=True) if content else ''
            
            compensation = self._extract_compensation(description)
            
            # Parse posted date if available
            posted_date = None
            if job_data.get('updated_at'):
                posted_date = job_data['updated_at']
            
            return JobPosting(
                title=title,
                company=company.title(),
                url=absolute_url,
                location=location,
                description=description,
                compensation=compensation,
                posted_date=posted_date
            )
        except Exception:
            return None
    
    def _scrape_company_jobs_html(self, company: str) -> List[JobPosting]:
        """Fallback to HTML scraping if API fails"""
        url = f"{self.base_url}/{company}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        jobs = []
        
        job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+'))
        
        for link in job_links[:3]:  # Limit to first 3 jobs per company for performance
            try:
                job_url = self.base_url + link.get('href')
                job = self._scrape_job_details(job_url, company)
                if job:
                    jobs.append(job)
                time.sleep(self.rate_limit_delay)
            except Exception as e:
                print(f"Error scraping job {link.get('href')}: {e}")
                continue
        
        return jobs
    
    def _scrape_job_details(self, job_url: str, company: str) -> Optional[JobPosting]:
        try:
            response = self.session.get(job_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_elem = soup.find('h1')
        title = title_elem.text.strip() if title_elem else "Unknown Title"
        
        location_elem = soup.find('div', {'class': 'location'})
        location = location_elem.text.strip() if location_elem else "Unknown Location"
        
        description_elem = soup.find('div', {'id': 'content'})
        description = description_elem.get_text(strip=True) if description_elem else ""
        
        compensation = self._extract_compensation(description)
        
        return JobPosting(
            title=title,
            company=company.title(),
            url=job_url,
            location=location,
            description=description,
            compensation=compensation
        )
    
    def _extract_compensation(self, description: str) -> Optional[str]:
        salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',
            r'\$[\d,]+k?\s*-\s*\$[\d,]+k?',
            r'salary:?\s*\$[\d,]+',
            r'compensation:?\s*\$[\d,]+'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _filter_recent_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Filter jobs to only include those posted in the past week"""
        if not jobs:
            return jobs
        
        cutoff_date = datetime.now() - timedelta(days=self.days_back)
        recent_jobs = []
        
        for job in jobs:
            if job.posted_date:
                try:
                    # Parse the date string (assuming ISO format from API)
                    job_date = datetime.fromisoformat(job.posted_date.replace('Z', '+00:00'))
                    if job_date >= cutoff_date:
                        recent_jobs.append(job)
                except Exception:
                    # If date parsing fails, include the job anyway
                    recent_jobs.append(job)
            else:
                # If no date available, include the job
                recent_jobs.append(job)
        
        return recent_jobs