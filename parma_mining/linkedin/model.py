from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class CompanyModel(BaseModel):
    name: str
    data_source: str
    link: str
    location: str
    industry: str
    industry_code: str
    description: str
    website: str
    phone: str  # indicate optional
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
