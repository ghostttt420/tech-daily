import requests
import random
import os
import json
import time
from datetime import datetime

# CONFIG: Niche Seeds
SEEDS = [
    "how to fix android",
    "roblox error code",
    "call of duty mobile lag",
    "whatsapp not sending",
    "best graphics settings for",
    "iphone battery draining fast",
    "roblox error code 277 fix android",
    "call of duty mobile lag fix low end device",
    "how to fix black screen on samsung a12",
    "instagram music not working nigeria region",
    "free fire sensitivity settings for headshot 2026"
]

# YOUR DIRECT LINK (The Money Trap)
AD_LINK = "https://www.effectivegatecpm.com/r7dzfzj7k3?key=149604651f31a5a4ab1b1cd51effc10b"

def get_dynamic_model(api_key):
    """
    Asks Google: 'What models can I use?' and picks the best one.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        r = requests.get(url)
        data = r.json()
        
        valid_models = []
        if 'models' in data:
            for m in data['models']:
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    valid_models.append(m['name'])
        
        if not valid_models:
            print(f"❌ No valid models found. Response: {data}")
            return None
            
        # Prefer 'flash' models (fast/free), then 'pro'
        chosen_model = next((m for m in valid_models if 'flash' in m), None)
        if not chosen_model:
            chosen_model = next((m for m in valid_models if 'pro' in m), valid_models[0])
            
        print(f"🧠 System selected model: {chosen_model}")
        return chosen_model

    except Exception as e:
        print(f"❌ Failed to list models: {e}")
        return None

def get_gemini_article(title):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ CRITICAL: No API Key found in Secrets!")
        return None

    model_name = get_dynamic_model(api_key)
    if not model_name:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    
    prompt = f"""
    Write a technical blog post titled '{title}'. 
    Format it in valid HTML (use <h2>, <p>, <ul>). 
    Do not use <html> or <body> tags. 
    Keep it under 600 words. 
    Tone: Helpful, technical, and clear.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        r = requests.post(url, json=payload, headers=headers)
        data = r.json()
        
        if "error" in data:
            print(f"⚠️ API Error: {data['error']['message']}")
            return None
        
        if "candidates" not in data:
            print(f"⚠️ Unexpected Response: {data}")
            return None
            
        return data['candidates'][0]['content']['parts'][0]['text']

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def update_homepage(filename, title):
    if not os.path.exists("index.html"):
        with open("index.html", "w") as f:
            f.write("<html><head><title>Tech Fix Daily</title></head><body><h1>Daily Tech Fixes</h1><ul></ul></body></html>")
            
    with open("index.html", "r") as f:
        content = f.read()
        
    new_link = f'<li><a href="{filename}">{title}</a> ({datetime.now().strftime("%Y-%m-%d")})</li>'
    
    if "<ul>" in content:
        content = content.replace("<ul>", f"<ul>\n{new_link}")
    else:
        content = content.replace("<body>", f"<body><ul>{new_link}</ul>")
        
    with open("index.html", "w") as f:
        f.write(content)

def main():
    topic_base = random.choice(SEEDS)
    suffixes = ["2026", "easy fix", "tutorial", "solved", "guide"]
    title = f"{topic_base} {random.choice(suffixes)}".title()
    
    print(f"💀 Generating Zombie Content for: {title}")
    
    article_body = get_gemini_article(title)
    
    if article_body:
        article_body = article_body.replace("```html", "").replace("```", "")
        
        filename = title.lower().replace(" ", "-") + ".html"
        
        # HTML TEMPLATE WITH THE TRAP BUTTON
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }}
                h1 {{ color: #2c3e50; }}
                .ad-space {{ 
                    background: #f8f9fa; 
                    padding: 25px; 
                    text-align: center; 
                    margin: 30px 0; 
                    border: 2px solid #e9ecef; 
                    border-radius: 8px;
                }}
                .action-btn {{
                    background-color: #e74c3c;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 5px;
                    display: inline-block;
                    margin-top: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
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
        print(f"🧟 Successfully birthed: {filename}")
    else:
        print("❌ Failed to generate content.")
        exit(1)

if __name__ == "__main__":
    main()
