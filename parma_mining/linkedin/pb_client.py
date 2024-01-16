"""Module for communicating with the Phantombuster API.

This module communicates with the Phantombuster API to discover and scrape
"""
import logging
import os
import time

import httpx
from dotenv import load_dotenv
from httpx import HTTPStatusError
from pydantic import ValidationError

from parma_mining.linkedin.model import CompanyModel, DiscoveryModel, ErrorInfoModel
from parma_mining.mining_common.const import HTTP_200
from parma_mining.mining_common.exceptions import CrawlingError, CrawlingExternalError
from parma_mining.mining_common.helper import collect_errors

logger = logging.getLogger(__name__)


class PhantombusterClient:
    """Class for communicating with the Phantombuster API."""

    def __init__(self, errors: dict[str, ErrorInfoModel]):
        """Initialize the PhantombusterClient class."""
        load_dotenv()
        self.errors = errors
        self.launch_url = str(os.getenv("PHANTOMBUSTER_API_LAUNCH_ENDPOINT") or "")
        self.fetch_url = str(os.getenv("PHANTOMBUSTER_API_FETCH_ENDPOINT") or "")
        self.container_fetch_url = str(os.getenv("CONTAINER_FETCH_ENDPOINT") or "")
        self.key = str(os.getenv("PHANTOMBUSTER_API_KEY") or "")
        self.company_scraper = str(os.getenv("COMPANY_SCRAPER_AGENT_ID") or "")
        self.discovery = str(os.getenv("DISCOVERY_AGENT_ID") or "")
        self.cookie = str(os.getenv("LINKEDIN_SESSION_COOKIE") or "")
        self.maximum_runtime_scraping_seconds = 600  # 10 minutes

    def discover_company(self, query: str) -> list[DiscoveryModel]:
        """Discover a company."""
        # Launch the company discovery agent
        payload = {
            "argument": {"queries": [query], "csvName": "result"},
            "id": self.discovery,
        }
        headers = {"content-type": "application/json", "X-Phantombuster-Key": self.key}
        response = httpx.post(self.launch_url, json=payload, headers=headers)
        container_id = str(response.json()["containerId"])
        container_fetch_url = self.container_fetch_url + "?id=" + container_id

        # Check the status of the container if it is done, go ahead, if it is not wait
        # for 10 seconds and check again
        while True:
            response = httpx.get(container_fetch_url, headers=headers)
            if response.status_code == HTTP_200:
                if response.json()["status"] == "finished":
                    break
            time.sleep(10)

        # Get the output of the container
        fetch_url = self.fetch_url + "?id=" + self.discovery

        s3_url = "https://phantombuster.s3.amazonaws.com/{orgS3Folder}/{s3Folder}/{filename}.json"
        response = httpx.get(fetch_url, headers=headers)

        json_response = response.json()
        org_s3_folder = json_response["orgS3Folder"]
        s3_folder = json_response["s3Folder"]
        filename = "result"
        s3_url = s3_url.format(
            orgS3Folder=org_s3_folder, s3Folder=s3_folder, filename=filename
        )
        response = httpx.get(s3_url).json()
        return [
            DiscoveryModel.model_validate(
                {"name": company["title"], "url": company["linkedinUrl"]}
            )
            for company in response
        ]

    def _launch_company_scraper(self, urls: list[str]) -> str | None:
        """Launch the company scraper."""
        payload = {
            "argument": {
                "companies": urls,
                "sessionCookie": self.cookie,
                "csvName": "companies",
            },
            "id": self.company_scraper,
        }
        headers = {"content-type": "application/json", "X-Phantombuster-Key": self.key}
        try:
            response = httpx.post(self.launch_url, json=payload, headers=headers)
            return str(response.json()["containerId"])
        except HTTPStatusError as e:
            msg = f"HTTP status error while launching company scraper: {e}"
            logger.error(msg)
            collect_errors("GENERAL", self.errors, CrawlingExternalError(msg))
            return None
        except Exception as e:
            msg = f"Generic exception while launching company scraper: {e}"
            logger.error(msg)
            collect_errors("GENERAL", self.errors, CrawlingExternalError(msg))
            return None

    def _wait_for_container(self, container_id: str) -> bool:
        """Wait for the container to finish."""
        container_fetch_url = self.container_fetch_url + "?id=" + container_id
        start_time = time.time()
        while time.time() - start_time < self.maximum_runtime_scraping_seconds:
            try:
                if self._is_container_finished(container_fetch_url):
                    return True
                else:
                    time.sleep(10)
            except HTTPStatusError as e:
                logger.error(
                    f"HTTP status error while getting container status: {e}"
                    f"Retrying in 20 seconds"
                )
                time.sleep(20)
            except httpx.TimeoutException:
                logger.warning(
                    "Timeout while getting container status. " "Retrying in 20 seconds"
                )
                time.sleep(20)
            except Exception as e:
                logger.error(
                    f"Generic exception while getting container status: {e}"
                    f"Retrying in 30 seconds"
                )
                time.sleep(30)

        msg = "Maximum runtime of 10 minutes reached " "while scraping companies!"
        logger.error(msg)
        collect_errors("GENERAL", self.errors, CrawlingExternalError(msg))
        return False

    def _is_container_finished(self, container_fetch_url: str) -> bool:
        """Check if the container is finished."""
        headers = {"content-type": "application/json", "X-Phantombuster-Key": self.key}
        response = httpx.get(container_fetch_url, headers=headers)
        response.raise_for_status()
        return (
            response.status_code == HTTP_200 and response.json()["status"] == "finished"
        )

    def _generate_s3_url(self, fetch_url: str) -> str:
        """Generate the S3 URL."""
        headers = {
            "accept": "application/json",
            "X-Phantombuster-Key": self.key,
        }
        response = httpx.get(fetch_url, headers=headers)
        json_response = response.json()
        s3_url_template = "https://phantombuster.s3.amazonaws.com/{orgS3Folder}/{s3Folder}/{filename}.json"
        return s3_url_template.format(
            orgS3Folder=json_response["orgS3Folder"],
            s3Folder=json_response["s3Folder"],
            filename="result",
        )

    def _collect_company_scraper_result(
        self, ids: list[str], errors: dict[str, ErrorInfoModel]
    ) -> list[CompanyModel]:
        """Collect the company scraper result."""
        fetch_url = self.fetch_url + "?id=" + self.company_scraper
        s3_url = self._generate_s3_url(fetch_url)

        try:
            response = httpx.get(s3_url, timeout=600)
            response.raise_for_status()
        except HTTPStatusError as e:
            msg = f"HTTP status error while getting company scraper result: {e}"
            logger.error(msg)
            collect_errors("GENERAL", errors, CrawlingExternalError(msg))
            return []
        except httpx.TimeoutException:
            msg = "Timeout while getting company scraper result!"
            logger.error(msg)
            collect_errors("GENERAL", errors, CrawlingExternalError(msg))
            return []
        except Exception as e:
            msg = f"Generic exception while getting company scraper result: {e}"
            logger.error(msg)
            collect_errors("GENERAL", errors, CrawlingExternalError(msg))
            return []

        output = response.json()
        if len(output) != len(ids):
            msg = "Mismatch in the number of companies in the input and output."
            logger.error(msg)
            collect_errors("GENERAL", errors, CrawlingError(msg))
            return []

        return self._process_company_data(output, ids, errors)

    def _extract_company_info(self, item: dict, company_id: str) -> dict:
        """Extract the company info from the item."""
        return {
            "id": company_id,
            "name": item["name"],
            "data_source": "linkedin",
            "link": item["companyUrl"],
            "location": item["location"] if "location" in item else "",
            "industry": item["industry"] if "industry" in item else "",
            "industry_code": item["industryCode"] if "industryCode" in item else "",
            "description": item["description"] if "description" in item else "",
            "website": item["website"] if "website" in item else "",
            "phone": item["phone"] if "phone" in item else "",
            "specialities": item["specialties"] if "specialties" in item else "",
            "size": item["companySize"] if "companySize" in item else "",
            "logo": item["logo"] if "logo" in item else "",
            "founded": item["founded"] if "founded" in item else "",
            "follower_count": item["followerCount"] if "followerCount" in item else "",
            "employee_count": item["employeesOnLinkedIn"]
            if "employeesOnLinkedIn" in item
            else "",
            "sales_navigator_link": item["salesNavigatorLink"]
            if "salesNavigatorLink" in item
            else "",
            "banner": item["banner"] if "banner" in item else "",
            "domain": item["domain"] if "domain" in item else "",
            "address": item["companyAddress"] if "companyAddress" in item else "",
            "headquarters": item["headquarters"] if "headquarters" in item else "",
            "timestamp": item["timestamp"],
            "query": item["query"] if "query" in item else "",
            "company_id": item["mainCompanyID"] if "mainCompanyID" in item else "",
            "linkedin_id": item["linkedinID"] if "linkedinID" in item else "",
        }

    def _process_company_data(
        self, output: list, ids: list[str], errors: dict[str, ErrorInfoModel]
    ) -> list[CompanyModel]:
        """Process the company data."""
        result = []
        for item in output:
            try:
                company = CompanyModel.model_validate(
                    self._extract_company_info(item, ids[output.index(item)])
                )
                result.append(company)
            except ValidationError as e:
                msg = f"Validation error for company {item['name']}: {e}"
                logger.error(msg)
                collect_errors(item["name"], errors, CrawlingError(msg))
            except Exception as e:
                msg = f"Unexpected error for company {item['name']}: {e}"
                logger.error(msg)
                collect_errors(item["name"], errors, CrawlingError(msg))
        return result

    def scrape_company(self, urls: list[str], ids: list[str]) -> list[CompanyModel]:
        """Scrape a company for details."""
        try:
            container_id: str | None = self._launch_company_scraper(urls)
            if not container_id:
                return []

            if not self._wait_for_container(container_id):
                return []

            return self._collect_company_scraper_result(ids, self.errors)
        except Exception as e:
            msg = (
                f"An unexpected error occurred while scraping companies for "
                f"urls: {urls}, "
                f"ids: {ids}, "
                f"Exception: {e}"
            )
            logger.error(msg)
            collect_errors("GENERAL", self.errors, CrawlingError(msg))
            return []
