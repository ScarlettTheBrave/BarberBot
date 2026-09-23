from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, Filter
from config import ADMIN_IDS
from core.database import db
from aiogram.fsm.context import FSMContext
from states.admin_states import AdminState
from keyboards.reply import main_menu # Для виходу в клієнтське меню
from keyboards.admin_kb import admin_main_kb, services_management_kb # Для керування послугами
from keyboards.admin_kb import reminder_dates_kb
from keyboards.inline import date_kb, time_kb


router = Router()

class IsAdmin(Filter):
    async def __call__(self, msg: Message) -> bool:
        return msg.from_user.id in ADMIN_IDS

@router.message(Command("admin"), IsAdmin())
async def admin_start(message: Message):
    await message.answer("Адмін-панель v2.0", reply_markup=admin_main_kb())


@router.message(F.text == "📋 Всі записи", IsAdmin())
async def view_all(message: Message):
    apps = await db.get_all_appointments()
    if not apps:
        await message.answer("Записів немає.")
        return

    for app in apps:
        status_icon = "✅" if app[8] else "⏳"
        text = (
            f"{status_icon} <b>Запис #{app[0]}</b>\n"
            f"👤 {app[1]} ({app[2]})\n"
            f"✂️ {app[3]} | 💈 {app[4]}\n"
            f"📅 {app[5]} {app[6]}"
        )

        kb = InlineKeyboardBuilder()
        if not app[8]:
            kb.button(text="✅ Підтвердити", callback_data=f"adm_confirm_{app[0]}")
        kb.button(text="❌ Скасувати", callback_data=f"adm_cancel_{app[0]}")

        await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("adm_confirm_"))
async def confirm_app(callback: CallbackQuery):
    app_id = callback.data.split("_")[2]
    await db.confirm_appointment(app_id)
    await callback.message.edit_text(f"✅ Запис #{app_id} ПІДТВЕРДЖЕНО! Клієнт отримає нагадування.")


@router.message(F.text == "👥 Графік майстрів (Beta)", IsAdmin())
async def master_schedule_start(message: Message):
    masters = await db.get_masters()
    kb = InlineKeyboardBuilder()
    for m in masters:
        kb.button(text=m[1], callback_data=f"sched_master_{m[0]}")
    await message.answer("Оберіть майстра:", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("sched_master_"))
async def show_master_schedule(callback: CallbackQuery):
    master_id = callback.data.split("_")[2]
    apps = await db.get_appointments_by_master(master_id)

    if not apps:
        await callback.message.edit_text("У цього майстра поки порожньо.")
        return

    await callback.message.delete()
    await callback.message.answer(f"📅 <b>Графік майстра:</b>", parse_mode="HTML")

    for app in apps:
        text = (
            f"👤 <b>{app[1]}</b> ({app[2]})\n"
            f"✂️ {app[3]}\n"
            f"📅 {app[4]} о <b>{app[5]}</b>"
        )

        kb = InlineKeyboardBuilder()
        kb.button(text="🔄 Перенести", callback_data=f"adm_move_{app[0]}")
        kb.button(text="❌ Скасувати", callback_data=f"adm_cancel_{app[0]}")
        kb.adjust(2)

        await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("adm_cancel_"))
async def admin_cancel_app(callback: CallbackQuery):
    app_id = callback.data.split("_")[2]

    import aiosqlite
    from config import DB_NAME
    user_id = None
    async with aiosqlite.connect(DB_NAME) as db_conn:
        async with db_conn.execute("SELECT user_id FROM appointments WHERE id = ?", (app_id,)) as cursor:
            res = await cursor.fetchone()
            if res:
                user_id = res[0]

    await db.delete_appointment(app_id)
    await callback.message.edit_text(f"❌ <b>Запис #{app_id} скасовано.</b>", parse_mode="HTML")
    await callback.answer("Запис видалено!")

    if user_id:
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text="На жаль, адміністратор скасував ваш запис. Зв'яжіться з нами для уточнення деталей."
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("adm_move_"))
async def start_reschedule(callback: CallbackQuery, state: FSMContext):
    app_id = callback.data.split("_")[2]
    await state.update_data(reschedule_app_id=app_id)
    await state.set_state(AdminState.reschedule_app_id)
    await callback.message.answer("Оберіть НОВУ дату для цього клієнта:", reply_markup=date_kb())
    await callback.answer()


@router.callback_query(AdminState.reschedule_app_id, F.data.startswith("date_"))
async def admin_choose_reschedule_date(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.split("_")[1]
    await state.update_data(reschedule_new_date=selected_date)
    await callback.message.edit_text(f"Нова дата: {selected_date}\nТепер оберіть новий час:",
                                     reply_markup=time_kb(taken_slots=[]))
    await state.set_state(AdminState.reschedule_new_date)
    await callback.answer()


@router.callback_query(AdminState.reschedule_new_date, F.data.startswith("time_"))
async def admin_finish_reschedule(callback: CallbackQuery, state: FSMContext):
    new_time = callback.data.split("_")[1]
    data = await state.get_data()

    app_id = data['reschedule_app_id']
    new_date = data['reschedule_new_date']

    user_id = await db.update_appointment_time(app_id, new_date, new_time)

    await callback.message.edit_text(f"✅ Запис #{app_id} успішно перенесено на {new_date} {new_time}!")

    if user_id:
        try:
            notification = (
                f"📢 <b>Ваш запис було перенесено адміністратором!</b>\n\n"
                f"Новий час: <b>{new_date} о {new_time}</b>.\n"
                f"Чекаємо на вас! 💈"
            )
            await callback.bot.send_message(chat_id=user_id, text=notification, parse_mode="HTML")
        except Exception:
            pass

    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("adm_move_"), IsAdmin())
