from backend.blocks.hubspot._auth import (
    HubSpotCredentials,
    HubSpotCredentialsField,
    HubSpotCredentialsInput,
)
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
from backend.util.request import requests


class HubSpotCompanyBlock(Block):
    class Input(BlockSchema):
        credentials: HubSpotCredentialsInput = HubSpotCredentialsField()
        operation: str = SchemaField(
            description="Yapılacak işlem (create, update, get)", default="get"
        )
        company_data: dict = SchemaField(
            description="Oluşturma/güncelleme işlemleri için şirket verileri", default={}
        )
        domain: str = SchemaField(
            description="Getirme/güncelleme işlemleri için şirket domaini", default=""
        )

    class Output(BlockSchema):
        company: dict = SchemaField(description="Şirket bilgisi")
        status: str = SchemaField(description="İşlem durumu")

    def __init__(self):
        super().__init__(
            id="3ae02219-d540-47cd-9c78-3ad6c7d9820a",
            description="HubSpot şirketlerini yönetir - şirket bilgilerini oluşturur, günceller ve getirir",
            categories={BlockCategory.CRM},
            input_schema=HubSpotCompanyBlock.Input,
            output_schema=HubSpotCompanyBlock.Output,
        )

    def run(
        self, input_data: Input, *, credentials: HubSpotCredentials, **kwargs
    ) -> BlockOutput:
        base_url = "https://api.hubapi.com/crm/v3/objects/companies"
        headers = {
            "Authorization": f"Bearer {credentials.api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

        if input_data.operation == "create":
            response = requests.post(
                base_url, headers=headers, json={"properties": input_data.company_data}
            )
            result = response.json()
            yield "company", result
            yield "status", "created"

        elif input_data.operation == "get":
            search_url = f"{base_url}/search"
            search_data = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "domain",
                                "operator": "EQ",
                                "value": input_data.domain,
                            }
                        ]
                    }
                ]
            }
            response = requests.post(search_url, headers=headers, json=search_data)
            result = response.json()
            yield "company", result.get("results", [{}])[0]
            yield "status", "retrieved"

        elif input_data.operation == "update":
            # Önce domain ile şirket ID'sini al
            search_response = requests.post(
                f"{base_url}/search",
                headers=headers,
                json={
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "domain",
                                    "operator": "EQ",
                                    "value": input_data.domain,
                                }
                            ]
                        }
                    ]
                },
            )
            company_id = search_response.json().get("results", [{}])[0].get("id")

            if company_id:
                response = requests.patch(
                    f"{base_url}/{company_id}",
                    headers=headers,
                    json={"properties": input_data.company_data},
                )
                result = response.json()
                yield "company", result
                yield "status", "updated"
            else:
                yield "company", {}
                yield "status", "company_not_found"
