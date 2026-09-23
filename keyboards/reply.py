from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✂️ Записатися"),
                KeyboardButton(text="📅 Мої записи")
            ],
            [
                KeyboardButton(text="ℹ️ Про нас"),
                KeyboardButton(text="📞 Контакти")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію з меню..."
    )
    return kb

#
def phone_request_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Надіслати номер телефону", request_contact=True)],
            [KeyboardButton(text="🔙 Назад")] # Щоб можна було вийти
        ],
        resize_keyboard=True,
        one_time_keyboard=True # Клавіатура зникне після натискання
    )
    return kb

def user_cancel_kb(app_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Скасувати запис", callback_data=f"user_cancel_{app_id}")
    return kb.as_markup()