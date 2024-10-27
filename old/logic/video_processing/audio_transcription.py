import os
import logging
import whisper
import tempfile
import ffmpeg
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import warnings
import logging
from pathlib import Path

# Подавление предупреждений
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
warnings.filterwarnings("ignore", message="torch.load with weights_only=False")

# Извлечение аудио из видео
def extract_audio_from_video(video_path, audio_output_path="audio.wav"):
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_output_path, logger=None)
        logging.info(f"Аудио извлечено из видео: {video_path}")
        return audio_output_path
    except Exception as e:
        logging.error(f"Ошибка извлечения аудио из видео {video_path}: {str(e)}")
        raise

# Транскрибирование аудио с использованием Whisper
def transcribe_audio_with_timestamps(audio_path):
    try:
        model = whisper.load_model("turbo")
        result = model.transcribe(audio_path)
        logging.info(f"Аудио транскрибировано: {audio_path}")
        return result
    except Exception as e:
        logging.error(f"Ошибка транскрипции аудио {audio_path}: {str(e)}")
        raise

# Транскрибирование видео и сохранение с таймкодами
def video_to_text_with_timestamps(video_path, output_folder="scenaries"):
    try:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        os.makedirs(output_folder, exist_ok=True)
        output_file_path = os.path.join(output_folder, f"{video_name}.txt")

        audio_path = extract_audio_from_video(video_path)
        transcription_result = transcribe_audio_with_timestamps(audio_path)

        with open(output_file_path, "w", encoding="utf-8") as f:
            for segment in transcription_result['segments']:
                start = segment['start']
                end = segment['end']
                text = segment['text']
                f.write(f"[{start:.2f} - {end:.2f}]: {text}\n")

        logging.info(f"Транскрипция видео сохранена: {output_file_path}")

        # Удаление временного аудиофайла
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return output_file_path
    except Exception as e:
        logging.error(f"Ошибка транскрибирования видео {video_path}: {str(e)}")
        raise

# Транскрибирование видео с Whisper и возврат результата без создания файла
def transcribe_video_with_whisper(video_path):
    try:
        audio_path = extract_audio_from_video(video_path)
        model = whisper.load_model("turbo")
        result = model.transcribe(audio_path)
        
        # Удаление временного аудиофайла
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        logging.info(f"Аудио транскрибировано: {video_path}")
        return result
    except Exception as e:
        logging.error(f"Ошибка транскрипции видео {video_path}: {str(e)}")
        raise

def add_subtitles_with_moviepy(video_path, transcription_result):
    video = VideoFileClip(video_path)
    subtitles = []

    for segment in transcription_result['segments']:
        start_time = segment['start']
        end_time = segment['end']
        duration = end_time - start_time
        text = segment['text'].strip().replace('\n', ' ')

        txt_clip = (TextClip(text, fontsize=24, color='white', stroke_color='black', stroke_width=2, method='caption', size=video.size)
                    .set_position(('center', 'bottom'))
                    .set_duration(duration)
                    .set_start(start_time))

        subtitles.append(txt_clip)

    final_video = CompositeVideoClip([video, *subtitles])
    output_video_path = video_path.replace('.mp4', '_with_subtitles.mp4')
    final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
    return output_video_path
