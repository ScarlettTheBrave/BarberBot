import os
from dotenv import load_dotenv

# змінна з .env
load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")

# Має видати список адмінів і приведе "123,456" в перелік чисел [123, 456].
# НЕ ЗАБУТИ ЧЕКНУТИ https://core.telegram.org/bots/api!!!
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id_str) for id_str in admin_ids_str.split(",") if id_str.strip()]

# ДБ
DB_NAME = "barbershop.db"

if not BOT_TOKEN:
    exit("Помилка: Не знайдено BOT_TOKEN в файлі .env")