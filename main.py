import random
import string
import zipfile
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InputFile
from aiogram.utils import executor
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneNumberBannedError
import time

API_TOKEN = '7504133005:AAH-knGjlCFi1EZrpjDWrRR_q8kAaiMftVw'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_data = {}

main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(
    KeyboardButton("🔐 Генерация токена по сессии"),
    KeyboardButton("📊 Мой профиль"),
    KeyboardButton("🧪 Проверка сессий")
)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"tokens": 0, "valid": 0, "invalid": 0}
    await message.answer(f"👋 Привет, {message.from_user.first_name}!\nВыбери действие ниже:", reply_markup=main_menu)

@dp.message_handler(lambda msg: msg.text == "📊 Мой профиль")
async def profile_handler(message: types.Message):
    data = user_data.get(message.from_user.id, {"tokens": 0, "valid": 0, "invalid": 0})
    await message.answer(
        f"📊 Твоя статистика:\n"
        f"Сгенерировано токенов: {data['tokens']}\n"
        f"Валидных сессий: {data['valid']}\n"
        f"Невалидных сессий: {data['invalid']}"
    )

@dp.message_handler(lambda msg: msg.text == "🔐 Генерация токена по сессии")
async def ask_for_session(message: types.Message):
    await message.answer("📩 Пришли .session или .json файл сессии")

@dp.message_handler(lambda msg: msg.text == "🧪 Проверка сессий")
async def ask_zip_file(message: types.Message):
    await message.answer("📦 Пришли архив .zip с сессиями (.session/.json)")

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_docs(message: types.Message):
    user_id = message.from_user.id
    doc = message.document
    file_path = f"downloads/{user_id}_{doc.file_name}"

    os.makedirs("downloads", exist_ok=True)
    await doc.download(destination_file=file_path)

    if doc.file_name.endswith(".zip"):
        valid, invalid = 0, 0
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            extract_path = f"downloads/extracted_{user_id}"
            zip_ref.extractall(extract_path)
            
            valid_dir = os.path.join(extract_path, "valid")
            invalid_dir = os.path.join(extract_path, "invalid")
            os.makedirs(valid_dir, exist_ok=True)
            os.makedirs(invalid_dir, exist_ok=True)

            for file in os.listdir(extract_path):
                if file.endswith(".session") or file.endswith(".json"):
                    full_path = os.path.join(extract_path, file)
                    try:
                        client = TelegramClient(full_path.replace('.session', ''), 26160389, '88f5d04e3d1c3c295ab7cb89ead79f89')
                        client.connect()
                        if not client.is_user_authorized():
                            raise Exception("not authorized")
                        valid += 1
                        os.rename(full_path, os.path.join(valid_dir, file))
                    except:
                        invalid += 1
                        os.rename(full_path, os.path.join(invalid_dir, file))
                    finally:
                        client.disconnect()

        zip_result = f"downloads/result_{user_id}.zip"
        with zipfile.ZipFile(zip_result, 'w') as result_zip:
            for folder in [valid_dir, invalid_dir]:
                for file in os.listdir(folder):
                    result_zip.write(os.path.join(folder, file), arcname=os.path.join(os.path.basename(folder), file))

        user_data[user_id]["valid"] += valid
        user_data[user_id]["invalid"] += invalid

        await message.answer(f"✅ Проверка завершена!\nВалидных: {valid}\nНевалидных: {invalid}")
        await message.answer_document(InputFile(zip_result))

    elif doc.file_name.endswith(".session") or doc.file_name.endswith(".json"):
        try:
            session_path = file_path.replace(".json", "")
            client = TelegramClient(session_path, 26160389, '88f5d04e3d1c3c295ab7cb89ead79f89')
            client.connect()
            if not client.is_user_authorized():
                raise Exception("not authorized")
            me = client.get_me()

            # Создание имени и username
            bot_name = "Bot" + ''.join(random.choices(string.ascii_letters, k=5))
            bot_username = ''.join(random.choices(string.ascii_lowercase, k=3)) + ''.join(random.choices(string.digits, k=3)) + "_bot"

            # Начинаем создание бота через BotFather
            botfather = await client.get_entity('@BotFather')
            await client.send_message(botfather, '/newbot')
            time.sleep(1)

            # Отправка названия бота
            await client.send_message(botfather, bot_name)
            time.sleep(1)

            # Отправка юзернейма для бота
            await client.send_message(botfather, bot_username)
            time.sleep(1)

            # Получаем токен для нового бота (после создания)
            messages = await client.get_messages(botfather, limit=5)
            bot_token = None
            for message in messages:
                if 'Use this token' in message.text:
                    bot_token = message.text.split('Use this token')[1].strip()
                    break

            if bot_token:
                await message.answer(
                    f"✅ Нам удалось создать бота!\n\n"
                    f"👤 Аккаунт: +{me.phone}\n"
                    f"🤖 Токен: {bot_token}"
                )

                user_data[user_id]["tokens"] += 1
            else:
                await message.answer("❌ Не удалось получить токен.")
            
            client.disconnect()

        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")

if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=True)
