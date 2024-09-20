print("\nЗапуск сервера\n")
from flask import Flask, request, send_file, jsonify, render_template, make_response, g
from werkzeug.utils import secure_filename
from flask_cors import CORS
import asyncio
import signal
import sys
import threading
import secrets
import string


from DatabaseModule import Users, Person, UserDatabase
from STTService import stt_module
from GPTservice import gpt_module, addMessage, importHistory
from TTSModule import tts_module
from Identifier import IDPool
from Utility import *
from TelegramBotModule import main as run_telegram_bot

def loadCfg(FileName):
    """
    Загружает конфигурацию из указанного JSON-файла.

    :param FileName: str Путь к файлу конфигурации.
    :return: dict Словарь с настройками конфигурации.
    :raises FileNotFoundError: Если файл конфигурации не найден.
    :raises Exception: Если произошла ошибка при чтении файла.
    """
    try:
        with open(FileName, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print("Файл конфигурации не найден. Остановка программы")
        sys.exit()
    except Exception as e:
        print(f"Ошибка во время чтения файла конфигурации:{e} \nОстановка программы")
        sys.exit()
def generate_random_key(length=16):
    # Определяем возможные символы для ключа (только цифры)
    characters = '0123456789'
    # Генерируем случайный ключ заданной длины
    random_key = ''.join(secrets.choice(characters) for _ in range(length))
    return random_key

ServerConfiguration = loadCfg("config.json")
print("-------------CONFIG--------------")
for key, value in ServerConfiguration.items():
    print(f"    {key} = {value}")

Database = Users  # UserId : ChatHistory
user_id_pool = IDPool(1000)

print("-----------SHUTDOWN--KEY---------")
shutdown_key = generate_random_key(32)
print(shutdown_key)
print("---------------------------------")
AiServer = Flask(__name__)
WebServer = Flask(__name__, template_folder=os.path.join(os.getcwd(), ServerConfiguration["TemplateFolder"]))

# Настраиваем CORS
CORS(AiServer)



def Shutdown():
    # Дождаться завершения всех потоков
    for thread in threads:
        thread.join()

    # Сохранить данные пользователей перед завершением
    for user in Database.values():
        user.save()

def FolderInit():
    """
    Инициализирует папки для ввода и вывода файлов, а также для шаблонов и бота Telegram.
    """
    os.makedirs(ServerConfiguration["INPUT_FOLDER"], exist_ok=True)
    os.makedirs(ServerConfiguration["OUTPUT_FOLDER"], exist_ok=True)
    os.makedirs(ServerConfiguration["TemplateFolder"], exist_ok=True)
    os.makedirs("TgBot", exist_ok=True)

def saveTextInDatabase(ID, database, text, role="user"):
    """
    Сохраняет текст сообщения в базе данных для указанного пользователя.

    :param ID: str Идентификатор пользователя.
    :param database: dict База данных пользователей.
    :param text: str Текст сообщения для сохранения.
    :param role: str Роль отправителя сообщения (по умолчанию "user").
    """
    if ID is not None:
        userchat = database[ID]
        userchat.append(role, text)

def signal_handler(sig, frame):
    """
    Обработчик сигнала завершения программы.

    :param sig: int Код сигнала.
    :param frame: object Контекст выполнения.
    """
    print("Завершение программы")
    sys.exit(0)

def run_server(app, host, port):
    """
    Запускает сервер Flask на указанном хосте и порту.

    :param app: Flask приложение для запуска.
    :param host: str Хост, на котором будет запущен сервер.
    :param port: int Порт, на котором будет запущен сервер.
    """
    app.run(host=host, port=port)

def allowed_file(filename):
    """
    Проверяет, допустимо ли расширение файла.

    :param filename: str Имя файла для проверки.
    :return: bool True, если файл допустим, иначе False.
    """
    return True  # Здесь можно добавить проверку на расширение файла

def process_audio(input_filepath, USERID=None):
    """
    Обрабатывает аудиофайл, извлекая текст и получая ответ от GPT.

    :param input_filepath: str Путь к входному аудиофайлу.
    :param USERID: str Идентификатор пользователя (по желанию).
    :return: tuple (response_filepath, answer_text) Путь к выходному файлу и текст ответа.
    """
    response_filepath = None
    answer_text = None
    try:
        # Выделяем текст из аудиофайла
        rec_text = stt_module(input_filepath, ServerConfiguration["OpenAiToken"])
        # Записываем в историю чата
        saveTextInDatabase(USERID, Database, rec_text)
        # Отправляем текст к GPT
        answer_text = gpt_module(ServerConfiguration["OpenAiToken"], user_text=rec_text, ID=USERID,
                                 json_path="Preset/gpt_template_chat.json", database=Database)
    except Exception as e:
        print(f"Ошибка в обработке запроса: {e}")
    answer_text = answer_text or "Извините. В текущий момент, я не могу обработать ваш запрос"
    return response_filepath, answer_text

async def run_telegram_bot_async():
    """
    Асинхронно запускает Telegram бота.
    """
    await run_telegram_bot()

def run_telegram_bot_in_thread(loop):
    """
    Запускает Telegram бота в отдельном потоке.

    :param loop: asyncio.AbstractEventLoop Асинхронный цикл событий.
    """
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_telegram_bot_async())



