import requests
import random
import os
import json
import time
import markdown  # New lib: pip install markdown
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
REPO_NAME = "tech-daily"
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY_OWNER')
AD_LINK = "https://www.effectivegatecpm.com/r7dzfzj7k3?key=149604651f31a5a4ab1b1cd51effc10b"

# --- NEW: LIVE TREND JACKING ---
def get_trending_topics():
    """Fetches real-time rising trends from Google (US Region)"""
    # We target US for higher CPM. Change geo=NG for Nigeria.
    rss_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    try:
        r = requests.get(rss_url, timeout=10)
        root = ET.fromstring(r.content)
        # Extract titles from the RSS feed
        trends = [item.find('title').text for item in root.findall('.//item')]
        return trends
    except Exception as e:
        print(f"⚠️ Trend fetch failed: {e}")
        return []

def get_dynamic_model(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        r = requests.get(url)
        data = r.json()
        valid_models = [m['name'] for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        if not valid_models: return None
        # Prefer Flash for speed, then Pro
        return next((m for m in valid_models if 'flash' in m), next((m for m in valid_models if 'pro' in m), valid_models[0]))
    except: return None

def get_gemini_article(title):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return None
    model_name = get_dynamic_model(api_key)
    
    # IMPROVED PROMPT: Forces the bot to write specific "How-To" guides for trends
    prompt = f"""
    You are a tech troubleshooter. Write a technical blog post about: "{title}".
    FOCUS: If this is a person or news event, ignore the news and write a guide on "How to fix/watch/access" it.
    
    Structure (Markdown):
    - H1 Title
    - Intro (Mention the error/issue clearly)
    - H2 Possible Causes
    - H2 Step-by-Step Fixes (Use numbered lists)
    - H2 FAQ
    
    Keep it under 700 words. Be direct.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return None

def update_homepage(filename, title):
    index_path = "index.html"
    entry = f'<li><a href="{filename}"><strong>{title}</strong></a> <small>({datetime.now().strftime("%H:%M")})</small></li>'
    
    if not os.path.exists(index_path):
        with open(index_path, "w") as f:
            f.write(f"<html><head><title>Tech Fix Daily</title><meta name='viewport' content='width=device-width, initial-scale=1'></head><body><h1>🔥 Trending Fixes</h1><ul>{entry}</ul></body></html>")
    else:
        with open(index_path, "r") as f: content = f.read()
        if "<ul>" in content:
            content = content.replace("<ul>", f"<ul>\n{entry}")
        with open(index_path, "w") as f: f.write(content)

def main():
    print("💀 Waking up the zombie...")
    
    # 1. GET LIVE TRENDS
    trends = get_trending_topics()
    
    # 2. FILTER & SELECT
    # We look for tech-adjacent keywords, or just pick the top rising one
    keywords = ['error', 'fix', 'crash', 'not working', 'down', 'iphone', 'android', 'windows', 'code', 'bug']
    tech_trends = [t for t in trends if any(k in t.lower() for k in keywords)]
    
    if tech_trends:
        topic = random.choice(tech_trends)
        # Add a "modifier" to make it a "How-to" query
        topic = f"Fix {topic} error"
    else:
        # Fallback if no tech trends: Pick top trend and make it a "How to watch/access" guide
        topic = f"How to access {random.choice(trends)}" if trends else "Fix Android System WebView Crash"

    print(f"🎯 Target Locked: {topic}")
    
    # 3. GENERATE CONTENT
    article_md = get_gemini_article(topic)
    
    if article_md:
        # 4. BETTER HTML CONVERSION (Uses 'markdown' lib)
        article_html = markdown.markdown(article_md)
        
        filename = topic.lower().replace(" ", "-")[:40] + ".html"
        
        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{topic} - Quick Fix</title>
            <meta name="description" content="Simple guide to fix {topic}. Step by step tutorial.">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #333; }}
                h1 {{ color: #d32f2f; }}
                h2 {{ margin-top: 30px; }}
                .ad-box {{ background: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0; }}
                .btn {{ background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <a href="index.html">← Back</a>
            
            <div class="ad-box">
                <b>⚡ Quick Fix Available</b><br>
                <small>System scan recommended for this error.</small><br>
                <a href="{AD_LINK}" class="btn">▶ REPAIR NOW</a>
            </div>

            {article_html}

            <div class="ad-box">
                <b>📂 Download Required Files</b><br>
                <a href="{AD_LINK}" class="btn">⬇ DOWNLOAD</a>
            </div>
        </body>
        </html>
        """
        
        with open(filename, "w") as f: f.write(full_html)
        update_homepage(filename, topic)
        print(f"✅ Published: {filename}")
        
    else:
        print("❌ Generation failed.")

if __name__ == "__main__":
    main()
