from flask import Flask, request, send_file, jsonify, render_template, make_response
from werkzeug.utils import secure_filename
from flask_cors import CORS
import asyncio
import os
import signal
import sys
import threading
import time

from STTService import stt_module
from GPTservice import gpt_module
from TTSModule import tts_module
from Identifier import IDPool
from Utility import *
from TelegramBotModule import main as run_telegram_bot

AiServer_enable = True
WebServer_enable = True
TgBot_enable = False

INPUT_FOLDER = "input_audio"
OUTPUT_FOLDER = "output_audio"
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'}

OpenAiToken = "sk-bP0zkdB03jPrmXavHzd6R0ZLqmhlnibi"

os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs("Page", exist_ok=True)
os.makedirs("TgBot", exist_ok=True)

user_id_pool = IDPool(100, 3600 / 2)

AiServer = Flask(__name__)
TgBot = Flask(__name__)
WebServer = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'Page'))

# Настраиваем CORS
CORS(AiServer)

def signal_handler(sig, frame):
    print("Завершение программы")
    sys.exit(0)

def run_server(app, host, port):
    app.run(host=host, port=port)

def allowed_file(filename):
    return True  # Здесь можно добавить проверку на расширение файла

def process_audio(input_filepath):
    rec_text = stt_module(input_filepath, OpenAiToken)
    answer_text = gpt_module(rec_text, OpenAiToken)
    response_filepath = tts_module(answer_text, OpenAiToken)
    return response_filepath, answer_text

async def run_telegram_bot_async():
    await run_telegram_bot()

def run_telegram_bot_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_telegram_bot_async())

@AiServer.route('/say', methods=['POST'])
def say():
    if 'file' not in request.files:
        return "No file part", 401

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 402

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_filepath = os.path.join(INPUT_FOLDER, filename)
        file.save(input_filepath)

        output_filepath, answer_text = process_audio(input_filepath)
        text = request.args.get('text')
        user_id = request.args.get('id')
        if user_id is None:
            user_id = user_id_pool.get_id(request.remote_addr, request.headers.get('User-Agent'))
        else:
            if user_id_pool.is_expired(user_id):
                user_id = user_id_pool.get_id(request.remote_addr, request.headers.get('User-Agent'))

        if text is not None:
            response_data = {
                "text": answer_text,
                "audio_file_url": f"/download/{os.path.basename(output_filepath)}"
            }
            return jsonify(response_data)

        return send_file(output_filepath, as_attachment=True, download_name=filename)

    return "File type not allowed", 403

@AiServer.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
    user_text = data['text']
    answer_text = gpt_module(user_text, OpenAiToken)
    return jsonify({"response": answer_text})

@AiServer.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

@WebServer.route("/live_chat", methods=['GET'])
def live_chat():
    return render_template("live_chat.html")

@WebServer.route("/live_chat_audio", methods=['GET'])
def live_chat_audio():
    return render_template('with_audio.html')

if __name__ == '__main__':
    threads = []
    if AiServer_enable:
        ai_thread = threading.Thread(target=run_server, args=(AiServer, '0.0.0.0', 5000))
        ai_thread.daemon = True
        ai_thread.start()
        threads.append(ai_thread)

    if WebServer_enable:
        web_thread = threading.Thread(target=run_server, args=(WebServer, '0.0.0.0', 5001))
        web_thread.daemon = True
        web_thread.start()
        threads.append(web_thread)

    if TgBot_enable:
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

    print("Все потоки завершены")
