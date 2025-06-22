#!/usr/bin/env python3
"""
HTML Collection Script
Fetches and saves HTML content from job URLs for HTML parsing
"""

import json
import requests
import time
import os
import hashlib
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class HTMLCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache_dir = "html_cache"
        self.rate_limit_delay = 1
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename"""
        # Extract meaningful parts from URL
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # Create filename: company_jobs_jobid.html
        if len(path_parts) >= 3:  # ['company', 'jobs', 'jobid']
            company = path_parts[0]
            job_id = path_parts[2].split('?')[0]  # Remove query params
            filename = f"{company}_jobs_{job_id}.html"
        else:
            # Fallback: use URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            filename = f"job_{url_hash}.html"
        
        return filename
    
    def fetch_and_save_html(self, url: str) -> bool:
        """Fetch HTML content and save to cache"""
        filename = self.url_to_filename(url)
        filepath = os.path.join(self.cache_dir, filename)
        
        # Skip if already cached
        if os.path.exists(filepath):
            print(f"✅ Already cached: {filename}")
            return True
        
        try:
            print(f"🌐 Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Save raw HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Save metadata
            metadata = {
                'url': url,
                'filename': filename,
                'status_code': response.status_code,
                'content_length': len(response.text),
                'fetch_time': time.time()
            }
            
            metadata_file = filepath.replace('.html', '_metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Saved: {filename} ({len(response.text)} chars)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to fetch {url}: {e}")
            return False
    
    def collect_all_urls(self, urls_file: str = "test_urls.json") -> dict:
        """Collect HTML for all URLs in the list"""
        # Load URLs
        try:
            with open(urls_file, 'r') as f:
                urls = json.load(f)
        except Exception as e:
            print(f"Error loading URLs: {e}")
            return {}
        
        print(f"📋 Processing {len(urls)} URLs...")
        
        results = {
            'total_urls': len(urls),
            'successful': 0,
            'failed': 0,
            'cached_files': []
        }
        
        for i, url in enumerate(urls, 1):
            print(f"\n--- {i}/{len(urls)} ---")
            
            if self.fetch_and_save_html(url):
                results['successful'] += 1
                filename = self.url_to_filename(url)
                results['cached_files'].append({
                    'url': url,
                    'filename': filename,
                    'filepath': os.path.join(self.cache_dir, filename)
                })
            else:
                results['failed'] += 1
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
        
        # Save collection summary
        with open('html_collection_summary.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 Collection Complete!")
        print(f"✅ Successful: {results['successful']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"📁 Files saved in: {self.cache_dir}/")
        
        return results
    
    def preview_cached_content(self, limit: int = 3):
        """Preview some cached HTML files"""
        html_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.html')]
        
        print(f"📂 Found {len(html_files)} cached HTML files")
        
        for filename in html_files[:limit]:
            filepath = os.path.join(self.cache_dir, filename)
            
            print(f"\n--- Preview: {filename} ---")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse with BeautifulSoup for preview
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.find('title')
            h1 = soup.find('h1')
            
            print(f"📄 Title: {title.text.strip() if title else 'No title'}")
            print(f"📰 H1: {h1.text.strip() if h1 else 'No H1'}")
            print(f"📊 Content length: {len(content)} characters")


def main():
    collector = HTMLCollector()
    
    print("🚀 HTML Collection for Claude Processing")
    print("=" * 50)
    
    # Collect all HTML files
    results = collector.collect_all_urls()
    
    # Preview some files
    print(f"\n📋 Preview of cached content:")
    collector.preview_cached_content(limit=3)
    
    print(f"\n✨ Ready for Claude processing!")
    print(f"Next step: Run claude_processor.py to extract job information")


if __name__ == "__main__":
    main()