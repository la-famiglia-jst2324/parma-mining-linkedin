import os
import httpx
from dotenv import load_dotenv
import json
from parma_mining.linkedin.model import CompanyModel


class PhantombusterClient:
    def __init__(self):
        load_dotenv()
        self.launch_url = os.getenv("PHANTOMBUSTER_API_LAUNCH_ENDPOINT")
        self.fetch_url = os.getenv("PHANTOMBUSTER_API_FETCH_ENDPOINT")
        self.key = os.getenv("PHANTOMBUSTER_API_KEY")
        self.company_scraper = os.getenv("COMPANY_SCRAPER_AGENT_ID")
        self.url_finder = os.getenv("URL_FINDER_AGENT_ID")
        self.linkedin_session = None

    def launch_url_finder(self):
        payload = {"id": self.url_finder}
        headers = {"content-type": "application/json", "X-Phantombuster-Key": self.key}
        response = httpx.post(self.launch_url, json=payload, headers=headers)
        print(response.text)

    def launch_company_scraper(self):
        payload = {"id": self.company_scraper}
        headers = {"content-type": "application/json", "X-Phantombuster-Key": self.key}
        response = httpx.post(self.launch_url, json=payload, headers=headers)
        print(response.text)

    def update_company_scraper(self):
        # TODO: implement
        pass

    def update_url_finder(self):
        # TODO: implement
        pass

    def collect_result(self) -> list[CompanyModel]:
        fetch_url = (
            "https://api.phantombuster.com/api/v2/agents/fetch"
            + "?id="
            + "1080851344440087"
        )  # precommit was complaining about using self.company_scraper and self fetch_url here so i directly used the link and id

        s3_url = "https://phantombuster.s3.amazonaws.com/{orgS3Folder}/{s3Folder}/{filename}.json"
        headers = {
            "accept": "application/json",
            "X-Phantombuster-Key": "MxriVo8BwOEfxhyFsL2sz1fr5qcwihcpNx5GSNmtm8Y",
        }
        response = httpx.get(fetch_url, headers=headers)

        org_s3_folder = json.loads(response.text)["orgS3Folder"]
        s3_folder = json.loads(response.text)["s3Folder"]
        filename = "company-details"

        s3_url = s3_url.format(
            orgS3Folder=org_s3_folder, s3Folder=s3_folder, filename=filename
        )
        response = httpx.get(s3_url)
        output = json.loads(response.text)
        result = []
        for item in output:
            company = CompanyModel.model_validate(
                {
                    "name": item["name"],
                    "data_source": "linkedin",
                    "link": item["companyUrl"],
                    "location": item["location"],
                    "industry": item["industry"],
                    "industry_code": item["industryCode"],
                    "description": item["description"],
                    "website": item["website"],
                    "phone": item["phone"] if "phone" in item else "",
                    "specialities": item["specialties"]
                    if "specialties" in item
                    else "",
                    "size": item["companySize"] if "companySize" in item else "",
                    "logo": item["logo"],
                    "founded": item["founded"] if "founded" in item else "",
                    "follower_count": item["followerCount"],
                    "employee_count": item["employeesOnLinkedIn"],
                    "sales_navigator_link": item["salesNavigatorLink"],
                    "banner": item["banner"],
                    "domain": item["domain"],
                    "address": item["companyAddress"],
                    "headquarters": item["headquarters"],
                    "timestamp": item["timestamp"],
                    "query": item["query"],
                    "company_id": item["mainCompanyID"],
                    "linkedin_id": item["linkedinID"],
                }
            )
            result.append(company)
        return result

    def update_linkedin_session(self):
        # TODO: implement
        pass
