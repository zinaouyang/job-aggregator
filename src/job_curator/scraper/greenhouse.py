import requests
from bs4 import BeautifulSoup
import time
from dataclasses import dataclass
from typing import List, Optional
import re
import json
import os
from datetime import datetime, timedelta
from .google_search import GoogleSearchService

@dataclass
class JobPosting:
    title: str
    company: str
    url: str
    location: str
    technical_skills: str  # Changed from description to technical_skills
    compensation: Optional[str] = None
    posted_date: Optional[str] = None

class GreenhouseScraper:
    def __init__(self, google_api_key: Optional[str] = None, google_cse_id: Optional[str] = None, use_cached_urls: bool = False):
        self.base_url = "https://boards.greenhouse.io"
        self.api_base_url = "https://boards-api.greenhouse.io/v1/boards"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.rate_limit_delay = 1
        self.days_back = 14  # Default to jobs from past 2 weeks
        self.use_cached_urls = use_cached_urls
        self.use_cached_html = os.path.exists('html_cache')
        
        # Initialize Google Search Service
        if not use_cached_urls:
            try:
                self.google_search = GoogleSearchService(google_api_key, google_cse_id)
            except ValueError as e:
                print(f"Warning: Google Search API not configured: {e}")
                self.google_search = None
        else:
            print("Using cached URLs for testing")
            self.google_search = None
    
    def scrape_jobs(self, job_title: str, max_results: int = 30) -> List[JobPosting]:
        """Scrape jobs from Greenhouse using Google Search API
        
        Args:
            job_title: Job title to search for (required)
            max_results: Maximum number of job results to return
        """
        if not job_title:
            raise ValueError("Job title is required")
        
        if not self.google_search and not self.use_cached_urls:
            raise ValueError("Google Search API is required. Please configure GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.")
        
        jobs = []
        
        try:
            # Use cached HTML processing if available
            if self.use_cached_html:
                print("📄 Using cached HTML files for processing...")
                jobs = self._process_cached_html()
                print(f"Processed {len(jobs)} jobs from cached HTML")
                return jobs
            
            # Fallback to URL-based processing
            if self.use_cached_urls:
                job_urls = self._load_cached_urls()
                print(f"Loaded {len(job_urls)} cached URLs for testing")
            else:
                print(f"Searching for '{job_title}' jobs on Greenhouse...")
                job_urls = self.google_search.search_greenhouse_jobs(job_title, max_results)
                self._save_urls_cache(job_urls)
            
            if not job_urls:
                print(f"No jobs found for '{job_title}'")
                return []
            
            print(f"Found {len(job_urls)} job URLs, scraping details...")
            
            # Extract job details using HTML parsing
            for i, job_url in enumerate(job_urls, 1):
                try:
                    job = self._extract_job_from_url(job_url)
                    if job:
                        jobs.append(job)
                        print(f"✅ {i}/{len(job_urls)}: {job.title} at {job.company}")
                    else:
                        print(f"❌ {i}/{len(job_urls)}: Not a job posting")
                    
                    time.sleep(self.rate_limit_delay)
                except Exception as e:
                    print(f"⚠️ {i}/{len(job_urls)}: Error - {e}")
                    continue
                    
        except Exception as e:
            print(f"Error during Google search: {e}")
            return []
        
        return jobs
    
    def _save_urls_cache(self, urls: List[str]) -> None:
        """Save URLs to cache file for testing"""
        cache_file = 'test_urls.json'
        try:
            with open(cache_file, 'w') as f:
                json.dump(urls, f, indent=2)
            print(f"Saved {len(urls)} URLs to {cache_file}")
        except Exception as e:
            print(f"Failed to save URLs cache: {e}")
    
    def _load_cached_urls(self) -> List[str]:
        """Load URLs from cache file"""
        cache_file = 'test_urls.json'
        try:
            with open(cache_file, 'r') as f:
                urls = json.load(f)
            return urls
        except Exception as e:
            print(f"Failed to load URLs cache: {e}")
            return []
    
    def _process_cached_html(self) -> List[JobPosting]:
        """Process jobs from cached HTML files"""
        cache_dir = "html_cache"
        html_files = [f for f in os.listdir(cache_dir) if f.endswith('.html')]
        
        jobs = []
        for filename in html_files:
            filepath = os.path.join(cache_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                if len(html_content) > 1000:  # Only process substantial files
                    job = self._extract_job_from_html(html_content, filename, url=None)
                    if job:
                        jobs.append(job)
                        
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
        
        return jobs
    
    def _extract_job_from_html(self, html_content: str, filename: str, url: str = None) -> Optional[JobPosting]:
        """Extract job information from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        page_title = title_tag.get_text().strip() if title_tag else ""
        
        # Parse title for job info
        job_title = ""
        company = ""
        location = ""
        
        if " - " in page_title:
            parts = page_title.split(" - ")
            if len(parts) >= 3:
                job_title = parts[0].strip()
                location = " - ".join(parts[1:-1]).strip()
                company = parts[-1].strip()
            elif len(parts) >= 2:
                job_title = parts[0].strip()
                company = parts[-1].strip()
        else:
            # Fallback: use page title as job title and extract company from filename or URL
            job_title = page_title
            # Extract company from filename or URL
            if "_jobs_" in filename:
                company = filename.split("_jobs_")[0].title()
            elif url and "boards.greenhouse.io/" in url:
                # Extract from URL pattern: https://boards.greenhouse.io/company/jobs/123
                url_match = re.search(r'boards\.greenhouse\.io/([^/]+)/', url)
                if url_match:
                    company = url_match.group(1).title()
                else:
                    company = "Unknown Company"
            else:
                company = "Unknown Company"
        
        # Look for JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        compensation = None
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'JobPosting':
                    job_title = data.get('title', job_title).strip()
                    if data.get('hiringOrganization'):
                        company = data['hiringOrganization'].get('name', company)
                    if data.get('jobLocation'):
                        job_location = data['jobLocation']
                        if isinstance(job_location, dict):
                            location = job_location.get('address', location)
                        elif isinstance(job_location, str):
                            location = job_location
                    
                    # Extract compensation from structured data
                    description = data.get('description', '')
                    if 'pay range' in description.lower():
                        salary_match = re.search(r'\$[\d,]+\s*[—\-]\s*\$[\d,]+', description)
                        if salary_match:
                            compensation = salary_match.group()
                    break
            except:
                continue
        
        # If location still not found, try all extraction methods and pick the best
        if not location or location == "":
            all_potential_locations = []
            
            # Strategy 1: Look for location in script tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_text = script.get_text()
                # Look for JSON-like data with location field
                if '"location":"' in script_text:
                    try:
                        # Extract location value from JSON-like structure
                        location_match = re.search(r'"location":"([^"]+)"', script_text)
                        if location_match:
                            potential_location = location_match.group(1).strip()
                            # Clean up location (remove trailing commas, etc.)
                            potential_location = potential_location.rstrip(',').strip()
                            # Validate it looks like a location
                            if len(potential_location) < 50 and self._is_location_text(potential_location):
                                all_potential_locations.append(potential_location)
                    except:
                        continue
            
            # Strategy 2: Look for common location selectors
            location_selectors = [
                'span.caption',  # Roblox uses this for location
                'div.location',
                '.location',
                '[data-qa="job-location"]',
                '.job-location',
                'div[class*="location"]',
                '.job-post-location',
                '.posting-location',
                'h4',  # Often contains full location info
            ]
            
            for selector in location_selectors:
                location_elems = soup.select(selector)
                for elem in location_elems:
                    text = elem.get_text().strip()
                    # Check if this looks like a location and collect all candidates
                    if self._is_location_text(text):
                        all_potential_locations.append(text)
            
            # Choose the most specific location from all candidates
            if all_potential_locations:
                location = self._choose_best_location(all_potential_locations)
            
            # Strategy 3: Look for h3 tags that might contain location
            if not location:
                h3_tags = soup.find_all('h3')
                for h3 in h3_tags:
                    text = h3.get_text().strip()
                    # Check if this looks like a location (but not a job title)
                    if self._is_location_text(text):
                        location = text
                        break
            
            # Strategy 4: Look for location in job description structure
            if not location:
                # Look for divs with text-section class (common in Greenhouse)
                text_sections = soup.find_all('div', class_='text-section')
                for section in text_sections:
                    text = section.get_text().strip()
                    # Extract location patterns from text
                    location_patterns = [
                        r'([^,]+,\s*[A-Z]{2}(?:,\s*United States)?)',  # City, State or City, State, United States
                        r'(Remote\s*[-–—]?\s*[^,\n]*)',  # Remote variations
                        r'([A-Z][a-z]+,\s*[A-Z]{2})',  # Simple City, State
                    ]
                    
                    for pattern in location_patterns:
                        match = re.search(pattern, text)
                        if match:
                            potential_location = match.group(1).strip()
                            if len(potential_location) < 50 and self._is_location_text(potential_location):
                                location = potential_location
                                break
                    if location:
                        break
        
        # Skills extraction removed - using empty string
        
        # Extract compensation if not found in structured data
        if not compensation:
            salary_patterns = [
                r'\$[\d,]+\s*[-–—]\s*\$[\d,]+',
                r'\$[\d,]+k?\s*-\s*\$[\d,]+k?'
            ]
            for pattern in salary_patterns:
                match = re.search(pattern, soup.get_text())
                if match:
                    compensation = match.group()
                    break
        
        # Validate and clean location before returning
        if location and job_title:
            # Don't use location if it's the same as job title or contains job title
            if (location.lower() == job_title.lower() or 
                job_title.lower() in location.lower() or
                any(word in location.lower() for word in ['scientist', 'engineer', 'manager', 'director', 'senior', 'staff', 'principal', 'data'])):
                location = ""
        
        # Only return if we have meaningful data
        if job_title and company and len(job_title) > 3:
            return JobPosting(
                title=job_title,
                company=company,
                url=filename,  # Use filename as URL for cached HTML
                location=location or "Location not specified",
                technical_skills="",
                compensation=compensation
            )
        
        return None
    
    
    def _extract_job_from_url(self, job_url: str) -> Optional[JobPosting]:
        """Extract job information from a URL using HTML parsing"""
        try:
            response = self.session.get(job_url, timeout=10)
            response.raise_for_status()
            
            # Use the same HTML extraction logic
            filename = job_url.split('/')[-1]
            job = self._extract_job_from_html(response.content.decode('utf-8'), filename, url=job_url)
            
            if job:
                # Update URL to be the actual URL instead of filename
                job.url = job_url
                return job
                
        except Exception as e:
            print(f"Error extracting job from {job_url}: {e}")
            
        return None
    
    def _is_location_text(self, text: str) -> bool:
        """Check if text looks like a location"""
        if not text or len(text) > 100 or len(text) < 2:
            return False
        
        # Skip if it contains job-related or non-location keywords
        non_location_keywords = [
            'scientist', 'engineer', 'manager', 'director', 'senior', 'staff', 'principal', 'data', 'analyst', 'developer',
            'careers', 'jobs', 'opportunities', 'openings', 'positions', 'apply', 'team', 'department',
            'benefits', 'salary', 'compensation', 'experience', 'requirements', 'qualifications'
        ]
        if any(keyword in text.lower() for keyword in non_location_keywords):
            return False
        
        # Check for location indicators
        location_indicators = [
            'remote', 'hybrid', 'office',
            'india', 'usa', 'united states', 'america',
            'california', 'texas', 'new york', 'florida', 'washington', 'massachusetts',
            'san francisco', 'new york', 'boston', 'seattle', 'austin', 'chicago', 'los angeles',
            'london', 'toronto', 'sydney', 'berlin', 'amsterdam',
            'ca', 'ny', 'tx', 'fl', 'wa', 'ma'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in location_indicators)
    
    def _choose_best_location(self, locations: list) -> str:
        """Choose the most specific/useful location from a list of candidates"""
        if not locations:
            return ""
        
        # Remove duplicates while preserving order
        unique_locations = []
        for loc in locations:
            if loc not in unique_locations:
                unique_locations.append(loc)
        
        # Scoring system for location specificity
        def location_score(loc):
            score = 0
            loc_lower = loc.lower()
            
            # City names (highest priority)
            cities = ['san francisco', 'new york', 'boston', 'seattle', 'austin', 'chicago', 'los angeles', 'denver', 'atlanta', 'miami']
            for city in cities:
                if city in loc_lower:
                    score += 100
            
            # Contains city, state pattern
            if ',' in loc and any(state in loc_lower for state in ['california', 'texas', 'new york', 'florida', 'washington', 'massachusetts']):
                score += 80
            
            # State abbreviations with comma (e.g., "San Francisco, CA")
            if re.search(r',\s*[A-Z]{2}(\s|$)', loc):
                score += 70
            
            # Remote indicators
            if 'remote' in loc_lower:
                score += 60
            
            # Specific countries/regions
            if 'india' in loc_lower:
                score += 50
            
            # State names
            states = ['california', 'texas', 'new york', 'florida', 'washington', 'massachusetts']
            if any(state in loc_lower for state in states):
                score += 40
            
            # Generic country names (lower priority)
            if loc_lower in ['united states', 'usa', 'america']:
                score += 10
            
            # Penalty for very short locations (likely abbreviations taken out of context)
            if len(loc) <= 3:
                score -= 20
            
            return score
        
        # Sort by score (highest first)
        scored_locations = [(loc, location_score(loc)) for loc in unique_locations]
        scored_locations.sort(key=lambda x: x[1], reverse=True)
        
        # Return the highest scoring location
        best_location = scored_locations[0][0]
        return best_location
    
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
                technical_skills=description,  # Use description as technical_skills for API data
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
    
    def _scrape_job_from_url(self, job_url: str) -> Optional[JobPosting]:
        """Scrape job details from a Greenhouse job URL"""
        # Extract company name from URL
        company_match = re.search(r'boards\.greenhouse\.io/([^/]+)', job_url)
        company = company_match.group(1) if company_match else "Unknown Company"
        
        return self._scrape_job_details(job_url, company)
    
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
            technical_skills=description,  # Use description as technical_skills for legacy HTML parsing
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