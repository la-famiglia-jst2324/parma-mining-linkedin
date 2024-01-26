"""Module for normalization map.

This module contains the normalization map for the Linkedin module.
"""


class LinkedinNormalizationMap:
    """Class for normalization map."""

    map_json = {
        "Source": "linkedin",
        "Mappings": [
            {
                "SourceField": "name",
                "DataType": "text",
                "MeasurementName": "company name",
            },
            {
                "SourceField": "linkedin_id",
                "DataType": "text",
                "MeasurementName": "linkedin id of company",
            },
            {
                "SourceField": "profile_url",
                "DataType": "link",
                "MeasurementName": "linkedin profile url",
            },
            {
                "SourceField": "ads_rule",
                "DataType": "text",
                "MeasurementName": "advertisement rule for company",
            },
            {
                "SourceField": "employee_count",
                "DataType": "int",
                "MeasurementName": "number of employees in company",
            },
            {
                "SourceField": "active",
                "DataType": "bool",
                "MeasurementName": "is company active",
            },
            {
                "SourceField": "job_search_url",
                "DataType": "link",
                "MeasurementName": "url for job search",
            },
            {
                "SourceField": "phone",
                "DataType": "text",
                "MeasurementName": "phone number of company",
            },
            {
                "SourceField": "tagline",
                "DataType": "text",
                "MeasurementName": "tagline of company",
            },
            {
                "SourceField": "description",
                "DataType": "text",
                "MeasurementName": "description of company",
            },
            {
                "SourceField": "website",
                "DataType": "link",
                "MeasurementName": "website of company",
            },
            {
                "SourceField": "logo_url",
                "DataType": "link",
                "MeasurementName": "logo url of company",
            },
            {
                "SourceField": "follower_count",
                "DataType": "int",
                "MeasurementName": "number of followers of company",
            },
            {
                "SourceField": "universal_name",
                "DataType": "text",
                "MeasurementName": "universal name of company",
            },
            {
                "SourceField": "headquarter_city",
                "DataType": "text",
                "MeasurementName": "headquarter city of company",
            },
            {
                "SourceField": "headquarter_country",
                "DataType": "text",
                "MeasurementName": "headquarter country of company",
            },
            {
                "SourceField": "head_quarter_postal_code",
                "DataType": "text",
                "MeasurementName": "headquarter postal code of company",
            },
            {
                "SourceField": "industries",
                "DataType": "text",
                "MeasurementName": "industries of company",
            },
            {
                "SourceField": "locations",
                "DataType": "text",
                "MeasurementName": "locations of company",
            },
            {
                "SourceField": "specialities",
                "DataType": "text",
                "MeasurementName": "specialities of company",
            },
            {
                "SourceField": "hashtags",
                "DataType": "text",
                "MeasurementName": "hashtags of company",
            },
            {
                "SourceField": "founded_year",
                "DataType": "int",
                "MeasurementName": "founded year of company",
            },
            {
                "SourceField": "founded_month",
                "DataType": "int",
                "MeasurementName": "founded month of company",
            },
            {
                "SourceField": "founded_day",
                "DataType": "int",
                "MeasurementName": "founded day of company",
            },
        ],
    }

    def get_normalization_map(self) -> dict:
        """Return the normalization map."""
        return self.map_json
