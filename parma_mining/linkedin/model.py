"""Data models for the LinkedIn module.

This module contains the data models for the LinkedIn module.
"""
import json

from pydantic import BaseModel


class CompanyModel(BaseModel):
    """Data model for a company."""

    id: str
    name: str
    data_source: str
    link: str
    location: str
    industry: str
    industry_code: str
    description: str
    website: str
    phone: str
    specialities: str
    size: str
    logo: str
    banner: str
    domain: str
    address: str
    headquarters: str
    founded: str
    follower_count: int
    employee_count: int
    company_id: int
    linkedin_id: str
    sales_navigator_link: str
    query: str
    timestamp: str

    def updated_model_dump(self) -> str:
        """Dump the CompanyModel instance to a JSON string."""
        # Convert other objects to string representation
        json_serializable_dict = self.model_dump()
        return json.dumps(json_serializable_dict, default=str)


class DiscoveryModel(BaseModel):
    """Data model for a company discovery."""

    name: str | None
    url: str | None


class CompaniesRequest(BaseModel):
    """Data model for a company request."""

    companies: dict[str, dict[str, list[str]]]
