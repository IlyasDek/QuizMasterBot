import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
import handlers
from dotenv import load_dotev

logging.basicConfig(level=logging.INFO)
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    raise ValueError("Токен бота не найден в переменных окружения!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(handlers.router)

async def process_event(event):
    update = types.Update.parse_raw(event['body'])
    await dp.feed_update(bot, update)

async def webhook(event, context):
    if event['httpMethod'] == 'POST':
        await process_event(event)
        return {'statusCode': 200, 'body': 'ok'}
    else:
        return {'statusCode': 405, 'body': 'Method Not Allowed'}