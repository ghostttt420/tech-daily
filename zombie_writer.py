import random
import os
import json
import time
import markdown
import requests
from curl_cffi import requests as crequests
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
REPO_NAME = "tech-daily"
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY_OWNER')
AD_LINK = "https://www.effectivegatecpm.com/r7dzfzj7k3?key=149604651f31a5a4ab1b1cd51effc10b"

# POP-UNDER AD SCRIPT
EXTRA_AD_SCRIPT = """
<script src="https://pl28512527.effectivegatecpm.com/1a/33/5b/1a335b7b5ff20ae1334e705bc03993aa.js"></script>
<meta name="google-site-verification" content="SEDgnZk0oQshc0PmWrzbpSiA04cVzbF2kwS07JEYZVI"/>
"""

# --- 1. CLEAN CONTENT FETCHER ---
def get_trending_topics():
    print("🕵️ Hunting for Tech Topics...")
    
    # Try Google Internal API
    try:
        url = "https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=0&geo=US&ns=15"
        r = crequests.get(url, impersonate="chrome110", timeout=15)
        if r.status_code == 200:
            data = json.loads(r.text.replace(")]}',\n", ""))
            trends = []
            for day in data.get('default', {}).get('trendingSearchesDays', []):
                for search in day.get('trendingSearches', []):
                    query = search.get('title', {}).get('query')
                    if query: trends.append(query)
            if trends: return trends
    except: pass

    # Backup Sources
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

# --- 2. AI WRITER ---
def get_gemini_article(title):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return None
    
    # Dynamic Model Selection
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        models = requests.get(url).json().get('models', [])
        model = next((m['name'] for m in models if 'flash' in m['name']), 'models/gemini-pro')
    except: model = 'models/gemini-pro'

    prompt = f"""
    Write a clear, helpful troubleshooting guide for: "{title}".
    - Ignore news/shopping. Focus on "How to Fix" or "How to Use".
    - Use Markdown.
    - Structure: H1 Title, Introduction, 3 Common Causes, Step-by-Step Fix, Conclusion.
    - Tone: Direct and professional.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}"
    payload = { "contents": [{"parts": [{"text": prompt}]}] }
    
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return None

# --- 3. SITE UPDATERS (HOMEPAGE + SITEMAP) ---
def update_homepage():
    index_path = "index.html"
    files = [f for f in os.listdir('.') if f.endswith('.html') and f not in ['index.html', '404.html']]
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    list_items = ""
    for f in files:
        clean_title = f.replace("-", " ").replace(".html", "").title()
        clean_title = clean_title.replace("Guide ", "Guide: ").replace("Solved ", "Solved: ")
        date_str = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%b %d, %Y")
        
        list_items += f"""
        <div class="post-item">
            <span class="post-date">{date_str}</span>
            <a href="{f}" class="post-link">{clean_title}</a>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tech Fix Database</title>
        {EXTRA_AD_SCRIPT}
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; max-width: 680px; margin: 40px auto; padding: 20px; color: #333; line-height: 1.6; }}
            header {{ margin-bottom: 50px; border-bottom: 2px solid #000; padding-bottom: 20px; }}
            h1 {{ margin: 0; font-size: 1.5rem; letter-spacing: -0.5px; }}
            .subtitle {{ color: #666; font-size: 0.9rem; margin-top: 5px; }}
            .post-item {{ padding: 15px 0; border-bottom: 1px solid #eee; display: flex; align-items: baseline; }}
            .post-date {{ font-size: 0.85rem; color: #888; width: 100px; flex-shrink: 0; font-family: monospace; }}
            .post-link {{ font-size: 1.1rem; text-decoration: none; color: #000; font-weight: 500; }}
            .post-link:hover {{ text-decoration: underline; color: #0056b3; }}
            footer {{ margin-top: 50px; font-size: 0.8rem; color: #999; text-align: center; }}
        </style>
    </head>
    <body>
        <header>
            <h1>Tech Fix Database</h1>
            <div class="subtitle">Automated Repository of Software Solutions</div>
        </header>
        <main>{list_items}</main>
        <footer>Updated Daily • <a href="{AD_LINK}" style="color:#666">System Tools</a></footer>
    </body>
    </html>
    """
    with open(index_path, "w") as f: f.write(html)

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

# --- MAIN LOOP ---
def main():
    print("💀 Zombie Bot Rising...")
    trends = get_trending_topics()
    random.shuffle(trends)
    
    ignore = ["deal", "sale", "off", "coupon", "mattress", "pillow", "fashion", "recipe", "movie", "review for"]
    selected_topic = None
    final_filename = None
    
    for raw in trends:
        clean = raw.strip()
        if any(bad in clean.lower() for bad in ignore): continue
        
        if "?" in clean or "why" in clean.lower(): title = f"Solved: {clean}"
        elif len(clean.split()) < 4: title = f"How to Fix {clean} Error"
        else: title = f"Guide: {clean}"
        
        fname = title.lower().replace(":", "").replace("?", "").replace("/", "").replace("'", "")
        fname = fname.replace(" ", "-")[:70] + ".html"
        
        if not os.path.exists(fname):
            selected_topic = title
            final_filename = fname
            break
            
    if not selected_topic:
        print("❌ No valid topics. Rebuilding index.")
        update_homepage()
        exit(0)

    print(f"🎯 Writing: {selected_topic}")
    
    content = get_gemini_article(selected_topic)
    if content:
        html_content = markdown.markdown(content)
        
        full_page = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{selected_topic}</title>
            {EXTRA_AD_SCRIPT}
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #333; line-height: 1.6; }}
                a {{ color: #0056b3; }}
                h1 {{ margin-bottom: 10px; }}
                .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 30px; }}
                .ad-box {{ background: #f8f9fa; border: 1px solid #ddd; padding: 15px; text-align: center; margin: 30px 0; border-radius: 4px; }}
                .btn {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; }}
                pre {{ background: #f4f4f4; padding: 10px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <a href="index.html">← Back to Index</a>
            <h1>{selected_topic}</h1>
            <div class="meta">Posted on {datetime.now().strftime("%b %d, %Y")}</div>
            <div class="ad-box">
                <strong>Recommended:</strong> Run a system scan to identify the root cause.<br><br>
                <a href="{AD_LINK}" class="btn">Start Diagnostic Scan</a>
            </div>
            {html_content}
            <div class="ad-box"><a href="{AD_LINK}" class="btn">Download Repair Tool</a></div>
        </body>
        </html>
        """
        
        with open(final_filename, "w") as f: f.write(full_page)
        
        # UPDATE BOTH HOMEPAGE AND SITEMAP
        update_homepage()
        update_sitemap(final_filename)
        print(f"✅ Published: {final_filename}")

if __name__ == "__main__":
    main()
