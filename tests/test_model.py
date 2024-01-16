import json

import pytest

from parma_mining.linkedin.model import CompanyModel


@pytest.fixture
def company_data():
    return {
        "id": "123",
        "name": "Test Company",
        "data_source": "Test Source",
        "link": "http://testcompany.com",
        "location": "Test Location",
        "industry": "Test Industry",
        "industry_code": "12345",
        "description": "Test Description",
        "website": "http://testcompany.com",
        "phone": "123-456-7890",
        "specialities": "Testing",
        "size": "100-200",
        "logo": "http://testcompany.com/logo.png",
        "banner": "http://testcompany.com/banner.png",
        "domain": "testcompany.com",
        "address": "123 Test St",
        "headquarters": "Test City",
        "founded": "2000",
        "follower_count": 1000,
        "employee_count": 200,
        "company_id": 1,
        "linkedin_id": "linkedin-test-id",
        "sales_navigator_link": "http://salesnavigator.testcompany.com",
        "query": "Test Query",
        "timestamp": "2023-01-01T00:00:00",
    }


def test_updated_model_dump(company_data):
    company_model = CompanyModel(**company_data)
    dumped_json = company_model.updated_model_dump()

    dumped_dict = json.loads(dumped_json)

    for key, value in company_data.items():
        if isinstance(value, int | float | bool):
            assert dumped_dict[key] == value
        else:
            assert dumped_dict[key] == str(value)
