from aiogram.fsm.state import State, StatesGroup

class AdminState(StatesGroup):
    add_service_name = State()     # Введення назви послуги
    add_service_price = State()    # Введення ціни
    add_service_duration = State() # Введення тривалості
    # НОВІ СТАНИ для перенесення
    reschedule_app_id = State()  # ID запису
    reschedule_new_date = State()  # Нова обрана дата