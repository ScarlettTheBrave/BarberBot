from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder



def admin_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Всі записи"), KeyboardButton(text="✂️ Керування послугами")],
            [KeyboardButton(text="👥 Графік майстрів (Beta)"), KeyboardButton(text="🔔 Нагадування")], # <-- Додано кнопку
            [KeyboardButton(text="🚪 Вийти")]
        ],
        resize_keyboard=True
    )


def services_management_kb(services: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # Кнопка додавання
    kb.button(text="➕ Додати нову послугу", callback_data="add_service")


    for service in services:
        # service[0]=id, service[1]=name
        kb.button(text=f"🗑 Видалити {service[1]}", callback_data=f"del_serv_{service[0]}")

    kb.adjust(1)
    return kb.as_markup()



def cancel_appointment_kb(app_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Скасувати цей запис", callback_data=f"cancel_app_{app_id}")
    return kb.as_markup()

def reminder_dates_kb(dates: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for date in dates:
        kb.button(text=f"📅 {date}", callback_data=f"remind_date_{date}")
    kb.adjust(1)
    return kb.as_markup()