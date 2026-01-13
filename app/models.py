"""Data models for accounts and dossiers"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class AccountTier(Enum):
    """Account tier classification"""
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class RecommendedAction(Enum):
    """Recommended action for an account"""
    DEEP_DIVE = "Deep Dive"
    STANDARD_OUTREACH = "Standard Outreach"
    DEPRIORITIZE = "Deprioritize"
    DISQUALIFIED = "Disqualified"


class DisqualificationReason(Enum):
    """Reasons for disqualifying an account"""
    TIER_D = "Account Tier D"
    BUSINESS_CLOSED = "Business no longer exists"
    STALE_ACCOUNT = "Last activity > 12 months"
    NO_TRAVEL_REASON = "No plausible travel reason"
    NONE = ""


@dataclass
class Account:
    """Represents a single account from the CSV"""

    # Core identifiers
    account_name: str
    website: Optional[str] = None
    account_tier: Optional[AccountTier] = None

    # Salesforce data
    last_activity: Optional[datetime] = None
    zi_revenue: Optional[int] = None
    industry: Optional[str] = None
    closed_lost_opportunities: int = 0
    employee_count: Optional[int] = None
    linkedin_employee_growth: Optional[float] = None  # Percentage

    # Kernel AI fields
    kernel_gbv_range: Optional[str] = None
    kernel_gbv_reasoning: Optional[str] = None
    kernel_ai_headcount: Optional[int] = None
    kernel_ai_headcount_reasoning: Optional[str] = None
    kernel_job_posts_travel: int = 0
    kernel_travelling_headcount: int = 0

    # Calculated fields
    priority_score: float = 0.0
    rank: Optional[int] = None
    travel_thesis: str = ""
    key_signals: List[str] = field(default_factory=list)
    score_justification: str = ""  # Explanation of how the score was calculated
    recommended_action: RecommendedAction = RecommendedAction.STANDARD_OUTREACH
    disqualification_reason: DisqualificationReason = DisqualificationReason.NONE

    # Flags
    is_disqualified: bool = False
    has_dossier: bool = False

    # Raw CSV data for reference
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert account to dictionary for JSON serialization"""
        return {
            'account_name': self.account_name,
            'website': self.website,
            'account_tier': self.account_tier.value if self.account_tier else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'zi_revenue': self.zi_revenue,
            'industry': self.industry,
            'closed_lost_opportunities': self.closed_lost_opportunities,
            'employee_count': self.employee_count,
            'linkedin_employee_growth': self.linkedin_employee_growth,
            'kernel_gbv_range': self.kernel_gbv_range,
            'kernel_travelling_headcount': self.kernel_travelling_headcount,
            'kernel_job_posts_travel': self.kernel_job_posts_travel,
            'priority_score': round(self.priority_score, 2),
            'rank': self.rank,
            'travel_thesis': self.travel_thesis,
            'key_signals': self.key_signals,
            'score_justification': self.score_justification,
            'recommended_action': self.recommended_action.value,
            'disqualification_reason': self.disqualification_reason.value,
            'is_disqualified': self.is_disqualified,
            'has_dossier': self.has_dossier,
        }


@dataclass
class CompanyOverview:
    """Company overview section of a dossier"""
    industry: str = ""
    employees: Optional[int] = None
    employee_growth: Optional[float] = None
    revenue: Optional[int] = None
    headquarters: str = ""
    office_locations: List[str] = field(default_factory=list)
    website: str = ""


@dataclass
class OutreachStrategy:
    """Recommended outreach strategy"""
    target_personas: List[Dict[str, str]] = field(default_factory=list)  # [{"title": "", "reason": ""}]
    talking_points: List[str] = field(default_factory=list)
    suggested_opening: str = ""


@dataclass
class Dossier:
    """Full research dossier for high-priority accounts"""

    account_name: str
    priority_score: float
    account_tier: str

    # Core sections
    executive_summary: str = ""
    travel_thesis_detailed: str = ""
    company_overview: CompanyOverview = field(default_factory=CompanyOverview)

    # Insights and intelligence
    key_insights: List[Dict[str, str]] = field(default_factory=list)  # [{"insight": "", "source": ""}]
    recent_news: List[Dict[str, str]] = field(default_factory=list)  # [{"item": "", "date": "", "source": ""}]
    linkedin_intelligence: Dict[str, Any] = field(default_factory=dict)

    # Strategy
    outreach_strategy: OutreachStrategy = field(default_factory=OutreachStrategy)
    risk_factors: List[str] = field(default_factory=list)

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert dossier to dictionary"""
        return {
            'account_name': self.account_name,
            'priority_score': round(self.priority_score, 2),
            'account_tier': self.account_tier,
            'executive_summary': self.executive_summary,
            'travel_thesis_detailed': self.travel_thesis_detailed,
            'company_overview': {
                'industry': self.company_overview.industry,
                'employees': self.company_overview.employees,
                'employee_growth': self.company_overview.employee_growth,
                'revenue': self.company_overview.revenue,
                'headquarters': self.company_overview.headquarters,
                'office_locations': self.company_overview.office_locations,
                'website': self.company_overview.website,
            },
            'key_insights': self.key_insights,
            'recent_news': self.recent_news,
            'linkedin_intelligence': self.linkedin_intelligence,
            'outreach_strategy': {
                'target_personas': self.outreach_strategy.target_personas,
                'talking_points': self.outreach_strategy.talking_points,
                'suggested_opening': self.outreach_strategy.suggested_opening,
            },
            'risk_factors': self.risk_factors,
            'generated_at': self.generated_at.isoformat(),
        }


@dataclass
class ProcessingJob:
    """Represents a CSV processing job"""
    job_id: str
    status: str  # 'processing', 'complete', 'error'
    total_accounts: int = 0
    disqualified: int = 0
    prioritized: int = 0
    dossiers_generated: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Results
    accounts: List[Account] = field(default_factory=list)
    dossiers: List[Dossier] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            'job_id': self.job_id,
            'status': self.status,
            'summary': {
                'total': self.total_accounts,
                'disqualified': self.disqualified,
                'prioritized': self.prioritized,
                'dossiers_generated': self.dossiers_generated,
            },
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'accounts': [acc.to_dict() for acc in self.accounts],
            'dossiers': [dos.to_dict() for dos in self.dossiers],
        }