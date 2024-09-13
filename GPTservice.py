import json
import requests


def gpt_module(recognized_text, token):
    # Путь к шаблону JSON
    template_path = "Preset/gpt_template.json"

    # Чтение шаблона JSON из файла
    with open(template_path, 'r') as file:
        gpt_request_data = json.load(file)

    # Добавляем сообщение от пользователя в массив "messages"
    gpt_request_data['messages'].append({
        "role": "user",
        "content": recognized_text
    })

    # URL GPT API
    url = "https://api.proxyapi.ru/openai/v1/chat/completions"

    # Заголовки с токеном
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Выполнение POST-запроса к GPT API
    response = requests.post(url, headers=headers, json=gpt_request_data)

    # Проверка успешности запроса
    if response.status_code == 200:
        # Получаем JSON-ответ от сервера
        gpt_response = response.json()

        # Передаем ответ следующему модулю для обработки
        assistant_message = gpt_response['choices'][0]['message']['content']
        return assistant_message
    else:
        print(f"Ошибка: {response.status_code} - {response.text}")


# Пример следующего модуля
def process_gpt_response(gpt_response):
    print("Ответ от GPT API:")
    #print(json.dumps(gpt_response, indent=2))  # Форматированный вывод ответа
    assistant_message = gpt_response['choices'][0]['message']['content']

    # Декодирование закодированных символов Unicode
    print(assistant_message)


# Пример использования модуля GPT
if __name__ == "__main__":
    recognized_text = "Расскажи мне какую нибудь историю"  # Пример распознанного текста
    token = "sk-bP0zkdB03jPrmXavHzd6R0ZLqmhlnibi"

    gpt_module(recognized_text, token)
