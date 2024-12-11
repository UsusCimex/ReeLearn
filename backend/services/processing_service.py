from dataclasses import dataclass
from typing import List, Dict, Optional
from whisper import load_model
import subprocess
import os
import logging
import uuid
from utils.s3_utils import upload_file_to_s3
from db.models.video_fragment import VideoFragment

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, model_name: str = "base"):
        self.model = load_model(model_name)
    
    def optimize_fragments(
        self,
        fragments: List[VideoFragment],
        target_duration: float = 4.5,
        max_duration: float = 5.5
    ) -> List[VideoFragment]:
        """
        Разбивает фрагменты на более мелкие части фиксированной длительности.
        
        Args:
            fragments: Исходные фрагменты
            target_duration: Целевая длительность фрагмента
            max_duration: Максимальная длительность фрагмента
        """
        if not fragments:
            return []
        
        optimized = []
        
        for fragment in fragments:
            duration = fragment.end_time - fragment.start_time
            
            # Если фрагмент короче целевой длительности, оставляем как есть
            if duration <= target_duration:
                optimized.append(fragment)
                continue
                
            # Разбиваем длинный фрагмент на части
            num_parts = max(2, int(duration / target_duration))
            part_duration = duration / num_parts
            
            # Создаем новые фрагменты
            for i in range(num_parts):
                start = fragment.start_time + (i * part_duration)
                end = min(fragment.end_time, start + part_duration)
                
                # Определяем текст для фрагмента
                text_start_ratio = (start - fragment.start_time) / duration
                text_end_ratio = (end - fragment.start_time) / duration
                text_words = fragment.text.split()
                text_start_idx = int(len(text_words) * text_start_ratio)
                text_end_idx = int(len(text_words) * text_end_ratio)
                text_part = ' '.join(text_words[text_start_idx:text_end_idx + 1])
                
                new_fragment = VideoFragment(
                    start_time=start,
                    end_time=end,
                    text=text_part,
                    sentences=[text_part],
                    language=fragment.language,
                    speech_confidence=fragment.speech_confidence,
                    no_speech_prob=fragment.no_speech_prob
                )
                optimized.append(new_fragment)
        
        return optimized

    def extract_audio(self, video_path: str) -> str:
        """Извлекает аудио из видео."""
        audio_path = f"{os.path.splitext(video_path)[0]}.wav"
        command = [
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            '-y', audio_path
        ]
        
        process = subprocess.run(command, capture_output=True, text=True)
        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {process.stderr}")
        
        return audio_path

    def extract_subtitles(self, video_path: str) -> List[VideoFragment]:
        """
        Извлекает субтитры из видео используя Whisper.
        
        Args:
            video_path: Путь к видео файлу
            
        Returns:
            List[VideoFragment]: Список фрагментов с субтитрами
        """
        try:
            # Транскрибируем видео
            result = self.model.transcribe(
                video_path,
                task="transcribe",
                language=None,
                word_timestamps=True
            )
            
            # Конвертируем результаты в VideoFragment
            fragments = []
            for segment in result['segments']:
                if segment.get('no_speech_prob', 0) > 0.5:
                    continue
                
                fragments.append(VideoFragment(
                    start_time=float(segment['start']),
                    end_time=float(segment['end']),
                    text=segment['text'].strip(),
                    sentences=[segment['text'].strip()],
                    language="",  # Language will be detected later
                    speech_confidence=1.0 - segment.get('no_speech_prob', 0),
                    no_speech_prob=segment.get('no_speech_prob', 0)
                ))
            
            # Оптимизируем фрагменты по длительности
            return self.optimize_fragments(fragments)
            
        except Exception as e:
            logger.error(f"Error extracting subtitles: {str(e)}")
            raise

    def cut_video_segment(
        self,
        video_path: str,
        output_path: str,
        start_time: float,
        end_time: float
    ) -> bool:
        """Вырезает сегмент из видео."""
        command = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(start_time),
            '-t', str(end_time - start_time),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',
            output_path
        ]
        
        process = subprocess.run(command, capture_output=True, text=True)
        return process.returncode == 0
    
    def process_and_upload_fragment(
        self,
        video_path: str,
        temp_dir: str,
        fragment: VideoFragment
    ) -> Optional[str]:
        """Обрабатывает и загружает фрагмент видео в S3."""
        try:
            fragment_filename = f"fragment_{uuid.uuid4()}.mp4"
            fragment_path = os.path.join(temp_dir, fragment_filename)
            
            # Вырезаем фрагмент видео
            if not self.cut_video_segment(
                video_path,
                fragment_path,
                fragment.start_time,
                fragment.end_time
            ):
                logger.error("Failed to cut video segment")
                return None
            
            # Загружаем фрагмент в S3
            s3_key = upload_file_to_s3(fragment_path, f"fragments/{fragment_filename}")
            
            # Очищаем временный файл
            try:
                os.remove(fragment_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {fragment_path}: {e}")
            
            return s3_key
            
        except Exception as e:
            logger.error(f"Error processing fragment: {str(e)}")
            return None
