"""Dossier generation service"""

from typing import List, Dict, Any
from datetime import datetime

from app.models import Account, Dossier, CompanyOverview, OutreachStrategy
from app.services.enricher import EnrichmentService
from config import Config


class DossierGenerator:
    """Generates detailed dossiers for high-priority accounts"""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.enricher = EnrichmentService(config)

    def generate_dossiers(self, accounts: List[Account], top_n: int = None) -> List[Dossier]:
        """
        Generate dossiers for top N accounts

        Args:
            accounts: List of scored and ranked accounts
            top_n: Number of dossiers to generate (default from config)

        Returns:
            List of Dossier objects
        """
        if top_n is None:
            top_n = self.config.MAX_DOSSIER_ACCOUNTS

        # Get top N accounts
        top_accounts = sorted(accounts, key=lambda x: x.priority_score, reverse=True)[:top_n]

        dossiers = []
        for account in top_accounts:
            try:
                dossier = self.generate_dossier(account)
                dossiers.append(dossier)
                account.has_dossier = True
            except Exception as e:
                print(f"Error generating dossier for {account.account_name}: {str(e)}")
                continue

        return dossiers

    def generate_dossier(self, account: Account) -> Dossier:
        """Generate a single comprehensive dossier"""

        # Get enrichment data
        enrichment = self.enricher.enrich_account_full(account)

        # Build dossier
        dossier = Dossier(
            account_name=account.account_name,
            priority_score=account.priority_score,
            account_tier=account.account_tier.value if account.account_tier else "Unknown",
        )

        # Generate each section
        dossier.executive_summary = self._generate_executive_summary(account, enrichment)
        dossier.travel_thesis_detailed = self._generate_detailed_travel_thesis(account, enrichment)
        dossier.company_overview = enrichment.get('company_overview', CompanyOverview())
        dossier.key_insights = enrichment.get('insights', [])
        dossier.recent_news = enrichment.get('news', [])
        dossier.linkedin_intelligence = enrichment.get('linkedin_intelligence', {})
        dossier.outreach_strategy = self._generate_outreach_strategy(account, enrichment)
        dossier.risk_factors = self._identify_risk_factors(account, enrichment)

        return dossier

    def _generate_executive_summary(self, account: Account, enrichment: Dict[str, Any]) -> str:
        """Generate 2-3 sentence executive summary"""

        score_description = "high-priority" if account.priority_score >= 70 else "priority"

        summary_parts = [
            f"{account.account_name} is a {score_description} opportunity with a score of {account.priority_score:.0f}/100."
        ]

        # Add key differentiator
        if account.kernel_travelling_headcount and account.kernel_travelling_headcount > 100:
            summary_parts.append(
                f"With an estimated {account.kernel_travelling_headcount} traveling employees, "
                f"this account represents significant travel spend potential."
            )
        elif account.industry:
            summary_parts.append(
                f"As a {account.industry} company, they likely have substantial business travel needs."
            )

        # Add growth/scale context
        if account.employee_count and account.employee_count > 1000:
            summary_parts.append(
                f"Enterprise scale with {account.employee_count:,} employees suggests established travel management needs."
            )
        elif account.linkedin_employee_growth and account.linkedin_employee_growth > 20:
            summary_parts.append(
                f"Rapid {account.linkedin_employee_growth:.0f}% growth indicates expanding travel requirements."
            )

        return " ".join(summary_parts)

    def _generate_detailed_travel_thesis(self, account: Account, enrichment: Dict[str, Any]) -> str:
        """Generate detailed travel thesis with supporting evidence"""

        thesis_parts = []

        # Start with basic thesis
        thesis_parts.append(f"{account.account_name} requires business travel for the following reasons:\n")

        # Primary drivers
        primary_drivers = []

        if account.kernel_travelling_headcount and account.kernel_travelling_headcount > 50:
            primary_drivers.append(
                f"**Traveling Workforce**: {account.kernel_travelling_headcount} employees "
                f"estimated to require regular business travel based on role analysis."
            )

        if account.kernel_job_posts_travel and account.kernel_job_posts_travel > 5:
            primary_drivers.append(
                f"**Active Hiring for Travel Roles**: {account.kernel_job_posts_travel} job postings "
                f"explicitly require travel, indicating ongoing need for field operations."
            )

        if account.industry:
            industry_context = self._get_industry_travel_context(account.industry)
            if industry_context:
                primary_drivers.append(f"**Industry Context**: {industry_context}")

        # Add company-specific insights from Kernel
        if account.kernel_gbv_reasoning:
            primary_drivers.append(
                f"**Estimated Travel Spend**: {account.kernel_gbv_range or 'Unknown'}. "
                f"{account.kernel_gbv_reasoning[:300]}"
            )

        if primary_drivers:
            thesis_parts.append("\n**Primary Drivers:**\n")
            for driver in primary_drivers:
                thesis_parts.append(f"- {driver}\n")

        # Add confidence assessment
        confidence = self._assess_travel_thesis_confidence(account)
        thesis_parts.append(f"\n**Confidence Level**: {confidence}")

        return "".join(thesis_parts)

    def _get_industry_travel_context(self, industry: str) -> str:
        """Get industry-specific travel context"""

        industry_lower = industry.lower()

        contexts = {
            'consulting': 'Consulting firms typically require 60-80% of employees to travel regularly for client engagements.',
            'professional services': 'Professional services require frequent on-site client work and relationship building.',
            'manufacturing': 'Multi-site manufacturing operations require travel between facilities and supplier/customer visits.',
            'sales': 'Sales-driven organizations require extensive travel for prospecting, demos, and relationship management.',
            'technology': 'Tech companies travel for customer success, sales engineering, and conference presence.',
            'software': 'Software companies require travel for implementation, training, and customer support.',
            'financial services': 'Financial services require travel for due diligence, client meetings, and deal closure.',
        }

        for key, context in contexts.items():
            if key in industry_lower:
                return context

        return f"{industry} companies typically require business travel for client engagement and operations."

    def _assess_travel_thesis_confidence(self, account: Account) -> str:
        """Assess confidence in travel thesis"""

        confidence_score = 0

        # Strong signals
        if account.kernel_travelling_headcount and account.kernel_travelling_headcount > 100:
            confidence_score += 3
        if account.kernel_job_posts_travel and account.kernel_job_posts_travel > 10:
            confidence_score += 3
        if account.employee_count and account.employee_count > 500:
            confidence_score += 2

        # Medium signals
        if account.industry:
            confidence_score += 1
        if account.kernel_gbv_reasoning:
            confidence_score += 1

        if confidence_score >= 6:
            return "High - Multiple strong indicators of travel need"
        elif confidence_score >= 3:
            return "Medium - Good indicators present, some gaps in data"
        else:
            return "Low - Limited data available, requires additional research"

    def _generate_outreach_strategy(self, account: Account, enrichment: Dict[str, Any]) -> OutreachStrategy:
        """Generate recommended outreach strategy based on web insights"""

        strategy = OutreachStrategy()

        # Target personas
        strategy.target_personas = [
            {
                'title': 'CFO / VP of Finance',
                'reason': 'Primary decision-maker for T&E spend and expense management tools'
            },
            {
                'title': 'Head of Operations / COO',
                'reason': 'Oversees operational efficiency and travel logistics'
            },
        ]

        # If strong sales signal, add sales leader
        if account.kernel_job_posts_travel and account.kernel_job_posts_travel > 10:
            strategy.target_personas.append({
                'title': 'VP of Sales / CRO',
                'reason': 'Manages large traveling sales team that would benefit from Navan'
            })

        # Build unique talking points from web insights
        talking_points = []
        insights = enrichment.get('insights', [])

        # Use web insights for talking points
        for insight_data in insights[:2]:  # Use top 2 insights
            insight_text = insight_data.get('insight', '')
            if insight_text and 'expansion' in insight_text.lower():
                talking_points.append(
                    f"As you're expanding operations, Navan can scale with you and simplify travel management across new locations"
                )
            elif insight_text and 'hiring' in insight_text.lower():
                talking_points.append(
                    f"With your growing team, Navan can help onboard new hires quickly with our intuitive platform"
                )

        # Add standard value props if we don't have enough from insights
        if len(talking_points) < 2:
            if account.linkedin_employee_growth and account.linkedin_employee_growth > 20:
                talking_points.append(
                    f"Growing {account.linkedin_employee_growth:.0f}% YoY - "
                    f"Navan scales seamlessly with your expanding team"
                )

            if account.kernel_travelling_headcount and account.kernel_travelling_headcount > 100:
                talking_points.append(
                    f"With {account.kernel_travelling_headcount}+ traveling employees, "
                    f"Navan can help you save 15-20% on travel spend"
                )

        if len(talking_points) < 3 and account.industry:
            talking_points.append(
                f"We work with leading {account.industry} companies to streamline travel management"
            )

        strategy.talking_points = talking_points if talking_points else [
            "Navan combines travel booking, expense management, and corporate cards in one platform",
            "Save time and money while giving your team a better travel experience"
        ]

        # Generate unique opening based on web insights
        strategy.suggested_opening = self._generate_unique_opening(account, insights)

        return strategy

    def _generate_unique_opening(self, account: Account, insights: List[Dict[str, str]]) -> str:
        """Generate a unique opening based on web insights"""

        company_name = account.account_name

        # Try to use web insights for a personalized opening
        if insights:
            for insight_data in insights:
                insight_text = insight_data.get('insight', '')
                source = insight_data.get('source', '')

                # Use the first substantial insight
                if insight_text and len(insight_text) > 50:
                    if 'expansion' in insight_text.lower() or 'expanding' in insight_text.lower():
                        return (
                            f"I noticed {company_name} is expanding operations. "
                            f"Companies in growth mode typically see 15-20% travel savings "
                            f"when they centralize with Navan. Would love to explore if it's a fit."
                        )
                    elif 'hiring' in insight_text.lower() or 'growing' in insight_text.lower():
                        return (
                            f"Saw that {company_name} is actively hiring. As your team grows, "
                            f"Navan can help you scale travel operations efficiently. "
                            f"Happy to share how we support fast-growing companies."
                        )
                    elif source == 'Web Search' and len(insight_text) > 80:
                        # Use a snippet of recent news
                        snippet = insight_text[:100].strip()
                        return (
                            f"I came across recent news about {company_name}. "
                            f"With your business momentum, wanted to share how Navan helps "
                            f"companies like yours streamline travel management. Worth a conversation?"
                        )

        # Fallback to data-driven opening
        if account.kernel_travelling_headcount and account.kernel_travelling_headcount > 100:
            return (
                f"I noticed {company_name} has a significant traveling workforce. "
                f"Companies like yours typically see 15-20% savings when they consolidate "
                f"travel and expense management with Navan."
            )
        elif account.linkedin_employee_growth and account.linkedin_employee_growth > 20:
            return (
                f"{company_name} is growing rapidly ({account.linkedin_employee_growth:.0f}% YoY). "
                f"Navan scales seamlessly with fast-growing teams - would love to share how "
                f"we're helping similar companies."
            )
        else:
            return (
                f"I saw that {company_name} is {self._get_company_activity(account)}. "
                f"Wanted to share how Navan is helping similar companies streamline travel management."
            )

    def _get_company_activity(self, account: Account) -> str:
        """Get a description of current company activity"""

        if account.linkedin_employee_growth and account.linkedin_employee_growth > 20:
            return f"growing rapidly (up {account.linkedin_employee_growth:.0f}%)"
        elif account.kernel_job_posts_travel and account.kernel_job_posts_travel > 5:
            return "actively hiring for roles requiring travel"
        elif account.employee_count and account.employee_count > 1000:
            return "operating at enterprise scale"
        else:
            return f"in the {account.industry or 'your'} space"

    def _identify_risk_factors(self, account: Account, enrichment: Dict[str, Any]) -> List[str]:
        """Identify potential risk factors or objections"""

        risks = []

        # Closed-lost history
        if account.closed_lost_opportunities and account.closed_lost_opportunities > 2:
            risks.append(
                f"Previously closed-lost {account.closed_lost_opportunities} times - "
                f"understand past objections before reaching out"
            )

        # Stale engagement
        if account.last_activity:
            days_since = (datetime.now() - account.last_activity).days
            if days_since > 180:
                risks.append(
                    f"No activity in {days_since} days - may need re-education on Navan's value prop"
                )

        # Negative growth
        if account.linkedin_employee_growth and account.linkedin_employee_growth < -10:
            risks.append(
                f"Contracting workforce ({account.linkedin_employee_growth:.0f}%) - "
                f"may be cutting costs and resistant to new vendors"
            )

        # Limited travel indicators
        if (not account.kernel_travelling_headcount or account.kernel_travelling_headcount < 20) and \
           (not account.kernel_job_posts_travel or account.kernel_job_posts_travel < 3):
            risks.append(
                "Limited travel indicators in data - validate travel volume before heavy pursuit"
            )

        return risks if risks else ["No significant risk factors identified"]