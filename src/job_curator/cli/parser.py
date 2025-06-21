import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Job Posting Curation Assistant - Find tech jobs from Greenhouse.io"
    )
    
    parser.add_argument(
        "--title", 
        type=str, 
        help="Job title to search for (partial matching)"
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
        help="Company name (optional)"
    )
    
    parser.add_argument(
        "--export", 
        type=str, 
        help="Export results to CSV file (provide filename)"
    )
    
    return parser.parse_args()