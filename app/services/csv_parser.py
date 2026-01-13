"""CSV parsing and validation service"""

import pandas as pd
from datetime import datetime
from typing import List, Tuple, Optional
from pathlib import Path

from app.models import Account, AccountTier


class CSVParseError(Exception):
    """Custom exception for CSV parsing errors"""
    pass


class CSVParser:
    """Handles CSV parsing and validation"""

    # Expected column mappings (CSV column name -> model field)
    COLUMN_MAPPING = {
        'Account Tier': 'account_tier',
        'Account Name': 'account_name',
        'Last Activity': 'last_activity',
        'ZI Revenue': 'zi_revenue',
        'Industry': 'industry',
        'Number of Closed Lost Opportunities': 'closed_lost_opportunities',
        'Number of Employees': 'employee_count',
        'LinkedIn Employee Growth': 'linkedin_employee_growth',
        'Website': 'website',
        'Kernel - GBV range': 'kernel_gbv_range',
        'Kernel - GBV range (Reasoning)': 'kernel_gbv_reasoning',
        'Kernel - AI Headcount': 'kernel_ai_headcount',
        'Kernel - AI Headcount (Reasoning)': 'kernel_ai_headcount_reasoning',
        'Kernel - Job posts with travel count': 'kernel_job_posts_travel',
        'Kernel - Travelling headcount': 'kernel_travelling_headcount',
    }

    REQUIRED_COLUMNS = ['Account Name', 'Account Tier']

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.accounts: List[Account] = []

    def validate_csv(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate CSV file format and columns

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        try:
            # Try multiple encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']

            for encoding in encodings:
                try:
                    self.df = pd.read_csv(file_path, encoding=encoding)
                    break  # Success, stop trying
                except UnicodeDecodeError:
                    continue  # Try next encoding
                except Exception as e:
                    # Other error, not encoding-related
                    errors.append(f"Failed to read CSV: {str(e)}")
                    return False, errors
            else:
                # None of the encodings worked
                errors.append(f"Failed to read CSV: Unable to detect file encoding. Tried: {', '.join(encodings)}")
                return False, errors

        except Exception as e:
            errors.append(f"Failed to read CSV: {str(e)}")
            return False, errors

        # Check if CSV is empty
        if self.df.empty:
            errors.append("CSV file is empty")
            return False, errors

        # Check for required columns
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in self.df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")

        # Check for duplicate column names
        if len(self.df.columns) != len(set(self.df.columns)):
            errors.append("CSV contains duplicate column names")

        return len(errors) == 0, errors

    def parse_csv(self, file_path: Path) -> List[Account]:
        """
        Parse CSV file and return list of Account objects

        Args:
            file_path: Path to the CSV file

        Returns:
            List of Account objects

        Raises:
            CSVParseError: If validation fails
        """
        # Validate first
        is_valid, errors = self.validate_csv(file_path)
        if not is_valid:
            raise CSVParseError(f"CSV validation failed: {'; '.join(errors)}")

        accounts = []

        for idx, row in self.df.iterrows():
            try:
                account = self._parse_row(row, idx)
                accounts.append(account)
            except Exception as e:
                # Log error but continue processing other rows
                print(f"Warning: Error parsing row {idx + 2}: {str(e)}")
                continue

        if not accounts:
            raise CSVParseError("No valid accounts could be parsed from CSV")

        self.accounts = accounts
        return accounts

    def _parse_row(self, row: pd.Series, row_idx: int) -> Account:
        """Parse a single CSV row into an Account object"""

        # Helper function to handle missing values
        def get_value(column_name: str, default=None):
            if column_name not in row:
                return default
            val = row[column_name]
            if pd.isna(val) or val == '-' or val == '':
                return default
            return val

        # Parse account tier
        tier_str = get_value('Account Tier')
        try:
            account_tier = AccountTier(tier_str) if tier_str else None
        except ValueError:
            account_tier = None

        # Parse last activity date
        last_activity = None
        last_activity_str = get_value('Last Activity')
        if last_activity_str:
            try:
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        last_activity = datetime.strptime(str(last_activity_str), fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        # Parse numeric fields with handling for missing values
        def parse_int(column: str) -> Optional[int]:
            val = get_value(column)
            if val is None:
                return None
            try:
                # Remove commas and convert
                if isinstance(val, str):
                    val = val.replace(',', '').strip()
                return int(float(val))
            except (ValueError, TypeError):
                return None

        def parse_float(column: str) -> Optional[float]:
            val = get_value(column)
            if val is None:
                return None
            try:
                if isinstance(val, str):
                    # Handle percentage strings
                    val = val.replace('%', '').replace(',', '').strip()
                return float(val)
            except (ValueError, TypeError):
                return None

        # Create Account object
        account = Account(
            account_name=get_value('Account Name', f'Unknown-{row_idx}'),
            website=get_value('Website'),
            account_tier=account_tier,
            last_activity=last_activity,
            zi_revenue=parse_int('ZI Revenue'),
            industry=get_value('Industry'),
            closed_lost_opportunities=parse_int('Number of Closed Lost Opportunities') or 0,
            employee_count=parse_int('Number of Employees'),
            linkedin_employee_growth=parse_float('LinkedIn Employee Growth'),
            kernel_gbv_range=get_value('Kernel - GBV range'),
            kernel_gbv_reasoning=get_value('Kernel - GBV range (Reasoning)'),
            kernel_ai_headcount=parse_int('Kernel - AI Headcount'),
            kernel_ai_headcount_reasoning=get_value('Kernel - AI Headcount (Reasoning)'),
            kernel_job_posts_travel=parse_int('Kernel - Job posts with travel count') or 0,
            kernel_travelling_headcount=parse_int('Kernel - Travelling headcount') or 0,
        )

        # Store raw data for reference
        account.raw_data = row.to_dict()

        return account

    def get_column_preview(self) -> dict:
        """Get a preview of detected columns for UI confirmation"""
        if self.df is None:
            return {}

        preview = {
            'total_rows': len(self.df),
            'columns': [],
        }

        for col in self.df.columns:
            mapped_field = self.COLUMN_MAPPING.get(col, 'unmapped')
            is_required = col in self.REQUIRED_COLUMNS
            preview['columns'].append({
                'csv_column': col,
                'mapped_to': mapped_field,
                'required': is_required,
                'sample_values': self.df[col].head(3).tolist(),
            })

        return preview