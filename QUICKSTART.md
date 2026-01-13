# Quick Start Guide

Get the Account Prioritization Tool up and running in 5 minutes!

## Installation (One-time setup)

```bash
# 1. Navigate to the project directory
cd account-prioritizer

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify setup (optional but recommended)
python test_setup.py
```

## Running the Application

```bash
# 1. Make sure you're in the project directory
cd account-prioritizer

# 2. Activate virtual environment (if not already active)
source venv/bin/activate

# 3. Start the Flask server
python run.py

# 4. Open your browser to:
# http://127.0.0.1:5000
```

## First Time Usage

1. **Prepare your CSV**: Export your accounts from Salesforce with the required columns
   - Minimum required: `Account Name`, `Account Tier`
   - For best results, include all Kernel fields

2. **Upload**: Click "Choose File" and select your CSV

3. **Configure**: Set the number of dossiers to generate (default: 15)

4. **Process**: Click "Upload and Process" and wait (typically 5-10 minutes for 150 accounts)

5. **Review**: Browse the prioritized list and dossiers in the dashboard

6. **Export**: Download the prioritized CSV for offline use

## Testing with Sample Data

The project includes `sample_data.csv` with 8 example accounts:

```bash
# Use this file to test the application
# Simply upload sample_data.csv through the web interface
```

The sample includes:
- Tier A, B, C, and D accounts
- Active and inactive businesses
- Various industries and company sizes
- Kernel AI fields populated

## Troubleshooting

**Issue**: `python: command not found`
- Solution: Use `python3` instead

**Issue**: `No module named 'flask'`
- Solution: Make sure you activated the virtual environment and installed requirements

**Issue**: Port 5000 already in use
- Solution: Edit `run.py` and change the port number

**Issue**: CSV upload fails
- Solution: Verify your CSV has `Account Name` and `Account Tier` columns

## Next Steps

After successful setup:

1. Review the full [README.md](README.md) for detailed documentation
2. Customize scoring weights in [config.py](config.py)
3. Process your real Salesforce export
4. Use the results to prioritize your outreach

## Daily Usage

Once set up, your daily workflow is:

```bash
cd account-prioritizer
source venv/bin/activate
python run.py
# Open http://127.0.0.1:5000 and upload your CSV
```

That's it! You're ready to prioritize accounts.