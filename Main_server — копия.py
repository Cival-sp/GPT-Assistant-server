import os
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

import subprocess

from STTService import stt_module
from GPTservice import gpt_module
from TTSModule import tts_module

app = Flask(__name__)

# Настраиваем CORS
CORS(app)

# Папка для сохранения входящих аудиофайлов
INPUT_FOLDER = "Input Audio"
# Папка для сохранения обработанных аудиофайлов
OUTPUT_FOLDER = "Output Audio"
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Маршрут для загрузки аудиофайла
@app.route('/upload', methods=['POST'])
def upload_audio():
    # Проверяем, есть ли файл в запросе
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']

    # Проверяем, что файл выбран
    if file.filename == '':
        return "No selected file", 400

    # Сохраняем файл с безопасным именем
    if file:
        filename = secure_filename(file.filename)
        input_filepath = os.path.join(INPUT_FOLDER, filename)
        file.save(input_filepath)

        # Вызываем другой модуль для обработки
        output_filepath = process_audio(input_filepath)

        # Возвращаем обработанный аудиофайл клиенту
        return send_file(output_filepath, as_attachment=True)


# Маршрут для обработки текстовых сообщений
@app.route('/chat', methods=['POST'])
def chat():
    # Получаем текст из запроса
    data = request.get_json()
    if 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    user_text = data['text']

    # Обрабатываем текст через GPT
    answer_text = gpt_module(user_text, token)

    # Возвращаем текстовый ответ
    return jsonify({"response": answer_text})


def process_audio(input_filepath):
    # Получаем текст из аудиофайла
    rec_text = stt_module(input_filepath, token)
    # Обрабатываем текст через GPT
    answer_text = gpt_module(rec_text, token)
    # Преобразуем ответ в аудиофайл
    response_filepath = tts_module(answer_text, token)

    return response_filepath


if __name__ == '__main__':
    token = "sk-bP0zkdB03jPrmXavHzd6R0ZLqmhlnibi"
    app.run('0.0.0.0', port=5000)
