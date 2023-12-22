"""Module for communicating with the Phantombuster API.

This module communicates with the Phantombuster API to discover and scrape
"""
import os
import time

import httpx
from dotenv import load_dotenv

from parma_mining.linkedin.model import CompanyModel, DiscoveryModel
from parma_mining.mining_common.const import HTTP_200


class PhantombusterClient:
    """Class for communicating with the Phantombuster API."""

    def __init__(self):
        """Initialize the PhantombusterClient class."""
        load_dotenv()
        self.launch_url = str(os.getenv("PHANTOMBUSTER_API_LAUNCH_ENDPOINT") or "")
        self.fetch_url = str(os.getenv("PHANTOMBUSTER_API_FETCH_ENDPOINT") or "")
        self.container_fetch_url = str(os.getenv("CONTAINER_FETCH_ENDPOINT") or "")
        self.key = str(os.getenv("PHANTOMBUSTER_API_KEY") or "")
        self.company_scraper = str(os.getenv("COMPANY_SCRAPER_AGENT_ID") or "")
        self.discovery = str(os.getenv("DISCOVERY_AGENT_ID") or "")
        self.cookie = str(os.getenv("LINKEDIN_SESSION_COOKIE") or "")

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

    def scrape_company(self, urls: list[str], ids: list[str]) -> list[CompanyModel]:
        """Scrape a company for details."""
        payload = {
            "argument": {
                "companies": urls,
                "sessionCookie": self.cookie,
                "csvName": "companies",
            },
            "id": self.company_scraper,
        }
        headers = {"content-type": "application/json", "X-Phantombuster-Key": self.key}
        response = httpx.post(self.launch_url, json=payload, headers=headers)

        # get details of the container
        container_id = str(response.json()["containerId"])
        container_fetch_url = self.container_fetch_url + "?id=" + container_id
        # Check the status of the container if it is done, go ahead, if it is
        # not wait for 10 seconds and check again
        while True:
            response = httpx.get(container_fetch_url, headers=headers)
            if response.status_code == HTTP_200:
                if response.json()["status"] == "finished":
                    break
            time.sleep(10)

        return self.collect_result(ids)

    def collect_result(self, ids: list[str]) -> list[CompanyModel]:
        """Collect the result of the company scraper agent."""
        fetch_url = self.fetch_url + "?id=" + self.company_scraper

        s3_url = "https://phantombuster.s3.amazonaws.com/{orgS3Folder}/{s3Folder}/{filename}.json"
        headers = {
            "accept": "application/json",
            "X-Phantombuster-Key": self.key,
        }

        response = httpx.get(fetch_url, headers=headers)

        json_response = response.json()  # convert to json
        org_s3_folder = json_response["orgS3Folder"]
        s3_folder = json_response["s3Folder"]
        filename = "companies"

        s3_url = s3_url.format(
            orgS3Folder=org_s3_folder, s3Folder=s3_folder, filename=filename
        )
        response = httpx.get(s3_url)
        output = response.json()
        result = []
        if len(output) != len(ids):
            raise Exception(
                "Company coun in the output is not equal to company count in the input"
            )
        for item in output:
            company = CompanyModel.model_validate(
                {
                    "id": ids[output.index(item)],
                    "name": item["name"],
                    "data_source": "linkedin",
                    "link": item["companyUrl"],
                    "location": item["location"] if "location" in item else "",
                    "industry": item["industry"] if "industry" in item else "",
                    "industry_code": item["industryCode"]
                    if "industryCode" in item
                    else "",
                    "description": item["description"] if "description" in item else "",
                    "website": item["website"] if "website" in item else "",
                    "phone": item["phone"] if "phone" in item else "",
                    "specialities": item["specialties"]
                    if "specialties" in item
                    else "",
                    "size": item["companySize"] if "companySize" in item else "",
                    "logo": item["logo"] if "logo" in item else "",
                    "founded": item["founded"] if "founded" in item else "",
                    "follower_count": item["followerCount"]
                    if "followerCount" in item
                    else "",
                    "employee_count": item["employeesOnLinkedIn"]
                    if "employeesOnLinkedIn" in item
                    else "",
                    "sales_navigator_link": item["salesNavigatorLink"]
                    if "salesNavigatorLink" in item
                    else "",
                    "banner": item["banner"] if "banner" in item else "",
                    "domain": item["domain"] if "domain" in item else "",
                    "address": item["companyAddress"]
                    if "companyAddress" in item
                    else "",
                    "headquarters": item["headquarters"]
                    if "headquarters" in item
                    else "",
                    "timestamp": item["timestamp"],
                    "query": item["query"] if "query" in item else "",
                    "company_id": item["mainCompanyID"]
                    if "mainCompanyID" in item
                    else "",
                    "linkedin_id": item["linkedinID"] if "linkedinID" in item else "",
                }
            )
            result.append(company)
        return result
