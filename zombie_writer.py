import random
import os
import json
import time
import markdown
import requests # Keep for Gemini/Dev.to interactions
from curl_cffi import requests as crequests # The "Stealth" Browser
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
REPO_NAME = "tech-daily"
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY_OWNER')
AD_LINK = "https://www.effectivegatecpm.com/r7dzfzj7k3?key=149604651f31a5a4ab1b1cd51effc10b"

# --- 1. ENGINEERED TREND FETCHER (TLS SPOOFING) ---
def get_trending_topics():
    print("🕵️ Attempting Stealth Connection to Google...")
    
    # We use Google's internal JSON API (Backdoor) instead of RSS
    # This endpoint is often less rate-limited than the RSS feed.
    google_json_url = "https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=0&geo=US&ns=15"
    
    try:
        # IMPERSONATE CHROME 110
        # This performs the SSL handshake exactly like a real browser
        r = crequests.get(google_json_url, impersonate="chrome110", timeout=15)
        
        if r.status_code == 200:
            # Google adds a ")]}',\n" prefix to prevent JSON hijacking. We must strip it.
            clean_json = r.text.replace(")]}',\n", "")
            data = json.loads(clean_json)
            
            # Extract trends from the nested JSON structure
            trends = []
            for day in data.get('default', {}).get('trendingSearchesDays', []):
                for search in day.get('trendingSearches', []):
                    query = search.get('title', {}).get('query')
                    if query:
                        trends.append(query)
            
            if trends:
                print(f"✅ Google Hacked: Found {len(trends)} trends via JSON API")
                return trends
                
    except Exception as e:
        print(f"❌ Google Stealth Failed: {e}")

    # --- FALLBACK SYSTEM (If Google still blocks us) ---
    print("⚠️ Google defense active. Switching to backup feeds.")
    backup_sources = [
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.feedburner.com/TechCrunch/"
    ]
    
    # Use standard requests for backups (TLS spoofing not needed for these)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    for rss_url in backup_sources:
        try:
            r = requests.get(rss_url, headers=headers, timeout=10)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                trends = []
                items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
                for item in items:
                    title = item.find('title')
                    if title is None: title = item.find('{http://www.w3.org/2005/Atom}title')
                    if title is not None and title.text: trends.append(title.text)
                if trends: 
                    print(f"✅ Backup Success: Found topics from {rss_url}")
                    return trends
        except: continue

    return []

# --- AI & UTILS ---
def get_dynamic_model(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        r = requests.get(url) # Standard requests is fine here
        data = r.json()
        valid_models = [m['name'] for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        if not valid_models: return None
        return next((m for m in valid_models if 'flash' in m), next((m for m in valid_models if 'pro' in m), valid_models[0]))
    except: return None

def get_gemini_article(title):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return None
    model_name = get_dynamic_model(api_key)
    
    prompt = f"""
    You are a technical writer. Write a blog post about: "{title}".
    IMPORTANT: If this is news, ignore the news aspect and write a "How-To" guide related to it.
    Use Markdown. Include H1, Intro, Causes, Steps, FAQ.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    payload = { "contents": [{"parts": [{"text": prompt}]}], "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}]}
    
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return None

def clean_filename(topic):
    clean = topic.lower().replace(":", "").replace("’", "").replace("'", "").replace('"', "")
    return clean.replace(" ", "-").replace("?", "").replace("/", "")[:50] + ".html"

def update_homepage(filename, title):
    index_path = "index.html"
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = f'<li><span style="color:#666; font-size:0.8em;">[{date_str}]</span> <a href="{filename}"><strong>{title}</strong></a></li>'
    if not os.path.exists(index_path):
        with open(index_path, "w") as f: f.write(f"<html><head><title>Daily Tech Fixes</title></head><body><h1>🔥 Latest Fixes</h1><ul>{entry}</ul></body></html>")
    else:
        with open(index_path, "r") as f: content = f.read()
        if filename in content: return
        if "<ul>" in content: content = content.replace("<ul>", f"<ul>\n{entry}")
        with open(index_path, "w") as f: f.write(content)

def update_sitemap(filename):
    sitemap_path = "sitemap.xml"
    base_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
    today = datetime.now().strftime("%Y-%m-%d")
    new_url = f"<url><loc>{base_url}{filename}</loc><lastmod>{today}</lastmod></url>"
    if not os.path.exists(sitemap_path):
        content = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{new_url}</urlset>'
    else:
        with open(sitemap_path, "r") as f: content = f.read()
        if filename in content: return
        if "</urlset>" in content: content = content.replace("</urlset>", new_url + "</urlset>")
    with open(sitemap_path, "w") as f: f.write(content)

def post_to_devto(title, content, original_url):
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key: return
    trap_content = f"{content}\n\n## ⚡ Quick Solution\n\n[**▶ CLICK HERE TO FIX THIS ERROR**]({AD_LINK})"
    requests.post("https://dev.to/api/articles", 
        json={"article": {"title": title, "published": True, "body_markdown": trap_content, "canonical_url": original_url}}, 
        headers={"api-key": api_key, "Content-Type": "application/json"})

def main():
    print("💀 Zombie Bot Rising...")
    
    # 1. Fetch Trends (Stealth Mode)
    trends = get_trending_topics()
    random.shuffle(trends)
    
    selected_topic = None
    final_filename = None
    
    for raw_topic in trends:
        # Enhanced Topic Logic
        if len(raw_topic.split()) > 6: 
             topic_title = f"Review: {raw_topic}"
        elif any(x in raw_topic.lower() for x in ['top', 'best', 'vs', 'review', 'list']):
             topic_title = f"Guide: {raw_topic} Explained"
        else:
             topic_title = f"How to Fix {raw_topic} Error"

        check_filename = clean_filename(topic_title)
        
        if os.path.exists(check_filename):
            print(f"⚠️ Duplicate Found: {check_filename}")
            continue
        else:
            selected_topic = topic_title
            final_filename = check_filename
            break
    
    if not selected_topic:
        print("❌ No fresh topics found.")
        exit(0)

    print(f"🎯 Target Locked: {selected_topic}")
    
    article_md = get_gemini_article(selected_topic)
    
    if article_md:
        article_html = markdown.markdown(article_md)
        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{selected_topic}</title>
            <style>
                body {{ font-family: sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #d32f2f; }}
                .ad-box {{ background: #e8f5e9; border: 2px solid #4caf50; padding: 20px; text-align: center; margin: 30px 0; }}
                .btn {{ background: #d32f2f; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <a href="index.html">← Back</a>
            <div class="ad-box"><h3>⚠️ Action Required</h3><a href="{AD_LINK}" class="btn">▶ START SCAN</a></div>
            {article_html}
            <div class="ad-box"><h3>⬇️ Download Fix</h3><a href="{AD_LINK}" class="btn">DOWNLOAD</a></div>
            <p><small>{datetime.now().strftime("%Y-%m-%d")}</small></p>
        </body>
        </html>
        """
        
        with open(final_filename, "w") as f: f.write(full_html)
        update_homepage(final_filename, selected_topic)
        update_sitemap(final_filename)
        original_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/{final_filename}"
        post_to_devto(selected_topic, article_md, original_url)
        print(f"✅ Successfully Published: {final_filename}")

if __name__ == "__main__":
    main()
