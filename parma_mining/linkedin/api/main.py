"""Main entrypoint for the API routes in of parma-analytics."""
import json
import logging
import os

from fastapi import Depends, FastAPI, HTTPException, status

from parma_mining.linkedin.api.analytics_client import AnalyticsClient
from parma_mining.linkedin.api.dependencies.auth import authenticate
from parma_mining.linkedin.model import (
    CompaniesRequest,
    CompanyModel,
    CrawlingFinishedInputModel,
    DiscoveryModel,
    ErrorInfoModel,
)
from parma_mining.linkedin.normalization_map import LinkedinNormalizationMap
from parma_mining.linkedin.pb_client import PhantombusterClient
from parma_mining.mining_common.exceptions import ClientInvalidBodyError
from parma_mining.mining_common.helper import collect_errors

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


@app.post(
    "/companies",
    response_model=list[CompanyModel],
    status_code=status.HTTP_200_OK,
)
def get_company_info(
    body: CompaniesRequest, token: str = Depends(authenticate)
) -> list[CompanyModel]:
    """Company details endpoint for the API."""
    task_id: int = body.task_id
    errors: dict[str, ErrorInfoModel] = {}
    pb_client = PhantombusterClient(errors)

    company_urls = []
    company_ids = []

    for company_id, company_data in body.companies.items():
        # iterate all input items and find a LinkedIn url
        url_exist = False
        for data_type, handles in company_data.items():
            for handle in handles:
                if "linkedin.com/" in handle:
                    url_exist = True
                    company_urls.append(handle)
                    company_ids.append(company_id)
                    break
        if not url_exist:
            msg = (
                f"No linkedin url found for "
                f"task_id: {task_id} and company_id: {company_id}"
            )
            logger.error(msg)
            e = ClientInvalidBodyError(msg)
            collect_errors(company_id, errors, e)

    logger.debug(
        f"Launching the company scraper agent with "
        f"task_id: {task_id}, "
        f"company_urls: {company_urls}, "
        f"company_ids: {company_ids}, "
        f"error: {errors}"
    )

    # launch the company scraper agent
    company_details: list[CompanyModel] = pb_client.scrape_company(
        company_urls, company_ids
    )
    for company in company_details:
        try:
            analytics_client.feed_raw_data(token, company)
        except HTTPException as e:
            msg = f"Can't send crawling data to the Analytics. Error: {str(e)}"
            logger.error(msg)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)

    return analytics_client.crawling_finished(
        token,
        json.loads(
            CrawlingFinishedInputModel(task_id=task_id, errors=errors).model_dump_json()
        ),
    )


@app.get(
    "/discover",
    response_model=list[DiscoveryModel],
    status_code=status.HTTP_200_OK,
)
def discover(query: str, token: str = Depends(authenticate)):
    """Discovery endpoint for the API."""
    errors: dict[str, ErrorInfoModel] = {}
    pb_client = PhantombusterClient(errors)
    try:
        response = pb_client.discover_company(query)
    except HTTPException as e:
        logger.error(f"Can't run discovery agent successfully. Error: {e}")
        raise HTTPException(f"Can't run discovery agent successfully. Error: {e}")
    return response
