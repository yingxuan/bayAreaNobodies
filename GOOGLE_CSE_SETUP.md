# Google Custom Search Engine (CSE) Setup Guide

This guide will help you set up Google CSE credentials to enable real article fetching from 1point3acres, Teamblind, and Xiaohongshu.

## Quick Setup Steps

### 1. Get Google API Key

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable "Custom Search API":
   - Navigate to: **APIs & Services** > **Library**
   - Search for "Custom Search API"
   - Click **Enable**
4. Create API Key:
   - Go to: **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **API Key**
   - Copy the API key (you'll need it later)

### 2. Create Custom Search Engine

1. Visit [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click **Add** to create a new search engine
3. Configure:
   - **Sites to search** (add one per line):
     ```
     1point3acres.com
     teamblind.com
     xiaohongshu.com
     ```
   - **Name**: "Bay Area Daily Search" (or any name you prefer)
4. Click **Create**
5. After creation, go to **Setup** > **Basics**
6. Copy your **Search Engine ID** (looks like: `017576662512468239146:omuauf_lfve`)

### 3. Create .env File

Create a `.env` file in the project root directory with your credentials:

```bash
GOOGLE_CSE_API_KEY=your_actual_api_key_here
GOOGLE_CSE_ID=your_actual_search_engine_id_here
```

**Example:**
```bash
GOOGLE_CSE_API_KEY=AIzaSyB1234567890abcdefghijklmnopqrstuvw
GOOGLE_CSE_ID=017576662512468239146:omuauf_lfve
```

### 4. Restart Docker Containers

After creating the `.env` file, restart your containers to load the new environment variables:

```bash
docker compose down
docker compose up --build
```

### 5. Test Your Credentials

Verify that your credentials are working:

```bash
docker compose exec api python test_google_cse.py
```

You should see:
```
✅ Google CSE credentials are working!
```

## Troubleshooting

### "API key not valid" error
- Make sure the Custom Search API is enabled in Google Cloud Console
- Check that your API key is correct (no extra spaces)
- Verify the API key hasn't been restricted to specific APIs

### "Search Engine ID not found" error
- Double-check your Search Engine ID
- Make sure you copied the entire ID (it's usually quite long)

### "No results returned" warning
- Verify your CSE includes the sites: `1point3acres.com`, `teamblind.com`, `xiaohongshu.com`
- Check that the sites are indexed (may take a few minutes after creation)
- Try a different search query

### API Quota Exceeded
- Google CSE free tier: 100 queries per day
- For production, consider upgrading to a paid plan
- The app uses Redis caching to minimize API calls

## What Happens Next?

Once credentials are set up:
- The scheduler will automatically fetch articles every hour
- Articles will be stored in the database
- They'll appear on the trending page at http://localhost:3000
- No more mock data warnings in the logs!

## Security Notes

- **Never commit your `.env` file to git** (it's already in `.gitignore`)
- Consider restricting your API key to only the Custom Search API
- For production, use environment variables from your hosting provider instead of a `.env` file

