from aiogram.fsm.state import State, StatesGroup

class BookingState(StatesGroup):
    choose_master = State() # вибор майстра
    choose_date = State()   # дата
    choose_time = State()   # час
    confirm = State()       # підтвердження