@AiServer.before_request
def RequestPreHandler():
    """
    Обрабатывает запросы перед их выполнением, устанавливая идентификатор пользователя.
    """
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    ID = user_id_pool.getId(user_ip, user_agent)
    g.user_id = ID
    ID = str(ID)
    emptyHistory = ChatHistory()
    Database.setdefault(ID, emptyHistory)
    print(f"Пользователь- ID:{ID} IP:{user_ip} User-Agent:{user_agent}")

@AiServer.route('/say', methods=['POST'])
def say():
    """
    Обрабатывает POST-запрос с аудиофайлом и возвращает ответ от GPT.

    :return: Response Ответ с файлом или сообщением об ошибке.
    """
    if 'file' not in request.files:
        return "No file part", 401

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 402

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_filepath = os.path.join(ServerConfiguration["INPUT_FOLDER"], filename)
        file.save(input_filepath)
        output_filepath, answer_text = process_audio(input_filepath)

        user_id = g.user_id
        if user_id is None:
            return "User doesn't have ID", 506
        if output_filepath is None:
            return "No output file found", 505
        return send_file(output_filepath, as_attachment=True, download_name=filename)

    return "File type not allowed", 403

@AiServer.route('/chat', methods=['POST'])
def chat():
    """
    Обрабатывает POST-запрос с текстом и возвращает ответ от GPT.

    :return: jsonify JSON-ответ с текстом ответа или ошибкой.
    """
    data = request.get_json()
    if 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
    user_text = data['text']
    answer_text = gpt_module(ServerConfiguration["OpenAiToken"], user_text=user_text, ID=g.user_id,
                             json_path="Preset/gpt_template_chat.json", database=Database)
    return jsonify({"response": answer_text})

@AiServer.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Позволяет пользователю скачать файл по указанному имени.

    :param filename: str Имя файла для скачивания.
    :return: Response Ответ с файлом или сообщением об ошибке.
    """
    return send_file(os.path.join(ServerConfiguration["OUTPUT_FOLDER"], filename), as_attachment=True)

@WebServer.route("/live_chat", methods=['GET'])
def live_chat():
    """
    Отображает страницу живого чата.

    :return: Response HTML-шаблон для живого чата.
    """
    return render_template("live_chat.html")

@WebServer.route("/live_chat_audio", methods=['GET'])
def live_chat_audio():
    """
    Отображает страницу живого чата с поддержкой аудио.

    :return: Response HTML-шаблон для живого чата с аудио.
    """
    return render_template('with_audio.html')
@WebServer.route("/favicon.ico", methods=['GET'])
def favicon():

    return

@WebServer.route("/shutdown", methods=['GET'])
def exit():
    req_key = request.args.get('key')
    #print(req_key)
    #print(shutdown_key)
    if req_key == shutdown_key:
        print("Завершение программы")
        Shutdown()
        sys.exit(0)
        return "Done", 200
    else: return "Bad key",400


if __name__ == '__main__':
    threads = []
    FolderInit()


    if ServerConfiguration["AiServer_enable"]:
        ai_thread = threading.Thread(target=run_server, args=(AiServer, '0.0.0.0', ServerConfiguration["AiServer_port"]))
        ai_thread.daemon = True
        ai_thread.start()
        threads.append(ai_thread)

    if ServerConfiguration["WebServer_enable"]:
        web_thread = threading.Thread(target=run_server, args=(WebServer, '0.0.0.0', ServerConfiguration["WebServer_port"]))
        web_thread.daemon = True
        web_thread.start()
        threads.append(web_thread)

    if ServerConfiguration["TgBot_enable"]:
        loop = asyncio.new_event_loop()
        tg_thread = threading.Thread(target=run_telegram_bot_in_thread, args=(loop,))
        tg_thread.daemon = True
        tg_thread.start()
        threads.append(tg_thread)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Основной поток прерван, программа завершится.")
        Shutdown()
        sys.exit(0)


    print("Все потоки завершены")

