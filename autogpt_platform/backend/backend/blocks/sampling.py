import random
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class SamplingMethod(str, Enum):
    RANDOM = "random"
    SYSTEMATIC = "systematic"
    TOP = "top"
    BOTTOM = "bottom"
    STRATIFIED = "stratified"
    WEIGHTED = "weighted"
    RESERVOIR = "reservoir"
    CLUSTER = "cluster"


class DataSamplingBlock(Block):
    class Input(BlockSchema):
        data: Union[Dict[str, Any], List[Union[dict, List[Any]]]] = SchemaField(
            description="Örnekleme yapılacak veri kümesi. Tek bir sözlük, sözlükler listesi veya listeler listesi olabilir.",
            placeholder="{'id': 1, 'value': 'a'} veya [{'id': 1, 'value': 'a'}, {'id': 2, 'value': 'b'}, ...]",
        )
        sample_size: int = SchemaField(
            description="Veri kümesinden alınacak örnek sayısı.",
            placeholder="10",
            default=10,
        )
        sampling_method: SamplingMethod = SchemaField(
            description="Örnekleme için kullanılacak yöntem.",
            default=SamplingMethod.RANDOM,
        )
        accumulate: bool = SchemaField(
            description="Örnekleme öncesinde verileri biriktirip biriktirmeyeceği.",
            default=False,
        )
        random_seed: Optional[int] = SchemaField(
            description="Rastgele sayı üreteci için tohum (isteğe bağlı).",
            default=None,
        )
        stratify_key: Optional[str] = SchemaField(
            description="Tabakalı örnekleme için kullanılacak anahtar (tabakalı örnekleme için gereklidir).",
            default=None,
        )
        weight_key: Optional[str] = SchemaField(
            description="Ağırlıklı örnekleme için kullanılacak anahtar (ağırlıklı örnekleme için gereklidir).",
            default=None,
        )
        cluster_key: Optional[str] = SchemaField(
            description="Küme örnekleme için kullanılacak anahtar (küme örnekleme için gereklidir).",
            default=None,
        )

    class Output(BlockSchema):
        sampled_data: List[Union[dict, List[Any]]] = SchemaField(
            description="Girdi verilerinin örneklenmiş alt kümesi."
        )
        sample_indices: List[int] = SchemaField(
            description="Örneklenen verilerin orijinal veri kümesindeki indeksleri."
        )

    def __init__(self):
        super().__init__(
            id="4a448883-71fa-49cf-91cf-70d793bd7d87",
            description="Bu blok, çeşitli örnekleme yöntemlerini kullanarak verilen bir veri kümesinden veri örnekler.",
            categories={BlockCategory.LOGIC},
            input_schema=DataSamplingBlock.Input,
            output_schema=DataSamplingBlock.Output,
            test_input={
                "data": [
                    {"id": i, "value": chr(97 + i), "group": i % 3} for i in range(10)
                ],
                "sample_size": 3,
                "sampling_method": SamplingMethod.STRATIFIED,
                "accumulate": False,
                "random_seed": 42,
                "stratify_key": "group",
            },
            test_output=[
                (
                    "sampled_data",
                    [
                        {"id": 0, "value": "a", "group": 0},
                        {"id": 1, "value": "b", "group": 1},
                        {"id": 8, "value": "i", "group": 2},
                    ],
                ),
                ("sample_indices", [0, 1, 8]),
            ],
        )
        self.accumulated_data = []

    def run(self, input_data: Input, **kwargs) -> BlockOutput:
        if input_data.accumulate:
            if isinstance(input_data.data, dict):
                self.accumulated_data.append(input_data.data)
            elif isinstance(input_data.data, list):
                self.accumulated_data.extend(input_data.data)
            else:
                raise ValueError(f"Desteklenmeyen veri türü: {type(input_data.data)}")

            # Yeterli veri yoksa, örnekleme yapmadan geri dön
            if len(self.accumulated_data) < input_data.sample_size:
                return

            data_to_sample = self.accumulated_data
        else:
            # Biriktirme yapılmıyorsa, girdi verilerini doğrudan kullan
            data_to_sample = (
                input_data.data
                if isinstance(input_data.data, list)
                else [input_data.data]
            )

        if input_data.random_seed is not None:
            random.seed(input_data.random_seed)

        data_size = len(data_to_sample)

        if input_data.sample_size > data_size:
            raise ValueError(
                f"Örnek boyutu ({input_data.sample_size}), veri kümesi boyutundan ({data_size}) büyük olamaz."
            )

        indices = []

        if input_data.sampling_method == SamplingMethod.RANDOM:
            indices = random.sample(range(data_size), input_data.sample_size)
        elif input_data.sampling_method == SamplingMethod.SYSTEMATIC:
            step = data_size // input_data.sample_size
            start = random.randint(0, step - 1)
            indices = list(range(start, data_size, step))[: input_data.sample_size]
        elif input_data.sampling_method == SamplingMethod.TOP:
            indices = list(range(input_data.sample_size))
        elif input_data.sampling_method == SamplingMethod.BOTTOM:
            indices = list(range(data_size - input_data.sample_size, data_size))
        elif input_data.sampling_method == SamplingMethod.STRATIFIED:
            if not input_data.stratify_key:
                raise ValueError(
                    "Tabakalı örnekleme için tabakalama anahtarı sağlanmalıdır."
                )
            strata = defaultdict(list)
            for i, item in enumerate(data_to_sample):
                if isinstance(item, dict):
                    strata_value = item.get(input_data.stratify_key)
                elif hasattr(item, input_data.stratify_key):
                    strata_value = getattr(item, input_data.stratify_key)
                else:
                    raise ValueError(
                        f"Tabakalama anahtarı '{input_data.stratify_key}', öğe {item} içinde bulunamadı"
                    )

                if strata_value is None:
                    raise ValueError(
                        f"Tabakalama anahtarı '{input_data.stratify_key}' için değer None"
                    )

                strata[str(strata_value)].append(i)

            # Her tabakadan alınacak örnek sayısını hesapla
            stratum_sizes = {
                k: max(1, int(len(v) / data_size * input_data.sample_size))
                for k, v in strata.items()
            }

            # Tam olarak sample_size kadar örnek aldığımızdan emin olmak için boyutları ayarla
            while sum(stratum_sizes.values()) != input_data.sample_size:
                if sum(stratum_sizes.values()) < input_data.sample_size:
                    stratum_sizes[
                        max(stratum_sizes, key=lambda k: stratum_sizes[k])
                    ] += 1
                else:
                    stratum_sizes[
                        max(stratum_sizes, key=lambda k: stratum_sizes[k])
                    ] -= 1

            for stratum, size in stratum_sizes.items():
                indices.extend(random.sample(strata[stratum], size))
        elif input_data.sampling_method == SamplingMethod.WEIGHTED:
            if not input_data.weight_key:
                raise ValueError("Ağırlıklı örnekleme için ağırlık anahtarı sağlanmalıdır.")
            weights = []
            for item in data_to_sample:
                if isinstance(item, dict):
                    weight = item.get(input_data.weight_key)
                elif hasattr(item, input_data.weight_key):
                    weight = getattr(item, input_data.weight_key)
                else:
                    raise ValueError(
                        f"Ağırlık anahtarı '{input_data.weight_key}', öğe {item} içinde bulunamadı"
                    )

                if weight is None:
                    raise ValueError(
                        f"Ağırlık anahtarı '{input_data.weight_key}' için değer None"
                    )
                try:
                    weights.append(float(weight))
                except ValueError:
                    raise ValueError(
                        f"Ağırlık değeri '{weight}', bir sayıya dönüştürülemez"
                    )

            if not weights:
                raise ValueError(
                    f"Ağırlık anahtarı '{input_data.weight_key}' kullanılarak geçerli ağırlık bulunamadı"
                )

            indices = random.choices(
                range(data_size), weights=weights, k=input_data.sample_size
            )
        elif input_data.sampling_method == SamplingMethod.RESERVOIR:
            indices = list(range(input_data.sample_size))
            for i in range(input_data.sample_size, data_size):
                j = random.randint(0, i)
                if j < input_data.sample_size:
                    indices[j] = i
        elif input_data.sampling_method == SamplingMethod.CLUSTER:
            if not input_data.cluster_key:
                raise ValueError("Küme örnekleme için küme anahtarı sağlanmalıdır.")
            clusters = defaultdict(list)
            for i, item in enumerate(data_to_sample):
                if isinstance(item, dict):
                    cluster_value = item.get(input_data.cluster_key)
                elif hasattr(item, input_data.cluster_key):
                    cluster_value = getattr(item, input_data.cluster_key)
                else:
                    raise TypeError(
                        f"Öğe {item}, küme anahtarı '{input_data.cluster_key}' içermiyor"
                    )

                clusters[str(cluster_value)].append(i)

            # Yeterli örnek alana kadar rastgele kümeler seç
            selected_clusters = []
            while (
                sum(len(clusters[c]) for c in selected_clusters)
                < input_data.sample_size
            ):
                available_clusters = [c for c in clusters if c not in selected_clusters]
                if not available_clusters:
                    break
                selected_clusters.append(random.choice(available_clusters))

            for cluster in selected_clusters:
                indices.extend(clusters[cluster])

            # Gerekenden fazla örnek varsa, rastgele bazılarını çıkar
            if len(indices) > input_data.sample_size:
                indices = random.sample(indices, input_data.sample_size)
        else:
            raise ValueError(f"Bilinmeyen örnekleme yöntemi: {input_data.sampling_method}")

        sampled_data = [data_to_sample[i] for i in indices]

        # Biriktirme etkinse, örnekleme sonrası birikmiş verileri temizle
        if input_data.accumulate:
            self.accumulated_data = []

        yield "sampled_data", sampled_data
        yield "sample_indices", indices
