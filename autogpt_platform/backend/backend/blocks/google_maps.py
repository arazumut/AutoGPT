from typing import Literal

import googlemaps
from pydantic import BaseModel, SecretStr

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
)
from backend.integrations.providers import ProviderName

# Test için kullanılan API anahtarı
TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="google_maps",
    api_key=SecretStr("mock-google-maps-api-key"),
    title="Mock Google Maps API key",
    expires_at=None,
)
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.type,
}

# Yer bilgilerini tutan model
class Place(BaseModel):
    name: str
    address: str
    phone: str
    rating: float
    reviews: int
    website: str

# Google Maps arama bloğu
class GoogleMapsSearchBlock(Block):
    class Input(BlockSchema):
        credentials: CredentialsMetaInput[
            Literal[ProviderName.GOOGLE_MAPS], Literal["api_key"]
        ] = CredentialsField(description="Google Maps API Anahtarı")
        query: str = SchemaField(
            description="Yerel işletmeler için arama sorgusu",
            placeholder="örneğin, 'New York'ta restoranlar'",
        )
        radius: int = SchemaField(
            description="Arama yarıçapı (maksimum 50000 metre)",
            default=5000,
            ge=1,
            le=50000,
        )
        max_results: int = SchemaField(
            description="Döndürülecek maksimum sonuç sayısı (maksimum 60)",
            default=20,
            ge=1,
            le=60,
        )

    class Output(BlockSchema):
        place: Place = SchemaField(description="Bulunan yer")
        error: str = SchemaField(description="Arama başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
            description="Bu blok Google Maps API kullanarak yerel işletmeleri arar.",
            categories={BlockCategory.SEARCH},
            input_schema=GoogleMapsSearchBlock.Input,
            output_schema=GoogleMapsSearchBlock.Output,
            test_input={
                "credentials": TEST_CREDENTIALS_INPUT,
                "query": "new york'ta restoranlar",
                "radius": 5000,
                "max_results": 5,
            },
            test_output=[
                (
                    "place",
                    {
                        "name": "Test Restoran",
                        "address": "123 Test St, New York, NY 10001",
                        "phone": "+1 (555) 123-4567",
                        "rating": 4.5,
                        "reviews": 100,
                        "website": "https://testrestaurant.com",
                    },
                ),
            ],
            test_mock={
                "search_places": lambda *args, **kwargs: [
                    {
                        "name": "Test Restoran",
                        "address": "123 Test St, New York, NY 10001",
                        "phone": "+1 (555) 123-4567",
                        "rating": 4.5,
                        "reviews": 100,
                        "website": "https://testrestaurant.com",
                    }
                ]
            },
            test_credentials=TEST_CREDENTIALS,
        )

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        places = self.search_places(
            credentials.api_key,
            input_data.query,
            input_data.radius,
            input_data.max_results,
        )
        for place in places:
            yield "place", place

    def search_places(self, api_key: SecretStr, query, radius, max_results):
        client = googlemaps.Client(key=api_key.get_secret_value())
        return self._search_places(client, query, radius, max_results)

    def _search_places(self, client, query, radius, max_results):
        results = []
        next_page_token = None
        while len(results) < max_results:
            response = client.places(
                query=query,
                radius=radius,
                page_token=next_page_token,
            )
            for place in response["results"]:
                if len(results) >= max_results:
                    break
                place_details = client.place(place["place_id"])["result"]
                results.append(
                    Place(
                        name=place_details.get("name", ""),
                        address=place_details.get("formatted_address", ""),
                        phone=place_details.get("formatted_phone_number", ""),
                        rating=place_details.get("rating", 0),
                        reviews=place_details.get("user_ratings_total", 0),
                        website=place_details.get("website", ""),
                    )
                )
            next_page_token = response.get("next_page_token")
            if not next_page_token:
                break
        return results
