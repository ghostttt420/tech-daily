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
AD_LINK = "https://www.effectivegatecpm.com/r7dzfzj7k3?key=149604651f31a5a4ab1b1cd51effc10b"

# --- 1. RELIABLE TECH SOURCES (No Google Blocking) ---
def get_trending_topics():
    sources = [
        "https://www.theverge.com/rss/index.xml",       # General Tech
        "https://feeds.feedburner.com/TechCrunch/",     # Startups/Apps
        "https://www.wired.com/feed/rss",               # Deep Tech/Culture
        "https://feeds.arstechnica.com/arstechnica/index" # IT/Hardware
    ]
    
    # Simple User-Agent is enough for RSS feeds
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    all_trends = []
    
    for rss_url in sources:
        try:
            print(f"🔌 Checking Source: {rss_url}...")
            r = requests.get(rss_url, headers=headers, timeout=10)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                # RSS Parsing
                items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
                for item in items:
                    title = item.find('title')
                    if title is None: title = item.find('{http://www.w3.org/2005/Atom}title')
                    if title is not None and title.text:
                        all_trends.append(title.text)
        except Exception as e:
            print(f"⚠️ Skipped {rss_url}: {e}")
            continue

    if all_trends:
        print(f"✅ Success! Collected {len(all_trends)} potential topics.")
        return all_trends
    
    return []

