import requests
import random
import os
import json
import time
import markdown
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
REPO_NAME = "tech-daily"
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY_OWNER')
# Your Money Link
AD_LINK = "https://www.effectivegatecpm.com/r7dzfzj7k3?key=149604651f31a5a4ab1b1cd51effc10b"

# --- 1. ADVANCED RSS FETCHER (ANTI-BLOCK) ---
def get_trending_topics():
    """Fetches trends using browser simulation and multiple Google endpoints"""
    
    sources = [
        # 1. Google Trends RSS (Standard)
        "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
        # 2. Google Trends Atom (Legacy - Often works when RSS fails)
        "https://trends.google.com/trends/hottrends/atom/feed?pn=p1",
        # 3. Backup: Tech News
        "https://www.theverge.com/rss/index.xml",
        # 4. Backup: Startups
        "https://feeds.feedburner.com/TechCrunch/"
    ]

    # Full Browser Headers to look like a real person
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    for rss_url in sources:
        try:
            print(f"🔌 Connecting to: {rss_url}...")
            r = requests.get(rss_url, headers=headers, timeout=10)
            
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                trends = []
                
                # Support both 'item' (RSS) and 'entry' (Atom) XML tags
                items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
                
                for item in items:
                    # Support both 'title' (RSS) and 'title' (Atom)
                    title = item.find('title')
                    if title is None:
                        # Atom namespace handling
                        title = item.find('{http://www.w3.org/2005/Atom}title')
                    
                    if title is not None and title.text:
                        trends.append(title.text)
                
                if trends:
                    print(f"✅ Success! Found {len(trends)} topics from {rss_url}")
                    return trends
            else:
                print(f"⚠️ Blocked ({r.status_code}). Trying next...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
            
    print("💀 All sources failed. Using emergency fallback.")
    return []

def get_dynamic_model(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        r = requests.get(url)
        data = r.json()
        valid_models = [m['name'] for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        if not valid_models: return None
        return next((m for m in valid_models if 'flash' in m), next((m for m in valid_models if 'pro' in m), valid_models[0]))
    except: return None

# --- 2. AI CONTENT GENERATOR ---
def get_gemini_article(title):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return None
    model_name = get_dynamic_model(api_key)
    
    prompt = f"""
    You are a technical writer. Write a blog post about: "{title}".
    
    IMPORTANT RULES:
    1. If the topic is a person or news event, ignore the news and write a guide on "How to fix/watch/access" it.
    2. Use Markdown formatting (##, -).
    3. Include a clear H1 title.
    
    Structure:
    - Introduction (The Issue)
    - 3 Common Causes
    - Step-by-Step Solution (Numbered list)
    - FAQ Section
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

# --- 3. SITE UPDATERS ---
def update_homepage(filename, title):
    index_path = "index.html"
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = f'<li><span style="color:#666; font-size:0.8em;">[{date_str}]</span> <a href="{filename}"><strong>{title}</strong></a></li>'
    
    if not os.path.exists(index_path):
        with open(index_path, "w") as f:
            f.write(f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Daily Tech Fixes</title>
                <style>
                    body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
                    ul {{ list-style-type: none; padding: 0; }}
                    li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
                    a {{ text-decoration: none; color: #007bff; font-size: 1.1em; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <h1>🔥 Latest Fixes & Guides</h1>
                <ul>{entry}</ul>
            </body>
            </html>
            """)
    else:
        with open(index_path, "r") as f: content = f.read()
        if "<ul>" in content:
            content = content.replace("<ul>", f"<ul>\n{entry}")
        with open(index_path, "w") as f: f.write(content)

def update_sitemap(filename):
    sitemap_path = "sitemap.xml"
    base_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
    today = datetime.now().strftime("%Y-%m-%d")
    
    new_url_block = f"""
  <url>
    <loc>{base_url}{filename}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
  </url>
"""
    if not os.path.exists(sitemap_path):
        content = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{new_url_block}</urlset>'
    else:
        with open(sitemap_path, "r") as f: content = f.read()
        if "</urlset>" in content:
            content = content.replace("</urlset>", new_url_block + "</urlset>")
    
    with open(sitemap_path, "w") as f: f.write(content)

def post_to_devto(title, content, original_url):
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key: return

    trap_content = f"{content}\n\n## ⚡ Quick Solution\n\n[**▶ CLICK HERE TO FIX THIS ERROR**]({AD_LINK})"
    
    url = "https://dev.to/api/articles"
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "article": {
            "title": title,
            "published": True,
            "body_markdown": trap_content,
            "tags": ["tutorial", "beginners", "productivity", "android"],
            "canonical_url": original_url
        }
    }
    try:
        requests.post(url, json=payload, headers=headers)
        print("🪞 Mirrored to Dev.to")
    except: pass

# --- MAIN EXECUTION ---
def main():
    print("💀 Zombie Bot Rising...")
    
    # 1. Get Topic
    trends = get_trending_topics()
    
    # Intelligent Filtering
    keywords = ['error', 'fix', 'crash', 'fail', 'slow', 'update', 'stuck', 'iphone', 'android', 'windows']
    tech_trends = [t for t in trends if any(k in t.lower() for k in keywords)]
    
    if tech_trends:
        raw_topic = random.choice(tech_trends)
        # SMART TITLE LOGIC
        if any(x in raw_topic.lower() for x in ['top', 'best', 'vs', 'review', 'list']):
             topic = f"Guide: {raw_topic} Explained"
        else:
             topic = f"How to Fix {raw_topic} Error"
             
    elif trends:
        raw_topic = random.choice(trends)
        if any(x in raw_topic.lower() for x in ['top', 'best', 'vs']):
             topic = f"Guide: {raw_topic} Review"
        else:
             topic = f"How to Watch or Access {raw_topic}"
    else:
        topic = "How to Fix Android System WebView Crash"

    print(f"🎯 Target Locked: {topic}")
    
    # 2. Generate Content
    article_md = get_gemini_article(topic)
    
    if article_md:
        # 3. HTML Conversion
        article_html = markdown.markdown(article_md)
        filename = topic.lower().replace(" ", "-").replace("?", "").replace("/", "")[:50] + ".html"
        
        # 4. Create Page with Ad Injection
        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{topic} - Quick Guide</title>
            <meta name="description" content="Step by step guide to fix {topic}. Works for 2026.">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #333; line-height: 1.6; }}
                h1 {{ color: #d32f2f; }}
                img {{ max-width: 100%; height: auto; }}
                pre {{ background: #f4f4f4; padding: 10px; overflow-x: auto; }}
                .ad-box {{ background: #e8f5e9; border: 2px solid #4caf50; padding: 20px; text-align: center; margin: 30px 0; border-radius: 8px; }}
                .btn {{ background: #d32f2f; color: white; padding: 12px 25px; text-decoration: none; font-weight: bold; border-radius: 5px; display: inline-block; margin-top: 10px; font-size: 1.1em; }}
                .btn:hover {{ background: #b71c1c; }}
            </style>
        </head>
        <body>
            <a href="index.html">← Back to Home</a>
            
            <div class="ad-box">
                <h3>⚠️ Recommended Action</h3>
                <p>Run a system scan to identify the root cause of this error.</p>
                <a href="{AD_LINK}" class="btn">▶ START SCAN</a>
            </div>

            {article_html}

            <div class="ad-box">
                <h3>⬇️ Download Fix</h3>
                <p>Get the necessary files to repair your system.</p>
                <a href="{AD_LINK}" class="btn">DOWNLOAD TOOLS</a>
            </div>
            
            <hr>
            <p><small>Posted on {datetime.now().strftime("%Y-%m-%d")}</small></p>
        </body>
        </html>
        """
        
        with open(filename, "w") as f: f.write(full_html)
        update_homepage(filename, topic)
        update_sitemap(filename)
        
        original_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/{filename}"
        post_to_devto(topic, article_md, original_url)
        
        print(f"✅ Successfully Published: {filename}")
        
    else:
        print("❌ Generation failed.")
        exit(1)

if __name__ == "__main__":
    main()
