import logging
from typing import TYPE_CHECKING, Callable, Optional, cast

from backend.data.block import BlockWebhookConfig, get_block
from backend.data.graph import set_node_webhook
from backend.data.model import CREDENTIALS_FIELD_NAME
from backend.integrations.webhooks import WEBHOOK_MANAGERS_BY_NAME

if TYPE_CHECKING:
    from backend.data.graph import GraphModel, NodeModel
    from backend.data.model import Credentials

    from ._base import BaseWebhooksManager

logger = logging.getLogger(__name__)

async def on_graph_activate(
    graph: "GraphModel", get_credentials: Callable[[str], "Credentials | None"]
):
    """
    Bir grafik etkinleştirildiğinde/oluşturulduğunda çağrılacak kanca.

    ⚠️ Düğüm varlıklarının grafik sürümleri arasında yeniden kullanılmadığını varsayarak, ⚠️
    bu kanca, bu grafikteki tüm düğümler üzerinde `on_node_activate` çağrısı yapar.

    Parametreler:
        get_credentials: `credentials_id` -> Credentials
    """
    güncellenmiş_düğümler = []
    for yeni_düğüm in graph.nodes:
        düğüm_kimlik_bilgileri = None
        if creds_meta := yeni_düğüm.input_default.get(CREDENTIALS_FIELD_NAME):
            düğüm_kimlik_bilgileri = get_credentials(creds_meta["id"])
            if not düğüm_kimlik_bilgileri:
                raise ValueError(
                    f"Düğüm #{yeni_düğüm.id} mevcut olmayan "
                    f"kimlik bilgileri #{düğüm_kimlik_bilgileri} ile güncellendi"
                )

        güncellenmiş_düğüm = await on_node_activate(
            graph.user_id, yeni_düğüm, credentials=düğüm_kimlik_bilgileri
        )
        güncellenmiş_düğümler.append(güncellenmiş_düğüm)

    graph.nodes = güncellenmiş_düğümler
    return graph

async def on_graph_deactivate(
    graph: "GraphModel", get_credentials: Callable[[str], "Credentials | None"]
):
    """
    Bir grafik devre dışı bırakıldığında/silindiğinde çağrılacak kanca.

    ⚠️ Düğüm varlıklarının grafik sürümleri arasında yeniden kullanılmadığını varsayarak, ⚠️
    bu kanca, `graph` içindeki tüm düğümler üzerinde `on_node_deactivate` çağrısı yapar.

    Parametreler:
        get_credentials: `credentials_id` -> Credentials
    """
    güncellenmiş_düğümler = []
    for düğüm in graph.nodes:
        düğüm_kimlik_bilgileri = None
        if creds_meta := düğüm.input_default.get(CREDENTIALS_FIELD_NAME):
            düğüm_kimlik_bilgileri = get_credentials(creds_meta["id"])
            if not düğüm_kimlik_bilgileri:
                logger.error(
                    f"Düğüm #{düğüm.id} mevcut olmayan "
                    f"kimlik bilgileri #{creds_meta['id']} referans aldı"
                )

        güncellenmiş_düğüm = await on_node_deactivate(düğüm, credentials=düğüm_kimlik_bilgileri)
        güncellenmiş_düğümler.append(güncellenmiş_düğüm)

    graph.nodes = güncellenmiş_düğümler
    return graph

