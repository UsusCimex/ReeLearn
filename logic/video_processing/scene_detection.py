from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
import logging
import warnings

# Подавление предупреждений о VideoManager
warnings.filterwarnings("ignore", message="VideoManager is deprecated and will be removed.")

# Функция для обнаружения сцен в видео
def find_scenes(video_file):
    try:
        video_manager = VideoManager([video_file])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector())

        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)

        scene_list = scene_manager.get_scene_list()
        scene_boundaries = [(scene[0].get_seconds(), scene[1].get_seconds()) for scene in scene_list]
        video_manager.release()

        logging.info(f"Найдено {len(scene_list)} сцен в видео: {video_file}")
        return scene_boundaries
    except Exception as e:
        logging.error(f"Ошибка обнаружения сцен в видео {video_file}: {str(e)}")
        raise
