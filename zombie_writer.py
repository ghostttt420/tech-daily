import requests
import random
import os
import json
import time
from datetime import datetime

# --- CONFIGURATION ---
REPO_NAME = "tech-daily"  # Change this if your repo name is different
# YOUR DIRECT LINK (The Money Trap)
AD_LINK = "https://www.effectivegatecpm.com/r7dzfzj7k3?key=149604651f31a5a4ab1b1cd51effc10b"

# INITIAL SEEDS (Only used if the seed file is empty)
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
    """Loads seeds from a file. If file doesn't exist, uses STARTER_SEEDS."""
    if os.path.exists("seeds.txt"):
        with open("seeds.txt", "r") as f:
            seeds = [line.strip() for line in f if line.strip()]
        if seeds:
            return seeds
    return STARTER_SEEDS

def save_new_seeds(new_seeds):
    """Appends new discovered keywords to the infinite list."""
    existing = set()
    if os.path.exists("seeds.txt"):
        with open("seeds.txt", "r") as f:
            existing = set(line.strip() for line in f if line.strip())
    
    # Add new seeds to the set (avoids duplicates)
    for s in new_seeds:
        existing.add(s)
        
    with open("seeds.txt", "w") as f:
        for s in existing:
            f.write(s + "\n")

def get_google_suggestions(seed):
    """Asks Google: 'What are people searching for related to X?'"""
    url = "http://google.com/complete/search"
    params = {"client": "chrome", "q": seed}
    try:
        r = requests.get(url, params=params, timeout=5)
        # Returns ["keyword", ["suggestion 1", "suggestion 2", ...]]
        suggestions = json.loads(r.text)[1]
        return suggestions
    except:
        return []

def get_dynamic_model(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        r = requests.get(url)
        data = r.json()
        valid_models = [m['name'] for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        if not valid_models: return None
        # Prefer flash, then pro
        return next((m for m in valid_models if 'flash' in m), next((m for m in valid_models if 'pro' in m), valid_models[0]))
    except:
        return None

def get_gemini_article(title):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return None
    model_name = get_dynamic_model(api_key)
    if not model_name: return None

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    prompt = f"Write a technical blog post titled '{title}'. Format in valid HTML (<h2>, <p>, <ul>). No <html>/<body> tags. Under 600 words. Tone: Helpful, technical."
    
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
    except:
        return None

def update_homepage(filename, title):
    if not os.path.exists("index.html"):
        with open("index.html", "w") as f:
            f.write("<html><head><title>Tech Fix Daily</title></head><body><h1>Daily Tech Fixes</h1><ul></ul></body></html>")
    with open("index.html", "r") as f:
        content = f.read()
    new_link = f'<li><a href="{filename}">{title}</a> ({datetime.now().strftime("%Y-%m-%d")})</li>'
    if "<ul>" in content: content = content.replace("<ul>", f"<ul>\n{new_link}")
    else: content = content.replace("<body>", f"<body><ul>{new_link}</ul>")
    with open("index.html", "w") as f:
        f.write(content)

def main():
    # 1. Load the Hydra Heads (Seeds)
    seeds = load_seeds()
    current_seed = random.choice(seeds)
    print(f"💀 Hunting based on seed: {current_seed}")
    
    # 2. Get new suggestions from Google (The Hydra grows)
    suggestions = get_google_suggestions(current_seed)
    
    if suggestions:
        # Save these suggestions for future days
        save_new_seeds(suggestions)
        print(f"🐍 Hydra grew {len(suggestions)} new heads (saved to seeds.txt)")
        
        # Pick one suggestion to be today's article
        # We filter out very short ones to ensure quality
        long_suggestions = [s for s in suggestions if len(s.split()) > 3]
        if long_suggestions:
            topic = random.choice(long_suggestions)
        else:
            topic = current_seed
    else:
        topic = current_seed

    title = topic.title()
    print(f"🧟 Resurrecting article for: {title}")
    
    # 3. Write the Article
    article_body = get_gemini_article(title)
    
    if article_body:
        article_body = article_body.replace("```html", "").replace("```", "")
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
            {article_body}
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
        
        with open(filename, "w") as f:
            f.write(full_html)
            
        update_homepage(filename, title)
        print(f"✅ Published: {filename}")
    else:
        print("❌ Failed to generate content.")
        exit(1)

if __name__ == "__main__":
    main()
