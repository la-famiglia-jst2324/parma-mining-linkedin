"""Main entrypoint for the API routes in of parma-analytics."""
import json
import logging
import os

from fastapi import Depends, FastAPI, HTTPException, status

from parma_mining.linkedin.api.analytics_client import AnalyticsClient
from parma_mining.linkedin.api.dependencies.auth import authenticate
from parma_mining.linkedin.model import CompaniesRequest, CompanyModel, DiscoveryModel
from parma_mining.linkedin.normalization_map import LinkedinNormalizationMap
from parma_mining.linkedin.pb_client import PhantombusterClient

env = os.getenv("DEPLOYMENT_ENV", "local")

if env == "prod":
    logging.basicConfig(level=logging.INFO)
elif env in ["staging", "local"]:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.warning(f"Unknown environment '{env}'. Defaulting to INFO level.")
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


app = FastAPI()

pb_client = PhantombusterClient()
analytics_client = AnalyticsClient()
normalization = LinkedinNormalizationMap()


@app.get("/", status_code=status.HTTP_200_OK)
def root():
    """Root endpoint for the API."""
    logger.debug("Root endpoint called")
    return {"welcome": "at parma-mining-linkedin"}


@app.get("/initialize", status_code=200)
def initialize(source_id: int, token: str = Depends(authenticate)) -> str:
    """Initialization endpoint for the API."""
    # init frequency
    time = "weekly"
    normalization_map = normalization.get_normalization_map()
    # register the measurements to analytics
    normalization_map = analytics_client.register_measurements(
        token, normalization_map, source_module_id=source_id
    )[1]

    # set and return results
    results = {}
    results["frequency"] = time
    results["normalization_map"] = str(normalization_map)
    return json.dumps(results)


# endpoint for collecting results
@app.post(
    "/companies",
    response_model=list[CompanyModel],
    status_code=status.HTTP_200_OK,
)
def get_company_info(
    companies: CompaniesRequest, token: str = Depends(authenticate)
) -> list[CompanyModel]:
    """Company details endpoint for the API."""
    company_urls = []
    company_ids = []
    for company in companies.companies:
        # iterate all input items and find a linkedin url
        url_exist = False
        for field in companies.companies[company]:
            for url in companies.companies[company][field]:
                if "linkedin.com/" in url:
                    url_exist = True
                    company_urls.append(url)
                    company_ids.append(company)
                    break
        if not url_exist:
            logger.error("No linkedin url found for the company")
            raise Exception("No linkedin url found for the company")
    # launch the company scraper agent
    logger.debug(company_urls)
    company_details = pb_client.scrape_company(company_urls, company_ids)
    for company in company_details:
        try:
            analytics_client.feed_raw_data(token, company)
        except HTTPException as e:
            logger.error(f"Can't send crawling data to the Analytics. Error: {e}")
            raise HTTPException(
                f"Can't send crawling data to the Analytics. Error: {e}"
            )
    return company_details


# endpoint for launching the company scraper agent
@app.get(
    "/discover",
    response_model=list[DiscoveryModel],
    status_code=status.HTTP_200_OK,
)
def discover(query: str, token: str = Depends(authenticate)):
    """Discovery endpoint for the API."""
    try:
        response = pb_client.discover_company(query)
    except HTTPException as e:
        logger.error(f"Can't run discovery agent successfully. Error: {e}")
        raise HTTPException(f"Can't run discovery agent successfully. Error: {e}")
    return response
