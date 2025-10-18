import asyncio
from functools import lru_cache

from gliner import GLiNER
from ..gliner.gliner_text_chunker import GlinerTextChunker
from src.core.services.anonymizer.schemas import AnonymizationResult

CACHE_DIR = "./models"
DEFAULT_MODEL = "knowledgator/gliner-pii-large-v1.0"
SEMAPHORE = asyncio.Semaphore(1)


@lru_cache
def get_gliner(model: str = DEFAULT_MODEL) -> "GlinerAnonymizer":
    return GlinerAnonymizer(model)


class GlinerAnonymizer:
    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = GLiNER.from_pretrained(model, cache_dir=CACHE_DIR)
        self.chunker = GlinerTextChunker(self.model.data_processor, max_tokens=768)

    async def anonymize(self, text: str, labels: list[str], threshold: float) -> AnonymizationResult:
        chunks: list[tuple[str, int, int]] = await self.chunker.chunk(text)

        all_entities = []
        async with SEMAPHORE:
            tasks = []
            for chunk_text, global_start, _ in chunks:
                task = asyncio.to_thread(self.model.predict_entities, chunk_text, labels, threshold=threshold)
                tasks.append((task, global_start))

            results = await asyncio.gather(*(t[0] for t in tasks))

            for entities, (task, global_start) in zip(results, tasks):
                for ent in entities:
                    ent["start"] += global_start
                    ent["end"] += global_start
                    ent["text"] = text[ent["start"] : ent["end"]]
                all_entities.extend(entities)

        # Умная дедупликация на основе score.
        # Оставляем сущность с наибольшей уверенностью для каждого диапазона (start, end).
        unique_entities_by_pos = {}
        for ent in all_entities:
            key = (ent["start"], ent["end"])
            # GLiNER возвращает 'score'
            current_score = ent.get("score", 0.0)

            if key not in unique_entities_by_pos or current_score > unique_entities_by_pos[key].get("score", 0.0):
                unique_entities_by_pos[key] = ent

        all_entities = list(unique_entities_by_pos.values())

        # Разрешение пересечений
        all_entities = self._resolve_overlapping_entities(all_entities)

        # Сортируем по start для корректной замены с конца
        all_entities.sort(key=lambda x: x["start"])

        # Шаг 5: строим глобальный anon_map и заменяем по позициям
        anon_map: dict[tuple, str] = {}
        placeholder_counters: dict[str, int] = {}
        result_chars = list(text)

        # Заменяем с КОНЦА, чтобы не сбивать индексы
        for ent in reversed(all_entities):
            label = ent["label"]
            original_text = ent["text"]

            key = (label, original_text)
            if key not in anon_map:
                counter = placeholder_counters.get(label, 1)
                placeholder = f"[{label}_{counter}]"
                anon_map[key] = placeholder
                placeholder_counters[label] = counter + 1

            placeholder = anon_map[key]
            result_chars[ent["start"] : ent["end"]] = list(placeholder)

        anonymized_text = "".join(result_chars)
        flat_anon_map = {v: k[1] for k, v in anon_map.items()}

        return AnonymizationResult(text=anonymized_text, map=flat_anon_map)

    @staticmethod
    def _resolve_overlapping_entities(entities: list[dict]) -> list[dict]:
        if not entities:
            return entities
        # Сортируем по start, затем по длине (длиннее — приоритетнее)
        entities = sorted(entities, key=lambda x: (x["start"], -(x["end"] - x["start"])))
        resolved = []
        last_end = -1
        for ent in entities:
            if ent["start"] >= last_end:
                resolved.append(ent)
                last_end = ent["end"]
        return resolved
