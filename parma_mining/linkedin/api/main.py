"""Main entrypoint for the API routes in of parma-analytics."""
import json
import logging
import os
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, status

from parma_mining.linkedin.analytics_client import AnalyticsClient
from parma_mining.linkedin.api.dependencies.auth import authenticate
from parma_mining.linkedin.client import LinkedinClient
from parma_mining.linkedin.model import (
    CompaniesRequest,
    CrawlingFinishedInputModel,
    DiscoveryRequest,
    ErrorInfoModel,
    FinalDiscoveryResponse,
    ResponseModel,
)
from parma_mining.linkedin.normalization_map import LinkedinNormalizationMap
from parma_mining.mining_common.exceptions import (
    AnalyticsError,
    ClientInvalidBodyError,
    CrawlingError,
)
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
linkedin_client = LinkedinClient()


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
    status_code=status.HTTP_200_OK,
)
def get_company_info(body: CompaniesRequest, token: str = Depends(authenticate)):
    """Endpoint to get detailed information about a dict of organizations."""
    errors: dict[str, ErrorInfoModel] = {}
    for company_id, company_data in body.companies.items():
        for data_type, handles in company_data.items():
            for handle in handles:
                if data_type == "urls":
                    try:
                        if "linkedin.com/" in handle:
                            org_details = linkedin_client.get_company_details([handle])
                        else:
                            logger.error(f"Not a valid Linkedin url: {handle}")
                    except CrawlingError as e:
                        logger.error(
                            f"Can't fetch company details from Linkedin Error: {e}"
                        )
                        collect_errors(company_id, errors, e)
                        continue

                    data = ResponseModel(
                        source_name="linkedin",
                        company_id=company_id,
                        raw_data=org_details,
                    )
                    # Write data to db via endpoint in analytics backend
                    try:
                        analytics_client.feed_raw_data(token, data)
                    except AnalyticsError as e:
                        logger.error(
                            f"Can't send crawling data to the Analytics. Error: {e}"
                        )
                        collect_errors(company_id, errors, e)

                else:
                    msg = f"Unsupported type error for {data_type} in {handle}"
                    logger.error(msg)
                    collect_errors(company_id, errors, ClientInvalidBodyError(msg))

    return analytics_client.crawling_finished(
        token,
        json.loads(
            CrawlingFinishedInputModel(
                task_id=body.task_id, errors=errors
            ).model_dump_json()
        ),
    )


@app.post(
    "/discover",
    response_model=FinalDiscoveryResponse,
    status_code=status.HTTP_200_OK,
)
def discover_companies(
    request: list[DiscoveryRequest], token: str = Depends(authenticate)
):
    """Endpoint to discover organizations based on provided names."""
    if not request:
        msg = "Request body cannot be empty for discovery"
        logger.error(msg)
        raise ClientInvalidBodyError(msg)

    response_data = {}
    for company in request:
        logger.debug(
            f"Discovering with name: {company.name} for company_id {company.company_id}"
        )
        response = linkedin_client.discover_company(company.name)
        response_data[company.company_id] = response

    current_date = datetime.now()
    valid_until = current_date + timedelta(days=180)

    return FinalDiscoveryResponse(identifiers=response_data, validity=valid_until)
