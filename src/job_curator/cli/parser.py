import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Job Posting Curation Assistant - Find tech jobs from Greenhouse.io"
    )
    
    parser.add_argument(
        "title", 
        type=str, 
        help="Job title to search for (required)"
    )
    
    parser.add_argument(
        "--location", 
        type=str, 
        help="Location (city/state/remote)"
    )
    
    parser.add_argument(
        "--keywords", 
        type=str, 
        help="Comma-separated keywords to search in job descriptions"
    )
    
    parser.add_argument(
        "--company", 
        type=str, 
        help="Company name filter (optional, applied locally)"
    )
    
    
    return parser.parse_args()