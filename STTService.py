import requests
import mimetypes

def stt_module(file_path, token):
    # URL STT API
    url = "https://api.proxyapi.ru/openai/v1/audio/transcriptions"

    # Формируем заголовки с авторизацией
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Параметры запроса
    data = {
        "model": "whisper-1",
        "response_format": "text"
    }

    # Определяем MIME-тип по расширению файла
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'audio/wav'  # По умолчанию, если не удается определить MIME-тип

    # Открываем файл для отправки
    with open(file_path, 'rb') as f:
        files = {
            'file': (file_path, f, mime_type)
        }

        # Выполняем POST-запрос к STT API
        response = requests.post(url, headers=headers, data=data, files=files)

        # Проверка статуса ответа
        if response.status_code == 200:
            # Получаем JSON-ответ
            result = response.json()

            # Извлекаем текст из ключа 'text'
            recognized_text = result.get("text")

            if recognized_text:
                print(f"Распознанный текст: {recognized_text}")

                # Возвращаем распознанный текст
                return recognized_text
            else:
                print("Ошибка: текст не найден в ответе.")
        else:
            print(f"Ошибка: {response.status_code} - {response.text}")


# Пример следующего модуля
def text_processing_module(recognized_text):
    print(f"Обработка текста: {recognized_text}")
    # Здесь можно реализовать дальнейшую обработку текста


# Пример использования модуля STT
if __name__ == "__main__":
    file_path = "Input Audio/329564358_469662544.ogg"
    token = "sk-bP0zkdB03jPrmXavHzd6R0ZLqmhlnibi"

    recognized_text = stt_module(file_path, token)
    if recognized_text:
        text_processing_module(recognized_text)
