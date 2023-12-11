"""Main entrypoint for the API routes in of parma-analytics."""
from fastapi import FastAPI, status
from parma_mining.linkedin.model import CompanyModel
from parma_mining.linkedin.pb_client import PhantombusterClient
from parma_mining.linkedin.api.analytics_client import AnalyticsClient
import json

app = FastAPI()
source_id = (
    "1"  # for now, we must define different module ids for different modules, formally
)
pb_client = PhantombusterClient()
analytics_client = AnalyticsClient()


# root endpoint
@app.get("/", status_code=200)
def root():
    """Root endpoint for the API."""
    return {"welcome": "at parma-mining-linkedin"}


# initialization endpoint
@app.get("/initialize", status_code=200)
def initialize() -> str:
    """Initialization endpoint for the API."""
    # init frequency
    time = "weekly"
    normalization_map = pb_client.initialize_normalization_map()
    # register the measurements to analytics
    analytics_client.register_measurements(
        normalization_map, source_module_id=source_id
    )

    # set and return results
    results = {}
    results["frequency"] = time
    results["normalization_map"] = str(normalization_map)
    return json.dumps(results)


# endpoint for collecting results
@app.get("/companies", status_code=status.HTTP_200_OK)
def get_company_info() -> list[CompanyModel]:
    results = pb_client.collect_result()
    return results


# endpoint for launching the url finder agent
@app.get("/launch_url_finder", status_code=status.HTTP_200_OK)
def launch_url_finder() -> str:
    response = pb_client.launch_url_finder()
    return response


# endpoint for launching the company scraper agent
@app.get("/launch_company_scraper", status_code=status.HTTP_200_OK)
def launch_company_scraper() -> str:
    response = pb_client.launch_company_scraper()
    return response
