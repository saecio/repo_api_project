# ============================================================
# STEP 5 — RE-SCRAPE /land/ ROWS
#
# /land/ URLs are Adzuna redirect links that trigger bot detection
# and return a garbage "Access Denied" page. The fix is to extract
# the job ID from the /land/ URL and reconstruct the /details/ URL,
# which is Adzuna-hosted and scrapes cleanly.
#
#   adzuna.it/land/ad/123?se=... → adzuna.it/details/123
#
# Output is saved to a new file — the original is never touched.
# ============================================================

import os
import re
import time
import shutil
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from adzuna_config import FINAL_OUTPUT_PATH, LAND_RESCRAPE_OUTPUT_PATH

# ------------------------------------------------------------
# SETUP — load data and start Firefox
# ------------------------------------------------------------
df = pd.read_excel(FINAL_OUTPUT_PATH)
print(f"✓ Loaded {len(df)} rows from {FINAL_OUTPUT_PATH}")

# Fix Homebrew PATH on Mac/Anaconda so geckodriver is found
if "/opt/homebrew/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

geckodriver_path = shutil.which("geckodriver") or GeckoDriverManager().install()

firefox_options = Options()
firefox_options.add_argument("--headless")
firefox_options.add_argument("--width=1920")
firefox_options.add_argument("--height=1080")

driver = webdriver.Firefox(service=Service(geckodriver_path), options=firefox_options)
print("✓ Firefox started\n")

# ------------------------------------------------------------
# SCRAPING LOOP
# ------------------------------------------------------------
total_land = df["redirect_url"].str.contains("/land/", na=False).sum()
done       = 0  # counts only /land/ rows processed

for i, row in df.iterrows():

    # Skip any row that is not a /land/ URL — nothing to fix there
    if "/land/" not in str(row["redirect_url"]):
        continue

    # Reconstruct the /details/ URL from the /land/ URL.
    # Both share the same domain and job ID, just different paths.
    #   https://www.adzuna.it/land/ad/5762128871?se=...
    #   → https://www.adzuna.it/details/5762128871
    m = re.match(r"(https://www\.adzuna\.[\w.]+?)(?:/jobs)?/land/ad/(\d+)", row["redirect_url"])
    if not m:
        print(f"  ⚠ Could not parse: {row['redirect_url']}")
        continue

    details_url = f"{m.group(1)}/details/{m.group(2)}"

    try:
        driver.get(details_url)
        time.sleep(2.5)  # wait for JS to render

        soup    = BeautifulSoup(driver.page_source, "html.parser")
        section = soup.find("section", class_=lambda c: c and "adp-body" in c)

        if section:
            # adp-body is the canonical Adzuna description container
            df.at[i, "description"] = section.get_text(separator="\n", strip=True)
        else:
            # Fallback: strip boilerplate tags and grab whatever text remains
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            df.at[i, "description"] = soup.get_text(separator=" ", strip=True)

    except Exception as e:
        print(f"  ✗ {details_url[:80]} — {e}")

    done += 1
    if done % 100 == 0:
        print(f"\n  💾 Progress: {done}/{total_land} /land/ rows scraped\n")

# ------------------------------------------------------------
# SAVE & CLEANUP
# ------------------------------------------------------------
driver.quit()

df.to_excel(LAND_RESCRAPE_OUTPUT_PATH, index=False)
print(f"\n✓ Saved to {LAND_RESCRAPE_OUTPUT_PATH}  (original unchanged)")