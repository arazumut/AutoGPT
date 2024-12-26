import uuid
from typing import Any, Literal

from pinecone import Pinecone, ServerlessSpec

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
)
from backend.integrations.providers import ProviderName

PineconeCredentials = APIKeyCredentials
PineconeCredentialsInput = CredentialsMetaInput[
    Literal[ProviderName.PINECONE],
    Literal["api_key"],
]


def PineconeCredentialsField() -> PineconeCredentialsInput:
    """Bir Pinecone kimlik bilgisi girişi oluşturur."""
    return CredentialsField(
        description="Pinecone entegrasyonu bir API Anahtarı ile kullanılabilir.",
    )


class PineconeInitBlock(Block):
    class Input(BlockSchema):
        credentials: PineconeCredentialsInput = PineconeCredentialsField()
        index_name: str = SchemaField(description="Pinecone indeksinin adı")
        dimension: int = SchemaField(
            description="Vektörlerin boyutu", default=768
        )
        metric: str = SchemaField(
            description="İndeks için mesafe metriği", default="cosine"
        )
        cloud: str = SchemaField(
            description="Sunucusuz için bulut sağlayıcı", default="aws"
        )
        region: str = SchemaField(
            description="Sunucusuz için bölge", default="us-east-1"
        )

    class Output(BlockSchema):
        index: str = SchemaField(description="Başlatılan Pinecone indeksinin adı")
        message: str = SchemaField(description="Durum mesajı")

    def __init__(self):
        super().__init__(
            id="48d8fdab-8f03-41f3-8407-8107ba11ec9b",
            description="Bir Pinecone indeksini başlatır",
            categories={BlockCategory.LOGIC},
            input_schema=PineconeInitBlock.Input,
            output_schema=PineconeInitBlock.Output,
        )

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        pc = Pinecone(api_key=credentials.api_key.get_secret_value())

        try:
            existing_indexes = pc.list_indexes()
            if input_data.index_name not in [index.name for index in existing_indexes]:
                pc.create_index(
                    name=input_data.index_name,
                    dimension=input_data.dimension,
                    metric=input_data.metric,
                    spec=ServerlessSpec(
                        cloud=input_data.cloud, region=input_data.region
                    ),
                )
                message = f"Yeni indeks oluşturuldu: {input_data.index_name}"
            else:
                message = f"Mevcut indeks kullanılıyor: {input_data.index_name}"

            yield "index", input_data.index_name
            yield "message", message
        except Exception as e:
            yield "message", f"Pinecone indeksi başlatılırken hata: {str(e)}"


class PineconeQueryBlock(Block):
    class Input(BlockSchema):
        credentials: PineconeCredentialsInput = PineconeCredentialsField()
        query_vector: list = SchemaField(description="Sorgu vektörü")
        namespace: str = SchemaField(
            description="Pinecone'da sorgulanacak ad alanı", default=""
        )
        top_k: int = SchemaField(
            description="Dönen en iyi sonuç sayısı", default=3
        )
        include_values: bool = SchemaField(
            description="Yanıtta vektör değerlerinin dahil edilip edilmeyeceği",
            default=False,
        )
        include_metadata: bool = SchemaField(
            description="Yanıtta meta verilerin dahil edilip edilmeyeceği", default=True
        )
        host: str = SchemaField(description="Pinecone için ana bilgisayar", default="")
        idx_name: str = SchemaField(description="Pinecone için indeks adı")

    class Output(BlockSchema):
        results: Any = SchemaField(description="Pinecone'dan sorgu sonuçları")
        combined_results: Any = SchemaField(
            description="Pinecone'dan birleştirilmiş sonuçlar"
        )

    def __init__(self):
        super().__init__(
            id="9ad93d0f-91b4-4c9c-8eb1-82e26b4a01c5",
            description="Bir Pinecone indeksini sorgular",
            categories={BlockCategory.LOGIC},
            input_schema=PineconeQueryBlock.Input,
            output_schema=PineconeQueryBlock.Output,
        )

    def run(
        self,
        input_data: Input,
        *,
        credentials: APIKeyCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            # Yeni bir istemci örneği oluştur
            pc = Pinecone(api_key=credentials.api_key.get_secret_value())

            # İndeksi al
            idx = pc.Index(input_data.idx_name)

            # Sorgu vektörünün doğru formatta olduğundan emin ol
            query_vector = input_data.query_vector
            if isinstance(query_vector, list) and len(query_vector) > 0:
                if isinstance(query_vector[0], list):
                    query_vector = query_vector[0]

            results = idx.query(
                namespace=input_data.namespace,
                vector=query_vector,
                top_k=input_data.top_k,
                include_values=input_data.include_values,
                include_metadata=input_data.include_metadata,
            ).to_dict()  # type: ignore
            combined_text = ""
            if results["matches"]:
                texts = [
                    match["metadata"]["text"]
                    for match in results["matches"]
                    if match.get("metadata", {}).get("text")
                ]
                combined_text = "\n\n".join(texts)

            # Hem ham eşleşmeleri hem de birleştirilmiş metni döndür
            yield "results", {
                "matches": results["matches"],
                "combined_text": combined_text,
            }
            yield "combined_results", combined_text

        except Exception as e:
            error_msg = f"Pinecone sorgulanırken hata: {str(e)}"
            raise RuntimeError(error_msg) from e


class PineconeInsertBlock(Block):
    class Input(BlockSchema):
        credentials: PineconeCredentialsInput = PineconeCredentialsField()
        index: str = SchemaField(description="Başlatılan Pinecone indeksi")
        chunks: list = SchemaField(description="Yüklenecek metin parçalarının listesi")
        embeddings: list = SchemaField(
            description="Parçalara karşılık gelen gömme listesi"
        )
        namespace: str = SchemaField(
            description="Pinecone'da kullanılacak ad alanı", default=""
        )
        metadata: dict = SchemaField(
            description="Her vektörle birlikte saklanacak ek meta veriler", default={}
        )

    class Output(BlockSchema):
        upsert_response: str = SchemaField(
            description="Pinecone ekleme işlemi yanıtı"
        )

    def __init__(self):
        super().__init__(
            id="477f2168-cd91-475a-8146-9499a5982434",
            description="Bir Pinecone indeksine veri yükler",
            categories={BlockCategory.LOGIC},
            input_schema=PineconeInsertBlock.Input,
            output_schema=PineconeInsertBlock.Output,
        )

    def run(
        self,
        input_data: Input,
        *,
        credentials: APIKeyCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            # Yeni bir istemci örneği oluştur
            pc = Pinecone(api_key=credentials.api_key.get_secret_value())

            # İndeksi al
            idx = pc.Index(input_data.index)

            vectors = []
            for chunk, embedding in zip(input_data.chunks, input_data.embeddings):
                vector_metadata = input_data.metadata.copy()
                vector_metadata["text"] = chunk
                vectors.append(
                    {
                        "id": str(uuid.uuid4()),
                        "values": embedding,
                        "metadata": vector_metadata,
                    }
                )
            idx.upsert(vectors=vectors, namespace=input_data.namespace)

            yield "upsert_response", "başarıyla eklendi"

        except Exception as e:
            error_msg = f"Pinecone'a yüklenirken hata: {str(e)}"
            raise RuntimeError(error_msg) from e
