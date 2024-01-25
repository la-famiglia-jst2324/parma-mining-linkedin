"""Data models for the LinkedIn module.

This module contains the data models for the LinkedIn module.
"""
import json
from datetime import datetime

from pydantic import BaseModel


class CompanyModel(BaseModel):
    """Data model for a company."""

    linkedin_id: str | None = None
    name: str | None = None
    profile_url: str | None = None
    ads_rule: str | None = None
    employee_count: int | None = None
    active: bool | None = None
    job_search_url: str | None = None
    phone: str | None = None
    tagline: str | None = None
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    follower_count: int | None = None
    universal_name: str | None = None
    headquarter_city: str | None = None
    headquarter_country: str | None = None
    head_quarter_postal_code: str | None = None
    industries: list[str] | None = None
    specialities: list[str] | None = None
    hashtags: list[str] | None = None
    locations: list[str] | None = None
    founded_year: int | None = None
    founded_month: int | None = None
    founded_day: int | None = None

    def updated_model_dump(self) -> str:
        """Dump the CompanyModel instance to a JSON string."""
        # Convert other objects to string representation
        json_serializable_dict = self.model_dump()
        return json.dumps(json_serializable_dict, default=str)


class DiscoveryRequest(BaseModel):
    """Request model for the discovery endpoint."""

    company_id: str
    name: str


class DiscoveryResponse(BaseModel):
    """Define the output model for the discovery endpoint."""

    urls: list[str] = []


class FinalDiscoveryResponse(BaseModel):
    """Define the final discovery response model."""

    identifiers: dict[str, DiscoveryResponse]
    validity: datetime


class CompaniesRequest(BaseModel):
    """Data model for a company request."""

    task_id: int
    companies: dict[str, dict[str, list[str]]]


class ResponseModel(BaseModel):
    """Response model for Crunchbase data."""

    source_name: str
    company_id: str
    raw_data: CompanyModel


class ErrorInfoModel(BaseModel):
    """Error info for the crawling_finished endpoint."""

    error_type: str
    error_description: str | None


class CrawlingFinishedInputModel(BaseModel):
    """Internal base model for the crawling_finished endpoints."""

    task_id: int
    errors: dict[str, ErrorInfoModel] | None = None
