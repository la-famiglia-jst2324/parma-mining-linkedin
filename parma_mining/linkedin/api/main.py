"""Main entrypoint for the API routes in of parma-analytics."""
from fastapi import FastAPI, HTTPException, status
from typing import List
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
def get_company_info() -> list:
    results = pb_client.collect_result()
    return results


# endpoint for launching the url finder agent
# TODO: implement


# endpoint for launching the company scraper agent
# TODO: implement


# endpoint for adding companies to company name list
# TODO: implement
