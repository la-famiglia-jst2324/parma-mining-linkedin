"""Module for communicating with Linkedin using Apify sccraper.

This module communicates with the Apify Scraper to discover and scrape
"""
import json
import logging
import os

from apify_client import ApifyClient
from dotenv import load_dotenv
from googlesearch import search

from parma_mining.linkedin.model import CompanyModel, DiscoveryResponse
from parma_mining.mining_common.exceptions import (
    ClientError,
    CrawlingError,
)

logger = logging.getLogger(__name__)


class LinkedinClient:
    """Class for communicating with the Linkedin via Apify."""

    def __init__(self):
        """Initialize the LinkedinClient class."""
        load_dotenv()
        self.key = str(os.getenv("APIFY_API_KEY") or "")
        self.cookie = self.parse_json_string(str(os.getenv("LINKEDIN_COOKIE") or "{}"))
        self.actor_id = str(os.getenv("APIFY_ACTOR_ID") or "")
        self.maximum_runtime_scraping_seconds = 600  # 10 minutes

    def parse_json_string(self, json_string):
        """Parse a JSON string."""
        return json.loads(json_string)

    def discover_company(self, query: str) -> DiscoveryResponse:
        """Discover a company.

        Take name as an input and find its linkedin url.
        """
        search_query = query + " linkedin"
        preferred_slash_count = 4
        urls = []
        try:
            for search_item in search(
                search_query, tld="co.in", num=10, stop=10, pause=2
            ):
                if (
                    search_item.count("/") == preferred_slash_count
                    and "https://www.linkedin.com/company/" in search_item
                ):
                    urls.append(search_item)
                    break
            if len(urls) == 0:
                raise Exception("No Linkedin profile url found with given query")
            return DiscoveryResponse.model_validate({"urls": urls})
        except Exception as e:
            msg = f"Error searching organizations for {query}: {e}"
            logger.error(msg)
            raise ClientError()

    def get_company_details(self, urls: list[str]) -> CompanyModel:
        """Scrape a company for details."""
        # Initialize the ApifyClient with your API token
        client = ApifyClient(self.key)
        # Prepare the Actor input
        run_input = {
            "urls": urls,
            "minDelay": 2,
            "maxDelay": 5,
            "cookie": self.cookie,
        }
        try:
            # Run the Actor and wait for it to finish
            run = client.actor(self.actor_id).call(run_input=run_input)

            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                company_data = {
                    "name": item["name"],
                    "linkedin_id": item["id"],
                    "website": item["websiteUrl"],
                    "profile_url": item["url"],
                    "ads_rule": item["adsRule"],
                    "employee_count": item["employeeCount"],
                    "active": item["active"],
                    "job_search_url": item["jobSearchUrl"],
                    "phone": item["phone"]["number"]
                    if item["phone"] is not None
                    else None,
                    "tagline": item["tagline"],
                    "description": item["description"],
                    "logo_url": item["logoUrl"],
                    "follower_count": item["followerCount"],
                    "universal_name": item["universalName"],
                    "specialities": item["specialities"],
                    "headquarter_city": item["headquarter"]["city"]
                    if item["headquarter"] is not None
                    else None,
                    "headquarter_country": item["headquarter"]["country"]
                    if item["headquarter"] is not None
                    else None,
                    "head_quarter_postal_code": item["headquarter"]["postalCode"]
                    if item["headquarter"] is not None
                    else None,
                    "industries": [industry["name"] for industry in item["industries"]]
                    if item["industries"] is not None
                    else None,
                    "locations": [
                        location["localizedName"]
                        for location in item["groupedLocations"]
                    ]
                    if item["groupedLocations"] is not None
                    else None,
                    "hashtags": [hashtag["displayName"] for hashtag in item["hashtag"]]
                    if item["hashtag"] is not None
                    else None,
                    "founded_year": item["foundedOn"]["year"]
                    if item["foundedOn"] is not None
                    else None,
                    "founded_month": item["foundedOn"]["month"]
                    if item["foundedOn"] is not None
                    else None,
                    "founded_day": item["foundedOn"]["day"]
                    if item["foundedOn"] is not None
                    else None,
                }
            return CompanyModel.model_validate(company_data)

        except Exception as e:
            msg = f"Error scraping company details: {e}"
            logger.error(msg)
            raise CrawlingError(msg)
