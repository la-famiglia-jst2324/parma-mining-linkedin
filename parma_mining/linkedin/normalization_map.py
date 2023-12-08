# This class represents our normalization map, will be used at initialization endpoint
class LinkedinNormalizationMap:
    map_json = {
        "Source": "Linkedin",
        "Mappings": [
            {
                "SourceField": "name",
                "DataType": "text",
                "MeasurementName": "company name",
            },
            {
                "SourceField": "link",
                "DataType": "link",
                "MeasurementName": "linkedin url of company",
            },
            {
                "SourceField": "location",
                "DataType": "text",
                "MeasurementName": "location of company",
            },
            {
                "SourceField": "industry",
                "DataType": "text",
                "MeasurementName": "company industry",
            },
            {
                "SourceField": "industry_code",
                "DataType": "tex",
                "MeasurementName": "company industry code",
            },
            {
                "SourceField": "description",
                "DataType": "text",
                "MeasurementName": "company description",
            },
            {
                "SourceField": "website",
                "DataType": "link",
                "MeasurementName": "company website link",
            },
            {
                "SourceField": "phone",
                "DataType": "text",
                "MeasurementName": "company phone number",
            },
            {
                "SourceField": "specialities",
                "DataType": "text",
                "MeasurementName": "company specialities",
            },
            {
                "SourceField": "size",
                "DataType": "text",
                "MeasurementName": "company size",
            },
            {
                "SourceField": "logo",
                "DataType": "link",
                "MeasurementName": "url of company logo",
            },
            {
                "SourceField": "banner",
                "DataType": "link",
                "MeasurementName": "banner url",
            },
            {
                "SourceField": "domain",
                "DataType": "link",
                "MeasurementName": "company domain",
            },
            {
                "SourceField": "address",
                "DataType": "text",
                "MeasurementName": "company address",
            },
            {
                "SourceField": "headquarters",
                "DataType": "text",
                "MeasurementName": "company headquarters",
            },
            {
                "SourceField": "founded",
                "DataType": "date",
                "MeasurementName": "date of foundation",
            },
            {
                "SourceField": "follower_count",
                "DataType": "int",
                "MeasurementName": "number of followers",
            },
            {
                "SourceField": "employee_count",
                "DataType": "int",
                "MeasurementName": "number of employees",
            },
            {
                "SourceField": "company_id",
                "DataType": "int",
                "MeasurementName": "company id",
            },
            {
                "SourceField": "linkedin_id",
                "DataType": "int",
                "MeasurementName": "company linkedin id",
            },
            {
                "SourceField": "sales_navigator_link",
                "DataType": "link",
                "MeasurementName": "url of sales navigator",
            },
            {
                "SourceField": "query",
                "DataType": "text",
                "MeasurementName": "search query",
            },
            {
                "SourceField": "timestamp",
                "DataType": "date",
                "MeasurementName": "timestamp of call",
            },
        ],
    }

    def get_normalization_map(self):
        return self.map_json
