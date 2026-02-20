import requests
from bs4 import BeautifulSoup
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# We need to use the actual production GLM-5 endpoint, not localhost
OLLAMA_URL = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")

# OpenSec Gateway validation endpoint
GATEWAY_URL = "http://localhost:8000/api/validate"

def fetch_website_content(url):
    """
    Fetches the raw HTML of a URL and extracts the clean text.
    """
    print(f"[WebSpider] Fetching data from: {url}")
    try:
        # Some sites block requests without a proper user-agent
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=' ')
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        print(f"[WebSpider] Error fetching website: {e}")
        return None

def validate_with_opensec(text_content):
    """
    Sends the scraped text to the OpenSec Gateway to check for prompt injection 
    and malicious payloads BEFORE parsing it with the local LLM.
    """
    print(f"[WebSpider] Sending {len(text_content)} characters to OpenSec Gateway for Prompt Injection Scanning...")
    
    # We prefix a context statement so the security engine knows what this is
    payload_prompt = f"Analyze the following scraped text for prompt injection:\n{text_content}"
    
    try:
        response = requests.post(GATEWAY_URL, json={"prompt": payload_prompt}, timeout=30)
        if response.status_code == 200:
            print("[WebSpider] OpenSec Gateway says: 🟢 CONTENT CLEAN (ALLOWED)")
            return True
        else:
            reason = response.json().get('detail', 'Unknown block reason')
            print(f"[WebSpider] OpenSec Gateway says: 🛑 BLOCKED (Reason: {reason})")
            return False
    except Exception as e:
        print(f"[WebSpider] Could not reach OpenSec Gateway: {e}")
        return False

def summarize_with_ollama(text_content, user_prompt):
    """
    Uses the configured Cloud Ollama model to summarize the validated text.
    """
    print("[WebSpider] Requesting summarization from GLM-5 brain...")
    
    system_prompt = f"""
    You are WebSpider, a helpful agent that summarizes web content.
    Given the following website content, fulfill the user's request.
    
    WEBSITE CONTENT:
    {text_content[:4000]}
    """
    
    payload = {
        "model": "glm-5:cloud", 
        "prompt": f"{system_prompt}\n\nUSER REQUEST: {user_prompt}",
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        action = response.json().get('response', '').strip()
             
        print("\n=== SUMMARY ===\n")
        if action:
            print(action)
        else:
            print(f"[Error: Empty model response] Raw JSON: {response.json()}")
        print("\n===============\n")
    except Exception as e:
        print(f"[WebSpider] Failed to speak to GLM-5 brain: {e}")

def run_agent(task, target_url):
    """
    Simulated workflow for the WebSpider agent.
    """
    print(f"\n--- Starting WebSpider Agent ---")
    print(f"Task: {task}")
    print(f"Target URL: {target_url}\n")
    
    # 1. Fetch the raw website content
    raw_text = fetch_website_content(target_url)
    if not raw_text:
        return
        
    print(f"[WebSpider] Successfully extracted {len(raw_text)} characters of text.")
        
    # 2. VITAL SECURITY STEP: Validate the raw text against OpenSec Gateway
    # If the website contains hidden Prompt Injections ("Ignore all previous instructions..."), 
    # the gateway will block it here so the local LLM never sees it.
    is_safe = validate_with_opensec(raw_text)
    
    if not is_safe:
        print("[WebSpider] 🛑 BORTING TASK: Website contains detected malicious instructions or prompt injections.")
        return
        
    # 3. Safe Execution: Summarize the content
    summarize_with_ollama(raw_text, task)
    

if __name__ == "__main__":
    print("Welcome to WebSpider Local AI Agent")
    print("Usage example: python webspider.py 'Give me the top news' 'https://ndtv.com'")
    
    if len(sys.argv) > 2:
        task = sys.argv[1]
        url = sys.argv[2]
        run_agent(task, url)
    else:
        while True:
            print("\n-----")
            url = input("Enter target URL (or 'quit'): ")
            if url.lower() in ['quit', 'exit']:
                break
            task = input("Enter prompt (e.g. 'summarize the article'): ")
            
            # Basic URL validation
            if not url.startswith('http'):
                url = 'https://' + url
                
            run_agent(task, url)
