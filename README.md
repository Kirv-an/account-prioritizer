# Account Prioritization & Research Tool for Navan AEs

A Python-based web application that helps Navan Account Executives prioritize and research accounts from Salesforce CSV exports. This tool automates account identification, scores accounts based on travel propensity, and generates actionable research dossiers.

## Features

- **Automated Account Filtering**: Automatically disqualifies Tier D accounts, closed businesses, and stale accounts
- **Intelligent Prioritization**: Scores accounts based on estimated travel spend and likelihood to adopt Navan
- **Travel Thesis Generation**: Creates detailed explanations of why each account needs business travel
- **Deep Research Dossiers**: Generates comprehensive research reports for top priority accounts
- **Interactive Dashboard**: Web-based interface for viewing, filtering, and exporting results
- **CSV Export**: Download prioritized account lists for offline use

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

### Installation

1. Clone or download this repository
2. Navigate to the project directory:
   ```bash
   cd account-prioritizer
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the Flask server:
   ```bash
   python run.py
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

3. Upload your Salesforce CSV export and wait for processing to complete

4. View your prioritized results and dossiers in the interactive dashboard

## Usage

### CSV Format Requirements

Your Salesforce CSV export should include these columns:

**Required:**
- `Account Name`
- `Account Tier` (A/B/C/D)

**Recommended:**
- `Website`
- `Industry`
- `Last Activity`
- `Number of Employees`
- `LinkedIn Employee Growth`
- `ZI Revenue`
- `Number of Closed Lost Opportunities`
- `Kernel - Travelling headcount`
- `Kernel - Job posts with travel count`
- `Kernel - GBV range`
- `Kernel - GBV range (Reasoning)`
- `Kernel - AI Headcount`
- `Kernel - AI Headcount (Reasoning)`

Missing fields are handled gracefully - the more data you provide, the better the prioritization.

### How Prioritization Works

The tool uses a sophisticated scoring algorithm:

**Priority Score = (Estimated Travel Spend) × (Likelihood to Adopt)**

**Estimated Travel Spend Factors:**
- Travelling headcount (25% weight)
- Job posts requiring travel (20% weight)
- Employee growth (15% weight)
- Industry travel propensity (10% weight)
- Employee count (8% weight)
- Revenue (5% weight)

**Likelihood to Adopt Factors:**
- Account Tier (15% weight)
- LinkedIn employee growth (15% weight)
- Closed lost opportunities (2% weight)

### Disqualification Rules

Accounts are automatically disqualified if:
1. Account Tier = "D"
2. Business no longer exists (website returns 404 or parked domain)
3. Last Activity > 12 months ago
4. No plausible travel reason (low-travel industry + small size + no travel indicators)

### Dashboard Features

**Account List:**
- Sortable and filterable table of all accounts
- Search by account name
- Filter by recommended action (Deep Dive, Standard Outreach, Deprioritize)
- View priority scores, travel thesis, and key signals

**Full Dossiers:**
- Generated for top 15 accounts (configurable)
- Executive summary
- Detailed travel thesis with confidence assessment
- Company overview
- Key insights from multiple sources
- LinkedIn intelligence
- Recommended outreach strategy with target personas
- Talking points and suggested opening
- Risk factors and objections to anticipate

**Export:**
- Download prioritized list as CSV
- Includes all qualified accounts with scores and recommendations

## Configuration

Edit `config.py` to customize:

```python
# Number of accounts to generate full dossiers for
MAX_DOSSIER_ACCOUNTS = 15

# Days threshold for stale accounts
DISQUALIFY_LAST_ACTIVITY_DAYS = 365

# Scoring weights (must sum to ~1.0)
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

# Industry travel propensity scores
INDUSTRY_PROPENSITY = {
    'Professional Services': 1.0,
    'Consulting': 1.0,
    'Technology': 0.6,
    # ... add more industries
}
```

## Project Structure

```
account-prioritizer/
├── app/
│   ├── __init__.py           # Flask app initialization
│   ├── models.py             # Data models
│   ├── routes.py             # API endpoints
│   ├── services/
│   │   ├── csv_parser.py     # CSV parsing and validation
│   │   ├── disqualifier.py   # Disqualification logic
│   │   ├── scorer.py         # Priority scoring engine
│   │   ├── enricher.py       # External research/enrichment
│   │   └── dossier.py        # Dossier generation
│   ├── templates/
│   │   ├── base.html         # Base template
│   │   ├── dashboard.html    # Upload page
│   │   └── results.html      # Results dashboard
│   └── static/
│       └── styles.css        # Styling
├── data/
│   ├── uploads/              # Uploaded CSV files
│   └── outputs/              # Generated reports
├── config.py                 # Configuration
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
└── README.md                 # This file
```

## API Endpoints

- `GET /` - Dashboard home page
- `POST /upload` - Upload CSV and start processing
- `GET /results/<job_id>` - Get processing results (JSON)
- `GET /results/<job_id>/view` - View results in dashboard
- `POST /dossier/<job_id>/<account_name>` - Generate/regenerate dossier
- `GET /export/<job_id>` - Export results as CSV
- `POST /settings` - Update scoring weights (future)

## Troubleshooting

**Issue: CSV upload fails**
- Ensure your CSV has the required columns: `Account Name` and `Account Tier`
- Check that the file is a valid CSV (not Excel or other format)
- Verify file size is under 16MB

**Issue: Processing takes too long**
- Large CSV files (>500 accounts) may take several minutes
- Website validation for each account involves network calls
- Consider processing in batches if you have >500 accounts

**Issue: Scores seem incorrect**
- Verify your CSV has the Kernel fields populated
- Check the `WEIGHTS` configuration in `config.py`
- Review the `INDUSTRY_PROPENSITY` mapping for your industries

**Issue: Dossiers have limited information**
- The tool uses publicly available data
- For production use, integrate with LinkedIn API, news APIs, etc.
- Current version uses data from your CSV plus basic web validation

## Future Enhancements

Potential improvements for future versions:

1. **Salesforce Integration** - Direct API connection
2. **CRM Sync** - Push prioritization back to Salesforce
3. **Email Sequence Generation** - Auto-generate outreach sequences
4. **LinkedIn API Integration** - Real LinkedIn data scraping
5. **News API Integration** - Recent company news and funding
6. **Team Collaboration** - Shared account lists and assignments
7. **Historical Tracking** - Track account progression over time
8. **Background Processing** - Async job processing with Celery
9. **Database Storage** - PostgreSQL for persistent storage
10. **Chrome Extension** - Quick research while browsing LinkedIn

## Security & Privacy

- CSV files are processed locally and not shared externally
- No sensitive credentials are stored in code (use environment variables)
- Web research is limited to publicly available information
- Users are responsible for compliance with data usage policies
- LinkedIn data should only be sourced from public profiles/company pages

## Performance

Expected processing times (approximate):
- 50 accounts: 2-3 minutes
- 150 accounts: 5-10 minutes
- 500 accounts: 15-20 minutes

Processing time depends on:
- Number of accounts
- Website response times
- Number of dossiers to generate
- Internet connection speed

## Support

For issues, questions, or feature requests:
1. Check this README for troubleshooting steps
2. Review the PRD document for detailed specifications
3. Check the code comments for implementation details

## License

This tool is provided as-is for internal use by Navan Account Executives.

## Version History

- **v1.0** (2026-01-12) - Initial release
  - CSV parsing and validation
  - Disqualification logic
  - Priority scoring engine
  - Dossier generation
  - Interactive dashboard
  - CSV export

---

**Built with:** Python, Flask, pandas, BeautifulSoup, and modern web technologies