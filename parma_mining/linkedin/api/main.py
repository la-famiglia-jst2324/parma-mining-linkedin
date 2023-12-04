"""Main entrypoint for the API routes in of parma-analytics."""
from fastapi import FastAPI, status
from parma_mining.linkedin.model import CompanyModel
from parma_mining.linkedin.pb_client import PhantombusterClient

app = FastAPI()

pb_client = PhantombusterClient()


# root endpoint
@app.get("/", status_code=200)
def root():
    """Root endpoint for the API."""
    return {"welcome": "at parma-mining-linkedin"}


# endpoint for collecting results
@app.get("/get_company_info", status_code=status.HTTP_200_OK)
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
