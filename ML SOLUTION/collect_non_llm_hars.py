import json
import os
import time
import re
from playwright.sync_api import sync_playwright

# settings
INPUT_JSON = "non_llm_sites.json"
OUTPUT_DIR = "har_data/non_llm_hars"
VISIT_TIMEOUT = 30000      # timeout after 30s of inactivity
WAIT_AFTER_LOAD = 5000     # record traffic for 5s after initial page load

# create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# sanitize URLs into safe filename by removing invalid characters
def sanitize_filename(url):
    domain = re.sub(r"https?://", "", url)
    domain = re.sub(r"[^\w.-]", "_", domain)
    return domain.strip("_")

# load all sites in list
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    sites = json.load(f)["non_llm_websites"]

print(f"Loaded {len(sites)} websites from {INPUT_JSON}\n")

# use playwright to visit pages and download HAR files
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()

	# loop through each site, set output path
    for i, url in enumerate(sites, start=1):
        filename = sanitize_filename(url) + ".har"
        har_path = os.path.join(OUTPUT_DIR, filename)

        # skip if HAR already collected
        if os.path.exists(har_path):
            print(f"[{i}/{len(sites)}] Skipping {url} (already exists)")
            continue

        print(f"[{i}/{len(sites)}] Visiting {url} → {filename}")

        try:
            # open browser in background 
            with p.chromium.launch(headless=True) as browser:
				
				# open new tab, visit site, download all HTTP traffic to HAR, and close tab
                context = browser.new_context(record_har_path=har_path)
                page = context.new_page()
                page.goto(url, timeout=VISIT_TIMEOUT)
                page.wait_for_timeout(WAIT_AFTER_LOAD)
                context.close()

            print(f"Saved: {har_path}")

		# throw exception if site cannot be reached
        except Exception as e:
            print(f"Error visiting {url}: {e}")
            
            # buffer between attempts
            time.sleep(2)
            continue

        # buffer between connections
        time.sleep(1)

    browser.close()

print("\nScript done. All files saved to: ", OUTPUT_DIR)
