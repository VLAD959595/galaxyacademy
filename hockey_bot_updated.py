#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
import sqlite3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio

# Импорт конфигурации и админ-панели
import config
from admin_panel import *

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            age INTEGER,
            skill_level TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица тренировок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trainings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            date_time TIMESTAMP,
            coach TEXT,
            max_participants INTEGER DEFAULT 15,
            skill_level TEXT,
            price INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица записей на тренировки
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            training_id INTEGER,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (training_id) REFERENCES trainings (id)
        )
    ''')
    
    # Добавляем примеры тренировок
    sample_trainings = [
        ("Техника катания", "Основы катания на коньках для начинающих", "2024-02-20 18:00", "Иван Петров", 12, "Начинающий", 1500),
        ("Работа с шайбой", "Отработка ведения и передач шайбы", "2024-02-21 19:00", "Алексей Сидоров", 10, "Средний", 2000),
        ("Силовая подготовка", "Физическая подготовка хоккеистов", "2024-02-22 17:00", "Мария Васильева", 15, "Продвинутый", 1800),
        ("Игровые ситуации", "Разбор тактических моментов", "2024-02-23 20:00", "Дмитрий Козлов", 8, "Продвинутый", 2500),
        ("Детская группа", "Тренировка для детей 6-12 лет", "2024-02-24 16:00", "Елена Иванова", 20, "Детская", 1200)
    ]
    
    cursor.execute("SELECT COUNT(*) FROM trainings")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO trainings (name, description, date_time, coach, max_participants, skill_level, price) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sample_trainings
        )
    
    conn.commit()
    conn.close()

# Клавиатуры
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🏒 Записаться на тренировку"), KeyboardButton("📅 Мои записи")],
        [KeyboardButton("📋 Расписание"), KeyboardButton("👨‍🏫 Тренеры")],
        [KeyboardButton("ℹ️ О академии"), KeyboardButton("📞 Контакты")],
        [KeyboardButton("⚙️ Мой профиль")]
    ]
    
    # Добавляем кнопку админ-панели для администраторов
    if config.ADMIN_IDS:
        keyboard.append([KeyboardButton("🔧 Админ-панель")])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_skill_keyboard():
    keyboard = [
        [InlineKeyboardButton("🟢 Начинающий", callback_data="skill_Начинающий")],
        [InlineKeyboardButton("🟡 Средний", callback_data="skill_Средний")],
        [InlineKeyboardButton("🔴 Продвинутый", callback_data="skill_Продвинутый")],
        [InlineKeyboardButton("👶 Детская группа", callback_data="skill_Детская")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
🏒 Добро пожаловать в {config.ACADEMY_NAME}! 

Привет, {user.first_name}! 

Я помогу вам:
• 📝 Записаться на тренировки
• 📅 Просмотреть расписание
• 👨‍🏫 Узнать о тренерах
• 📊 Отслеживать ваш прогресс

Для начала давайте зарегистрируем вас в системе!
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard()
    )
    
    # Проверяем, есть ли пользователь в БД
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
    if not cursor.fetchone():
        await update.message.reply_text(
            "Для полного использования бота необходимо заполнить профиль. Используйте команду /profile"
        )
    conn.close()

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Давайте заполним ваш профиль!\n\n"
        "Укажите ваш возраст:"
    )
    context.user_data['awaiting'] = 'age'

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, date_time, coach, skill_level, price, 
               (SELECT COUNT(*) FROM registrations WHERE training_id = trainings.id) as registered
        FROM trainings 
        WHERE date_time > datetime('now') 
        ORDER BY date_time
    """)
    
    trainings = cursor.fetchall()
    conn.close()
    
    if not trainings:
        await update.message.reply_text("📅 На данный момент нет запланированных тренировок.")
        return
    
    schedule_text = "📅 <b>Расписание тренировок:</b>\n\n"
    
    for training in trainings:
        name, date_time, coach, skill_level, price, registered = training
        dt = datetime.strptime(date_time, '%Y-%m-%d %H:%M')
        formatted_date = dt.strftime('%d.%m.%Y в %H:%M')
        
        schedule_text += f"🏒 <b>{name}</b>\n"
        schedule_text += f"📅 {formatted_date}\n"
        schedule_text += f"👨‍🏫 Тренер: {coach}\n"
        schedule_text += f"📊 Уровень: {skill_level}\n"
        schedule_text += f"💰 Цена: {price}₽\n"
        schedule_text += f"👥 Записано: {registered}/15\n"
        schedule_text += "─" * 20 + "\n\n"
    
    await update.message.reply_text(schedule_text, parse_mode='HTML')

async def trainings_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, date_time, coach, skill_level, price,
               (SELECT COUNT(*) FROM registrations WHERE training_id = trainings.id) as registered,
               max_participants
        FROM trainings 
        WHERE date_time > datetime('now') 
        ORDER BY date_time
    """)
    
    trainings = cursor.fetchall()
    conn.close()
    
    if not trainings:
        await update.message.reply_text("🚫 Нет доступных тренировок для записи.")
        return
    
    keyboard = []
    for training in trainings:
        training_id, name, date_time, coach, skill_level, price, registered, max_participants = training
        dt = datetime.strptime(date_time, '%Y-%m-%d %H:%M')
        formatted_date = dt.strftime('%d.%m в %H:%M')
        
        button_text = f"{name} - {formatted_date} ({registered}/{max_participants})"
        if registered >= max_participants:
            button_text += " ❌"
        else:
            button_text += " ✅"
            
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"register_{training_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    
    await update.message.reply_text(
        "🏒 <b>Выберите тренировку для записи:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def my_registrations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.name, t.date_time, t.coach, t.skill_level, r.registration_date, t.id
        FROM registrations r
        JOIN trainings t ON r.training_id = t.id
        WHERE r.user_id = ? AND t.date_time > datetime('now')
        ORDER BY t.date_time
    """, (user_id,))
    
    registrations = cursor.fetchall()
    conn.close()
    
    if not registrations:
        await update.message.reply_text("📝 У вас нет активных записей на тренировки.")
        return
    
    text = "📝 <b>Ваши записи на тренировки:</b>\n\n"
    keyboard = []
    
    for reg in registrations:
        name, date_time, coach, skill_level, reg_date, training_id = reg
        dt = datetime.strptime(date_time, '%Y-%m-%d %H:%M')
        formatted_date = dt.strftime('%d.%m.%Y в %H:%M')
        
        text += f"🏒 <b>{name}</b>\n"
        text += f"📅 {formatted_date}\n"
        text += f"👨‍🏫 {coach}\n"
        text += f"📊 {skill_level}\n"
        text += "─" * 20 + "\n\n"
        
        keyboard.append([InlineKeyboardButton(f"❌ Отменить '{name}'", callback_data=f"cancel_{training_id}")])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def coaches_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coaches_text = """
👨‍🏫 <b>Наши тренеры:</b>

🏒 <b>Иван Петров</b>
• Мастер спорта по хоккею
• Опыт работы: 15 лет
• Специализация: техника катания
• Чемпион России 2010 года

🏒 <b>Алексей Сидоров</b>
• Кандидат в мастера спорта
• Опыт работы: 8 лет
• Специализация: работа с шайбой
• Участник молодёжной сборной

🏒 <b>Мария Васильева</b>
• Мастер спорта международного класса
• Опыт работы: 12 лет
• Специализация: физическая подготовка
• Олимпийская чемпионка 2014

🏒 <b>Дмитрий Козлов</b>
• Заслуженный тренер России
• Опыт работы: 20 лет
• Специализация: тактическая подготовка
• Тренер сборной России

🏒 <b>Елена Иванова</b>
• Педагог-психолог
• Опыт работы: 10 лет
• Специализация: детские группы
• Автор методики "Хоккей с радостью"
"""
    
    await update.message.reply_text(coaches_text, parse_mode='HTML')

async def academy_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = f"""
🏒 <b>{config.ACADEMY_NAME}</b>

📍 <b>Адрес:</b> {config.ACADEMY_ADDRESS}
🕐 <b>Режим работы:</b> Пн-Вс 08:00-23:00

🎯 <b>Наша миссия:</b>
Развитие хоккея и воспитание чемпионов! Мы создаем комфортную среду для изучения хоккея на любом уровне.

⭐ <b>Что мы предлагаем:</b>
• Индивидуальные и групповые тренировки
• Программы для всех возрастов (от 6 лет)
• Профессиональные тренеры
• Современная ледовая арена
• Аренда экипировки
• Участие в турнирах

🏆 <b>Наши достижения:</b>
• 15+ лет успешной работы
• 500+ выпускников
• 50+ медалистов различных соревнований
• Лучшая детская хоккейная школа 2023 года

💰 <b>Цены:</b>
• Разовое занятие: от 1200₽
• Абонемент (8 занятий): от 8500₽
• Индивидуальная тренировка: от 3000₽
• Аренда коньков: 300₽/час
"""
    
    await update.message.reply_text(info_text, parse_mode='HTML')

async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contacts_text = f"""
📞 <b>Контактная информация:</b>

📱 <b>Телефон:</b> {config.ACADEMY_PHONE}
📧 <b>Email:</b> {config.ACADEMY_EMAIL}
🌐 <b>Сайт:</b> {config.ACADEMY_WEBSITE}

📍 <b>Адрес:</b> 
{config.ACADEMY_ADDRESS}
Ледовый дворец "Арктика"

🚇 <b>Как добраться:</b>
• Метро "Спортивная" (5 мин пешком)
• Автобус №15, 23 до ост. "Ледовый дворец"
• Парковка для авто (бесплатная)

🕐 <b>Администрация работает:</b>
Пн-Пт: 09:00-21:00
Сб-Вс: 10:00-20:00

📱 <b>Социальные сети:</b>
• Instagram: @icewolves_academy
• VK: vk.com/icewolves
• Telegram: @icewolves_news
"""
    
    await update.message.reply_text(contacts_text, parse_mode='HTML')

# Обработчики callback'ов
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    # Обработка админ callback'ов
    if data == "admin_panel":
        await admin_panel(update, context)
        return
    elif data == "admin_stats":
        await admin_stats(query, context)
        return
    elif data == "admin_add_training":
        await admin_add_training(query, context)
        return
    elif data == "admin_manage_trainings":
        await admin_manage_trainings(query, context)
        return
    elif data == "admin_users":
        await admin_users(query, context)
        return
    elif data == "admin_broadcast":
        await admin_broadcast(query, context)
        return
    
    # Выбор уровня навыков
    if data.startswith('skill_'):
        skill_level = data.split('_')[1]
        context.user_data['skill_level'] = skill_level
        
        # Сохраняем пользователя в БД
        user = update.effective_user
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, phone, age, skill_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, user.username, user.first_name, user.last_name,
            context.user_data.get('phone', ''), 
            context.user_data.get('age', 0), 
            skill_level
        ))
        
        conn.commit()
        conn.close()
        
        context.user_data.clear()
        
        await query.edit_message_text(
            "✅ <b>Профиль успешно создан!</b>\n\n"
            "Теперь вы можете записываться на тренировки и пользоваться всеми возможностями бота!",
            parse_mode='HTML'
        )
        return
    
    if data.startswith('register_'):
        training_id = int(data.split('_')[1])
        
        # Проверяем, есть ли пользователь в БД
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            await query.edit_message_text(
                "❌ Сначала необходимо заполнить профиль!\nИспользуйте команду /profile"
            )
            conn.close()
            return
        
        # Проверяем, не записан ли уже пользователь
        cursor.execute("SELECT * FROM registrations WHERE user_id = ? AND training_id = ?", (user_id, training_id))
        if cursor.fetchone():
            await query.edit_message_text("⚠️ Вы уже записаны на эту тренировку!")
            conn.close()
            return
        
        # Проверяем доступность мест
        cursor.execute("""
            SELECT t.max_participants, COUNT(r.id) as registered
            FROM trainings t
            LEFT JOIN registrations r ON t.id = r.training_id
            WHERE t.id = ?
            GROUP BY t.id
        """, (training_id,))
        
        result = cursor.fetchone()
        if result:
            max_participants, registered = result
            if registered >= max_participants:
                await query.edit_message_text("❌ Извините, все места заняты!")
                conn.close()
                return
        
        # Записываем пользователя
        cursor.execute(
            "INSERT INTO registrations (user_id, training_id) VALUES (?, ?)",
            (user_id, training_id)
        )
        
        # Получаем информацию о тренировке
        cursor.execute("SELECT name, date_time, coach FROM trainings WHERE id = ?", (training_id,))
        training_info = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if training_info:
            name, date_time, coach = training_info
            dt = datetime.strptime(date_time, '%Y-%m-%d %H:%M')
            formatted_date = dt.strftime('%d.%m.%Y в %H:%M')
            
            await query.edit_message_text(
                f"✅ <b>Запись успешна!</b>\n\n"
                f"🏒 Тренировка: {name}\n"
                f"📅 Дата: {formatted_date}\n"
                f"👨‍🏫 Тренер: {coach}\n\n"
                f"📝 Детали тренировки будут отправлены за день до занятия.\n"
                f"❗ Для отмены записи используйте 'Мои записи'",
                parse_mode='HTML'
            )
    
    elif data.startswith('cancel_'):
        training_id = int(data.split('_')[1])
        
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM registrations WHERE user_id = ? AND training_id = ?", (user_id, training_id))
        
        if cursor.rowcount > 0:
            await query.edit_message_text("✅ Запись успешно отменена!")
        else:
            await query.edit_message_text("❌ Запись не найдена.")
        
        conn.commit()
        conn.close()

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    # Обработка ввода данных профиля
    if context.user_data.get('awaiting') == 'age':
        try:
            age = int(text)
            if age < 6 or age > 80:
                await update.message.reply_text("❌ Введите корректный возраст (6-80 лет):")
                return
            
            context.user_data['age'] = age
            context.user_data['awaiting'] = 'phone'
            await update.message.reply_text("📱 Введите номер телефона:")
            
        except ValueError:
            await update.message.reply_text("❌ Введите возраст числом:")
            return
    
    elif context.user_data.get('awaiting') == 'phone':
        context.user_data['phone'] = text
        context.user_data['awaiting'] = 'skill'
        
        await update.message.reply_text(
            "🏒 Выберите ваш уровень подготовки:",
            reply_markup=get_skill_keyboard()
        )
    
    # Обработка кнопок главного меню
    elif text == "🏒 Записаться на тренировку":
        await trainings_list(update, context)
    
    elif text == "📅 Мои записи":
        await my_registrations(update, context)
    
    elif text == "📋 Расписание":
        await schedule(update, context)
    
    elif text == "👨‍🏫 Тренеры":
        await coaches_info(update, context)
    
    elif text == "ℹ️ О академии":
        await academy_info(update, context)
    
    elif text == "📞 Контакты":
        await contacts(update, context)
    
    elif text == "🔧 Админ-панель":
        await admin_panel(update, context)
    
    elif text == "⚙️ Мой профиль":
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            _, username, first_name, last_name, phone, age, skill_level, reg_date = user_data
            profile_text = f"""
👤 <b>Ваш профиль:</b>

📝 Имя: {first_name} {last_name or ''}
📱 Телефон: {phone}
🎂 Возраст: {age} лет
🏒 Уровень: {skill_level}
📅 Регистрация: {reg_date[:10]}

Для изменения данных используйте /profile
"""
            await update.message.reply_text(profile_text, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Профиль не найден. Используйте /profile для создания.")

# Основная функция
def main():
    # Проверяем наличие токена
    if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Ошибка: Необходимо указать токен бота в файле .env")
        print("1. Скопируйте .env.example в .env")
        print("2. Получите токен у @BotFather в Telegram")
        print("3. Укажите токен в файле .env")
        return
    
    # Инициализация БД
    init_db()
    
    # Создание приложения
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("schedule", schedule))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("add_training", add_training_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    print(f"🏒 {config.ACADEMY_NAME} бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()