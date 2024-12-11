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
import torch
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import os
import shutil
from db.models.video_fragment import VideoFragment

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
        ) -> List[SubtitleSegment]:
        """
        Корректирует границы фрагментов для достижения оптимальной длительности.
        
        Args:
            segments: Список исходных сегментов
            
        Returns:
            Список оптимизированных сегментов
        """
        if not segments:
            return []
            
        optimized = []
        current_group = {
            'segments': [segments[0]],
            'start': segments[0].start_time,
            'end': segments[0].end_time,
            'language': segments[0].language
        }
        
        for next_seg in segments[1:]:
            # Вычисляем длительность если добавим следующий сегмент
            potential_duration = next_seg.end_time - current_group['start']
            current_duration = current_group['end'] - current_group['start']
            gap_duration = next_seg.start_time - current_group['end']
            
            # Проверяем условия для объединения
            can_merge = (
                current_group['language'] == next_seg.language and  # Один язык
                gap_duration <= 0.5 and                            # Небольшой разрыв
                potential_duration <= self.optimal_duration * 1.2   # Не сильно превышает оптимальную длительность
            )
            
            # Если текущая группа слишком короткая и можно объединить
            if current_duration < self.optimal_duration and can_merge:
                current_group['segments'].append(next_seg)
                current_group['end'] = next_seg.end_time
            else:
                # Создаем новый сегмент из текущей группы
                combined_text = ' '.join(seg.text for seg in current_group['segments'])
                optimized.append(SubtitleSegment(
                    start_time=current_group['start'],
                    end_time=current_group['end'],
                    text=combined_text,
                    language=current_group['language']
                ))
                
                # Начинаем новую группу
                current_group = {
                    'segments': [next_seg],
                    'start': next_seg.start_time,
                    'end': next_seg.end_time,
                    'language': next_seg.language
                }
        
        # Добавляем последнюю группу
        if current_group['segments']:
            combined_text = ' '.join(seg.text for seg in current_group['segments'])
            optimized.append(SubtitleSegment(
                start_time=current_group['start'],
                end_time=current_group['end'],
                text=combined_text,
                language=current_group['language']
            ))
        
        return optimized

    def process_subtitles(
            self,
            subtitles: List[SubtitleSegment]
        ) -> List[VideoFragment]:
        """
        Основной метод обработки субтитров.
        
        Args:
            subtitles: Список объектов SubtitleSegment
            
        Returns:
            Список VideoFragment с оптимизированными границами
        """
        # Фильтрация пустых сегментов
        segments = [sub for sub in subtitles if sub.text.strip()]
        if not segments:
            return []
            
        # Оптимизация границ фрагментов
        optimized_segments = self._adjust_fragment_boundaries(segments)
        
        # Создание фрагментов
        fragments = []
        for segment in optimized_segments:
            # Разбиение текста на предложения
            sentences = self._split_into_sentences(segment.text, segment.language)
            
            # Создание фрагмента
            fragment = VideoFragment(
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=segment.text,
                sentences=sentences,
                language=segment.language,
                tags=[]  # TODO: Добавить извлечение тегов
            )
            fragments.append(fragment)
            
        return fragments

    def process_video(self, video_path: str) -> List[VideoFragment]:
        """
        Process video file and extract fragments with subtitles.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            List[VideoFragment]: List of video fragments with subtitles
        """
        try:
            # Import VideoProcessor here to avoid circular import
            from services.processing_service import VideoProcessor
            
            # Extract subtitles using VideoProcessor
            processor = VideoProcessor()
            fragments = processor.extract_subtitles(video_path)
            
            # Convert fragments to SubtitleSegments
            segments = []
            for fragment in fragments:
                # Detect language for each fragment
                language = self._detect_language(fragment.text)
                fragment.language = language
                
                segment = SubtitleSegment(
                    start_time=fragment.start_time,
                    end_time=fragment.end_time,
                    text=fragment.text,
                    language=language
                )
                segments.append(segment)
            
            # Process segments into optimized fragments
            video_fragments = self.process_subtitles(segments)
            
            # Create temporary directory for fragment processing
            temp_dir = os.path.join(os.path.dirname(video_path), 'temp_fragments')
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # Process each fragment
                for fragment in video_fragments:
                    # Cut and upload fragment
                    s3_url = processor.process_and_upload_fragment(
                        video_path,
                        temp_dir,
                        fragment
                    )
                    # Update fragment with S3 URL
                    fragment.s3_url = s3_url
                
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                return video_fragments
                
            except Exception as e:
                logger.error(f"Error processing video fragments: {e}")
                # Clean up on error
                shutil.rmtree(temp_dir, ignore_errors=True)
                raise
                
        except Exception as e:
            logger.error(f"Error in video processing: {e}")
            raise
