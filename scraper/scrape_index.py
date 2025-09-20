# scrape_index.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

URL = "https://www.aromaweb.com/essential-oils/"

# Output file
OUTPUT_FILE = "all_oils_to_scrape.json"

# Setup Chrome
options = webdriver.ChromeOptions()
# Uncomment below to see browser
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--log-level=3")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get(URL)
wait = WebDriverWait(driver, 15)

oil_links = []

# Try multiple selectors as fallback
selectors = [
    "ul.primarycontentlinksul li a",
    "ul li a[href*='essential-oils']"  # fallback: any <a> in <ul> linking to essential oils
]

for sel in selectors:
    try:
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, sel)))
        for el in elements:
            href = el.get_attribute("href")
            name = el.text.strip()
            if href and name:
                oil_links.append({
                    "oil_name": name,
                    "url": href
                })
        if oil_links:
            break  # stop if we found links
    except TimeoutException:
        continue  # try next selector

driver.quit()

# Assign IDs
for idx, oil in enumerate(oil_links, start=1):
    oil["oil_id"] = idx

# Save
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(oil_links, f, indent=2, ensure_ascii=False)

print(f"Scraped {len(oil_links)} oils.")
for oil in oil_links:
    print(f"{oil['oil_id']}: {oil['oil_name']} -> {oil['url']}")
