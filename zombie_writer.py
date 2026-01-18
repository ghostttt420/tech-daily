import random
import os
import json
import time
import markdown
import requests  # Standard requests for Gemini/Dev.to
from curl_cffi import requests as crequests  # Stealth browser for Google
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
REPO_NAME = "tech-daily"
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY_OWNER')
AD_LINK = "https://www.effectivegatecpm.com/r7dzfzj7k3?key=149604651f31a5a4ab1b1cd51effc10b"

# --- 1. STEALTH TREND FETCHER ---
def get_trending_topics():
    print("🕵️ Attempting Stealth Connection...")
    
    # 1. Try Google Internal API (Chrome Impersonation)
    try:
        url = "https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=0&geo=US&ns=15"
        r = crequests.get(url, impersonate="chrome110", timeout=15)
        if r.status_code == 200:
            clean_json = r.text.replace(")]}',\n", "")
            data = json.loads(clean_json)
            trends = []
            for day in data.get('default', {}).get('trendingSearchesDays', []):
                for search in day.get('trendingSearches', []):
                    query = search.get('title', {}).get('query')
                    if query: trends.append(query)
            if trends:
                print(f"✅ Google Success: Found {len(trends)} topics.")
                return trends
    except Exception as e:
        print(f"⚠️ Google Failed: {e}")

    # 2. Fallback to Tech News RSS
    print("🔌 Switching to Backup Feeds...")
    sources = [
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.feedburner.com/TechCrunch/",
        "https://www.wired.com/feed/rss"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    
    all_trends = []
    for rss_url in sources:
        try:
            r = requests.get(rss_url, headers=headers, timeout=10)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
                for item in items:
                    title = item.find('title')
                    if title is None: title = item.find('{http://www.w3.org/2005/Atom}title')
                    if title is not None and title.text: all_trends.append(title.text)
        except: continue
        
    return all_trends if all_trends else ["Android System WebView Crash"]

# --- 2. AI CONTENT GENERATOR ---
def get_dynamic_model(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        r = requests.get(url)
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
    INSTRUCTIONS:
    - If this is news, ignore the news and write a "How-To" guide related to the tech.
    - If this is an error, write a fix.
    - Use Markdown.
    - Tone: Professional, helpful, direct.
    
    Structure:
    - H1 Title
    - Intro
    - 3 Possible Causes
    - Step-by-Step Solution
    - Conclusion
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    payload = { "contents": [{"parts": [{"text": prompt}]}], "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}]}
    
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return None

# --- 3. UTILS & SELF-HEALING HOMEPAGE ---
def clean_filename(topic):
    clean = topic.lower().replace(":", "").replace("’", "").replace("'", "").replace('"', "")
    return clean.replace(" ", "-").replace("?", "").replace("/", "")[:50] + ".html"

def update_homepage_rebuild():
    """Scans the folder and completely rebuilds index.html to fix design & duplicates"""
    index_path = "index.html"
    
    # Scan for all HTML files (excluding system files)
    all_files = [f for f in os.listdir('.') if f.endswith('.html') and f not in ['index.html', '404.html']]
    # Sort by newest
    all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    cards_html = ""
    for article_file in all_files:
        display_title = article_file.replace("-", " ").replace(".html", "").title()
        display_date = datetime.fromtimestamp(os.path.getmtime(article_file)).strftime("%Y-%m-%d")
        
        cards_html += f"""
        <div class="article-card">
            <div class="card-header">
                <span class="badge">GUIDE</span>
                <span class="date">{display_date}</span>
            </div>
            <a href="{article_file}" class="card-link">
                <h3>{display_title}</h3>
            </a>
            <p style="font-size:0.9em; color:#64748b;">Status: <strong>✅ Solution Available</strong></p>
            <a href="{article_file}" class="read-btn">View Fix →</a>
        </div>
        """

    full_page = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tech Fix Daily - Database</title>
        <style>
            :root {{ --primary: #2563eb; --bg: #f8fafc; --card-bg: #ffffff; --text: #1e293b; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 0; }}
            .hero {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 60px 20px; text-align: center; }}
            .hero h1 {{ margin: 0; font-size: 2.5rem; }}
            .hero p {{ opacity: 0.8; margin-top: 10px; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }}
            .article-card {{ background: var(--card-bg); border-radius: 12px; padding: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; display: flex; flex-direction: column; }}
            .article-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-color: var(--primary); transition: 0.2s; }}
            .card-header {{ display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 0.8em; }}
            .badge {{ background: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
            h3 {{ margin: 0 0 15px 0; font-size: 1.1rem; line-height: 1.4; color: #0f172a; flex-grow: 1; }}
            .card-link {{ text-decoration: none; color: inherit; }}
            .read-btn {{ display: inline-block; margin-top: auto; text-decoration: none; background: var(--primary); color: white; padding: 10px 20px; border-radius: 6px; text-align: center; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>Tech Fix Daily</h1>
            <p>Automated Troubleshooting Database</p>
        </div>
        <div class="container">
            <div class="grid">{cards_html}</div>
        </div>
    </body>
    </html>
    """
    
    with open(index_path, "w") as f: f.write(full_page)

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

# --- MAIN EXECUTION ---
def main():
    print("💀 Zombie Bot Rising...")
    
    # 1. Fetch & Shuffle Topics
    trends = get_trending_topics()
    random.shuffle(trends)
    
    selected_topic = None
    final_filename = None
    
    # 2. Find a Non-Duplicate Topic
    for raw_topic in trends:
        # Title Logic
        if len(raw_topic.split()) > 7: topic_title = f"Review: {raw_topic}"
        elif any(x in raw_topic.lower() for x in ['top', 'best', 'vs', 'list']): topic_title = f"Guide: {raw_topic} Explained"
        else: topic_title = f"How to Fix {raw_topic} Error"

        check_filename = clean_filename(topic_title)
        
        if os.path.exists(check_filename):
            print(f"⚠️ Duplicate exists: {check_filename}")
            continue
        else:
            selected_topic = topic_title
            final_filename = check_filename
            break
    
    if not selected_topic:
        print("❌ No fresh topics found. Exiting.")
        # Optional: Force a rebuild of homepage even if no new content
        update_homepage_rebuild()
        exit(0)

    print(f"🎯 Target Locked: {selected_topic}")
    
    # 3. Generate Content
    article_md = get_gemini_article(selected_topic)
    
    if article_md:
        article_html = markdown.markdown(article_md)
        
        # Social Image (Viral Tag)
        social_image = f"https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80" 

        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{selected_topic}</title>
            <meta property="og:title" content="{selected_topic}">
            <meta property="og:image" content="{social_image}">
            <meta property="og:type" content="article">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #333; line-height: 1.6; }}
                h1 {{ color: #0f172a; }}
                img {{ max-width: 100%; border-radius: 8px; margin: 20px 0; }}
                .ad-box {{ background: #f0fdf4; border: 2px solid #22c55e; padding: 20px; text-align: center; margin: 30px 0; border-radius: 8px; }}
                .btn {{ background: #dc2626; color: white; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 5px; display: inline-block; margin-top: 10px; }}
                .btn:hover {{ background: #b91c1c; }}
            </style>
        </head>
        <body>
            <a href="index.html" style="text-decoration:none; color:#666;">← Back to Home</a>
            <h1>{selected_topic}</h1>
            
            <div class="ad-box">
                <h3>⚠️ Action Required</h3>
                <p>System scan recommended for this issue.</p>
                <a href="{AD_LINK}" class="btn">▶ RUN DIAGNOSTIC SCAN</a>
            </div>

            {article_html}

            <div class="ad-box">
                <h3>⬇️ Download Fix</h3>
                <p>Get the necessary drivers/patch.</p>
                <a href="{AD_LINK}" class="btn">DOWNLOAD NOW</a>
            </div>
            <hr>
            <p><small>Updated: {datetime.now().strftime("%Y-%m-%d")}</small></p>
        </body>
        </html>
        """
        
        with open(final_filename, "w") as f: f.write(full_html)
        
        # 4. Rebuild Homepage & Update Sitemap
        update_homepage_rebuild()
        update_sitemap(final_filename)
        
        # 5. Mirror
        original_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/{final_filename}"
        post_to_devto(selected_topic, article_md, original_url)
        
        print(f"✅ Published: {final_filename}")

if __name__ == "__main__":
    main()
