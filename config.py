import os
from pathlib import Path

class Config:
    """Configuration settings for the Account Prioritization Tool"""

    # Base directory
    BASE_DIR = Path(__file__).parent

    # Folder paths
    UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'
    OUTPUT_FOLDER = BASE_DIR / 'data' / 'outputs'

    # Ensure directories exist
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    # Processing settings
    MAX_DOSSIER_ACCOUNTS = 15
    DISQUALIFY_LAST_ACTIVITY_DAYS = 365

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Scoring weights (adjustable via UI or config)
    WEIGHTS = {
        'travelling_headcount': 0.25,
        'job_posts_with_travel': 0.20,
        'employee_growth': 0.15,
        'account_tier': 0.15,
        'industry_propensity': 0.10,
        'employee_count': 0.08,
        'revenue': 0.05,
        'closed_lost_opps': 0.02
    }

    # Industry travel propensity mapping
    INDUSTRY_PROPENSITY = {
        # Very High
        'Professional Services': 1.0,
        'Consulting': 1.0,
        'Manufacturing': 0.9,
        'Sales': 0.95,

        # High
        'Financial Services': 0.8,
        'Venture Capital': 0.85,
        'Private Equity': 0.85,
        'Construction': 0.8,
        'Healthcare': 0.75,
        'Logistics': 0.8,

        # Medium
        'Technology': 0.6,
        'Software': 0.6,
        'Media': 0.5,
        'Entertainment': 0.5,
        'Non-Profit': 0.5,

        # Lower
        'Retail': 0.3,
        'Education': 0.3,
        'Local Services': 0.2,
    }

    # Account tier scoring
    TIER_SCORES = {
        'A': 1.0,
        'B': 0.7,
        'C': 0.4,
        'D': 0.0
    }

    # Web scraping settings
    REQUEST_TIMEOUT = 10  # seconds
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'