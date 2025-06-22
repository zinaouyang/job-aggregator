#!/usr/bin/env python3
"""
Test Parsing Script
Uses test_urls.json to test HTML parsing improvements efficiently
"""

import json
import requests
from bs4 import BeautifulSoup
from src.job_curator.scraper.greenhouse import GreenhouseScraper


def test_location_extraction():
    """Test location extraction with URLs from test_urls.json"""
    
    # Load test URLs
    try:
        with open('test_urls.json', 'r') as f:
            test_urls = json.load(f)
    except FileNotFoundError:
        print("❌ test_urls.json not found")
        return
    
    print("🧪 Testing Location Extraction")
    print("=" * 50)
    
    # Create scraper instance for HTML extraction method
    scraper = GreenhouseScraper(use_cached_urls=True)
    
    # Test first 5 URLs for quick feedback
    test_urls_sample = test_urls[:5]
    
    for i, url in enumerate(test_urls_sample, 1):
        print(f"\n📄 Test {i}/5: {url}")
        
        try:
            # Get HTML content
            response = scraper.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Extract job info using our HTML parsing method
            filename = url.split('/')[-1]
            job = scraper._extract_job_from_html(response.content.decode('utf-8'), filename, url=url)
            
            if job:
                print(f"   ✅ Title: {job.title}")
                print(f"   🏢 Company: {job.company}")
                print(f"   📍 Location: {job.location}")
                print(f"   💰 Compensation: {job.compensation or 'Not specified'}")
                
                # Highlight location extraction success
                if job.location and job.location != "Location not specified":
                    print(f"   🎯 Location extracted successfully!")
                else:
                    print(f"   ⚠️ Location not found")
            else:
                print(f"   ❌ No job info extracted")
                
        except Exception as e:
            print(f"   💥 Error: {e}")
    
    print(f"\n✅ Location extraction test complete")


def test_specific_url_parsing(url):
    """Test parsing for a specific URL with detailed debugging"""
    
    print(f"🔍 Detailed Parsing Test for: {url}")
    print("=" * 60)
    
    try:
        scraper = GreenhouseScraper(use_cached_urls=True)
        response = scraper.session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Debug title extraction
        print("📋 Title Analysis:")
        title_tag = soup.find('title')
        if title_tag:
            print(f"   Page Title: {title_tag.get_text().strip()}")
        
        # Debug JSON-LD data
        print("\n📊 JSON-LD Analysis:")
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for i, script in enumerate(json_ld_scripts):
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'JobPosting':
                    print(f"   JobPosting found:")
                    print(f"     Title: {data.get('title')}")
                    print(f"     jobLocation: {data.get('jobLocation')}")
                    if data.get('jobLocation'):
                        loc = data['jobLocation']
                        if isinstance(loc, dict):
                            print(f"     Location address: {loc.get('address')}")
                        else:
                            print(f"     Location value: {loc}")
                    break
            except Exception as e:
                print(f"   Error parsing JSON-LD {i}: {e}")
        
        # Debug location selectors
        print("\n🎯 Location Selector Analysis:")
        location_selectors = [
            'div.location', '.location', '[data-qa="job-location"]',
            '.job-location', 'div[class*="location"]'
        ]
        
        for selector in location_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"   {selector}: {[elem.get_text().strip() for elem in elements[:3]]}")
        
        # Debug text content for location keywords
        print("\n🔍 Location Keywords in Text:")
        text_content = soup.get_text()
        location_keywords = ['India', 'Remote', 'San Francisco', 'New York', 'Boston', 'Seattle', 'USA', 'United States', 'CA', 'NY']
        
        for keyword in location_keywords:
            if keyword in text_content:
                print(f"   Found '{keyword}' in text")
                # Show context around the keyword
                lines = text_content.split('\n')
                for line in lines:
                    if keyword in line and len(line.strip()) < 100:
                        print(f"     Context: {line.strip()}")
        
        # Debug HTML structure around location
        print("\n🏗️ HTML Structure Analysis:")
        # Look for any elements containing location keywords
        for keyword in ['India', 'Remote', 'San Francisco']:
            if keyword in text_content:
                elements = soup.find_all(string=lambda text: text and keyword in text)
                for i, element in enumerate(elements[:3]):
                    if element.parent:
                        parent_tag = element.parent.name
                        parent_class = element.parent.get('class', [])
                        parent_id = element.parent.get('id', '')
                        print(f"   '{keyword}' found in <{parent_tag}> class={parent_class} id={parent_id}")
                        print(f"     Text: {element.strip()[:100]}")
        
        # Debug why extraction might be failing
        print("\n🚨 Extraction Debugging:")
        if " - " in soup.find('title').get_text():
            parts = soup.find('title').get_text().split(" - ")
            print(f"   Title parts: {parts}")
        else:
            print("   No ' - ' found in title for parsing")
        
        # Test actual extraction
        print(f"\n🧪 Final Extraction Result:")
        filename = url.split('/')[-1]
        job = scraper._extract_job_from_html(response.content.decode('utf-8'), filename, url=url)
        
        if job:
            print(f"   Title: {job.title}")
            print(f"   Company: {job.company}")
            print(f"   Location: {job.location}")
            print(f"   Compensation: {job.compensation}")
        else:
            print(f"   ❌ No job extracted")
            
    except Exception as e:
        print(f"💥 Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific URL if provided
        test_url = sys.argv[1]
        test_specific_url_parsing(test_url)
    else:
        # Run general location extraction test
        test_location_extraction()