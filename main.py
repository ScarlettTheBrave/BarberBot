import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from core.database import db
from handlers import client, admin

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)  # Створюємо бота тут, щоб він був доступний в циклі



async def scheduler():
    while True:
        try:

            apps = await db.get_appointments_to_remind()

            now = datetime.now()

            for app in apps:
                # app: id, user_id, service_name, date, time
                # Парсимо дату і час запису
                app_dt_str = f"{app[3]} {app[4]}"  # "2023-02-12 14:00"
                app_dt = datetime.strptime(app_dt_str, "%Y-%m-%d %H:%M")

                # Рахуємо різницю
                time_diff = app_dt - now

                # Якщо до візиту менше 3 годин (і це не минуле)
                if timedelta(minutes=0) < time_diff <= timedelta(hours=3):
                    try:
                        await bot.send_message(
                            app[1],
                            f"🔔 <b>Нагадування!</b>\n"
                            f"Через 3 години у вас запис на {app[2]}.\n"
                            f"Чекаємо на вас о {app[4]}!"
                        )
                        await db.mark_reminder_sent(app[0])  # Ставить галочку "відправлено"
                        print(f"Нагадування відправлено для {app[1]}")
                    except Exception as e:
                        print(f"Не вдалося надіслати (може бот заблокований): {e}")

        except Exception as e:
            print(f"Помилка в планувальнику: {e}")

        await asyncio.sleep(60)  # Перевіряємо кожну хвилину


async def main():
    await db.create_tables()
    await db.add_test_data()

    dp = Dispatcher()
    dp.include_router(admin.router)
    dp.include_router(client.router)

    #  планувальник у фоні
    asyncio.create_task(scheduler())

    print("🤖 Бот 2.0 запущено!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stop")