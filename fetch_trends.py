# fetch_trends.py
# Requires: pytrends, requests
# Usage: run in GitHub Actions; secrets must be set as env variables
import os
import time
import json
import requests
from datetime import datetime

try:
    from pytrends.request import TrendReq
except Exception as e:
    print("pytrends not installed or failed import:", e)
    raise

# Configuration
HOSTINGER_PUSH_URL = os.getenv("https://blackbrain.in/DailyQubit/trending/trending_receiver.php")  # e.g. https://yourdomain.com/trending_receiver.php
TRENDING_AUTH_TOKEN = os.getenv("TRENDINXQ4zV6yJkFpT9aC2hG7eL0mR8sU3wB1dY5nK6qP4xZ2jM8vN7rW9tA1bC5dV0uE6fI3gH4iJ2kL0mO8pQ7rS9tU1vW5xY6zD3fG9hJ1kL0mN8pQ7rS9tU1G_AUTH_TOKEN")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")  # optional
PERPLEXITY_KEY = os.getenv("PERPLEXITY_KEY")  # optional
SERPAPI_KEY = os.getenv("SERPAPI_KEY")  # optional

# Countries you asked for with pytrends 'pn' mapping and optional X WOEID mapping
COUNTRIES = {
    "IN": {"pn": "india", "woeid": 23424848},
    "US": {"pn": "united_states", "woeid": 23424977},
    "CN": {"pn": "china", "woeid": None},
    "JP": {"pn": "japan", "woeid": None},
    "GB": {"pn": "united_kingdom", "woeid": 23424975},
    "DE": {"pn": "germany", "woeid": 23424829},
    "CA": {"pn": "canada", "woeid": 23424775},
    "KR": {"pn": "south_korea", "woeid": None},
    "FR": {"pn": "france", "woeid": 23424819}
}

# Helper: POST JSON to Hostinger
def push_json_to_host(source, country, top_list):
    if not HOSTINGER_PUSH_URL or not TRENDING_AUTH_TOKEN:
        print("HOSTINGER_PUSH_URL or TRENDING_AUTH_TOKEN missing; not pushing.")
        return False
    payload = {
        "source": source,
        "country": country,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "top": top_list
    }
    headers = {
        "Authorization": f"Bearer {TRENDING_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(HOSTINGER_PUSH_URL, headers=headers, json=payload, timeout=30)
        print("Push", source, country, r.status_code, r.text)
        return r.status_code >= 200 and r.status_code < 300
    except Exception as e:
        print("Push error", e)
        return False

# Fetch Google trending searches using pytrends
def fetch_google_trending(country_code):
    pn = COUNTRIES.get(country_code, {}).get("pn", None)
    pytrends = TrendReq(hl='en-US', tz=330)
    results = []
    try:
        if pn:
            df = pytrends.trending_searches(pn=pn)
        else:
            # fallback: global
            df = pytrends.trending_searches(pn='united_states')
        # df is a DataFrame with one column; iterate top 10
        for i, row in enumerate(df.head(10).itertuples(index=False), start=1):
            query = str(row[0])
            results.append({"rank": i, "title": query, "query": query, "url": ""})
    except Exception as e:
        print("pytrends error for", country_code, e)
    return results

# Fetch X (Twitter) trending topics (v1.1 endpoint)
def fetch_x_trending(country_code):
    if not X_BEARER_TOKEN:
        print("X_BEARER_TOKEN not present; skipping X trends")
        return []
    woeid = COUNTRIES.get(country_code, {}).get("woeid", None)
    if not woeid:
        print("WOEID missing for", country_code)
        return []
    url = f"https://api.twitter.com/1.1/trends/place.json?id={woeid}"
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code != 200:
            print("X trends HTTP", r.status_code, r.text)
            return []
        data = r.json()
        results = []
        if isinstance(data, list) and len(data) > 0:
            trends = data[0].get('trends', [])
            for i, t in enumerate(trends[:10], start=1):
                name = t.get('name') or t.get('query') or ''
                query = t.get('query') or name
                url_t = t.get('url') or ''
                results.append({"rank": i, "title": name, "query": query, "url": url_t})
        return results
    except Exception as e:
        print("X trends fetch error", e)
        return []

# Placeholder for AI provider (Perplexity / ChatGPT-like)
def fetch_ai_trending(country_code):
    # If you have PERPLEXITY_KEY, implement an API call here per provider docs.
    # For now this returns an empty list or crude placeholder.
    if not PERPLEXITY_KEY:
        print("PERPLEXITY_KEY not present; skipping AI trends")
        return []
    # Example idea (must adapt to real Perplexity API):
    try:
        q = f"Top trending search queries in {country_code}"
        headers = {"Authorization": f"Bearer {PERPLEXITY_KEY}", "Content-Type": "application/json"}
        # endpoint may differ; please consult provider docs
        r = requests.post("https://api.perplexity.ai/search", headers=headers, json={"query": q}, timeout=20)
        if r.status_code != 200:
            print("Perplexity API error", r.status_code, r.text)
            return []
        data = r.json()
        # parse data to create top list. Implementation depends on provider response.
        # For now return empty.
        return []
    except Exception as e:
        print("Perplexity fetch error", e)
        return []

def main():
    for country in COUNTRIES.keys():
        print("Processing", country)
        # Google
        google_top = fetch_google_trending(country)
        if google_top:
            push_json_to_host("google", country, google_top)
            time.sleep(1)

        # X
        x_top = fetch_x_trending(country)
        if x_top:
            push_json_to_host("x", country, x_top)
            time.sleep(1)

        # AI
        ai_top = fetch_ai_trending(country)
        if ai_top:
            push_json_to_host("ai", country, ai_top)
            time.sleep(1)

if __name__ == "__main__":
    main()
