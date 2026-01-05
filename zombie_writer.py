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
    ​"call of duty mobile lag fix low end device",
    ​"how to fix black screen on samsung a12",
    ​"instagram music not working nigeria region",
    ​"free fire sensitivity settings for headshot 2026"]

def get_dynamic_model(api_key):
    """
    Asks Google: 'What models can I use?' and picks the best one.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        r = requests.get(url)
        data = r.json()
        
        # Look for a model that supports 'generateContent'
        valid_models = []
        if 'models' in data:
            for m in data['models']:
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    valid_models.append(m['name'])
        
        if not valid_models:
            print(f"❌ No valid models found. Response: {data}")
            return None
            
        # Prefer 'flash' models (fast/free), then 'pro', then whatever is left
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

    # STEP 1: Find a valid model name dynamically
    model_name = get_dynamic_model(api_key)
    if not model_name:
        return None

    # STEP 2: Generate Content
    # Note: model_name already contains 'models/', e.g., 'models/gemini-1.5-flash'
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
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
                h1 {{ color: #333; }}
                .ad-space {{ background: #eee; padding: 20px; text-align: center; margin: 20px 0; border: 1px dashed #ccc; }}
            </style>
        </head>
        <body>
            <a href="index.html">← Back to Home</a>
            <h1>{title}</h1>
            <div class="ad-space"><p>Sponsored Advertisement</p></div>
            {article_body}
            <div class="ad-space"><p>Sponsored Advertisement</p></div>
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
