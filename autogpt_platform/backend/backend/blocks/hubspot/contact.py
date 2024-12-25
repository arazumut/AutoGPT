from backend.blocks.hubspot._auth import (
    HubSpotCredentials,
    HubSpotCredentialsField,
    HubSpotCredentialsInput,
)
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
from backend.util.request import requests


class HubSpotContactBlock(Block):
    class Input(BlockSchema):
        credentials: HubSpotCredentialsInput = HubSpotCredentialsField()
        operation: str = SchemaField(
            description="Yapılacak işlem (create, update, get)", default="get"
        )
        contact_data: dict = SchemaField(
            description="Oluşturma/güncelleme işlemleri için iletişim verileri", default={}
        )
        email: str = SchemaField(
            description="Getirme/güncelleme işlemleri için e-posta adresi", default=""
        )

    class Output(BlockSchema):
        contact: dict = SchemaField(description="İletişim bilgileri")
        status: str = SchemaField(description="İşlem durumu")

    def __init__(self):
        super().__init__(
            id="5267326e-c4c1-4016-9f54-4e72ad02f813",
            description="HubSpot kişilerini yönetir - iletişim bilgilerini oluşturur, günceller ve getirir",
            categories={BlockCategory.CRM},
            input_schema=HubSpotContactBlock.Input,
            output_schema=HubSpotContactBlock.Output,
        )

    def run(
        self, input_data: Input, *, credentials: HubSpotCredentials, **kwargs
    ) -> BlockOutput:
        base_url = "https://api.hubapi.com/crm/v3/objects/contacts"
        headers = {
            "Authorization": f"Bearer {credentials.api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

        if input_data.operation == "create":
            response = requests.post(
                base_url, headers=headers, json={"properties": input_data.contact_data}
            )
            result = response.json()
            yield "contact", result
            yield "status", "created"

        elif input_data.operation == "get":
            # E-posta ile iletişim arama
            search_url = f"{base_url}/search"
            search_data = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": input_data.email,
                            }
                        ]
                    }
                ]
            }
            response = requests.post(search_url, headers=headers, json=search_data)
            result = response.json()
            yield "contact", result.get("results", [{}])[0]
            yield "status", "retrieved"

        elif input_data.operation == "update":
            search_response = requests.post(
                f"{base_url}/search",
                headers=headers,
                json={
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "email",
                                    "operator": "EQ",
                                    "value": input_data.email,
                                }
                            ]
                        }
                    ]
                },
            )
            contact_id = search_response.json().get("results", [{}])[0].get("id")

            if contact_id:
                response = requests.patch(
                    f"{base_url}/{contact_id}",
                    headers=headers,
                    json={"properties": input_data.contact_data},
                )
                result = response.json()
                yield "contact", result
                yield "status", "updated"
            else:
                yield "contact", {}
                yield "status", "contact_not_found"
