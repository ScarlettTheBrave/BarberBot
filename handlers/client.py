from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from keyboards.reply import main_menu, phone_request_kb
from keyboards.inline import services_kb, masters_kb, date_kb, time_kb, confirm_kb, user_cancel_kb
from core.database import db
from states.client_states import BookingState
from datetime import datetime


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(f"Вітаю, {message.from_user.first_name}! 👋\nОберіть дію:", reply_markup=main_menu())


@router.message(F.text == "✂️ Записатися")
async def start_booking_check_phone(message: Message):
    user_id = message.from_user.id
    phone = await db.get_user_phone(user_id)
    if not phone:
        await message.answer(
            "📞 Для запису нам потрібен ваш номер телефону, щоб ми могли підтвердити візит.",
            reply_markup=phone_request_kb()
        )
        return

    services = await db.get_services()
    if not services:
        await message.answer("Послуги відсутні. Зверніться до адміністратора.")
        return
    await message.answer("Оберіть послугу:", reply_markup=services_kb(services))


@router.message(F.contact)
async def get_contact(message: Message):
    if message.contact.user_id == message.from_user.id:
        await db.update_user_phone(message.from_user.id, message.contact.phone_number)
        await message.answer("✅ Номер збережено! Натисніть '✂️ Записатися' ще раз.", reply_markup=main_menu())
    else:
        await message.answer("Будь ласка, надішліть СВІЙ номер за допомогою кнопки.")


@router.callback_query(F.data.startswith("service_"))
async def choose_service(callback: CallbackQuery, state: FSMContext):
    service_id = callback.data.split("_")[1]
    await state.update_data(service_id=service_id)
    masters = await db.get_masters()
    await callback.message.edit_text("Чудовий вибір! Тепер оберіть майстра:", reply_markup=masters_kb(masters))
    await state.set_state(BookingState.choose_master)
    await callback.answer()


@router.callback_query(F.data.startswith("master_"))
async def choose_master(callback: CallbackQuery, state: FSMContext):
    master_id = callback.data.split("_")[1]
    await state.update_data(master_id=master_id)
    await callback.message.edit_text("Оберіть зручну дату для візиту:", reply_markup=date_kb())
    await state.set_state(BookingState.choose_date)
    await callback.answer()


@router.callback_query(F.data.startswith("date_"))
async def choose_date(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.split("_")[1]
    await state.update_data(chosen_date=selected_date)
    data = await state.get_data()

    master_id = data.get("master_id")
    user_id = callback.from_user.id  # get ID клієнта

    # айняті години майстра
    master_slots = await db.get_taken_slots(master_id, selected_date)
    #  зайняті години КЛІЄНТА
    user_slots = await db.get_user_taken_slots(user_id, selected_date)

    # Об'єднуємо їх! Якщо 16:00 є в user_slots, воно потрапить сюди
    taken_slots = list(set(master_slots + user_slots))

    now = datetime.now()
    current_date_str = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H:%M")

    if selected_date == current_date_str:
        all_possible_times = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00",
                              "20:00"]
        for t in all_possible_times:
            if t <= current_time_str and t not in taken_slots:
                taken_slots.append(t)

    # Клавіатура time_kb відфільтрує всі години, які є в taken_slots
    await callback.message.edit_text(
        f"Дата: {selected_date}\nОберіть вільний час:",
        reply_markup=time_kb(taken_slots)
    )
    await state.set_state(BookingState.choose_time)
    await callback.answer()

@router.callback_query(F.data.startswith("time_"))
async def choose_time(callback: CallbackQuery, state: FSMContext):
    selected_time = callback.data.split("_")[1]
    await state.update_data(chosen_time=selected_time)
    data = await state.get_data()

    service_info = await db.get_service_by_id(data.get("service_id"))
    master_name = await db.get_master_by_id(data.get("master_id"))

    summary_text = (
        f"📝 <b>Перевірте дані запису:</b>\n\n"
        f"✂️ <b>Послуга:</b> {service_info[0]}\n"
        f"💈 <b>Майстер:</b> {master_name}\n"
        f"💰 <b>Вартість:</b> {service_info[1]} грн\n"
        f"📅 <b>Дата:</b> {data.get('chosen_date')}\n"
        f"⏰ <b>Час:</b> {selected_time}\n"
    )
    await callback.message.edit_text(summary_text, reply_markup=confirm_kb(), parse_mode="HTML")
    await state.set_state(BookingState.confirm)
    await callback.answer()


@router.callback_query(F.data == "confirm_booking")
async def finish_booking(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await db.add_appointment(
        callback.from_user.id, data.get("master_id"), data.get("service_id"),
        data.get("chosen_date"), data.get("chosen_time")
    )
    await state.clear()
    await callback.message.edit_text(
        "🎉 <b>Вашу заявку прийнято!</b>\n"
        "Очікуйте підтвердження від адміністратора. Ми надішлемо вам сповіщення.",
        parse_mode="HTML"
    )
    await callback.answer()



@router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    services = await db.get_services()
    await callback.message.edit_text("Оберіть послугу:", reply_markup=services_kb(services))


@router.callback_query(F.data == "back_to_masters")
async def back_to_masters(callback: CallbackQuery, state: FSMContext):
    masters = await db.get_masters()
    await callback.message.edit_text("Оберіть майстра:", reply_markup=masters_kb(masters))
    await state.set_state(BookingState.choose_master)


@router.callback_query(F.data == "back_to_dates")
async def back_to_dates(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Оберіть зручну дату для візиту:", reply_markup=date_kb())
    await state.set_state(BookingState.choose_date)


@router.callback_query(F.data == "cancel")
async def cancel_booking_process(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Запис скасовано.")



@router.message(F.text == "📅 Мої записи")
async def my_appointments(message: Message):
    apps = await db.get_user_appointments(message.from_user.id)
    if not apps:
        await message.answer("У вас немає активних записів.")
        return

    for app in apps:
        status = "✅ Підтверджено" if app[5] else "⏳ Очікує підтвердження"
        text = (
            f"✂️ <b>{app[1]}</b>\n"
            f"💈 Майстер: {app[2]}\n"
            f"📅 {app[3]} о {app[4]}\n"
            f"Статус: {status}"
        )
        await message.answer(text, reply_markup=user_cancel_kb(app[0]), parse_mode="HTML")


@router.callback_query(F.data.startswith("user_cancel_"))
async def user_cancel_appointment(callback: CallbackQuery):
    app_id = callback.data.split("_")[2]
    await db.delete_appointment(app_id)
    await callback.message.edit_text(
        "💔 <b>Запис скасовано...</b>\n\n"
        "Нашому майстру дуже шкода, що так вийшло. Сподіваємось, ви повернетесь до нас пізніше!",
        parse_mode="HTML"
    )


# --- Інші кнопки ---
@router.message(F.text == "ℹ️ Про нас")
async def cmd_about(message: Message):
    await message.answer(
        "💈 KremenBarber - кращий стиль у місті!\nМи працюємо щодня з 10:00 до 21:00.\n📍 Адреса: вул. Соборна, 15")


@router.message(F.text == "📞 Контакти")
async def cmd_contacts(message: Message):
    await message.answer("📞 Телефон: +380991234567\n Адмін: Харитонов Денис Русланович")