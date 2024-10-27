from fuzzywuzzy import fuzz
import logging

# Поиск наиболее релевантных фрагментов в сценарии
def find_top_fragments_in_file(query, file_path, threshold, top_n):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        matches = []

        for line in lines:
            parts = line.split("]:")
            if len(parts) == 2:
                timecode = parts[0].strip("[]")
                text = parts[1].strip()

                score = fuzz.partial_ratio(query.lower(), text.lower())

                if score >= threshold:
                    matches.append((timecode, text, score))

        matches = sorted(matches, key=lambda x: x[2], reverse=True)
        logging.info(f"Найдено {len(matches)} совпадений для запроса '{query}' в файле {file_path}")
        return matches[:top_n]
    except Exception as e:
        logging.error(f"Ошибка поиска в файле {file_path}: {str(e)}")
        raise
