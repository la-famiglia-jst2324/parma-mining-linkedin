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
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
            )
            for search_item in search(
                search_query,
                tld="co.in",
                num=10,
                stop=10,
                pause=5,
                user_agent=user_agent,
            ):
                print(search_item)
                if (
                    search_item.count("/") == preferred_slash_count
                    or (
                        search_item.count("/") == preferred_slash_count + 1
                        and search_item.endswith("/")
                    )
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
                    "name": item["name"] if "name" in item else None,
                    "linkedin_id": item["id"] if "id" in item else None,
                    "website": item["websiteUrl"] if "websiteUrl" in item else None,
                    "profile_url": item["url"] if "url" in item else None,
                    "ads_rule": item["adsRule"] if "adsRule" in item else None,
                    "employee_count": item["employeeCount"]
                    if "employeeCount" in item
                    else None,
                    "active": item["active"] if "active" in item else None,
                    "job_search_url": item["jobSearchUrl"]
                    if "jobSearchUrl" in item
                    else None,
                    "phone": item["phone"]["number"]
                    if item["phone"] is not None
                    else None,
                    "tagline": item["tagline"] if "tagline" in item else None,
                    "description": item["description"]
                    if "description" in item
                    else None,
                    "logo_url": item["logoUrl"] if "logoUrl" in item else None,
                    "follower_count": item["followerCount"]
                    if "followerCount" in item
                    else None,
                    "universal_name": item["universalName"]
                    if "universalName" in item
                    else None,
                    "specialities": item["specialities"]
                    if "specialities" in item
                    else None,
                    "headquarter_city": item["headquarter"]["city"]
                    if "headquarter" in item
                    else None,
                    "headquarter_country": item["headquarter"]["country"]
                    if "headquarter" in item
                    else None,
                    "head_quarter_postal_code": item["headquarter"]["postalCode"]
                    if "headquarter" in item
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
