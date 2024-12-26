import logging
from typing import Optional, cast

from autogpt_libs.auth.models import DEFAULT_USER_ID
from fastapi import HTTPException
from prisma import Json
from prisma.models import User

from backend.data.db import prisma
from backend.data.model import UserIntegrations, UserMetadata, UserMetadataRaw
from backend.util.encryption import JSONCryptor

logger = logging.getLogger(__name__)

# Kullanıcıyı al veya oluştur
async def get_or_create_user(user_data: dict) -> User:
    user_id = user_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token'da Kullanıcı ID'si bulunamadı")

    user_email = user_data.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Token'da Email bulunamadı")

    user = await prisma.user.find_unique(where={"id": user_id})
    if not user:
        user = await prisma.user.create(
            data={
                "id": user_id,
                "email": user_email,
                "name": user_data.get("user_metadata", {}).get("name"),
            }
        )
    return User.model_validate(user)

# Kullanıcıyı ID ile al
async def get_user_by_id(user_id: str) -> Optional[User]:
    user = await prisma.user.find_unique(where={"id": user_id})
    return User.model_validate(user) if user else None

# Varsayılan kullanıcı oluştur
async def create_default_user() -> Optional[User]:
    user = await prisma.user.find_unique(where={"id": DEFAULT_USER_ID})
    if not user:
        user = await prisma.user.create(
            data={
                "id": DEFAULT_USER_ID,
                "email": "default@example.com",
                "name": "Varsayılan Kullanıcı",
            }
        )
    return User.model_validate(user)

# Kullanıcı metadata'sını al
async def get_user_metadata(user_id: str) -> UserMetadata:
    user = await User.prisma().find_unique_or_raise(
        where={"id": user_id},
    )

    metadata = cast(UserMetadataRaw, user.metadata)
    return UserMetadata.model_validate(metadata)

# Kullanıcı metadata'sını güncelle
async def update_user_metadata(user_id: str, metadata: UserMetadata):
    await User.prisma().update(
        where={"id": user_id},
        data={"metadata": Json(metadata.model_dump())},
    )

# Kullanıcı entegrasyonlarını al
async def get_user_integrations(user_id: str) -> UserIntegrations:
    user = await User.prisma().find_unique_or_raise(
        where={"id": user_id},
    )

    encrypted_integrations = user.integrations
    if not encrypted_integrations:
        return UserIntegrations()
    else:
        return UserIntegrations.model_validate(
            JSONCryptor().decrypt(encrypted_integrations)
        )

# Kullanıcı entegrasyonlarını güncelle
async def update_user_integrations(user_id: str, data: UserIntegrations):
    encrypted_data = JSONCryptor().encrypt(data.model_dump())
    await User.prisma().update(
        where={"id": user_id},
        data={"integrations": encrypted_data},
    )

# Kullanıcı entegrasyonlarını migrate ve şifrele
async def migrate_and_encrypt_user_integrations():
    """Entegrasyon kimlik bilgilerini ve OAuth durumlarını metadata'dan entegrasyonlar sütununa taşı."""
    users = await User.prisma().find_many(
        where={
            "metadata": {
                "path": ["integration_credentials"],
                "not": Json({"a": "yolo"}),  # anahtarın var olup olmadığını kontrol etmek için sahte değer
            }  # type: ignore
        }
    )
    logger.info(f"{len(users)} kullanıcı için entegrasyon kimlik bilgileri taşınıyor")

    for user in users:
        raw_metadata = cast(UserMetadataRaw, user.metadata)
        metadata = UserMetadata.model_validate(raw_metadata)

        # Mevcut entegrasyon verilerini al
        integrations = await get_user_integrations(user_id=user.id)

        # Kimlik bilgilerini ve oauth durumlarını metadata'dan kopyala
        if metadata.integration_credentials and not integrations.credentials:
            integrations.credentials = metadata.integration_credentials
        if metadata.integration_oauth_states:
            integrations.oauth_states = metadata.integration_oauth_states

        # Entegrasyonlar sütununa kaydet
        await update_user_integrations(user_id=user.id, data=integrations)

        # Metadata'dan kaldır
        raw_metadata = dict(raw_metadata)
        raw_metadata.pop("integration_credentials", None)
        raw_metadata.pop("integration_oauth_states", None)

        # Entegrasyon verisi olmadan metadata'yı güncelle
        await User.prisma().update(
            where={"id": user.id},
            data={"metadata": Json(raw_metadata)},
        )