async def on_node_activate(
    user_id: str,
    node: "NodeModel",
    *,
    credentials: Optional["Credentials"] = None,
) -> "NodeModel":
    """Düğüm etkinleştirildiğinde/oluşturulduğunda çağrılacak kanca"""

    block = get_block(node.block_id)
    if not block:
        raise ValueError(
            f"Düğüm #{node.id} bilinmeyen blok #{node.block_id} örneğidir"
        )

    if not block.webhook_config:
        return node

    provider = block.webhook_config.provider
    if provider not in WEBHOOK_MANAGERS_BY_NAME:
        raise ValueError(
            f"Blok #{block.id} webhook_config sağlayıcısı {provider} "
            "webhookları desteklemiyor"
        )

    logger.debug(
        f"Webhook düğümü #{node.id} yapılandırma ile etkinleştiriliyor {block.webhook_config}"
    )

    webhooks_manager = WEBHOOK_MANAGERS_BY_NAME[provider]()

    if auto_setup_webhook := isinstance(block.webhook_config, BlockWebhookConfig):
        try:
            resource = block.webhook_config.resource_format.format(**node.input_default)
        except KeyError:
            resource = None
        logger.debug(
            f"Girdi {node.input_default} ile kaynak dizesi {resource} oluşturuldu"
        )
    else:
        resource = ""  # manuel webhooks için geçerli değil

    needs_credentials = CREDENTIALS_FIELD_NAME in block.input_schema.model_fields
    credentials_meta = (
        node.input_default.get(CREDENTIALS_FIELD_NAME) if needs_credentials else None
    )
    event_filter_input_name = block.webhook_config.event_filter_input
    has_everything_for_webhook = (
        resource is not None
        and (credentials_meta or not needs_credentials)
        and (
            not event_filter_input_name
            or (
                event_filter_input_name in node.input_default
                and any(
                    is_on
                    for is_on in node.input_default[event_filter_input_name].values()
                )
            )
        )
    )

    if has_everything_for_webhook and resource is not None:
        logger.debug(f"Düğüm #{node} webhook için her şeye sahip!")
        if credentials_meta and not credentials:
            raise ValueError(
                f"Düğüm #{node.id} için webhook ayarlanamıyor: "
                f"kimlik bilgileri #{credentials_meta['id']} mevcut değil"
            )

        if event_filter_input_name:
            # Olay filtresinin şekli Block.__init__ içinde zorlanır
            event_filter = cast(dict, node.input_default[event_filter_input_name])
            events = [
                block.webhook_config.event_format.format(event=event)
                for event, enabled in event_filter.items()
                if enabled is True
            ]
            logger.debug(f"Abone olunacak webhook olayları: {', '.join(events)}")
        else:
            events = []

        # Düğüme uygun bir webhook bul ve ekle
        if auto_setup_webhook:
            assert credentials is not None
            new_webhook = await webhooks_manager.get_suitable_auto_webhook(
                user_id,
                credentials,
                block.webhook_config.webhook_type,
                resource,
                events,
            )
        else:
            # Manuel webhook -> kimlik bilgisi yok -> kaydetme ama oluştur
            new_webhook = await webhooks_manager.get_manual_webhook(
                user_id,
                node.graph_id,
                block.webhook_config.webhook_type,
                events,
            )
        logger.debug(f"Edinilen webhook: {new_webhook}")
        return await set_node_webhook(node.id, new_webhook.id)
    else:
        logger.debug(f"Düğüm #{node.id} webhook için her şeye sahip değil")

    return node

async def on_node_deactivate(
    node: "NodeModel",
    *,
    credentials: Optional["Credentials"] = None,
    webhooks_manager: Optional["BaseWebhooksManager"] = None,
) -> "NodeModel":
    """Düğüm devre dışı bırakıldığında/silindiğinde çağrılacak kanca"""

    logger.debug(f"Düğüm #{node.id} devre dışı bırakılıyor")
    block = get_block(node.block_id)
    if not block:
        raise ValueError(
            f"Düğüm #{node.id} bilinmeyen blok #{node.block_id} örneğidir"
        )

    if not block.webhook_config:
        return node

    provider = block.webhook_config.provider
    if provider not in WEBHOOK_MANAGERS_BY_NAME:
        raise ValueError(
            f"Blok #{block.id} webhook_config sağlayıcısı {provider} "
            "webhookları desteklemiyor"
        )

    webhooks_manager = WEBHOOK_MANAGERS_BY_NAME[provider]()

    if node.webhook_id:
        logger.debug(f"Düğüm #{node.id} webhook_id {node.webhook_id} var")
        if not node.webhook:
            logger.error(f"Düğüm #{node.id} webhook_id var ama webhook nesnesi yok")
            raise ValueError("node.webhook dahil edilmedi")

        # Düğümden webhook'u ayır
        logger.debug(f"Düğüm #{node.id} webhook'tan ayrılıyor")
        güncellenmiş_düğüm = await set_node_webhook(node.id, None)

        # Webhook başka bir yerde kullanılmıyorsa buda ve kaydını sil
        webhook = node.webhook
        logger.debug(
            f"Webhook #{webhook.id} budanıyor{' ve kaydı siliniyor' if credentials else ''}"
        )
        await webhooks_manager.prune_webhook_if_dangling(webhook.id, credentials)
        if (
            CREDENTIALS_FIELD_NAME in block.input_schema.model_fields
            and not credentials
        ):
            logger.warning(
                f"Webhook #{webhook.id} kaydı silinemiyor: kimlik bilgileri "
                f"#{webhook.credentials_id} mevcut değil "
                f"({webhook.provider.value} webhook ID: {webhook.provider_webhook_id})"
            )
        return güncellenmiş_düğüm

    logger.debug(f"Düğüm #{node.id} webhook_id yok, geri dönüyor")
    return node
