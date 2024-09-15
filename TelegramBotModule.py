import asyncio
import io
import aiohttp
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

BOT_TOKEN = '7394227511:AAE3d1iyhGaWLQhRqv-9LUvrIMDQyBXEw34'

TEXT_URL = 'http://localhost:5000/chat'
AUDIO_URL = 'http://localhost:5000/say'

async def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    await update.message.reply_text(
        'Привет! Отправь мне текст или голосовое сообщение.\nК сожалению, я пока не запоминаю историю сообщений, задавай полный вопрос.'
    )

async def handle_text(update: Update, context: CallbackContext) -> None:
    """Обработка текстового сообщения"""
    text = update.message.text
    print(f"Запрос: {text}")

    # Асинхронный POST-запрос для отправки текста на сервер
    async with aiohttp.ClientSession() as session:
        async with session.post(TEXT_URL, json={'text': text}) as response:
            if response.status == 200:
                result = await response.json()
                result_text = result.get('response', 'Ошибка обработки текста')
                print(f"Ответ: {result_text}")
                await update.message.reply_text(result_text)
            else:
                await update.message.reply_text('Ошибка запроса к серверу.')

async def handle_audio(update: Update, context: CallbackContext) -> None:
    """Обработка голосового сообщения"""
    file = await update.message.voice.get_file()

    # Скачивание голосового сообщения как bytearray
    audio_data = await file.download_as_bytearray()

    # Преобразование bytearray в BytesIO
    audio_bytes = io.BytesIO(audio_data)

    # Создание формы для отправки файла на сервер
    form = aiohttp.FormData()
    form.add_field('file', audio_bytes, filename='audio.ogg', content_type='audio/ogg')

    # Асинхронный POST-запрос для отправки аудиофайла на сервер
    async with aiohttp.ClientSession() as session:
        async with session.post(AUDIO_URL, data=form) as response:
            if response.status == 200:
                audio_wav = io.BytesIO(await response.read())
                await update.message.reply_voice(voice=InputFile(audio_wav, filename='response.wav'))
            else:
                await update.message.reply_text('Ошибка запроса к серверу.')

async def main() -> None:
    """Основная функция для запуска бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчики команд и сообщений
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_audio))

    # Запуск long-polling
    await application.run_polling()