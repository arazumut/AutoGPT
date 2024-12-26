import logging

from autogpt_libs.utils.cache import thread_cached

from backend.data.block import (
    Block,
    BlockCategory,
    BlockInput,
    BlockOutput,
    BlockSchema,
    BlockType,
    get_block,
)
from backend.data.execution import ExecutionStatus
from backend.data.model import SchemaField

logger = logging.getLogger(__name__)


@thread_cached
def get_executor_manager_client():
    from backend.executor import ExecutionManager
    from backend.util.service import get_service_client

    return get_service_client(ExecutionManager)


@thread_cached
def get_event_bus():
    from backend.data.execution import RedisExecutionEventBus

    return RedisExecutionEventBus()


class AgentExecutorBlock(Block):
    class Input(BlockSchema):
        user_id: str = SchemaField(description="Kullanıcı ID'si")
        graph_id: str = SchemaField(description="Graf ID'si")
        graph_version: int = SchemaField(description="Graf Versiyonu")

        data: BlockInput = SchemaField(description="Graf için giriş verisi")
        input_schema: dict = SchemaField(description="Graf için giriş şeması")
        output_schema: dict = SchemaField(description="Graf için çıkış şeması")

    class Output(BlockSchema):
        pass

    def __init__(self):
        super().__init__(
            id="e189baac-8c20-45a1-94a7-55177ea42565",
            description="Ajanınızın içinde mevcut bir ajanı çalıştırır",
            input_schema=AgentExecutorBlock.Input,
            output_schema=AgentExecutorBlock.Output,
            block_type=BlockType.AGENT,
            categories={BlockCategory.AGENT},
        )

    def run(self, input_data: Input, **kwargs) -> BlockOutput:
        executor_manager = get_executor_manager_client()
        event_bus = get_event_bus()

        graph_exec = executor_manager.add_execution(
            graph_id=input_data.graph_id,
            graph_version=input_data.graph_version,
            user_id=input_data.user_id,
            data=input_data.data,
        )
        log_id = f"Graf #{input_data.graph_id}-V{input_data.graph_version}, exec-id: {graph_exec.graph_exec_id}"
        logger.info(f"{log_id} çalıştırması başlatılıyor")

        for event in event_bus.listen(
            graph_id=graph_exec.graph_id, graph_exec_id=graph_exec.graph_exec_id
        ):
            logger.info(
                f"{log_id} çalıştırması giriş {event.input_data} çıkış {event.output_data} üretti"
            )

            if not event.node_id:
                if event.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
                    logger.info(f"{log_id} çalıştırması {event.status} durumu ile sona erdi")
                    break
                else:
                    continue

            if not event.block_id:
                logger.warning(f"{log_id} block_id olmadan bir olay aldı {event}")
                continue

            block = get_block(event.block_id)
            if not block or block.block_type != BlockType.OUTPUT:
                continue

            output_name = event.input_data.get("name")
            if not output_name:
                logger.warning(f"{log_id} isimsiz bir çıkış üretti {event}")
                continue

            for output_data in event.output_data.get("output", []):
                logger.info(f"{log_id} {output_name}: {output_data} üretti")
                yield output_name, output_data
