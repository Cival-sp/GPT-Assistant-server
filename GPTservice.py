import json
import requests

def addMessage(json_data, role, msg):
    """
    Добавляет новое сообщение в JSON-данные.

    :param json_data: dict Объект JSON, в который будет добавлено сообщение.
    :param role: str Роль отправителя сообщения (например, "user" или "assistant").
    :param msg: str Содержимое сообщения, которое будет добавлено.
    :return: dict Обновленный объект JSON с добавленным сообщением.
    """
    if "messages" not in json_data:
        json_data["messages"] = []
    json_data["messages"].append({"role": role, "content": msg})
    #print(f"Added message: role={role}, msg={msg}")
    return json_data

def extractMessageContext(token, Message_):
    """
    Извлекает контекст из сообщения с помощью GPT-модуля.

    :param token: str Токен для авторизации запроса к API.
    :param Message_: str Сообщение, из которого будет извлечен контекст.
    :return: int Длина нового сообщения, полученного из GPT.
    """
    context = gpt_module(token, Message_, json_path="Preset/gpt_extract_context.json")
    Message_ = context
    return len(context)

def importHistory(token, json_data, database, ID, message_limit=10):
    """
    Импортирует историю сообщений из базы данных в JSON-данные.

    :param token: str Токен для авторизации запроса.
    :param json_data: dict Объект JSON, в который будет импортирована история сообщений.
    :param database: dict База данных, содержащая истории сообщений по ID.
    :param ID: str Идентификатор пользователя для получения его истории сообщений.
    :param message_limit: int Ограничение на количество импортируемых сообщений (по умолчанию 20).
    :return: dict Обновленный объект JSON с добавленной историей сообщений.
    """
    if database is None:
        print("Database is None")
        return json_data

    if ID not in database:
        print(f"Не найдена история сообщений для ID: {ID}")
        return json_data

    history = database[ID].get_history()  # Получаем историю сообщений из ChatHistory
    if not isinstance(history, list):
        print(f"Expected list for history, got {type(history).__name__}")
        return json_data

    # Ограничиваем количество сообщений
    if message_limit is not None:
        history = history[:message_limit]

    for index, msg in enumerate(history):
        if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
            print(f"Invalid message format at index {index}: {msg}")
            continue
        #if index >= 3 and len(msg["content"]) > 300:
            #msg["content"] = extractMessageContext(token, msg["content"])
        json_data = addMessage(json_data, msg['role'], msg['content'])

    return json_data

def gpt_module(token, user_text=None, *, ID=None, json_path="Preset/gpt_template_voice.json", database=None):
    """
    Выполняет запрос к GPT API и обрабатывает ответ.

    :param token: str Токен для авторизации запроса к API.
    :param user_text: str Сообщение от пользователя для отправки в GPT.
    :param ID: str Идентификатор пользователя для получения истории сообщений (по желанию).
    :param json_path: str Путь к файлу шаблона JSON для запроса (по умолчанию "Preset/gpt_template_voice.json").
    :param database: dict База данных, содержащая истории сообщений по ID (по желанию).
    :return: str Ответ от GPT, если запрос успешен; иначе None.
    """
    url = "https://api.proxyapi.ru/openai/v1/chat/completions"
    if ID is not None:
        ID = str(ID)
    if user_text is not None:
        # Чтение шаблона JSON из файла
        try:
            with open(json_path, 'r') as file:
                gpt_request_data = json.load(file)
        except FileNotFoundError:
            print(f"Template file {json_path} not found.")
            return

        gpt_request_data = importHistory(token, gpt_request_data, database, ID)

        # Добавляем текущее сообщение от пользователя в массив "messages"
        if 'messages' not in gpt_request_data:
            gpt_request_data['messages'] = []
        gpt_request_data['messages'].append({
            "role": "user",
            "content": user_text
        })

        # Заголовки с токеном
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        #print(f"Request data: {json.dumps(gpt_request_data, ensure_ascii=False, indent=2)}")

        # Выполнение POST-запроса к GPT API
        print(gpt_request_data)
        response = requests.post(url, headers=headers, json=gpt_request_data)


        if response.status_code == 200:
            gpt_response = response.json()
            # Извлекаем из json ответа строку с текстом ответа
            assistant_message = gpt_response['choices'][0]['message']['content']

            if ID is not None and database is not None and ID in database:
                # Дописываем историю сообщений по ID пользователя
                print("Записано")
                database[ID].add("user", user_text)
                database[ID].add("assistant", assistant_message)

            # Передаем ответ следующему модулю для обработки
            #print(gpt_response)
            return assistant_message
        else:
            print(f"Ошибка: {response.status_code} - {response.text}")

    return