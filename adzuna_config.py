# Shared configuration used across all scripts.
# Centralizing settings here means you only change them in one place.

EUROPEAN_COUNTRIES = [
    "at",  # Austria
    "be",  # Belgium
    "fr",  # France
    "de",  # Germany
    "it",  # Italy
    "nl",  # Netherlands
    "pl",  # Poland
    "es",  # Spain
    "ch",  # Switzerland
    "gb",  # United Kingdom
]

SEARCH_QUERY      = "data analyst"
RESULTS_PER_PAGE  = 50
RAW_OUTPUT_PATH      = "data/raw_jobs.csv"
SCRAPED_OUTPUT_PATH  = "data/scraped_jobs.csv"
FINAL_OUTPUT_PATH    = "data/final_jobs.xlsx"

LAND_RESCRAPE_OUTPUT_PATH = "data/final_jobs_fixed.xlsx"