# Google Search API Setup

The job aggregator now uses Google Custom Search API to find Greenhouse job postings. Follow these steps to set up the API:

## 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Custom Search API:
   - Go to "APIs & Services" > "Library"
   - Search for "Custom Search API"
   - Click "Enable"

## 2. Create API Key

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the API key
4. (Optional) Restrict the API key to Custom Search API only for security

## 3. Create Custom Search Engine

1. Go to [Google Custom Search Engine](https://cse.google.com/cse/)
2. Click "Add" to create a new search engine
3. In "Sites to search", enter: `boards.greenhouse.io/*`
4. Give it a name like "Greenhouse Job Search"
5. Click "Create"
6. Copy the Search Engine ID from the setup page

## 4. Set Environment Variables

Set these environment variables in your system:

```bash
export GOOGLE_API_KEY="your_api_key_here"
export GOOGLE_CSE_ID="your_search_engine_id_here"
```

Or create a `.env` file in the project root:

```
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_search_engine_id_here
```

## 5. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

Now you can search for jobs with just a job title:

```bash
python job_curator.py "software engineer"
python job_curator.py "data scientist" --location "remote"
python job_curator.py "product manager" --company "stripe"
```

## API Limits

- Google Custom Search API has a free tier of 100 searches per day
- Additional searches cost $5 per 1000 queries
- The scraper implements rate limiting to respect API limits

## Fallback Mode

If Google API is not configured, the scraper will fall back to the legacy method of searching predefined companies directly.