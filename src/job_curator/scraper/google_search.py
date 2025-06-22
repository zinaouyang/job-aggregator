import os
from typing import List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import time


class GoogleSearchService:
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """
        Initialize Google Search API service
        
        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            search_engine_id: Custom Search Engine ID (or set GOOGLE_CSE_ID env var)
        """
        self.api_key = api_key or os.environ.get('GOOGLE_API_KEY')
        self.search_engine_id = search_engine_id or os.environ.get('GOOGLE_CSE_ID')
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError(
                "Google API key and Custom Search Engine ID are required. "
                "Set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables."
            )
        
        self.service = build("customsearch", "v1", developerKey=self.api_key)
        self.rate_limit_delay = 1  # Delay between requests
    
    def search_greenhouse_jobs(self, job_title: str, max_results: int = 30) -> List[str]:
        """
        Search for Greenhouse job postings using Google Search API
        
        Args:
            job_title: Job title to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of Greenhouse job URLs
        """
        # Build search query (site restriction handled by CSE configuration)
        query = f'"{job_title}"'
        
        # Removed date restriction to get more relevant results
        date_restrict = None
        
        job_urls = []
        start_index = 1
        
        try:
            while len(job_urls) < max_results and start_index <= 91:  # Google API limit
                # Execute search
                search_params = {
                    'q': query,
                    'cx': self.search_engine_id,
                    'start': start_index,
                    'num': min(10, max_results - len(job_urls))  # Max 10 per request
                }
                
                # Only add dateRestrict if it's not None
                if date_restrict:
                    search_params['dateRestrict'] = date_restrict
                
                result = self.service.cse().list(**search_params).execute()
                
                # Extract URLs from results
                items = result.get('items', [])
                if not items:
                    break
                
                for item in items:
                    url = item.get('link', '')
                    if url:  # Just check that URL exists
                        job_urls.append(url)
                
                start_index += 10
                time.sleep(self.rate_limit_delay)  # Rate limiting
                
        except HttpError as e:
            print(f"Google Search API error: {e}")
            return job_urls
        
        return job_urls[:max_results]
    
    
    def get_search_info(self, job_title: str) -> dict:
        """
        Get search metadata (total results, etc.)
        
        Args:
            job_title: Job title to search for
            
        Returns:
            Dictionary with search metadata
        """
        query = f'"{job_title}"'
        
        try:
            result = self.service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=1  # Just get metadata
            ).execute()
            
            search_info = result.get('searchInformation', {})
            return {
                'total_results': search_info.get('totalResults', '0'),
                'search_time': search_info.get('searchTime', 0),
                'formatted_total_results': search_info.get('formattedTotalResults', '0')
            }
        except HttpError as e:
            print(f"Error getting search info: {e}")
            return {'total_results': '0', 'search_time': 0, 'formatted_total_results': '0'}