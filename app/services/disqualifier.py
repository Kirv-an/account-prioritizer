"""Account disqualification logic"""

from datetime import datetime, timedelta
from typing import List
import requests
from bs4 import BeautifulSoup

from app.models import Account, AccountTier, DisqualificationReason, RecommendedAction
from config import Config


class Disqualifier:
    """Handles account disqualification logic"""

    def __init__(self, config: Config = None):
        self.config = config or Config()

    def disqualify_accounts(self, accounts: List[Account]) -> tuple[List[Account], List[Account]]:
        """
        Apply disqualification rules to accounts

        Returns:
            Tuple of (qualified_accounts, disqualified_accounts)
        """
        qualified = []
        disqualified = []

        for account in accounts:
            reason = self._check_disqualification(account)

            if reason != DisqualificationReason.NONE:
                account.is_disqualified = True
                account.disqualification_reason = reason
                account.recommended_action = RecommendedAction.DISQUALIFIED
                disqualified.append(account)
            else:
                qualified.append(account)

        return qualified, disqualified

    def _check_disqualification(self, account: Account) -> DisqualificationReason:
        """
        Check if account should be disqualified

        Returns DisqualificationReason if disqualified, otherwise NONE
        """
        # Rule 1: Account Tier D - Auto-disqualify
        if account.account_tier == AccountTier.D:
            return DisqualificationReason.TIER_D

        # Rule 2: Stale account (Last Activity > 12 months ago)
        if account.last_activity:
            cutoff_date = datetime.now() - timedelta(days=self.config.DISQUALIFY_LAST_ACTIVITY_DAYS)
            if account.last_activity < cutoff_date:
                return DisqualificationReason.STALE_ACCOUNT

        # Rule 3: Business no longer exists (check website)
        if account.website:
            if not self._website_is_active(account.website):
                return DisqualificationReason.BUSINESS_CLOSED

        # Rule 4: No plausible travel reason
        if self._has_no_travel_reason(account):
            return DisqualificationReason.NO_TRAVEL_REASON

        return DisqualificationReason.NONE

    def _website_is_active(self, url: str) -> bool:
        """
        Check if website is active and not a parked domain

        Returns True if active, False if inactive/closed
        """
        if not url:
            return True  # Don't disqualify for missing website

        # Normalize URL
        if not url.startswith('http'):
            url = 'https://' + url

        try:
            response = requests.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT,
                headers={'User-Agent': self.config.USER_AGENT},
                allow_redirects=True
            )

            # 404 or other error status
            if response.status_code >= 400:
                return False

            # Check for parked domain indicators
            content = response.text.lower()
            parked_indicators = [
                'domain for sale',
                'this domain is for sale',
                'parked domain',
                'buy this domain',
                'domain parking',
                'this website is for sale',
                'company closed',
                'business closed',
                'ceased operations',
            ]

            if any(indicator in content for indicator in parked_indicators):
                return False

            return True

        except requests.exceptions.RequestException:
            # If we can't reach the site, don't auto-disqualify
            # Could be temporary issue or firewall
            return True

    def _has_no_travel_reason(self, account: Account) -> bool:
        """
        Determine if account has no plausible travel reason

        Returns True if no travel reason found
        """
        # If there's strong evidence of travel, don't disqualify
        if account.kernel_travelling_headcount and account.kernel_travelling_headcount > 10:
            return False

        if account.kernel_job_posts_travel and account.kernel_job_posts_travel > 5:
            return False

        # Check industry
        industry = account.industry or ""
        industry_lower = industry.lower()

        # Low-travel industries with additional signals
        low_travel_industries = [
            'retail',
            'restaurant',
            'local service',
            'salon',
            'spa',
            'fitness',
            'gym',
        ]

        # Check if it's a low-travel industry AND small/single-location
        is_low_travel_industry = any(term in industry_lower for term in low_travel_industries)

        if is_low_travel_industry:
            # Additional check: small employee count suggests single location
            if account.employee_count and account.employee_count < 50:
                # Check if they have very low travelling headcount
                if account.kernel_travelling_headcount is not None and account.kernel_travelling_headcount < 5:
                    return True

        # Don't auto-disqualify based solely on industry
        # Let scoring handle it instead
        return False

    def quick_disqualify_tier_d(self, accounts: List[Account]) -> tuple[List[Account], List[Account]]:
        """
        Fast pre-filter for Tier D accounts only (no network calls)

        Returns:
            Tuple of (non_tier_d_accounts, tier_d_accounts)
        """
        non_tier_d = []
        tier_d = []

        for account in accounts:
            if account.account_tier == AccountTier.D:
                account.is_disqualified = True
                account.disqualification_reason = DisqualificationReason.TIER_D
                account.recommended_action = RecommendedAction.DISQUALIFIED
                tier_d.append(account)
            else:
                non_tier_d.append(account)

        return non_tier_d, tier_d