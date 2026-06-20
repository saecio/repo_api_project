# ============================================================
# STEP 2 — SCRAPE
# Loads the raw jobs CSV, visits each job URL with a headless
# Firefox browser, extracts the full job description, saves
# checkpoints during the run, and skips already-scraped jobs
# when restarted.
# ============================================================

import os
import time
import shutil
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from adzuna_config import RAW_OUTPUT_PATH, SCRAPED_OUTPUT_PATH

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
raw_df = pd.read_csv(RAW_OUTPUT_PATH)
print(f"✓ Loaded {len(raw_df)} jobs from {RAW_OUTPUT_PATH}")

# Protect an existing full scrape from being overwritten by a tiny input file.
# This catches cases where data/raw_jobs.csv accidentally contains only a sample.
if os.path.exists(SCRAPED_OUTPUT_PATH):
    existing_rows = len(pd.read_csv(SCRAPED_OUTPUT_PATH))
    if existing_rows > len(raw_df) and len(raw_df) < 1000:
        raise SystemExit(
            f"Stopped: {RAW_OUTPUT_PATH} has only {len(raw_df)} rows, but "
            f"{SCRAPED_OUTPUT_PATH} already has {existing_rows}. Restore the "
            "full raw input before running the scraper."
        )

# Make sure the description column exists so resume logic works
if "description" not in raw_df.columns:
    raw_df["description"] = pd.NA

# ------------------------------------------------------------
# CLEAR SHORT/TRUNCATED DESCRIPTIONS FOR RE-SCRAPE
# ------------------------------------------------------------
# Jobs with descriptions under 500 chars are likely truncated.
# Clear them so the loop re-scrapes them properly.
# Jobs with long descriptions are kept as-is to save time.
short_mask = raw_df["description"].str.len() < 500
raw_df.loc[short_mask, "description"] = pd.NA
print(f"✓ Flagged {short_mask.sum()} short/truncated jobs for re-scraping")
print(f"✓ Keeping {(~short_mask).sum()} already well-scraped jobs")

# ------------------------------------------------------------
# GECKODRIVER SETUP
# ------------------------------------------------------------
# Add Homebrew to PATH if missing (fixes Anaconda/Jupyter PATH issue on Mac)
if "/opt/homebrew/bin" not in os.environ["PATH"]:
    os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ["PATH"]

# Find geckodriver in PATH, or download it automatically via webdriver-manager
geckodriver_path = shutil.which("geckodriver") or GeckoDriverManager().install()
print(f"✓ geckodriver found at: {geckodriver_path}")

# ------------------------------------------------------------
# FIREFOX OPTIONS
# ------------------------------------------------------------
firefox_options = Options()
firefox_options.add_argument("--headless")    # run without opening a browser window
firefox_options.add_argument("--width=1920")  # realistic screen width
firefox_options.add_argument("--height=1080") # realistic screen height

driver = webdriver.Firefox(
    service=Service(geckodriver_path),
    options=firefox_options
)

# ------------------------------------------------------------
# SCRAPING LOOP
# ------------------------------------------------------------
total         = len(raw_df)
scraped_count = 0  # counts jobs actually processed in this run (not skipped)

print(f"\nScraping full descriptions from {total} job pages...")

for i, row in raw_df.iterrows():

    # Skip jobs that already have a good description from a previous run
    # This lets the script resume without re-scraping everything
    if pd.notna(raw_df.at[i, "description"]) and len(str(raw_df.at[i, "description"])) > 500:
        continue

    try:
        # Open the job page in the headless browser
        driver.get(row["redirect_url"])
        time.sleep(2)  # wait 3 seconds for JS to fully render the page

        # Parse the fully rendered HTML with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")

        if "/land/" in row["redirect_url"]:
            # --- STRATEGY: LAND URLs (redirect links) ---
            # Strip all noise and grab whatever text remains
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            full_desc = soup.get_text(separator=" ", strip=True)

        else:
            # --- STRATEGY: DETAILS URLs (Adzuna-hosted pages) ---
            # Description always lives in <section class="adp-body ...">.
            section = soup.find("section", class_=lambda c: c and "adp-body" in c)

            if section:
                # adp-body found — extract clean text
                full_desc = section.get_text(separator="\n", strip=True)
            else:
                # adp-body not found — fall back to full page text
                for tag in soup(["script", "style", "nav", "header", "footer"]):
                    tag.decompose()
                full_desc = soup.get_text(separator=" ", strip=True)

        # Store the extracted description back into the dataframe
        if full_desc:
            raw_df.at[i, "description"] = full_desc

    except Exception as e:
        pass  # silently continue on error, checkpoint will save progress

    # Increment the counter for every job actually processed in this run
    scraped_count += 1

    # Every 100 actually-processed jobs: print progress and save checkpoint
    if scraped_count % 100 == 0:
        scraped_total = raw_df["description"].notna().sum()
        pct           = round(scraped_total / total * 100, 1)
        print(f"  💾 [{scraped_total}/{total} — {pct}%] Checkpoint saved at job {i}")
        raw_df.to_csv(SCRAPED_OUTPUT_PATH, index=False)

# ------------------------------------------------------------
# CLEANUP
# ------------------------------------------------------------
driver.quit()  # close the browser and free up memory

# Final save at the end of the run
raw_df.to_csv(SCRAPED_OUTPUT_PATH, index=False)
print(f"\n✓ Scraping done — saved to {SCRAPED_OUTPUT_PATH}")

# Summary of description lengths to confirm meaningful content was extracted
print(raw_df["description"].str.len().describe())
