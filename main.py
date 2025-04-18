import os
import random
import string
import asyncio
import zipfile
from io import BytesIO
from telethon import TelegramClient
from telethon.tl.functions.messages import SendMessageRequest
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware

# Ваши настройки API
api_id = 26160389  # Ваш api_id
api_hash = '88f5d04e3d1c3c295ab7cb89ead79f89'  # Ваш api_hash

# Файл для хранения токенов
TOKEN_FILE = "tokens.txt"

# Вводим ваш токен для бота
bot_token = "ВАШ_ТОКЕН_ДЛЯ_Бота"

# Создаем объект бота и диспетчера для Aiogram
bot = Bot(token=bot_token)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Профиль
profile_data = {"valid_sessions": 0, "invalid_sessions": 0}

# Генерация случайного юзернейма для бота
def generate_username():
    letters = string.ascii_lowercase
    digits = string.digits
    username = ''.join(random.choice(letters + digits) for i in range(3)) + ''.join(random.choice(digits) for i in range(3)) + '_bot'
    return username

# Функция для создания бота через BotFather
async def create_bot():
    client = TelegramClient('anon', api_id, api_hash)
    await client.start()

    # Получаем все чаты
    dialogs = await client.get_dialogs()

    # Ищем BotFather
    bot_father = None
    for dialog in dialogs:
        if dialog.name == "BotFather":
            bot_father = dialog.entity
            break

    if not bot_father:
        return None

    # Отправляем команду на создание бота
    username = generate_username()
    await client.send_message(bot_father, f"/newbot")
    response = await client.get_response(bot_father)
    if "Отлично! Теперь придумайте имя" in response.text:
        await client.send_message(bot_father, "Test Bot Name")
        response = await client.get_response(bot_father)

    if "Теперь отправь мне юзернейм для бота" in response.text:
        await client.send_message(bot_father, username)
        response = await client.get_response(bot_father)

    # Вытаскиваем токен бота
    token = response.text.split(' ')[-1]
    await client.disconnect()

    return token

# Функция для проверки сессий на валидность
async def check_sessions():
    valid_sessions = []
    invalid_sessions = []
    
    # Список сессий
    sessions = ["session1.session", "session2.session", "session3.session"]  # Пример, замените на ваши сессии
    for session in sessions:
        # Проверьте, валидная ли сессия (псевдокод, замените на свою логику)
        if random.choice([True, False]):  # Симуляция проверки сессии
            valid_sessions.append(session)
        else:
            invalid_sessions.append(session)
    
    return valid_sessions, invalid_sessions

# Функция для создания архива с сессиями
def create_zip(valid_sessions, invalid_sessions):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for session in valid_sessions:
            zipf.writestr(session, "valid")  # Здесь ваши данные
        for session in invalid_sessions:
            zipf.writestr(session, "invalid")  # Здесь ваши данные
    buffer.seek(0)
    return buffer

# Статистика профиля
@dp.message_handler(commands=['profile'])
async def profile(message: types.Message):
    await message.answer(f"Профиль:\n\n"
                         f"Валидных сессий: {profile_data['valid_sessions']}\n"
                         f"Невалидных сессий: {profile_data['invalid_sessions']}")

# Мои токены
@dp.message_handler(commands=['tokens'])
async def my_tokens(message: types.Message):
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            tokens = file.readlines()
        if tokens:
            await message.answer("Ваши токены:\n\n" + "\n".join(tokens))
        else:
            await message.answer("У вас нет токенов.")
    else:
        await message.answer("У вас нет токенов.")

# Проверка сессий
@dp.message_handler(commands=['check_sessions'])
async def check_session(message: types.Message):
    valid_sessions, invalid_sessions = await check_sessions()

    # Обновляем статистику
    profile_data['valid_sessions'] += len(valid_sessions)
    profile_data['invalid_sessions'] += len(invalid_sessions)

    await message.answer(f"Проверка сессий завершена.\n\n"
                         f"Валидных сессий: {len(valid_sessions)}\n"
                         f"Невалидных сессий: {len(invalid_sessions)}")

    # Создаем архив с результатами
    zip_buffer = create_zip(valid_sessions, invalid_sessions)

    # Отправляем архив
    await message.answer_document(document=zip_buffer, filename="sessions.zip")

# Команда на создание нового бота
@dp.message_handler(commands=['create_bot'])
async def create_new_bot(message: types.Message):
    token = await create_bot()
    if token:
        # Сохраняем токен в файл
        with open(TOKEN_FILE, "a") as file:
            file.write(f"{token}\n")
        await message.answer(f"Новый бот создан! Токен: {token}")
    else:
        await message.answer("Ошибка при создании бота.")

# Запуск бота
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp)
