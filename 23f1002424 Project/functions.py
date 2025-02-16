import re
import time
from fuzzywuzzy import fuzz
from datetime import datetime
import requests
from dotenv import load_dotenv
import os
import logging

# Configure logging to show in terminal
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

logger.info("Loading .env file...")
load_dotenv()

# Debug environment variables
logger.debug("Environment variables: %s", dict(os.environ))

AIPROXY_TOKEN = os.getenv('AIPROXY_TOKEN')
if not AIPROXY_TOKEN:
    logger.error("AIPROXY_TOKEN not found in environment variables")
    raise ValueError("AIPROXY_TOKEN is required")
else:
    logger.debug("AIPROXY_TOKEN loaded successfully (first 10 chars): %s", AIPROXY_TOKEN[:10])


def get_task_output(task):
    max_retries = 3
    retry_delay = 2  # seconds
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    logger.debug("Using AIPROXY_TOKEN (first 10 chars): %s", token[:10])
    token = os.getenv('AIPROXY_TOKEN')
    if not token:
        logger.error("AIPROXY_TOKEN not found in environment variables")
        return "Error: Missing API token"
    
    # Configure timeout settings
    timeout_config = httpx.Timeout(10.0, connect=30.0)
    logger.debug("Setting API timeout: %s", timeout_config)
        
    logger.debug("Using token (first 10 chars): %s...", token[:10])
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    logger.debug("Request headers: %s", headers)
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": task}]
    }
    
    for attempt in range(max_retries):
        try:
            logger.debug("Attempt %d/%d: Making API request to %s", attempt + 1, max_retries, url)
            with httpx.Client(timeout=timeout_config) as client:
                response = client.post(url, headers=headers, json=data)
            logger.debug("API response status: %s", response.status_code)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            if "quota" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return f"Error processing task: {str(e)}"

def count_days(dayname: str):
    days = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }
    dayvalue = -1
    day = None
    
    for d in days:
        if d in dayname.lower():
            dayvalue = days[d]
            day = d
            break
    
    try:
        with open("data/dates.txt", "r") as file:
            data = file.readlines()
            count = sum([1 for line in data if datetime.strptime(line.strip(), "%Y-%m-%d").weekday() == dayvalue])
            with open(f"data/{day}-count", "w") as f:
                f.write(str(count))
    except Exception as e:
        return f"Error counting days: {str(e)}"

def extract_dayname(task: str):
    match = re.search(r'count\s+(\w+)', task)
    if match:
        return match.group(1)
    return ""

def extract_package(task: str):
    match = re.search(r'install\s+(\w+)', task)
    if match:
        return match.group(1)
    return ""

def get_correct_pkgname(pkgname: str):
    with open("packages.txt", "r", encoding="utf-8") as file:
        data = file.read().strip()
        packages = [line.strip() for line in data.split(" ")]
        corrects = []
        for pkg in packages:
            if fuzz.ratio(pkgname, pkg) >= 90:
                corrects.append(pkg)
        if corrects:
            return corrects[-1]
        return ""
