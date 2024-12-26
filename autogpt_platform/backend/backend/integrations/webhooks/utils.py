from backend.util.settings import Config

# Uygulama yapılandırmasını yükle
app_config = Config()

# TODO: Bu URL'nin gerçek API yoluyla eşleştiğini doğrulamak için test ekleyin
def webhook_ingress_url(provider_name: str, webhook_id: str) -> str:
    """
    Verilen sağlayıcı adı ve webhook kimliği ile webhook giriş URL'sini oluşturur.

    Args:
        provider_name (str): Sağlayıcı adı
        webhook_id (str): Webhook kimliği

    Returns:
        str: Webhook giriş URL'si
    """
    return (
        f"{app_config.platform_base_url}/api/integrations/{provider_name}"
        f"/webhooks/{webhook_id}/ingress"
    )
