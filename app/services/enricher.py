"""External enrichment and web research service"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import time

from app.models import Account, CompanyOverview
from config import Config


class EnrichmentService:
    """Handles external research and enrichment of account data"""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.config.USER_AGENT})

    def enrich_account_basic(self, account: Account) -> Dict[str, Any]:
        """
        Basic enrichment for all accounts (quick scan)

        Returns dictionary with basic enrichment data
        """
        enrichment = {
            'website_active': True,
            'website_validated': False,
            'company_info': {},
        }

        # Validate website exists and is active
        if account.website:
            enrichment['website_active'], info = self._validate_website(account.website)
            enrichment['website_validated'] = True
            enrichment['company_info'] = info

        return enrichment

    def enrich_account_full(self, account: Account) -> Dict[str, Any]:
        """
        Full enrichment for top priority accounts

        Returns comprehensive enrichment data for dossier generation
        """
        enrichment = self.enrich_account_basic(account)

        # Add more detailed research
        enrichment['company_overview'] = self._build_company_overview(account)
        enrichment['insights'] = self._gather_insights(account)
        enrichment['news'] = self._find_recent_news(account)
        enrichment['linkedin_intelligence'] = self._gather_linkedin_intelligence(account)

        return enrichment

    def _validate_website(self, url: str) -> tuple[bool, Dict[str, Any]]:
        """
        Validate website and extract basic information

        Returns (is_active, info_dict)
        """
        if not url:
            return True, {}

        # Normalize URL
        if not url.startswith('http'):
            url = 'https://' + url

        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT, allow_redirects=True)

            if response.status_code >= 400:
                return False, {}

            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract basic info
            info = {
                'title': soup.title.string if soup.title else '',
                'description': '',
                'final_url': response.url,
            }

            # Try to get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                info['description'] = meta_desc.get('content')

            return True, info

        except requests.exceptions.RequestException as e:
            # Connection issues - assume active (could be firewall/temporary)
            return True, {'error': str(e)}

    def _build_company_overview(self, account: Account) -> CompanyOverview:
        """Build comprehensive company overview"""

        overview = CompanyOverview(
            industry=account.industry or "",
            employees=account.employee_count,
            employee_growth=account.linkedin_employee_growth,
            revenue=account.zi_revenue,
            headquarters="",  # Would need external API
            office_locations=[],  # Would need external API
            website=account.website or "",
        )

        # Try to extract locations from website
        if account.website:
            locations = self._extract_locations_from_website(account.website)
            overview.office_locations = locations

        return overview

    def _extract_locations_from_website(self, url: str) -> List[str]:
        """Extract office locations from company website"""

        if not url:
            return []

        # Normalize URL
        if not url.startswith('http'):
            url = 'https://' + url

        locations = []

        try:
            # Try common "about" or "locations" pages
            potential_pages = [
                url,
                f"{url}/about",
                f"{url}/locations",
                f"{url}/contact",
                f"{url}/about-us",
            ]

            for page_url in potential_pages[:2]:  # Limit to avoid too many requests
                try:
                    response = self.session.get(page_url, timeout=self.config.REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        text = soup.get_text().lower()

                        # Look for location patterns (very basic)
                        # This is a simplified version - would be enhanced with NLP
                        if 'headquarters' in text or 'hq' in text:
                            # Try to extract nearby city names (very basic)
                            pass

                        # Look for "offices in" pattern
                        if 'offices in' in text or 'locations in' in text:
                            pass

                    time.sleep(0.5)  # Be polite with requests

                except:
                    continue

        except:
            pass

        return locations

    def _gather_insights(self, account: Account) -> List[Dict[str, str]]:
        """Gather key insights from web research - NO Salesforce data"""

        insights = []

        # Try to get real web insights from the company website and news
        if account.website:
            website_insights = self._extract_insights_from_website(account.website, account.account_name)
            insights.extend(website_insights)

        # Search for recent news and developments
        news_insights = self._search_company_news(account.account_name, account.industry)
        insights.extend(news_insights)

        # If no web insights found, return empty list rather than Salesforce data
        return insights[:5]  # Limit to top 5

    def _extract_insights_from_website(self, url: str, company_name: str) -> List[Dict[str, str]]:
        """Extract relevant insights from company website"""
        insights = []

        if not url:
            return insights

        # Normalize URL
        if not url.startswith('http'):
            url = 'https://' + url

        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract meta description as an insight
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    desc = meta_desc.get('content').strip()
                    if len(desc) > 50:
                        insights.append({
                            'insight': desc[:250],
                            'source': 'Company Website'
                        })

                # Look for key business information in common sections
                # Check for expansion/growth announcements
                text_content = soup.get_text().lower()

                # Look for expansion keywords
                if any(word in text_content for word in ['expansion', 'opening new', 'expanding to', 'new location']):
                    insights.append({
                        'insight': f"{company_name} shows signs of geographic expansion based on website content",
                        'source': 'Company Website'
                    })

                # Look for hiring/growth signals
                if any(word in text_content for word in ['we are hiring', 'join our team', 'careers', 'job openings']):
                    insights.append({
                        'insight': f"{company_name} is actively hiring, indicating business growth",
                        'source': 'Company Website'
                    })

        except Exception as e:
            pass

        return insights

    def _search_company_news(self, company_name: str, industry: Optional[str]) -> List[Dict[str, str]]:
        """Search for recent company news and developments"""
        insights = []

        # For V1, we'll use basic web scraping
        # In production, this would use Google News API or similar

        try:
            # Try DuckDuckGo HTML search (no API key needed)
            search_query = f"{company_name} news"
            if industry:
                search_query += f" {industry}"

            search_url = f"https://html.duckduckgo.com/html/?q={search_query.replace(' ', '+')}"

            response = self.session.get(search_url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract search result snippets
                results = soup.find_all('a', class_='result__snippet')[:3]
                for result in results:
                    snippet = result.get_text().strip()
                    if snippet and len(snippet) > 30:
                        insights.append({
                            'insight': snippet[:200],
                            'source': 'Web Search'
                        })

        except Exception as e:
            # If web search fails, that's okay - we'll just have fewer insights
            pass

        return insights

    def _find_recent_news(self, account: Account) -> List[Dict[str, str]]:
        """
        Find recent news about the company

        Note: In production, this would use a news API (e.g., NewsAPI, Google News API)
        For now, returns placeholder/limited results
        """
        news_items = []

        # This would integrate with a news API in production
        # For now, we'll return empty or use web search if available

        # Placeholder - would be replaced with actual API calls
        # Example structure:
        # news_items.append({
        #     'item': 'Company announces expansion into new markets',
        #     'date': '2026-01-10',
        #     'source': 'TechCrunch'
        # })

        return news_items

    def _gather_linkedin_intelligence(self, account: Account) -> Dict[str, Any]:
        """
        Gather LinkedIn intelligence

        Note: In production, this would use LinkedIn API or web scraping
        For now, returns data from account fields
        """
        intelligence = {
            'company_post_themes': [],
            'executive_activity': [],
            'hiring_signals': [],
            'employee_growth': account.linkedin_employee_growth,
        }

        # Hiring signals from job posts
        if account.kernel_job_posts_travel:
            intelligence['hiring_signals'].append(
                f"{account.kernel_job_posts_travel} job posts requiring travel detected"
            )

        # Growth signal
        if account.linkedin_employee_growth and account.linkedin_employee_growth > 10:
            intelligence['hiring_signals'].append(
                f"{account.linkedin_employee_growth:.0f}% employee growth year-over-year"
            )

        return intelligence

    def batch_enrich_basic(self, accounts: List[Account]) -> Dict[str, Dict[str, Any]]:
        """
        Batch process basic enrichment for multiple accounts

        Returns dict mapping account_name -> enrichment_data
        """
        results = {}

        for account in accounts:
            try:
                enrichment = self.enrich_account_basic(account)
                results[account.account_name] = enrichment
                time.sleep(0.2)  # Rate limiting
            except Exception as e:
                print(f"Error enriching {account.account_name}: {str(e)}")
                results[account.account_name] = {'error': str(e)}

        return results