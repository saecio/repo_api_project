# ============================================================
# STEP 3 — EXPORT
# Loads the scraped jobs CSV, selects the most useful columns,
# drops duplicate listings, and exports a clean Excel file.
# ============================================================

import os
import pandas as pd
from adzuna_config import SCRAPED_OUTPUT_PATH, FINAL_OUTPUT_PATH

# Load scraped data
df = pd.read_csv(SCRAPED_OUTPUT_PATH)
print(f"✓ Loaded {len(df)} jobs from {SCRAPED_OUTPUT_PATH}")

# Keep only the most relevant columns
# Adjust this list based on what the Adzuna API actually returned
columns_to_keep = [
    "id",
    "title",
    "company",
    "location",
    "country",
    "salary_min",
    "salary_max",
    "contract_type",
    "redirect_url",
    "description",
    "created",
]
# Only keep columns that actually exist in the dataframe (avoids KeyError)
df = df[[col for col in columns_to_keep if col in df.columns]]

# Drop exact duplicate job IDs (same job posted in multiple countries/pages)
before = len(df)
df = df.drop_duplicates(subset="id")
print(f"✓ Dropped {before - len(df)} duplicates — {len(df)} jobs remaining")

# Create data/ folder if it doesn't exist
os.makedirs("data", exist_ok=True)

# Export to Excel
df.to_excel(FINAL_OUTPUT_PATH, index=False)
print(f"✓ Export done — saved to {FINAL_OUTPUT_PATH}")