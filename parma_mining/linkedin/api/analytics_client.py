# The duty of this file is to make necessary calls to Analytics API
import httpx


class AnalyticsClient:
    measurement_url = "http://localhost:8000/source-measurement"  # local host for now, must be changed

    def send_post_request(self, data):
        api_endpoint = self.measurement_url
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_TOKEN",
        }
        response = httpx.post(api_endpoint, json=data, headers=headers)

        if response.status_code == 201:
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

            print(measurement_data)

            measurement_data["id"] = self.send_post_request(measurement_data)

            if "NestedMappings" in field_mapping:
                nested_measurements = self.register_measurements(
                    {"Mappings": field_mapping["NestedMappings"]},
                    parent_id=measurement_data["id"],
                    source_module_id=source_module_id,
                )
                result.extend(nested_measurements)

            result.append(measurement_data)

        return result
