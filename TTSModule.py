import os
import json
import requests
import uuid


def tts_module(text, token):
    # Путь к шаблону JSON
    template_path = "Preset/tts_template.json"

    # Папка для сохранения аудиофайлов
    output_folder = "Output Audio"
    os.makedirs(output_folder, exist_ok=True)  # Создаем папку, если её нет

    # Чтение шаблона JSON из файла
    with open(template_path, 'r') as file:
        tts_request_data = json.load(file)

    # Добавляем ключ "input" с текстом, если его нет
    if "input" not in tts_request_data:
        tts_request_data["input"] = text
    else:
        # Если ключ уже существует, обновляем значение
        tts_request_data["input"] = text

    # URL TTS API
    url = "https://api.proxyapi.ru/openai/v1/audio/speech"

    # Заголовки с токеном
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Выполнение POST-запроса к TTS API
    response = requests.post(url, headers=headers, json=tts_request_data)

    # Проверка успешности запроса
    if response.status_code == 200:
        # Получаем бинарные данные аудио из ответа
        audio_data = response.content

        # Генерируем случайное имя файла
        audio_filename = f"{uuid.uuid4()}.ogg"
        audio_filepath = os.path.join(output_folder, audio_filename)

        # Сохраняем аудиофайл
        with open(audio_filepath, 'wb') as audio_file:
            audio_file.write(audio_data)

        print(f"Аудиофайл сохранен: {audio_filepath}")

        # Возвращаем путь к сохраненному файлу
        return audio_filepath
    else:
        print(f"Ошибка: {response.status_code} - {response.text}")
        return None


# Пример использования модуля TTS
if __name__ == "__main__":
    text = "Привет, это пример текста для генерации аудио."  # Пример текста для TTS
    token = "sk-bP0zkdB03jPrmXavHzd6R0ZLqmhlnibi"

    audio_file_path = tts_module(text, token)
    if audio_file_path:
        print(f"Путь к аудиофайлу: {audio_file_path}")
