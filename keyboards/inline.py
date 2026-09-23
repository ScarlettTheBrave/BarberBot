from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from datetime import datetime, timedelta



def services_kb(services: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for service in services:
        # service[0]=id, service[1]=name, service[2]=price
        kb.button(
            text=f"{service[1]} - {service[2]} грн",
            callback_data=f"service_{service[0]}"
        )
    kb.button(text="❌ Скасувати", callback_data="cancel")
    kb.adjust(1)
    return kb.as_markup()



def masters_kb(masters: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for master in masters:
        # master[0]=id, master[1]=name
        kb.button(
            text=f"💈 {master[1]}",
            callback_data=f"master_{master[0]}"
        )
    kb.button(text="🔙 Назад", callback_data="back_to_services")
    kb.adjust(1)
    return kb.as_markup()



def date_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    current_date = datetime.now()


    for i in range(7):
        date_to_show = current_date + timedelta(days=i)


        button_text = date_to_show.strftime("%d.%m")


        callback_data = f"date_{date_to_show.strftime('%Y-%m-%d')}"

        kb.button(text=f"📅 {button_text}", callback_data=callback_data)

    kb.button(text="🔙 Назад", callback_data="back_to_masters")


    kb.adjust(3)
    return kb.as_markup()

def time_kb(taken_slots: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # Робочий день: з 10:00 до 20:00
    start_hour = 10
    end_hour = 20

    for hour in range(start_hour, end_hour + 1):
        time_str = f"{hour}:00"

        # створення кнопки скіп
        if time_str in taken_slots:
            continue

        kb.button(text=f"⏰ {time_str}", callback_data=f"time_{time_str}")

    kb.button(text="🔙 Назад", callback_data="back_to_dates")
    kb.adjust(4)  # По 4 кнопки в ряд
    return kb.as_markup()

def confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Підтвердити запис", callback_data="confirm_booking")
    kb.button(text="❌ Скасувати", callback_data="cancel")
    kb.adjust(1)
    return kb.as_markup()

def user_cancel_kb(app_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Скасувати запис", callback_data=f"user_cancel_{app_id}")
    return kb.as_markup()