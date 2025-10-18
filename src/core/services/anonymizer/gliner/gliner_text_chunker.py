import asyncio
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class GlinerTextChunker:
    """
    Класс для иерархического разбиения текста на фрагменты,
    подходящие для обработки GLiNER (максимум 768 токенов).

    Алгоритм работает жадно и иерархически:
    1. Весь текст → если укладывается в лимит — вернуть.
    2. Иначе — разбить на абзацы и жадно объединять.
    3. Если абзац слишком длинный — разбить на предложения.
    4. Если предложение слишком длинное — разбить по запятым/точкам с запятой.
    5. Если и это не помогает — разбить на слова (с защитой от атак через сверхдлинные слова).
    6. После разбиения короткие чанки (< 1/3 max_tokens) объединяются со следующими, если возможно.

    Поддерживает сохранение символьных позиций (start, end) для последующего восстановления контекста.
    """

    def __init__(self, data_processor: Any, max_tokens: int = 768):
        """
        Инициализация чанкера.

        :param data_processor: Объект, содержащий:
                               - words_splitter(text) → list[tuple[word, start, end]]
                               - transformer_tokenizer (HuggingFace tokenizer)
        :param max_tokens: Максимальное количество токенов в одном чанке (по умолчанию 768).
        """
        self.data_processor = data_processor
        self.max_tokens = max_tokens
        self.char_limit_per_chunk = max_tokens * 4

    async def chunk(self, text: str) -> list[tuple[str, int, int]]:
        return await asyncio.to_thread(self._chunk, text)

    def _count_tokens(self, text: str) -> int:
        """
        Подсчитывает количество токенов, которые займёт текст в GLiNER.

        :param text: Входной текст.
        :return: Количество токенов (включая специальные токены).
        """
        if not text.strip():
            return 0
        words = [w for w, _, _ in self.data_processor.words_splitter(text)]
        if not words:
            return 0
        enc = self.data_processor.transformer_tokenizer(
            words, is_split_into_words=True, add_special_tokens=True, return_length=True
        )
        return enc["length"][0]

    @staticmethod
    def _split_into_paragraphs(text: str) -> list[tuple[str, int, int]]:
        """Разбивает текст на абзацы с сохранением символьных позиций."""
        paragraphs = []
        # Паттерн ищет блоки текста, разделенные двумя или более переносами строки.
        # re.DOTALL позволяет '.' совпадать с '\n'
        for match in re.finditer(r"\S(?:.|\n)*?(?=\n{2,}|$)", text, re.DOTALL):
            paragraph_text = match.group(0).strip()
            if paragraph_text:
                paragraphs.append((paragraph_text, match.start(), match.end()))
        return paragraphs

    @staticmethod
    def _split_into_sentences(text: str, start_offset: int = 0) -> list[tuple[str, int, int]]:
        """Разбивает текст на предложения, используя более надежный regex."""
        sentences = []
        # Этот regex пытается учесть сокращения (типа г., д., стр.) и не разбивать по ним.
        # Он ищет конец предложения (.!?) за которым следует пробел и заглавная буква, или конец строки.
        sentence_ends = [m.end() for m in re.finditer(r'[.!?]\s+(?=[А-ЯA-Z"«(])|(?<=[.!?])\s*$', text)]

        last_idx = 0
        for end_idx in sentence_ends:
            sentence_text = text[last_idx:end_idx].strip()
            if sentence_text:
                sentences.append((sentence_text, start_offset + last_idx, start_offset + end_idx))
            last_idx = end_idx

        if last_idx < len(text):
            sentence_text = text[last_idx:].strip()
            if sentence_text:
                sentences.append((sentence_text, start_offset + last_idx, start_offset + len(text)))

        if not sentences and text.strip():
            return [(text.strip(), start_offset, start_offset + len(text))]

        return sentences

    @staticmethod
    def _split_by_delimiters(text: str, start_offset: int = 0) -> list[tuple[str, int, int]]:
        """
        Резервная разбивка по запятым и точкам с запятой с сохранением позиций.

        :param text: Текст для разбиения.
        :param start_offset: Смещение начала текста в исходном документе.
        :return: Список кортежей (фрагмент, start, end).
        """
        parts = []
        last = 0
        for i, c in enumerate(text):
            if c in ",;":
                part = text[last : i + 1].strip()
                if part:
                    parts.append((part, start_offset + last, start_offset + i + 1))
                last = i + 1
        # Добавляем остаток
        if last < len(text):
            part = text[last:].strip()
            if part:
                parts.append((part, start_offset + last, start_offset + len(text)))
        return parts

    def _force_split_oversized_chunk(self, chunk_text: str, start_offset: int) -> list[tuple[str, int, int]]:
        """
        Принудительно нарезает слишком длинный фрагмент текста, который не удалось разбить
        другими способами (например, одно очень длинное слово без пробелов).
        """
        sub_chunks = []
        for i in range(0, len(chunk_text), self.char_limit_per_chunk):
            sub_text = chunk_text[i : i + self.char_limit_per_chunk]
            sub_start = start_offset + i
            sub_end = sub_start + len(sub_text)
            sub_chunks.append((sub_text, sub_start, sub_end))
        return sub_chunks

    def _chunk_by_words(self, text: str, start_offset: int = 0) -> list[tuple[str, int, int]]:
        """
        Крайний случай: разбивка по словам с учётом позиций.
        Защищает от атак с использованием сверхдлинных слов.

        :param text: Текст для разбиения.
        :param start_offset: Смещение начала текста в исходном документе.
        :return: Список кортежей (фрагмент, start, end).
        """
        words_with_pos = list(self.data_processor.words_splitter(text))
        if not words_with_pos:
            return [(text, start_offset, start_offset + len(text))]

        chunks = []
        w = 0
        total = len(words_with_pos)
        base_char_start = words_with_pos[0][1]

        while w < total:
            word_chunk = []
            word_start = start_offset + (words_with_pos[w][1] - base_char_start)
            x = w

            # Жадно набираем слова, пока укладываемся в лимит
            while x < total:
                test_words = [word for word, _, _ in words_with_pos[w : x + 1]]
                test_str = " ".join(test_words)
                if self._count_tokens(test_str) <= self.max_tokens:
                    word_chunk = test_words
                    x += 1
                else:
                    break

            if word_chunk:
                word_text = " ".join(word_chunk)
                word_end = start_offset + (words_with_pos[x - 1][2] - base_char_start)
                chunks.append((word_text, word_start, word_end))
                w = x
            else:
                # НЕ удалось добавить даже одно слово (words_with_pos[w]).
                # Это означает, что само слово слишком длинное для модели.
                long_word, word_char_start, word_char_end = words_with_pos[w]
                logger.warning(
                    "Encountered a word too long for the model: '%.50s...' (length: %d chars). Splitting it.",
                    long_word,
                    len(long_word),
                )
                # Вычисляем глобальную позицию этого слова в исходном тексте
                global_word_start = start_offset + (word_char_start - base_char_start)
                # Принудительно разбиваем это одно слово на части
                forced_chunks = self._force_split_oversized_chunk(long_word, global_word_start)
                chunks.extend(forced_chunks)
                w += 1  # переходим к следующему слову

        return chunks

    def _merge_short_chunks(self, chunks: list[tuple[str, int, int]]) -> list[tuple[str, int, int]]:
        """
        Объединяет короткие чанки (< 1/3 max_tokens) со следующими, если это не нарушает лимит.

        :param chunks: Список чанков до объединения.
        :return: Список чанков после объединения.
        """
        if len(chunks) <= 1:
            return chunks

        merged = []
        i = 0
        threshold = self.max_tokens // 3

        while i < len(chunks):
            current_text, current_start, current_end = chunks[i]
            current_token_count = self._count_tokens(current_text)

            # Пытаемся объединить с последующим чанком
            if current_token_count < threshold and i + 1 < len(chunks):
                next_text, _, next_end = chunks[i + 1]
                combined = current_text + " " + next_text
                if self._count_tokens(combined) <= self.max_tokens:
                    merged.append((combined, current_start, next_end))
                    i += 2
                    continue

            merged.append(chunks[i])
            i += 1

        return merged

    def _chunk(self, text: str) -> list[tuple[str, int, int]]:
        """Основной метод: разбивает текст на чанки, подходящие для GLiNER."""
        if self._count_tokens(text) <= self.max_tokens:
            return [(text, 0, len(text))]

        # Иерархически применяем стратегии разбиения
        chunks = self._split_and_process([(text, 0, len(text))], self._split_into_paragraphs)
        chunks = self._split_and_process(chunks, self._split_into_sentences)
        chunks = self._split_and_process(chunks, self._split_by_delimiters)
        chunks = self._split_and_process(chunks, self._chunk_by_words)

        return self._merge_short_chunks(chunks)

    def _split_and_process(
        self,
        chunks_to_process: list[tuple[str, int, int]],
        split_func: callable,
    ) -> list[tuple[str, int, int]]:
        """
        Применяет функцию разбиения `split_func` к каждому чанку, который слишком длинный.
        """
        final_chunks = []
        for text, start, _ in chunks_to_process:
            if self._count_tokens(text) <= self.max_tokens:
                final_chunks.append((text, start, start + len(text)))
                continue

            # Чанк слишком длинный, разбиваем его дальше
            sub_chunks = split_func(text, start)

            # Жадное объединение полученных под-чанков
            i = 0
            n = len(sub_chunks)
            while i < n:
                current_text, current_start, _ = sub_chunks[i]
                current_end = sub_chunks[i][2]
                j = i + 1
                while j < n:
                    next_text = sub_chunks[j][0]
                    # Восстанавливаем разделитель из исходного текста для точного подсчета токенов
                    separator = text[(sub_chunks[j - 1][2] - start) : (sub_chunks[j][1] - start)]
                    test_text = current_text + separator + next_text

                    if self._count_tokens(test_text) <= self.max_tokens:
                        current_text = test_text
                        current_end = sub_chunks[j][2]
                        j += 1
                    else:
                        break

                final_chunks.append((current_text, current_start, current_end))
                i = j

        return final_chunks
