from typing import List, Optional, Dict
from dataclasses import dataclass
from langdetect import detect
import nltk
from core.config import settings
from nltk.tokenize import sent_tokenize
from nltk.tokenize.punkt import PunktSentenceTokenizer
import numpy as np
from core.logger import logger
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
    tags: List[str] = None

class SmartVideoFragmenter:
    def __init__(
        self,
        min_fragment_duration: float = settings.VIDEO_MIN_FRAGMENT_DURATION,
        max_fragment_duration: float = settings.VIDEO_MAX_FRAGMENT_DURATION,
        optimal_duration: float = settings.VIDEO_OPTIMAL_DURATION,
        default_language: str = settings.VIDEO_DEFAULT_LANGUAGE,
        max_sentences_per_fragment: int = settings.VIDEO_MAX_SENTENCES_PER_FRAGMENT
    ):
        self.min_duration = min_fragment_duration
        self.max_duration = max_fragment_duration
        self.optimal_duration = optimal_duration
        self.default_language = default_language
        self.max_sentences = max_sentences_per_fragment
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
        current_start_time = current_segment.start_time

        def create_fragment(end_time):
            return VideoFragment(
                start_time=current_start_time,
                end_time=end_time,
                text=" ".join(current_text),
                sentences=current_sentences.copy(),
                language=current_segment.language
            )

        for next_segment in segments[1:]:
            next_sentences = self._split_into_sentences(next_segment.text, next_segment.language)
            next_duration = next_segment.end_time - current_start_time
            
            # Создаем новый фрагмент если:
            # 1. Изменился язык
            # 2. Превышен лимит предложений
            # 3. Превышена оптимальная длительность И текущее предложение завершено
            if (current_segment.language != next_segment.language or 
                len(current_sentences) >= self.max_sentences or 
                (next_duration > self.optimal_duration and 
                 not (current_text[-1].endswith('...') or 
                      next_segment.text.startswith('...')))):
                
                fragments.append(create_fragment(next_segment.start_time))
                current_start_time = next_segment.start_time
                current_segment = next_segment
                current_text = [current_segment.text]
                current_sentences = next_sentences
                continue

            # Продолжаем накапливать текст
            current_text.append(next_segment.text)
            current_sentences.extend(next_sentences)
            current_segment = next_segment

        # Добавляем последний фрагмент
        if current_text:
            fragments.append(create_fragment(segments[-1].end_time))

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
        if not subtitles:
            return []

        # Преобразуем входные данные в SubtitleSegment и определяем язык
        segments = []
        for sub in subtitles:
            # Пропускаем пустые субтитры
            if not sub['text'].strip():
                continue
                
            # Определяем язык для каждого сегмента
            language = self._detect_language(sub['text'])
            
            # Разбиваем текст на предложения
            sentences = self._split_into_sentences(sub['text'], language)
            
            # Если нет предложений, используем весь текст как одно предложение
            if not sentences:
                sentences = [sub['text']]
            
            # Вычисляем среднюю длительность на символ
            duration = sub['end'] - sub['start']
            chars_per_second = len(sub['text']) / duration if duration > 0 else 1.0
            
            # Если сегмент слишком длинный, разбиваем его на части
            if duration > self.max_duration:
                current_start = sub['start']
                current_text = []
                current_chars = 0
                
                for sentence in sentences:
                    sentence_chars = len(sentence)
                    sentence_duration = sentence_chars / chars_per_second
                    
                    # Если добавление предложения превысит оптимальную длительность
                    # и уже есть накопленный текст, создаем новый сегмент
                    if current_text and (current_chars + sentence_chars) / chars_per_second > self.optimal_duration:
                        text = " ".join(current_text)
                        segment_duration = current_chars / chars_per_second
                        segments.append(SubtitleSegment(
                            start_time=current_start,
                            end_time=current_start + segment_duration,
                            text=text,
                            language=language
                        ))
                        current_start = current_start + segment_duration
                        current_text = [sentence]
                        current_chars = sentence_chars
                    else:
                        current_text.append(sentence)
                        current_chars += sentence_chars
                
                # Добавляем последний накопленный текст
                if current_text:
                    segments.append(SubtitleSegment(
                        start_time=current_start,
                        end_time=sub['end'],
                        text=" ".join(current_text),
                        language=language
                    ))
            else:
                segments.append(SubtitleSegment(
                    start_time=sub['start'],
                    end_time=sub['end'],
                    text=sub['text'],
                    language=language
                ))

        if not segments:
            return []

        # Объединяем короткие сегменты
        merged_segments = []
        current = segments[0]
        
        for next_seg in segments[1:]:
            # Проверяем возможность объединения
            merged_duration = next_seg.end_time - current.start_time
            gap_duration = next_seg.start_time - current.end_time
            
            can_merge = (
                current.language == next_seg.language and  # Один язык
                merged_duration <= self.max_duration and   # Не превышает максимальную длительность
                gap_duration <= 0.1 and                    # Нет большого разрыва между сегментами
                len(self._split_into_sentences(current.text + " " + next_seg.text, current.language)) <= self.max_sentences  # Не превышает лимит предложений
            )
            
            if can_merge:
                # Объединяем сегменты
                current = SubtitleSegment(
                    start_time=current.start_time,
                    end_time=next_seg.end_time,
                    text=f"{current.text} {next_seg.text}",
                    language=current.language
                )
            else:
                merged_segments.append(current)
                current = next_seg
        
        # Добавляем последний сегмент
        merged_segments.append(current)

        # Преобразуем в VideoFragment
        fragments = []
        for segment in merged_segments:
            sentences = self._split_into_sentences(segment.text, segment.language)
            if not sentences:
                sentences = [segment.text]
            
            fragments.append(VideoFragment(
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=segment.text,
                sentences=sentences,
                language=segment.language
            ))

        return fragments