async def start_reschedule(callback: CallbackQuery, state: FSMContext):
    app_id = callback.data.split("_")[2]
    await state.update_data(reschedule_app_id=app_id)
    await state.set_state(AdminState.reschedule_app_id)


    await callback.message.answer("Оберіть НОВУ дату для цього клієнта:", reply_markup=date_kb())
    await callback.answer()



@router.callback_query(AdminState.reschedule_app_id, F.data.startswith("date_"))
async def admin_choose_reschedule_date(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.split("_")[1]
    await state.update_data(reschedule_new_date=selected_date)


    await callback.message.edit_text(f"Нова дата: {selected_date}\nТепер оберіть новий час:",
                                     reply_markup=time_kb(taken_slots=[]))
    await state.set_state(AdminState.reschedule_new_date)
    await callback.answer()


# Фінал перенесення
@router.callback_query(AdminState.reschedule_new_date, F.data.startswith("time_"))
async def admin_finish_reschedule(callback: CallbackQuery, state: FSMContext):
    new_time = callback.data.split("_")[1]
    data = await state.get_data()

    app_id = data['reschedule_app_id']
    new_date = data['reschedule_new_date']

    # Оновлюємо в базі та отримуємо ID клієнта
    user_id = await db.update_appointment_time(app_id, new_date, new_time)

    await callback.message.edit_text(f"✅ Запис #{app_id} успішно перенесено на {new_date} {new_time}!")

    # Автоматичне повідомлення клієнту
    if user_id:
        try:
            notification = (
                f"📢 <b>Ваш запис було перенесено адміністратором!</b>\n\n"
                f"Новий час: <b>{new_date} о {new_time}</b>.\n"
                f"Чекаємо на вас! 💈"
            )
            await callback.bot.send_message(chat_id=user_id, text=notification, parse_mode="HTML")
        except Exception as e:
            print(f"Не вдалося повідомити клієнта {user_id}: {e}")

    await state.clear()
    await callback.answer()

@router.message(F.text == "🚪 Вийти", IsAdmin())
async def admin_exit(message: Message):
    await message.answer("Ви повернулися в режим клієнта.", reply_markup=main_menu())

@router.message(F.text == "✂️ Керування послугами", IsAdmin())
async def manage_services(message: Message):
    services = await db.get_services()
    await message.answer(
        "Оберіть дію або послугу для видалення:",
        reply_markup=services_management_kb(services)
    )

@router.callback_query(F.data.startswith("del_serv_"))
async def delete_service_handler(callback: CallbackQuery):
    service_id = callback.data.split("_")[2]
    await db.delete_service(service_id)
    services = await db.get_services()
    await callback.message.edit_text(
        "✅ Послугу видалено. Оберіть дію:",
        reply_markup=services_management_kb(services)
    )

@router.callback_query(F.data == "add_service")
async def start_add_service(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введіть НАЗВУ нової послуги (наприклад: Дитяча стрижка):")
    await state.set_state(AdminState.add_service_name)
    await callback.answer()

@router.message(AdminState.add_service_name)
async def add_service_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введіть ЦІНУ (тільки цифри, наприклад: 300):")
    await state.set_state(AdminState.add_service_price)

@router.message(AdminState.add_service_price)
async def add_service_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer("Введіть ТРИВАЛІСТЬ у хвилинах (тільки цифри, наприклад: 45):")
        await state.set_state(AdminState.add_service_duration)
    except ValueError:
        await message.answer("⚠️ Будь ласка, введіть число (без літер і пробілів).")

@router.message(AdminState.add_service_duration)
async def add_service_finish(message: Message, state: FSMContext):
    try:
        duration = int(message.text)
        data = await state.get_data()
        await db.add_service(data['name'], data['price'], duration)
        await message.answer(
            f"✅ Послуга '{data['name']}' успішно додана в меню!",
            reply_markup=admin_main_kb()
        )
        await state.clear()
    except ValueError:
        await message.answer("⚠️ Введіть ціле число хвилин.")

# --- НАГАДУВАННЯ ---
@router.message(F.text == "🔔 Нагадування", IsAdmin())
async def manual_reminders_menu(message: Message):
    dates = await db.get_dates_for_reminders()
    if not dates:
        await message.answer("✅ Немає підтверджених записів, які потребують нагадування.")
        return
    await message.answer(
        "Оберіть дату, на яку хочете розіслати нагадування клієнтам:",
        reply_markup=reminder_dates_kb(dates)
    )

@router.callback_query(F.data.startswith("remind_date_"))
async def send_reminders_for_date(callback: CallbackQuery):
    date = callback.data.split("_")[2]
    appointments = await db.get_appointments_for_reminder_by_date(date)

    if not appointments:
        await callback.message.edit_text(f"На {date} немає кому відправляти нагадування.")
        return

    success_count = 0
    await callback.message.edit_text(f"⏳ Розпочинаю розсилку на {date}...")

    for app in appointments:
        app_id, user_id, service_name, app_time = app
        text = (
            f"🔔 <b>Нагадування про візит!</b>\n\n"
            f"Чекаємо на вас <b>{date}</b> о <b>{app_time}</b>.\n"
            f"Послуга: {service_name}\n\n"
            f"<i>До зустрічі у KremenBarber!</i>"
        )
        try:
            await callback.bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
            await db.mark_reminder_sent(app_id)
            success_count += 1
        except Exception as e:
            print(f"Помилка відправки користувачу {user_id}: {e}")

    await callback.message.answer(f"✅ Розсилка на {date} завершена!\nУспішно відправлено: {success_count} шт.")
    await callback.answer()