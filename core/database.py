import aiosqlite
from config import DB_NAME
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.path = DB_NAME

    async def create_tables(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    name TEXT,
                    phone TEXT,
                    is_admin BOOLEAN DEFAULT 0
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS masters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    photo_id TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    price REAL,
                    duration INTEGER
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    master_id INTEGER,
                    service_id INTEGER,
                    appointment_date TEXT,
                    appointment_time TEXT,
                    is_confirmed BOOLEAN DEFAULT 0,
                    reminder_sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(telegram_id),
                    FOREIGN KEY(master_id) REFERENCES masters(id),
                    FOREIGN KEY(service_id) REFERENCES services(id)
                )
            """)
            await db.commit()

    # --- ТЕСТОВІ ДАНІ ---
    async def add_test_data(self):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT count(*) FROM services") as cursor:
                if (await cursor.fetchone())[0] == 0:
                    await db.execute("INSERT INTO services (name, price, duration) VALUES ('Чоловіча стрижка', 500, 60)")
                    await db.execute("INSERT INTO services (name, price, duration) VALUES ('Стрижка бороди', 300, 30)")
                    await db.execute("INSERT INTO services (name, price, duration) VALUES ('Комплекс', 700, 90)")
                    await db.commit()
            async with db.execute("SELECT count(*) FROM masters") as cursor:
                if (await cursor.fetchone())[0] == 0:
                    await db.execute("INSERT INTO masters (name, description) VALUES ('Григорій', 'Топ-барбер')")
                    await db.execute("INSERT INTO masters (name, description) VALUES ('Олександр', 'Спеціаліст по бородах')")
                    await db.execute("INSERT INTO masters (name, description) VALUES ('Максим', 'Junior-майстер')")
                    await db.commit()

    # --- МЕТОДИ КОРИСТУВАЧА
    async def add_user(self, telegram_id, username, full_name):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                INSERT INTO users (telegram_id, username, name) VALUES (?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET name=excluded.name, username=excluded.username
            """, (telegram_id, username, full_name))
            await db.commit()

    async def update_user_phone(self, user_id, phone):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET phone = ? WHERE telegram_id = ?", (phone, user_id))
            await db.commit()

    async def get_user_phone(self, user_id):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT phone FROM users WHERE telegram_id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None

    async def add_appointment(self, user_id, master_id, service_id, date, time):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                INSERT INTO appointments (user_id, master_id, service_id, appointment_date, appointment_time, is_confirmed, reminder_sent)
                VALUES (?, ?, ?, ?, ?, 0, 0)
            """, (user_id, master_id, service_id, date, time))
            await db.commit()

    async def get_user_appointments(self, user_id):
        async with aiosqlite.connect(self.path) as db:
            query = """
                SELECT a.id, s.name, m.name, a.appointment_date, a.appointment_time, a.is_confirmed
                FROM appointments a
                JOIN services s ON a.service_id = s.id
                JOIN masters m ON a.master_id = m.id
                WHERE a.user_id = ?
                ORDER BY a.appointment_date, a.appointment_time
            """
            async with db.execute(query, (user_id,)) as cursor:
                return await cursor.fetchall()

    async def delete_appointment(self, appointment_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            await db.commit()

    # --- МЕТОДИ АДМІНА
    async def get_all_appointments(self):
        async with aiosqlite.connect(self.path) as db:
            query = """
                SELECT a.id, u.name, u.phone, s.name, m.name, a.appointment_date, a.appointment_time, u.username, a.is_confirmed
                FROM appointments a
                LEFT JOIN users u ON a.user_id = u.telegram_id
                JOIN services s ON a.service_id = s.id
                JOIN masters m ON a.master_id = m.id
                ORDER BY a.appointment_date, a.appointment_time
            """
            async with db.execute(query) as cursor:
                return await cursor.fetchall()

    async def confirm_appointment(self, app_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE appointments SET is_confirmed = 1 WHERE id = ?", (app_id,))
            await db.commit()

    async def get_appointments_by_master(self, master_id):
        async with aiosqlite.connect(self.path) as db:
            query = """
                SELECT a.id, u.name, u.phone, s.name, a.appointment_date, a.appointment_time, a.is_confirmed
                FROM appointments a
                LEFT JOIN users u ON a.user_id = u.telegram_id
                JOIN services s ON a.service_id = s.id
                WHERE a.master_id = ?
                ORDER BY a.appointment_date, a.appointment_time
            """
            async with db.execute(query, (master_id,)) as cursor:
                return await cursor.fetchall()

    async def add_service(self, name, price, duration):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO services (name, price, duration) VALUES (?, ?, ?)", (name, price, duration))
            await db.commit()

    async def delete_service(self, service_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM services WHERE id = ?", (service_id,))
            await db.commit()

    # --- НАГАДУВАННЯ
    async def get_appointments_to_remind(self):
        async with aiosqlite.connect(self.path) as db:
            query = """
                SELECT a.id, a.user_id, s.name, a.appointment_date, a.appointment_time
                FROM appointments a
                JOIN services s ON a.service_id = s.id
                WHERE a.is_confirmed = 1 AND a.reminder_sent = 0
            """
            async with db.execute(query) as cursor:
                return await cursor.fetchall()

    async def mark_reminder_sent(self, app_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE appointments SET reminder_sent = 1 WHERE id = ?", (app_id,))
            await db.commit()


    async def get_services(self):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT id, name, price FROM services") as cursor:
                return await cursor.fetchall()

    async def get_masters(self):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT id, name FROM masters") as cursor:
                return await cursor.fetchall()

    async def get_taken_slots(self, master_id, date):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT appointment_time FROM appointments WHERE master_id = ? AND appointment_date = ?", (master_id, date)) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_service_by_id(self, service_id):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT name, price FROM services WHERE id = ?", (service_id,)) as cursor:
                return await cursor.fetchone()

    async def get_master_by_id(self, master_id):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT name FROM masters WHERE id = ?", (master_id,)) as cursor:
                res = await cursor.fetchone()
                return res[0] if res else "Майстер"

    async def get_dates_for_reminders(self):
        async with aiosqlite.connect(self.path) as db:
            query = """
                    SELECT DISTINCT appointment_date
                    FROM appointments
                    WHERE is_confirmed = 1 \
                      AND reminder_sent = 0
                    ORDER BY appointment_date \
                    """
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_appointments_for_reminder_by_date(self, date):
        async with aiosqlite.connect(self.path) as db:
            query = """
                    SELECT a.id, a.user_id, s.name, a.appointment_time
                    FROM appointments a
                             JOIN services s ON a.service_id = s.id
                    WHERE a.appointment_date = ? \
                      AND a.is_confirmed = 1 \
                      AND a.reminder_sent = 0 \
                    """
            async with db.execute(query, (date,)) as cursor:
                return await cursor.fetchall()

    async def update_appointment_time(self, app_id, new_date, new_time):
        async with aiosqlite.connect(self.path) as db:

            await db.execute("""
                UPDATE appointments 
                SET appointment_date = ?, appointment_time = ?, is_confirmed = 1 
                WHERE id = ?
            """, (new_date, new_time, app_id))


            async with db.execute("SELECT user_id FROM appointments WHERE id = ?", (app_id,)) as cursor:
                res = await cursor.fetchone()
                await db.commit()
                return res[0] if res else None

    async def update_appointment_time(self, app_id, new_date, new_time):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                UPDATE appointments 
                SET appointment_date = ?, appointment_time = ?, is_confirmed = 1 
                WHERE id = ?
            """, (new_date, new_time, app_id))

            async with db.execute("SELECT user_id FROM appointments WHERE id = ?", (app_id,)) as cursor:
                res = await cursor.fetchone()
                await db.commit()
                return res[0] if res else None

    async def get_user_taken_slots(self, user_id, date):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                    "SELECT appointment_time FROM appointments WHERE user_id = ? AND appointment_date = ?",
                    (user_id, date)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
db = Database()