#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config

# Проверка на админа
def is_admin(user_id):
    return user_id in config.ADMIN_IDS

# Клавиатура админ-панели
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("➕ Добавить тренировку", callback_data="admin_add_training")],
        [InlineKeyboardButton("📋 Управление тренировками", callback_data="admin_manage_trainings")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("📨 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Админ-панель
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    admin_text = f"""
🔧 <b>Панель администратора</b>

Добро пожаловать в админ-панель {config.ACADEMY_NAME}!

Выберите действие:
"""
    
    await update.message.reply_text(
        admin_text,
        reply_markup=get_admin_keyboard(),
        parse_mode='HTML'
    )

# Статистика
async def admin_stats(query, context):
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trainings WHERE date_time > datetime('now')")
    upcoming_trainings = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM registrations")
    total_registrations = cursor.fetchone()[0]
    
    # Статистика по уровням
    cursor.execute("""
        SELECT skill_level, COUNT(*) 
        FROM users 
        WHERE skill_level IS NOT NULL 
        GROUP BY skill_level
    """)
    skill_stats = cursor.fetchall()
    
    # Популярные тренировки
    cursor.execute("""
        SELECT t.name, COUNT(r.id) as registrations
        FROM trainings t
        LEFT JOIN registrations r ON t.id = r.training_id
        WHERE t.date_time > datetime('now')
        GROUP BY t.id, t.name
        ORDER BY registrations DESC
        LIMIT 5
    """)
    popular_trainings = cursor.fetchall()
    
    conn.close()
    
    stats_text = f"""
📊 <b>Статистика академии</b>

👥 <b>Пользователи:</b> {total_users}
🏒 <b>Предстоящие тренировки:</b> {upcoming_trainings}
📝 <b>Всего записей:</b> {total_registrations}

📈 <b>Распределение по уровням:</b>
"""
    
    for skill, count in skill_stats:
        stats_text += f"• {skill}: {count} чел.\n"
    
    stats_text += "\n🔥 <b>Популярные тренировки:</b>\n"
    for name, registrations in popular_trainings:
        stats_text += f"• {name}: {registrations} записей\n"
    
    await query.edit_message_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]),
        parse_mode='HTML'
    )

# Добавление тренировки
async def admin_add_training(query, context):
    add_text = """
➕ <b>Добавление новой тренировки</b>

Для добавления тренировки отправьте сообщение в формате:

<code>/add_training Название|Описание|ГГГГ-ММ-ДД ЧЧ:ММ|Тренер|Макс.участников|Уровень|Цена</code>

<b>Пример:</b>
<code>/add_training Техника броска|Отработка точности бросков|2024-02-25 19:00|Иван Петров|12|Средний|2000</code>

<b>Уровни:</b> Начинающий, Средний, Продвинутый, Детская
"""
    
    await query.edit_message_text(
        add_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]),
        parse_mode='HTML'
    )

# Управление тренировками
async def admin_manage_trainings(query, context):
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, date_time, 
               (SELECT COUNT(*) FROM registrations WHERE training_id = trainings.id) as registered,
               max_participants
        FROM trainings 
        WHERE date_time > datetime('now') 
        ORDER BY date_time
        LIMIT 10
    """)
    
    trainings = cursor.fetchall()
    conn.close()
    
    if not trainings:
        await query.edit_message_text(
            "📋 Нет предстоящих тренировок.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]])
        )
        return
    
    keyboard = []
    manage_text = "📋 <b>Управление тренировками:</b>\n\n"
    
    for training in trainings:
        training_id, name, date_time, registered, max_participants = training
        dt = datetime.strptime(date_time, '%Y-%m-%d %H:%M')
        formatted_date = dt.strftime('%d.%m в %H:%M')
        
        manage_text += f"🏒 {name}\n📅 {formatted_date} ({registered}/{max_participants})\n\n"
        keyboard.append([InlineKeyboardButton(f"✏️ {name[:20]}...", callback_data=f"edit_training_{training_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
    
    await query.edit_message_text(
        manage_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

# Управление пользователями
async def admin_users(query, context):
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    
    # Последние зарегистрированные пользователи
    cursor.execute("""
        SELECT first_name, last_name, age, skill_level, registration_date
        FROM users 
        ORDER BY registration_date DESC 
        LIMIT 10
    """)
    
    recent_users = cursor.fetchall()
    conn.close()
    
    users_text = "👥 <b>Последние пользователи:</b>\n\n"
    
    for user in recent_users:
        first_name, last_name, age, skill_level, reg_date = user
        full_name = f"{first_name} {last_name or ''}".strip()
        reg_date_formatted = reg_date[:10] if reg_date else "Неизвестно"
        
        users_text += f"👤 {full_name}\n"
        users_text += f"🎂 {age} лет | 🏒 {skill_level}\n"
        users_text += f"📅 {reg_date_formatted}\n\n"
    
    await query.edit_message_text(
        users_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]),
        parse_mode='HTML'
    )

# Команда добавления тренировки
async def add_training_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Неверный формат. Используйте:\n"
            "/add_training Название|Описание|ГГГГ-ММ-ДД ЧЧ:ММ|Тренер|Макс.участников|Уровень|Цена"
        )
        return
    
    try:
        training_data = ' '.join(context.args).split('|')
        
        if len(training_data) != 7:
            await update.message.reply_text("❌ Неверное количество параметров.")
            return
        
        name, description, date_time, coach, max_participants, skill_level, price = training_data
        
        # Валидация данных
        datetime.strptime(date_time.strip(), '%Y-%m-%d %H:%M')
        max_participants = int(max_participants.strip())
        price = int(price.strip())
        
        # Добавляем в БД
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trainings (name, description, date_time, coach, max_participants, skill_level, price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name.strip(), description.strip(), date_time.strip(), coach.strip(), 
              max_participants, skill_level.strip(), price))
        
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ <b>Тренировка добавлена!</b>\n\n"
            f"🏒 {name.strip()}\n"
            f"📅 {date_time.strip()}\n"
            f"👨‍🏫 {coach.strip()}\n"
            f"💰 {price}₽",
            parse_mode='HTML'
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ Ошибка в данных: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")

# Рассылка сообщений
async def admin_broadcast(query, context):
    broadcast_text = """
📨 <b>Рассылка сообщений</b>

Для отправки сообщения всем пользователям используйте:
<code>/broadcast Ваше сообщение</code>

<b>Пример:</b>
<code>/broadcast Новая тренировка! Запись открыта на завтра в 19:00</code>

⚠️ <b>Внимание:</b> Сообщение будет отправлено всем зарегистрированным пользователям.
"""
    
    await query.edit_message_text(
        broadcast_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]),
        parse_mode='HTML'
    )

# Команда рассылки
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Введите текст сообщения для рассылки.")
        return
    
    message_text = ' '.join(context.args)
    
    # Получаем всех пользователей
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    successful = 0
    failed = 0
    
    await update.message.reply_text(f"📤 Начинаю рассылку {len(users)} пользователям...")
    
    for user_tuple in users:
        user_id_to_send = user_tuple[0]
        try:
            await context.bot.send_message(
                chat_id=user_id_to_send,
                text=f"📢 <b>Сообщение от администрации</b>\n\n{message_text}",
                parse_mode='HTML'
            )
            successful += 1
        except Exception:
            failed += 1
    
    await update.message.reply_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📤 Отправлено: {successful}\n"
        f"❌ Не удалось: {failed}",
        parse_mode='HTML'
    )