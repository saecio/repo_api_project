# ============================================================
# STEP 2 — EXTRACT
# Pull job listings from the Adzuna API for all configured
# European countries, page by page, and save raw results to CSV.
#
# The debug comments show exactly where execution stops when 
# the script is running.
# ============================================================

import sys
print("DEBUG: script started", flush=True)  # Confirms the script itself launched correctly

import os
print("DEBUG: os imported", flush=True)      # Used for env vars and path creation

import time
print("DEBUG: time imported", flush=True)    # Used to add a small delay between API requests

import requests
print("DEBUG: requests imported", flush=True)  # HTTP library for calling the Adzuna REST API

import pandas as pd
print("DEBUG: pandas imported", flush=True)  # Used to build and save the final DataFrame

from dotenv import load_dotenv
print("DEBUG: dotenv imported", flush=True)  # Loads API credentials from the .env file

# Import all pipeline constants from the shared config file:
# - EUROPEAN_COUNTRIES: list of country codes (e.g. "nl", "de", "es")
# - SEARCH_QUERY: the job title / keyword to search (e.g. "data analyst")
# - RESULTS_PER_PAGE: how many jobs to request per API call
# - RAW_OUTPUT_PATH: file path where the raw CSV will be saved
print("DEBUG: importing adzuna_config...", flush=True)
from adzuna_config import (
    EUROPEAN_COUNTRIES,
    SEARCH_QUERY,
    RESULTS_PER_PAGE,
    RAW_OUTPUT_PATH,
)
print("DEBUG: adzuna_config imported", flush=True)

# Load API credentials from the .env file into the process environment
print("DEBUG: calling load_dotenv()", flush=True)
load_dotenv()
print("DEBUG: load_dotenv finished", flush=True)

# Read app_id and app_key from environment variables — never hardcode these
app_id = os.getenv("app_id")
app_key = os.getenv("app_key")

# Confirm whether the keys were found before making any requ
