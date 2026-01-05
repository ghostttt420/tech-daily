import requests
import random
import os
import json
import time
from datetime import datetime

# --- CONFIGURATION ---
REPO_NAME = "tech-daily"  # MAKE SURE THIS MATCHES YOUR REPO NAME
GITHUB_USERNAME = os.environ.get('GITHUB_REPOSITORY_OWNER')
# YOUR DIRECT LINK (The Money Trap)
AD_LINK = "https://www.effectivegatecpm.com/r7dzfzj7k3?key=149604651f31a5a4ab1b1cd51effc10b"

# INITIAL SEEDS
STARTER_SEEDS = [
    "how to fix android",
    "roblox error code",
    "call of duty mobile lag",
    "whatsapp not sending",
    "iphone battery draining fast",
    "free fire sensitivity settings",
    "tiktok not working nigeria",
    "windows 11 blue screen fix"
]

def load_seeds():
    if os.path.exists("seeds.txt"):
        with open("seeds.txt", "r") as f:
            seeds = [line.strip() for line in f if line.strip()]
        if seeds: return seeds
    return STARTER_SEEDS

def save_new_seeds(new_seeds):
    existing = set()
    if os.path.exists("seeds.txt"):
        with open("seeds.txt", "r") as f:
            existing = set(line.strip() for line in f if line.strip())
    for s in new_seeds: existing.add(s)
    with open("seeds.txt", "w") as f:
        for s in existing: f.write(s + "\n")

def get_google_suggestions(seed):
    url = "http://google.com/complete/search"
    params = {"client": "chrome", "q": seed}
    try:
        r = requests.get(url, params=params, timeout=5)
        return json.loads(r.text)[1]
    except: return []

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
    if not model_name: return None

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    # We ask for Markdown for Dev.to compatibility
    prompt = f"Write a technical blog post titled '{title}'. Use Markdown formatting (##, -). Do not use HTML tags like <html>. Keep it under 600 words. Tone: Helpful, technical."
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return None

def update_homepage(filename, title):
    if not os.path.exists("index.html"):
        with open("index.html", "w") as f:
            f.write("<html><head><title>Tech Fix Daily</title></head><body><h1>Daily Tech Fixes</h1><ul></ul></body></html>")
    with open("index.html", "r") as f: content = f.read()
    new_link = f'<li><a href="{filename}">{title}</a> ({datetime.now().strftime("%Y-%m-%d")})</li>'
    if "<ul>" in content: content = content.replace("<ul>", f"<ul>\n{new_link}")
    else: content = content.replace("<body>", f"<body><ul>{new_link}</ul>")
    with open("index.html", "w") as f: f.write(content)

def update_sitemap(filename):
    sitemap_path = "sitemap.xml"
    base_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
    today = datetime.now().strftime("%Y-%m-%d")
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    footer = '</urlset>'
    new_entry = f"  <url>\n    <loc>{base_url}{filename}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>daily</changefreq>\n  </url>\n"
    if not os.path.exists(sitemap_path): content = header + new_entry + footer
    else:
        with open(sitemap_path, "r") as f: content = f.read()
        if footer in content: content = content.replace(footer, new_entry + footer)
        else: content = header + new_entry + footer
    with open(sitemap_path, "w") as f: f.write(content)

def post_to_devto(title, content, original_url):
    """Teleports the article to Dev.to"""
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key:
        print("⚠️ No Dev.to Key found. Skipping mirror.")
        return

    # Add the Trap Link to the Dev.to version too!
    trap_content = f"{content}\n\n## 🚀 Need a Quick Fix?\n\n[**▶ SCAN DEVICE / DOWNLOAD TOOL**]({AD_LINK})"
    
    url = "https://dev.to/api/articles"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "article": {
            "title": title,
            "published": True,
            "body_markdown": trap_content,
            "tags": ["android", "tutorial", "beginners", "productivity"],
            "canonical_url": original_url
        }
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code == 201:
            print("🪞 Successfully mirrored to Dev.to!")
        else:
            print(f"❌ Dev.to Error: {r.text}")
    except Exception as e:
        print(f"❌ Dev.to Connection Failed: {e}")

def main():
    seeds = load_seeds()
    current_seed = random.choice(seeds)
    print(f"💀 Hunting based on seed: {current_seed}")
    
    suggestions = get_google_suggestions(current_seed)
    if suggestions:
        save_new_seeds(suggestions)
        long_suggestions = [s for s in suggestions if len(s.split()) > 3]
        topic = random.choice(long_suggestions) if long_suggestions else current_seed
    else: topic = current_seed

    title = topic.title()
    print(f"🧟 Resurrecting article for: {title}")
    
    # Get Content (Markdown format now)
    article_md = get_gemini_article(title)
    
    if article_md:
        # Convert Markdown to HTML for the Zombie Site
        # (Simple conversion for basic structure)
        article_html = article_md.replace("##", "<h2>").replace("\n", "<br>")
        
        filename = title.lower().replace(" ", "-").replace("?", "").replace("/", "")[:50] + ".html"
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }}
                h1 {{ color: #2c3e50; }}
                .ad-space {{ background: #f8f9fa; padding: 25px; text-align: center; margin: 30px 0; border: 2px solid #e9ecef; border-radius: 8px; }}
                .action-btn {{ background-color: #e74c3c; color: white; padding: 15px 30px; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 5px; display: inline-block; margin-top: 10px; }}
                .action-btn:hover {{ background-color: #c0392b; }}
            </style>
        </head>
        <body>
            <a href="index.html" style="text-decoration:none;">← Back to Home</a>
            <h1>{title}</h1>
            <div class="ad-space">
                <h3>⚠️ System Performance Check</h3>
                <p>Ensure your device settings are optimized for this fix.</p>
                <a href="{AD_LINK}" class="action-btn" target="_blank">▶ SCAN DEVICE NOW</a>
            </div>
            {article_html}
            <div class="ad-space">
                <h3>🚀 Recommended Tool</h3>
                <p>Fix lag and battery drain automatically.</p>
                <a href="{AD_LINK}" class="action-btn" target="_blank">▶ DOWNLOAD FIX</a>
            </div>
            <hr>
            <p><small>Generated by The Zombie System</small></p>
        </body>
        </html>
        """
        
        with open(filename, "w") as f: f.write(full_html)
        update_homepage(filename, title)
        update_sitemap(filename)
        
        # --- MIRROR STEP ---
        original_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/{filename}"
        post_to_devto(title, article_md, original_url)
        # -------------------
        
        print(f"✅ Published: {filename}")
    else:
        print("❌ Failed to generate content.")
        exit(1)

if __name__ == "__main__":
    main()
