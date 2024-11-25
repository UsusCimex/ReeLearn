from typing import List, Dict, Tuple
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize.punkt import PunktSentenceTokenizer
import numpy as np
from dataclasses import dataclass
from core.logger import logger
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

# Download required NLTK data for multiple languages
SUPPORTED_LANGUAGES = {
    'ar': 'arabic',
    'az': 'azerbaijani',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'fi': 'finnish',
    'fr': 'french',
    'de': 'german',
    'el': 'greek',
    'hu': 'hungarian',
    'id': 'indonesian',
    'it': 'italian',
    'kk': 'kazakh',
    'ne': 'nepali',
    'no': 'norwegian',
    'pl': 'polish',
    'pt': 'portuguese',
    'ro': 'romanian',
    'ru': 'russian',
    'sl': 'slovene',
    'es': 'spanish',
    'sv': 'swedish',
    'tr': 'turkish',
    'uk': 'ukrainian',
}

try:
    # Download the complete punkt package once
    nltk.download('punkt', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK punkt data: {e}")

@dataclass
class SubtitleSegment:
    start_time: float
    end_time: float
    text: str
    language: str = None

@dataclass
class VideoFragment:
    start_time: float
    end_time: float
    text: str
    sentences: List[str]
    language: str
    
class SmartVideoFragmenter:
    def __init__(
        self,
        min_fragment_duration: float = 10.0,  # минимальная длительность в секундах
        max_fragment_duration: float = 30.0,   # максимальная длительность в секундах
        optimal_duration: float = 20.0,        # оптимальная длительность
        default_language: str = 'en'           # язык по умолчанию, если не удается определить
    ):
        self.min_duration = min_fragment_duration
        self.max_duration = max_fragment_duration
        self.optimal_duration = optimal_duration
        self.default_language = default_language
        self.sentence_tokenizers = {}
        
    def _detect_language(self, text: str) -> str:
        """Определяет язык текста."""
        try:
            detected_lang = detect(text)
            if detected_lang in SUPPORTED_LANGUAGES:
                return detected_lang
            logger.warning(f"Detected language {detected_lang} is not supported, using default")
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}")
        return self.default_language

    def _get_tokenizer(self, language: str) -> PunktSentenceTokenizer:
        """Получает или создает токенизатор для указанного языка."""
        if language not in self.sentence_tokenizers:
            try:
                # Пытаемся использовать предобученную модель для языка
                if language in SUPPORTED_LANGUAGES:
                    self.sentence_tokenizers[language] = nltk.data.load(
                        f'tokenizers/punkt/{SUPPORTED_LANGUAGES[language]}.pickle'
                    )
                else:
                    # Если язык не поддерживается, используем английский токенизатор
                    logger.warning(f"Using English tokenizer for unsupported language: {language}")
                    self.sentence_tokenizers[language] = nltk.data.load(
                        'tokenizers/punkt/english.pickle'
                    )
            except Exception as e:
                logger.error(f"Error loading tokenizer for {language}: {e}")
                self.sentence_tokenizers[language] = PunktSentenceTokenizer()
        
        return self.sentence_tokenizers[language]
        
    def _split_into_sentences(self, text: str, language: str) -> List[str]:
        """Разбивает текст на предложения с учетом языка."""
        try:
            tokenizer = self._get_tokenizer(language)
            return tokenizer.tokenize(text)
        except Exception as e:
            logger.warning(f"Error in sentence tokenization for {language}: {e}")
            # Fallback to simple splitting by punctuation
            return [s.strip() for s in text.split('.') if s.strip()]

    def _calculate_segment_coherence(self, segment1: SubtitleSegment, segment2: SubtitleSegment) -> float:
        """Оценивает связность двух сегментов текста."""
        # Проверяем, что сегменты на одном языке
        if segment1.language != segment2.language:
            return 0.0

        # Используем простую метрику для оценки связности
        words1 = set(segment1.text.lower().split())
        words2 = set(segment2.text.lower().split())
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return intersection / union if union > 0 else 0

    def _merge_coherent_segments(
        self,
        segments: List[SubtitleSegment],
        coherence_threshold: float = 0.2
    ) -> List[SubtitleSegment]:
        """Объединяет связанные по смыслу сегменты."""
        if not segments:
            return []

        merged = [segments[0]]
        for curr_segment in segments[1:]:
            prev_segment = merged[-1]
            
            # Проверяем длительность потенциального объединенного сегмента
            merged_duration = curr_segment.end_time - prev_segment.start_time
            if merged_duration > self.max_duration:
                merged.append(curr_segment)
                continue

            # Оцениваем связность текста
            coherence = self._calculate_segment_coherence(prev_segment, curr_segment)

            if coherence >= coherence_threshold:
                # Объединяем сегменты
                merged[-1] = SubtitleSegment(
                    start_time=prev_segment.start_time,
                    end_time=curr_segment.end_time,
                    text=f"{prev_segment.text} {curr_segment.text}",
                    language=prev_segment.language
                )
            else:
                merged.append(curr_segment)

        return merged

    def _adjust_fragment_boundaries(
        self,
        segments: List[SubtitleSegment]
    ) -> List[VideoFragment]:
        """Корректирует границы фрагментов для достижения оптимальной длительности."""
        fragments = []
        current_segment = segments[0]
        current_text = [current_segment.text]
        current_sentences = self._split_into_sentences(
            current_segment.text,
            current_segment.language
        )

        for next_segment in segments[1:]:
            # Если язык изменился, создаем новый фрагмент
            if current_segment.language != next_segment.language:
                fragments.append(VideoFragment(
                    start_time=current_segment.start_time,
                    end_time=next_segment.start_time,
                    text=" ".join(current_text),
                    sentences=current_sentences,
                    language=current_segment.language
                ))
                current_segment = next_segment
                current_text = [current_segment.text]
                current_sentences = self._split_into_sentences(
                    current_segment.text,
                    current_segment.language
                )
                continue

            potential_duration = next_segment.end_time - current_segment.start_time
            
            if potential_duration <= self.optimal_duration:
                # Продолжаем накапливать текст
                current_text.append(next_segment.text)
                current_sentences.extend(
                    self._split_into_sentences(next_segment.text, next_segment.language)
                )
            else:
                # Создаем новый фрагмент
                fragments.append(VideoFragment(
                    start_time=current_segment.start_time,
                    end_time=next_segment.start_time,
                    text=" ".join(current_text),
                    sentences=current_sentences,
                    language=current_segment.language
                ))
                # Начинаем новый фрагмент
                current_segment = next_segment
                current_text = [current_segment.text]
                current_sentences = self._split_into_sentences(
                    current_segment.text,
                    current_segment.language
                )

        # Добавляем последний фрагмент
        fragments.append(VideoFragment(
            start_time=current_segment.start_time,
            end_time=segments[-1].end_time,
            text=" ".join(current_text),
            sentences=current_sentences,
            language=current_segment.language
        ))

        return fragments

    def process_subtitles(
        self,
        subtitles: List[Dict[str, float]]
    ) -> List[VideoFragment]:
        """
        Основной метод обработки субтитров.
        
        Args:
            subtitles: Список словарей с ключами 'start', 'end', 'text'
            
        Returns:
            Список VideoFragment с оптимизированными границами
        """
        # Преобразуем входные данные в SubtitleSegment и определяем язык
        segments = []
        for sub in subtitles:
            language = self._detect_language(sub['text'])
            segment = SubtitleSegment(
                start_time=sub['start'],
                end_time=sub['end'],
                text=sub['text'],
                language=language
            )
            segments.append(segment)

        # Объединяем связанные сегменты
        merged_segments = self._merge_coherent_segments(segments)
        
        # Корректируем границы для достижения оптимальной длительности
        fragments = self._adjust_fragment_boundaries(merged_segments)

        # Логируем результаты
        logger.info(f"Processed {len(subtitles)} subtitles into {len(fragments)} fragments")
        language_stats = {}
        for fragment in fragments:
            language_stats[fragment.language] = language_stats.get(fragment.language, 0) + 1
            
        logger.info("Language distribution in fragments:")
        for lang, count in language_stats.items():
            lang_name = SUPPORTED_LANGUAGES.get(lang, lang)
            logger.info(f"- {lang_name}: {count} fragments")

        return fragments
