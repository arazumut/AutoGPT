from functools import wraps
from typing import Any, Callable, Concatenate, Coroutine, ParamSpec, TypeVar, cast

from backend.data.credit import get_user_credit_model
from backend.data.execution import (
    ExecutionResult,
    RedisExecutionEventBus,
    create_graph_execution,
    get_execution_results,
    get_incomplete_executions,
    get_latest_execution,
    update_execution_status,
    update_graph_execution_stats,
    update_node_execution_stats,
    upsert_execution_input,
    upsert_execution_output,
)
from backend.data.graph import get_graph, get_node
from backend.data.user import (
    get_user_integrations,
    get_user_metadata,
    update_user_integrations,
    update_user_metadata,
)
from backend.util.service import AppService, expose, register_pydantic_serializers
from backend.util.settings import Config

P = ParamSpec("P")
R = TypeVar("R")
config = Config()


class VeritabaniYoneticisi(AppService):
    def __init__(self):
        super().__init__()
        self.veritabani_kullan = True
        self.redis_kullan = True
        self.etkinlik_kuyrugu = RedisExecutionEventBus()

    @classmethod
    def portu_al(cls) -> int:
        return config.database_api_port

    @expose
    def yürütme_güncellemesi_gönder(self, yürütme_sonucu: ExecutionResult):
        self.etkinlik_kuyrugu.publish(yürütme_sonucu)

    @staticmethod
    def açığa_çıkmış_çalıştır_ve_bekle(
        f: Callable[P, Coroutine[None, None, R]]
    ) -> Callable[Concatenate[object, P], R]:
        @expose
        @wraps(f)
        def sarmalayıcı(self, *args: P.args, **kwargs: P.kwargs) -> R:
            coroutine = f(*args, **kwargs)
            sonuç = self.run_and_wait(coroutine)
            return sonuç

        # Fonksiyon üzerindeki açıklamalar için serileştiricileri kaydet
        register_pydantic_serializers(f)

        return sarmalayıcı

    # Yürütmeler
    create_graph_execution = açığa_çıkmış_çalıştır_ve_bekle(create_graph_execution)
    get_execution_results = açığa_çıkmış_çalıştır_ve_bekle(get_execution_results)
    get_incomplete_executions = açığa_çıkmış_çalıştır_ve_bekle(get_incomplete_executions)
    get_latest_execution = açığa_çıkmış_çalıştır_ve_bekle(get_latest_execution)
    update_execution_status = açığa_çıkmış_çalıştır_ve_bekle(update_execution_status)
    update_graph_execution_stats = açığa_çıkmış_çalıştır_ve_bekle(update_graph_execution_stats)
    update_node_execution_stats = açığa_çıkmış_çalıştır_ve_bekle(update_node_execution_stats)
    upsert_execution_input = açığa_çıkmış_çalıştır_ve_bekle(upsert_execution_input)
    upsert_execution_output = açığa_çıkmış_çalıştır_ve_bekle(upsert_execution_output)

    # Grafikler
    get_node = açığa_çıkmış_çalıştır_ve_bekle(get_node)
    get_graph = açığa_çıkmış_çalıştır_ve_bekle(get_graph)

    # Krediler
    kullanıcı_kredi_modeli = get_user_credit_model()
    kredi_al_veya_doldur = cast(
        Callable[[Any, str], int],
        açığa_çıkmış_çalıştır_ve_bekle(kullanıcı_kredi_modeli.get_or_refill_credit),
    )
    kredi_harcamak = cast(
        Callable[[Any, str, int, str, dict[str, str], float, float], int],
        açığa_çıkmış_çalıştır_ve_bekle(kullanıcı_kredi_modeli.spend_credits),
    )

    # Kullanıcı + Kullanıcı Metadata + Kullanıcı Entegrasyonları
    kullanıcı_metadata_al = açığa_çıkmış_çalıştır_ve_bekle(get_user_metadata)
    kullanıcı_metadata_güncelle = açığa_çıkmış_çalıştır_ve_bekle(update_user_metadata)
    kullanıcı_entegrasyonları_al = açığa_çıkmış_çalıştır_ve_bekle(get_user_integrations)
    kullanıcı_entegrasyonları_güncelle = açığa_çıkmış_çalıştır_ve_bekle(update_user_integrations)
