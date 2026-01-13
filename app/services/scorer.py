"""Priority scoring engine"""

from typing import List, Tuple
from app.models import Account, AccountTier, RecommendedAction
from config import Config


class PriorityScorer:
    """Calculates priority scores for accounts"""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.weights = self.config.WEIGHTS

    def score_accounts(self, accounts: List[Account]) -> List[Account]:
        """
        Calculate priority scores for all accounts and rank them

        Args:
            accounts: List of non-disqualified Account objects

        Returns:
            List of accounts with scores and rankings, sorted by priority
        """
        # Calculate scores
        for account in accounts:
            account.priority_score, account.score_justification = self._calculate_score(account)
            account.travel_thesis = self._generate_travel_thesis(account)
            account.key_signals = self._extract_key_signals(account)
            account.recommended_action = self._recommend_action(account)

        # Sort by priority score (highest first)
        accounts.sort(key=lambda x: x.priority_score, reverse=True)

        # Assign ranks
        for idx, account in enumerate(accounts, start=1):
            account.rank = idx

        return accounts

    def _calculate_score(self, account: Account) -> Tuple[float, str]:
        """
        Calculate priority score based on weighted factors

        Formula: Priority Score = (Estimated Travel Spend) × (Likelihood to Adopt)

        Returns:
            Tuple of (score, justification)
        """
        # Component 1: Estimated Travel Spend
        travel_spend_score, travel_factors = self._calculate_travel_spend_score(account)

        # Component 2: Likelihood to Adopt
        adoption_score, adoption_factors = self._calculate_adoption_score(account)

        # Combined score (0-100 scale)
        raw_score = travel_spend_score * adoption_score

        # Normalize to 0-100
        normalized_score = min(100, max(0, raw_score * 100))

        # Generate justification
        justification = self._generate_score_justification(
            normalized_score,
            travel_spend_score,
            adoption_score,
            travel_factors,
            adoption_factors
        )

        return normalized_score, justification

    def _calculate_travel_spend_score(self, account: Account) -> Tuple[float, List[str]]:
        """Calculate estimated travel spend score (0-1) and return contributing factors"""

        score = 0.0
        factors = []

        # Factor 1: Travelling headcount (high weight)
        if account.kernel_travelling_headcount:
            # Normalize: 0-500 employees traveling -> 0-1
            travelling_score = min(1.0, account.kernel_travelling_headcount / 500)
            contribution = self.weights['travelling_headcount'] * travelling_score
            score += contribution
            factors.append(f"{account.kernel_travelling_headcount} traveling employees (+{contribution*100:.1f} pts)")

        # Factor 2: Job posts with travel (high weight)
        if account.kernel_job_posts_travel:
            # Normalize: 0-50 posts -> 0-1
            job_posts_score = min(1.0, account.kernel_job_posts_travel / 50)
            contribution = self.weights['job_posts_with_travel'] * job_posts_score
            score += contribution
            factors.append(f"{account.kernel_job_posts_travel} job posts with travel (+{contribution*100:.1f} pts)")

        # Factor 3: Number of employees (medium weight)
        if account.employee_count:
            # Normalize: 0-5000 employees -> 0-1
            employee_score = min(1.0, account.employee_count / 5000)
            contribution = self.weights['employee_count'] * employee_score
            score += contribution
            factors.append(f"{account.employee_count:,} employees (+{contribution*100:.1f} pts)")

        # Factor 4: ZI Revenue (low-medium weight)
        if account.zi_revenue:
            # Normalize: $0-$1B -> 0-1
            revenue_score = min(1.0, account.zi_revenue / 1_000_000_000)
            contribution = self.weights['revenue'] * revenue_score
            score += contribution
            factors.append(f"${account.zi_revenue/1_000_000:.1f}M revenue (+{contribution*100:.1f} pts)")

        # Factor 5: Industry propensity (high weight)
        industry_score = self._get_industry_propensity(account.industry)
        contribution = self.weights['industry_propensity'] * industry_score
        score += contribution
        if account.industry:
            factors.append(f"{account.industry} industry ({industry_score*100:.0f}% travel propensity, +{contribution*100:.1f} pts)")

        return min(1.0, score), factors

    def _calculate_adoption_score(self, account: Account) -> Tuple[float, List[str]]:
        """Calculate likelihood to adopt Navan score (0-1) and return contributing factors"""

        score = 0.0
        factors = []

        # Factor 1: Account Tier (high weight)
        tier_score = self.config.TIER_SCORES.get(
            account.account_tier.value if account.account_tier else 'C',
            0.4
        )
        contribution = self.weights['account_tier'] * tier_score
        score += contribution
        tier_name = account.account_tier.value if account.account_tier else 'Unknown'
        factors.append(f"Tier {tier_name} account (+{contribution*100:.1f} pts)")

        # Factor 2: LinkedIn Employee Growth (high weight)
        if account.linkedin_employee_growth is not None:
            # Normalize: 0-100% growth -> 0-1
            growth_score = min(1.0, abs(account.linkedin_employee_growth) / 100)
            # Positive growth is better
            if account.linkedin_employee_growth < 0:
                growth_score *= 0.5  # Penalty for negative growth
            contribution = self.weights['employee_growth'] * growth_score
            score += contribution
            factors.append(f"{account.linkedin_employee_growth:.0f}% employee growth (+{contribution*100:.1f} pts)")

        # Factor 3: Closed Lost Opportunities (medium weight)
        if account.closed_lost_opportunities:
            # Having prior opportunities suggests validated fit
            # Normalize: 1-5 opps -> 0.5-1.0
            opp_score = min(1.0, 0.5 + (account.closed_lost_opportunities * 0.1))
            contribution = self.weights['closed_lost_opps'] * opp_score
            score += contribution
            factors.append(f"{account.closed_lost_opportunities} prior opportunities (+{contribution*100:.1f} pts)")

        return min(1.0, score), factors

    def _generate_score_justification(
        self,
        final_score: float,
        travel_score: float,
        adoption_score: float,
        travel_factors: List[str],
        adoption_factors: List[str]
    ) -> str:
        """Generate a human-readable justification for the score"""

        justification_parts = []

        # Overall score
        justification_parts.append(f"**Final Score: {final_score:.1f}/100**\n")
        justification_parts.append(f"Formula: Travel Spend Score ({travel_score:.2f}) × Adoption Score ({adoption_score:.2f}) × 100\n\n")

        # Travel spend factors
        if travel_factors:
            justification_parts.append("**Travel Spend Indicators:**\n")
            for factor in travel_factors:
                justification_parts.append(f"• {factor}\n")
            justification_parts.append("\n")

        # Adoption factors
        if adoption_factors:
            justification_parts.append("**Adoption Likelihood Indicators:**\n")
            for factor in adoption_factors:
                justification_parts.append(f"• {factor}\n")

        return "".join(justification_parts)

    def _get_industry_propensity(self, industry: str) -> float:
        """Get industry travel propensity score (0-1)"""

        if not industry:
            return 0.5  # Default/unknown

        industry_lower = industry.lower()

        # Check against known industry mappings
        for industry_key, propensity in self.config.INDUSTRY_PROPENSITY.items():
            if industry_key.lower() in industry_lower:
                return propensity

        # Check for keywords
        high_travel_keywords = ['consulting', 'professional services', 'sales', 'manufacturing']
        medium_travel_keywords = ['technology', 'software', 'tech', 'saas']
        low_travel_keywords = ['retail', 'local', 'education']

        if any(kw in industry_lower for kw in high_travel_keywords):
            return 0.9

        if any(kw in industry_lower for kw in medium_travel_keywords):
            return 0.6

        if any(kw in industry_lower for kw in low_travel_keywords):
            return 0.3

        # Default for unknown industries
        return 0.5

    def _generate_travel_thesis(self, account: Account) -> str:
        """Generate a 1-2 sentence travel thesis"""

        company_name = account.account_name

        # Determine primary driver
        primary_driver = ""
        confidence = "Medium"

        if account.kernel_travelling_headcount and account.kernel_travelling_headcount > 100:
            primary_driver = f"{account.kernel_travelling_headcount} estimated traveling employees suggests significant business travel need"
            confidence = "High"
        elif account.kernel_job_posts_travel and account.kernel_job_posts_travel > 10:
            primary_driver = f"{account.kernel_job_posts_travel} job posts requiring travel indicates active travel culture"
            confidence = "High"
        elif account.industry:
            industry_score = self._get_industry_propensity(account.industry)
            if industry_score >= 0.8:
                primary_driver = f"{account.industry} industry typically requires significant client-facing travel"
                confidence = "High"
            elif industry_score >= 0.5:
                primary_driver = f"{account.industry} companies often have moderate travel needs for sales and customer success"
                confidence = "Medium"
            else:
                primary_driver = f"{account.industry} industry has limited typical business travel"
                confidence = "Low"
        else:
            primary_driver = "limited data available to assess travel needs"
            confidence = "Low"

        # Build thesis
        if account.employee_count and account.employee_count > 500:
            scale_context = f" With {account.employee_count:,} employees, enterprise-scale operations likely drive travel demand."
        elif account.linkedin_employee_growth and account.linkedin_employee_growth > 20:
            scale_context = f" {account.linkedin_employee_growth:.0f}% employee growth suggests expanding operations and increased travel."
        else:
            scale_context = ""

        thesis = f"{company_name}: {primary_driver}.{scale_context}"

        return thesis

    def _extract_key_signals(self, account: Account) -> List[str]:
        """Extract top 3 positive signals for this account"""

        signals = []

        # Collect all signals with their strength
        signal_candidates = []

        if account.kernel_travelling_headcount and account.kernel_travelling_headcount > 50:
            signal_candidates.append(
                (account.kernel_travelling_headcount / 10,
                 f"{account.kernel_travelling_headcount} traveling employees")
            )

        if account.kernel_job_posts_travel and account.kernel_job_posts_travel > 5:
            signal_candidates.append(
                (account.kernel_job_posts_travel * 2,
                 f"{account.kernel_job_posts_travel} jobs requiring travel")
            )

        if account.linkedin_employee_growth and account.linkedin_employee_growth > 10:
            signal_candidates.append(
                (account.linkedin_employee_growth,
                 f"{account.linkedin_employee_growth:.0f}% employee growth")
            )

        if account.account_tier == AccountTier.A:
            signal_candidates.append((30, "Tier A account (high confidence fit)"))

        if account.employee_count and account.employee_count > 1000:
            signal_candidates.append((20, f"{account.employee_count:,} employees (enterprise scale)"))

        if account.closed_lost_opportunities and account.closed_lost_opportunities > 0:
            signal_candidates.append(
                (account.closed_lost_opportunities * 5,
                 f"{account.closed_lost_opportunities} prior opportunities (validated interest)")
            )

        industry_score = self._get_industry_propensity(account.industry)
        if industry_score >= 0.8:
            signal_candidates.append((25, f"High-travel industry ({account.industry})"))

        # Sort by strength and take top 3
        signal_candidates.sort(key=lambda x: x[0], reverse=True)
        signals = [sig[1] for sig in signal_candidates[:3]]

        return signals if signals else ["Limited data available"]

    def _recommend_action(self, account: Account) -> RecommendedAction:
        """Recommend action based on score"""

        if account.priority_score >= 70:
            return RecommendedAction.DEEP_DIVE
        elif account.priority_score >= 40:
            return RecommendedAction.STANDARD_OUTREACH
        else:
            return RecommendedAction.DEPRIORITIZE