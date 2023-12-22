# The duty of this file is to make necessary calls to Analytics API
import json
import os
import urllib.parse

import httpx
from dotenv import load_dotenv

from parma_mining.linkedin.model import CompanyModel
from parma_mining.mining_common.const import HTTP_201, HTTP_404


class AnalyticsClient:
    load_dotenv()
    analytics_base = str(os.getenv("ANALYTICS_BASE_URL") or "")

    measurement_url = urllib.parse.urljoin(analytics_base, "/source-measurement")
    feed_raw_url = urllib.parse.urljoin(analytics_base, "/feed-raw-data")

    def send_post_request(self, data):
        api_endpoint = self.measurement_url
        headers = {
            "Content-Type": "application/json",
        }
        response = httpx.post(api_endpoint, json=data, headers=headers)

        if response.status_code == HTTP_201:
            return response.json().get("id")
        else:
            raise Exception(
                f"API request failed with status code {response.status_code}"
            )

    def register_measurements(self, mapping, parent_id=None, source_module_id=None):
        result = []
        for field_mapping in mapping["Mappings"]:
            measurement_data = {
                "source_module_id": source_module_id,
                "type": field_mapping["DataType"],
                "measurement_name": field_mapping["MeasurementName"],
            }

            if parent_id is not None:
                measurement_data["parent_measurement_id"] = parent_id

            measurement_data["source_measurement_id"] = self.send_post_request(
                measurement_data
            )

            # add the source measurement id to mapping
            field_mapping["source_measurement_id"] = measurement_data[
                "source_measurement_id"
            ]

            if "NestedMappings" in field_mapping:
                nested_measurements = self.register_measurements(
                    {"Mappings": field_mapping["NestedMappings"]},
                    parent_id=measurement_data["source_measurement_id"],
                    source_module_id=source_module_id,
                )[0]
                result.extend(nested_measurements)
            result.append(measurement_data)
        return result, mapping

    def feed_raw_data(self, company: CompanyModel):
        api_endpoint = self.feed_raw_url
        headers = {
            "Content-Type": "application/json",
        }
        # make the company model json serializable
        raw_data = json.loads(company.updated_model_dump())
        data = {
            "source_name": str(company.data_source),
            "company_id": str(company.id),
            "raw_data": raw_data,
        }

        response = httpx.post(api_endpoint, json=data, headers=headers)

        if response.status_code == HTTP_201:
            return response.json()
        elif response.status_code == HTTP_404:
            pass
        else:
            raise Exception(
                f"API request is failed with status code {response.status_code}"
            )
