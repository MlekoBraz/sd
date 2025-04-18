import os
import random
import string
import zipfile
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.account import GetAuthorizationsRequest
from telethon.tl.functions.contacts import GetContactsRequest

API_ID = 26160389
API_HASH = '88f5d04e3d1c3c295ab7cb89ead79f89'
TG_BOT_TOKEN = '7504133005:AAH-knGjlCFi1EZrpjDWrRR_q8kAaiMftVw'

bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher(bot)

# Генерация случайного имени бота
def generate_username():
    letters = ''.join(random.choices(string.ascii_lowercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return letters + numbers

# Приветственное сообщение при команде /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Это бот для создания новых ботов. Отправь мне файл .session или архив .zip, и я создам нового бота для твоего аккаунта.")

# Обработка файлов
@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_session_file(message: types.Message):
    # Если файл не имеет расширение .session или .zip, просим переслать правильный формат
    if not (message.document.file_name.endswith('.session') or message.document.file_name.endswith('.zip')):
        await message.reply("Пожалуйста, отправьте файл с расширением .session или архив .zip с сессиями и tdata.")
        return

    # Скачиваем файл
    file_path = f"sessions/{message.document.file_name}"
    await message.document.download(destination_file=file_path)

    # Обрабатываем .zip файл
    if file_path.endswith('.zip'):
        # Извлекаем архив
        extract_path = f"sessions/{message.document.file_name.replace('.zip', '')}"
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
            extracted_files = zip_ref.namelist()

        # Проходим по всем файлам в архиве
        session_files = [os.path.join(extract_path, fname) for fname in extracted_files if fname.endswith('.session')]

        # Если нашли .session файлы в архиве
        if session_files:
            for sess_path in session_files:
                await process_session_file(sess_path, message)

        else:
            await message.reply("В архиве не найдено файлов .session.")

    # Если это просто .session файл
    elif file_path.endswith('.session'):
        await process_session_file(file_path, message)

    # Удаляем временный файл
    os.remove(file_path)

# Функция для обработки сессии
async def process_session_file(sess_path, message):
    try:
        # Инициализация клиента Telegram с .session файлом
        client = TelegramClient(sess_path.replace('.session', ''), API_ID, API_HASH)
        await client.connect()

        # Проверка авторизации
        if not await client.is_user_authorized():
            await message.reply(f"Сессия {sess_path} не авторизована.")
            await client.disconnect()
            return

        # Получаем данные о пользователе
        me = await client.get_me()
        phone_number = me.phone or "Неизвестен"
        name = me.first_name or "Без имени"

        # Создаём нового бота через BotFather
        await client.send_message("BotFather", "/newbot")
        await client.send_message("BotFather", "MyBot")

        bot_username = generate_username()
        await client.send_message("BotFather", bot_username)

        # Ищем сообщение с токеном
        async for msg in client.iter_messages("BotFather", limit=5):
            if "Use this token to access the HTTP API" in msg.message:
                token_line = msg.message.split("`")[1]
                await message.reply(f"Авторизовано как {name}\nНомер аккаунта: +{phone_number}\nТокен: {token_line}")
                break
        await client.disconnect()

    except Exception as e:
        await message.reply(f"Ошибка при обработке {sess_path}: {str(e)}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