# --- AI SETUP ---
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
    
    IMPORTANT INSTRUCTIONS:
    1. If the topic is news (e.g. "Apple released X"), write a guide on "How to use/update X".
    2. If the topic is an error, write "How to Fix".
    3. Use Markdown.
    4. Make it look like a helpful tutorial.
    
    Structure:
    - H1 Title
    - Intro (What is happening?)
    - Key Features / or / Common Causes
    - Step-by-Step Guide
    - Conclusion
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    payload = { "contents": [{"parts": [{"text": prompt}]}], "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}]}
    
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return None

# --- UTILS & HTML GENERATION ---
def clean_filename(topic):
    clean = topic.lower().replace(":", "").replace("’", "").replace("'", "").replace('"', "")
    return clean.replace(" ", "-").replace("?", "").replace("/", "")[:50] + ".html"

def update_homepage(filename, title):
    index_path = "index.html"
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 1. THE NEW CARD DESIGN (HTML Chunk)
    new_card = f"""
        <div class="article-card">
            <div class="card-header">
                <span class="badge">GUIDE</span>
                <span class="date">{date_str}</span>
            </div>
            <a href="{filename}" class="card-link">
                <h3>{title}</h3>
            </a>
            <p>Status: <strong>Solution Found</strong></p>
            <a href="{filename}" class="read-btn">View Fix →</a>
        </div>
    """
    
    # 2. THE FULL PAGE TEMPLATE (Used if creating a fresh index.html)
    header_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tech Fix Daily - Database</title>
        <style>
            :root {{ --primary: #2563eb; --bg: #f8fafc; --card-bg: #ffffff; --text: #1e293b; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 0; }}
            
            /* HERO SECTION */
            .hero {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: white; padding: 60px 20px; text-align: center; }}
            .hero h1 {{ margin: 0; font-size: 2.5rem; letter-spacing: -1px; }}
            .hero p {{ opacity: 0.8; margin-top: 10px; font-size: 1.1rem; }}
            .search-fake {{ background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); padding: 12px; border-radius: 8px; max-width: 500px; margin: 20px auto 0; text-align: left; color: #94a3b8; font-size: 0.9rem; }}
            
            /* GRID LAYOUT */
            .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }}
            
            /* ARTICLE CARD */
            .article-card {{ background: var(--card-bg); border-radius: 12px; padding: 25px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: transform 0.2s, box-shadow 0.2s; border: 1px solid #e2e8f0; display: flex; flex-direction: column; justify-content: space-between; }}
            .article-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border-color: var(--primary); }}
            
            .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; font-size: 0.8rem; }}
            .badge {{ background: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
            .date {{ color: #64748b; }}
            
            h3 {{ margin: 0 0 10px 0; font-size: 1.2rem; line-height: 1.4; color: #0f172a; flex-grow: 1; }}
            .card-link {{ text-decoration: none; color: inherit; }}
            
            .read-btn {{ display: inline-block; margin-top: 15px; text-decoration: none; background: var(--primary); color: white; padding: 10px 20px; border-radius: 6px; text-align: center; font-weight: 600; transition: background 0.2s; }}
            .read-btn:hover {{ background: #1d4ed8; }}
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>Tech Fix Daily</h1>
            <p>Automated Troubleshooting Database & Repair Guides</p>
            <div class="search-fake">🔍 Search for error codes, glitches, or bugs...</div>
        </div>
        
        <div class="container">
            <h2 style="margin-bottom: 20px; color: #334155;">Latest Solutions</h2>
            <div class="grid">
                {new_card}
            </div>
        </div>
    </body>
    </html>
    """

    # 3. WRITE TO FILE
    if not os.path.exists(index_path):
        # Create fresh if doesn't exist
        with open(index_path, "w") as f:
            f.write(header_html)
    else:
        with open(index_path, "r") as f: content = f.read()
        
        # Check if filename already exists to prevent duplicates
        if filename in content:
            return

        # Check if we are using the NEW design or the OLD design
        if "" in content:
            # We have the new design, inject cleanly
            content = content.replace("", f"\n{new_card}")
            with open(index_path, "w") as f: f.write(content)
        else:
            # We have the OLD ugly design. Overwrite it completely with the new header + new card.
            # (Note: This deletes old links from the homepage, but the pages still exist on Google. 
            # This is actually good to clean up your messy "Microsoft" duplicates).
            with open(index_path, "w") as f: f.write(header_html)


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
    
    # 1. Fetch Reliable Tech Trends
    trends = get_trending_topics()
    random.shuffle(trends)
    
    selected_topic = None
    final_filename = None
    
    for raw_topic in trends:
        # Title Logic
        if len(raw_topic.split()) > 7: topic_title = f"Review: {raw_topic}"
        elif any(x in raw_topic.lower() for x in ['top', 'best', 'vs', 'list']): topic_title = f"Guide: {raw_topic} Explained"
        else: topic_title = f"How to Fix {raw_topic} Error"

        check_filename = clean_filename(topic_title)
        
        # 2. Duplicate Check
        if os.path.exists(check_filename):
            print(f"⚠️ Duplicate: {check_filename}")
            continue
        else:
            selected_topic = topic_title
            final_filename = check_filename
            break
    
    if not selected_topic:
        print("❌ No fresh topics found. Exiting.")
        exit(0)

    print(f"🎯 Target Locked: {selected_topic}")
    
    article_md = get_gemini_article(selected_topic)
    
    if article_md:
        article_html = markdown.markdown(article_md)
        
        # --- NEW: VIRAL SOCIAL TAGS ---
        random_img_id = random.randint(1, 1000)
        # Random tech image for social preview
        social_image = f"https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80" 

        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{selected_topic}</title>
            
            <meta property="og:title" content="{selected_topic}">
            <meta property="og:description" content="Quick guide and solution. Read more...">
            <meta property="og:image" content="{social_image}">
            <meta property="og:type" content="article">
            <meta name="twitter:card" content="summary_large_image">

            <style>
                body {{ font-family: sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #333; line-height: 1.6; }}
                h1 {{ color: #2c3e50; }}
                img {{ max-width: 100%; border-radius: 8px; }}
                .ad-box {{ background: #f0fdf4; border: 2px solid #22c55e; padding: 20px; text-align: center; margin: 30px 0; border-radius: 8px; }}
                .btn {{ background: #dc2626; color: white; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 5px; display: inline-block; margin-top: 10px; }}
                .btn:hover {{ background: #b91c1c; }}
            </style>
        </head>
        <body>
            <a href="index.html">← Back to Home</a>
            
            <h1>{selected_topic}</h1>
            
            <div class="ad-box">
                <h3>⚠️ Action Required</h3>
                <p>We found potential issues related to this error.</p>
                <a href="{AD_LINK}" class="btn">▶ RUN DIAGNOSTIC SCAN</a>
            </div>

            {article_html}

            <div class="ad-box">
                <h3>⬇️ Download Fix</h3>
                <p>Get the necessary files to repair your system.</p>
                <a href="{AD_LINK}" class="btn">DOWNLOAD NOW</a>
            </div>
            
            <hr>
            <p><small>Updated: {datetime.now().strftime("%Y-%m-%d")}</small></p>
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
