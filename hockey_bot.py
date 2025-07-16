import logging
import os
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import asyncio

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "8063979941:AAHaqabigWgdIoVF-XDNmxXTY1WdYE9oUVE"

# Admin chat ID (замените на свой Telegram ID)
ADMIN_CHAT_ID = "YOUR_ADMIN_CHAT_ID"  # Получите свой ID у @userinfobot

# Conversation states
REGISTER_NAME, REGISTER_AGE, REGISTER_PHONE, REGISTER_EXPERIENCE = range(4)

# Store user registrations (in production, use a proper database)
user_registrations = {}

# Store user carts and orders
user_carts = {}
user_orders = {}

# File for storing registrations
REGISTRATIONS_FILE = "registrations.json"
ORDERS_FILE = "orders.json"

# Shop catalog
SHOP_CATALOG = {
    "🏒 Клюшки": {
        "🥅 Клюшка для вратаря": {"price": 450, "description": "Профессиональная клюшка для вратарей", "stock": 10},
        "⚡ Клюшка нападающего": {"price": 380, "description": "Легкая клюшка для нападающих и полузащитников", "stock": 15},
        "🛡️ Клюшка защитника": {"price": 400, "description": "Усиленная клюшка для защитников", "stock": 12}
    },
    "👕 Форма": {
        "🏒 Игровая форма Galaxy": {"price": 220, "description": "Фирменная игровая форма Galaxy Hockey Academy", "stock": 25},
        "🥶 Тренировочная форма": {"price": 180, "description": "Удобная форма для тренировок", "stock": 30},
        "🧤 Перчатки хоккейные": {"price": 280, "description": "Защитные перчатки для игры", "stock": 20}
    },
    "🪖 Защита": {
        "⛑️ Шлем с маской": {"price": 320, "description": "Защитный шлем с решеткой", "stock": 18},
        "🦵 Щитки": {"price": 250, "description": "Защитные щитки для ног", "stock": 22},
        "🦴 Нагрудник": {"price": 380, "description": "Защита груди и спины", "stock": 15}
    },
    "👕 Одежда Galaxy": {
        "🧥 Худи Galaxy": {"price": 120, "description": "Фирменное худи Galaxy Hockey Academy", "stock": 40},
        "👕 Футболка Galaxy": {"price": 80, "description": "Стильная футболка с логотипом", "stock": 50},
        "🧢 Кепка Galaxy": {"price": 60, "description": "Бейсболка с логотипом академии", "stock": 35}
    }
}

def load_registrations():
    """Load registrations from file."""
    global user_registrations
    try:
        if os.path.exists(REGISTRATIONS_FILE):
            with open(REGISTRATIONS_FILE, 'r', encoding='utf-8') as f:
                user_registrations = json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки регистраций: {e}")
        user_registrations = {}

def save_registrations():
    """Save registrations to file."""
    try:
        with open(REGISTRATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_registrations, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения регистраций: {e}")

def load_orders():
    """Load orders from file."""
    global user_orders
    try:
        if os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                user_orders = json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки заказов: {e}")
        user_orders = {}

def save_orders():
    """Save orders to file."""
    try:
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_orders, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения заказов: {e}")

async def notify_admin(context, user_data, user_info):
    """Notify admin about new registration."""
    if ADMIN_CHAT_ID != "YOUR_ADMIN_CHAT_ID":
        notification = f"""
🏒 *НОВАЯ РЕГИСТРАЦИЯ В GALAXY HOCKEY ACADEMY* 🏒

👤 *Пользователь:* @{user_info.username or 'без username'} ({user_info.first_name} {user_info.last_name or ''})
📋 *Данные:*
• Имя: {user_data['name']}
• Возраст: {user_data['age']} лет
• Телефон: {user_data['phone']}
• Уровень: {user_data['experience']}
• Дата записи: {user_data['registration_date']}

📱 *Telegram ID:* {user_info.id}
        """
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=notification,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админу: {e}")

class HockeyBot:
    def __init__(self):
        self.training_schedule = {
            "Tuesday": "🧒 Ю9 и Ю12 — лёд в 19:45\n🧑 Ю15 и Ю18 — лёд в 20:45",
            "Thursday": "🧒 Ю9 и Ю12 — лёд в 19:45\n🧑 Ю15 и Ю18 — лёд в 20:45", 
            "Sunday": "🧒 Ю9 и Ю12 — лёд в 08:00\n🧑 Ю15 и Ю18 — лёд в 09:00"
        }
        
        self.training_programs = {
            "🥅 Beginner Program": {
                "description": "Perfect for those new to hockey. Learn basic skating, stick handling, and shooting.",
                "duration": "8 weeks",
                "price": "1200 AED",
                "age": "6+ years"
            },
            "⚡ Intermediate Program": {
                "description": "Build on your skills with advanced techniques and game strategies.",
                "duration": "10 weeks", 
                "price": "1500 AED",
                "age": "10+ years"
            },
            "🏆 Advanced Program": {
                "description": "Elite training for competitive players. Tournament preparation included.",
                "duration": "12 weeks",
                "price": "2000 AED", 
                "age": "14+ years"
            },
            "👨‍👩‍👧‍👦 Family Package": {
                "description": "Special rates for families. Learn together, play together!",
                "duration": "8 weeks",
                "price": "2800 AED (up to 4 family members)",
                "age": "All ages"
            }
        }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    
    welcome_text = f"""
🏒 Добро пожаловать в Galaxy Hockey Academy, {user.first_name}! 🏒

🌟 Дубай's Premier Ice Hockey Training Center 🌟

Мы предлагаем:
⭐ Профессиональные тренировки для всех уровней
⭐ Современное оборудование и ледовая арена
⭐ Опытные тренеры из разных стран
⭐ Индивидуальный подход к каждому ученику

Используйте меню ниже для навигации! 👇
    """
    
    keyboard = [
        [InlineKeyboardButton("📅 Расписание", callback_data='schedule')],
        [InlineKeyboardButton("📝 Записаться на тренировку", callback_data='register')],
        [InlineKeyboardButton("🛒 Магазин Galaxy", callback_data='shop')],
        [InlineKeyboardButton("🏒 Программы обучения", callback_data='programs')],
        [InlineKeyboardButton("📞 Контакты", callback_data='contact')],
        [InlineKeyboardButton("📰 Новости", callback_data='news')],
        [InlineKeyboardButton("💡 Советы по хоккею", callback_data='tips')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'schedule':
        await show_schedule(update, context)
    elif query.data == 'register':
        await start_registration(update, context)
    elif query.data == 'shop':
        await show_shop_categories(update, context)
    elif query.data == 'programs':
        await show_programs(update, context)
    elif query.data == 'contact':
        await show_contact(update, context)
    elif query.data == 'news':
        await show_news(update, context)
    elif query.data == 'tips':
        await show_tips(update, context)
    elif query.data == 'back_to_main':
        await start(update, context)
    elif query.data == 'back_to_shop':
        await show_shop_categories(update, context)
    elif query.data == 'view_cart':
        await show_cart(update, context)
    elif query.data.startswith('shop_category_'):
        category = query.data.replace('shop_category_', '').replace('_', ' ')
        await show_category_items(update, context, category)
    elif query.data.startswith('shop_item_'):
        item_data = query.data.replace('shop_item_', '').split('|')
        await show_item_details(update, context, item_data[0], item_data[1])
    elif query.data.startswith('add_to_cart_'):
        item_data = query.data.replace('add_to_cart_', '').split('|')
        await add_to_cart(update, context, item_data[0], item_data[1])
    elif query.data.startswith('remove_from_cart_'):
        item_data = query.data.replace('remove_from_cart_', '').split('|')
        await remove_from_cart(update, context, item_data[0], item_data[1])
    elif query.data == 'checkout':
        await checkout(update, context)
    elif query.data.startswith('program_'):
        await show_program_details(update, context, query.data.split('_')[1])

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show training schedule."""
    schedule_text = """
📍 *Локация:*
Galaxy Hockey Academy  
Sport Society Mall, район Мердив, Дубай 🇦🇪

📆 *Расписание тренировок:*

*Вторник и Четверг:*
• 🧒 Ю9 и Ю12 — лёд в *19:45*  
• 🧑 Ю15 и Ю18 — лёд в *20:45*

*Воскресенье:*
• 🧒 Ю9 и Ю12 — лёд в *08:00*  
• 🧑 Ю15 и Ю18 — лёд в *09:00*

🧢 *Магазин Galaxy:*
У нас вы можете приобрести фирменную хоккейную экипировку: клюшки, форму, шлемы, худи и многое другое.  
*Теперь доступна онлайн‑покупка прямо в этом боте!*

📞 *Контакт:* +971 50 859 9547  
📸 *Instagram:* [galaxy_hockey_academy](https://www.instagram.com/galaxy_hockey_academy?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==)

*Galaxy — сильнейшая хоккейная академия в Персидском заливе!*
    """
    
    keyboard = [
        [InlineKeyboardButton("🛒 Магазин Galaxy", callback_data='shop')],
        [InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=schedule_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def show_programs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show training programs."""
    programs_text = "🏒 *Наши программы обучения* 🏒\n\n"
    
    keyboard = []
    bot = HockeyBot()
    
    for program_name, details in bot.training_programs.items():
        programs_text += f"{program_name}\n"
        programs_text += f"📝 {details['description']}\n"
        programs_text += f"⏱️ Длительность: {details['duration']}\n"
        programs_text += f"💰 Цена: {details['price']}\n"
        programs_text += f"👥 Возраст: {details['age']}\n\n"
        
        # Create callback data for each program
        callback_data = f"program_{program_name.split()[1].lower()}"
        keyboard.append([InlineKeyboardButton(f"Выбрать {program_name}", callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=programs_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show contact information."""
    contact_text = """
📞 *Контактная информация*

🏢 *Galaxy Hockey Academy*
📍 Адрес: Sport Society Mall, район Мердив, Дубай 🇦🇪

📱 Телефон: +971 50 859 9547
📸 Instagram: [galaxy_hockey_academy](https://www.instagram.com/galaxy_hockey_academy?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==)

🕐 *Расписание тренировок:*
*Вторник и Четверг:*
• 🧒 Ю9 и Ю12 — лёд в *19:45*  
• 🧑 Ю15 и Ю18 — лёд в *20:45*

*Воскресенье:*
• 🧒 Ю9 и Ю12 — лёд в *08:00*  
• 🧑 Ю15 и Ю18 — лёд в *09:00*

🚗 *Как добраться:*
• Метро: Ближайшая станция Rashidiya
• Парковка: Бесплатная парковка в Sport Society Mall
• Такси: До Sport Society Mall, Мердив

💬 *Связаться с нами:*
Используйте команду /info или напишите нам здесь!
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=contact_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def show_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show latest news."""
    news_text = """
📰 *Последние новости Galaxy Hockey Academy*

🎉 *15 января 2024*
Открытие нового сезона! Специальные скидки для новых учеников - 20% на первый месяц обучения.

🏆 *10 января 2024* 
Наши юниоры заняли 1-е место в Dubai Youth Hockey Championship! Поздравляем команду!

⭐ *5 января 2024*
Новое оборудование CCM и Bauer уже в нашей академии. Обновленная экипировка для всех программ.

🎯 *1 января 2024*
С Новым Годом! Специальный новогодний турнир для всех учеников 15 января.

📅 *Предстоящие события:*
• 20 января - День открытых дверей
• 25 января - Мастер-класс с профессиональным игроком NHL
• 30 января - Семейный хоккейный день
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=news_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def show_tips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show hockey tips."""
    tips_text = """
💡 *Полезные советы по хоккею от наших тренеров*

🥅 *Для новичков:*
• Начните с основ катания - это фундамент хоккея
• Держите голову поднятой на льду
• Практикуйте владение шайбой каждый день
• Изучите правила игры

⚡ *Техника катания:*
• Короткие, быстрые шаги эффективнее длинных
• Наклон тела вперед для лучшего баланса
• Отталкивайтесь внешней стороной конька
• Тренируйте повороты в обе стороны

🏒 *Работа с клюшкой:*
• Клюшка - продолжение ваших рук
• Мягкие руки для лучшего контроля
• Практикуйте пас и прием шайбы
• Отрабатывайте бросок с разных позиций

🎯 *Ментальная подготовка:*
• Визуализируйте успешные действия
• Анализируйте игру профессионалов
• Работайте в команде
• Не бойтесь ошибок - учитесь на них!

📈 *Физическая подготовка:*
• Укрепляйте мышцы ног и кора
• Развивайте гибкость
• Кардио тренировки вне льда
• Правильное питание и отдых
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=tips_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration process."""
    await update.callback_query.edit_message_text(
        "📝 *Регистрация на тренировки*\n\n"
        "Давайте зарегистрируем вас на тренировки!\n"
        "Как вас зовут? (Имя и Фамилия)",
        parse_mode='Markdown'
    )
    return REGISTER_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save name and ask for age."""
    user_id = update.effective_user.id
    name = update.message.text
    
    if user_id not in user_registrations:
        user_registrations[user_id] = {}
    user_registrations[user_id]['name'] = name
    
    await update.message.reply_text(
        f"Приятно познакомиться, {name}! 👋\n\n"
        "Сколько вам лет?"
    )
    return REGISTER_AGE

async def register_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save age and ask for phone."""
    user_id = update.effective_user.id
    try:
        age = int(update.message.text)
        user_registrations[user_id]['age'] = age
        
        await update.message.reply_text(
            "Отлично! 📱\n\n"
            "Теперь укажите ваш номер телефона для связи:"
        )
        return REGISTER_PHONE
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите возраст числом (например: 25)"
        )
        return REGISTER_AGE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save phone and ask for experience."""
    user_id = update.effective_user.id
    phone = update.message.text
    user_registrations[user_id]['phone'] = phone
    
    keyboard = [
        ["🆕 Новичок", "🎯 Есть опыт"],
        ["🏆 Продвинутый", "🌟 Профессионал"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Отлично! 🏒\n\n"
        "Какой у вас уровень подготовки в хоккее?",
        reply_markup=reply_markup
    )
    return REGISTER_EXPERIENCE

async def register_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Complete registration."""
    user_id = update.effective_user.id
    user_info = update.effective_user
    experience = update.message.text
    user_registrations[user_id]['experience'] = experience
    user_registrations[user_id]['registration_date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    user_registrations[user_id]['telegram_username'] = user_info.username or 'без username'
    user_registrations[user_id]['telegram_name'] = f"{user_info.first_name} {user_info.last_name or ''}".strip()
    
    # Save to file
    save_registrations()
    
    # Get user data
    user_data = user_registrations[user_id]
    
    # Notify admin
    await notify_admin(context, user_data, user_info)
    
    # Recommend program based on experience
    recommended_program = ""
    if "Новичок" in experience:
        recommended_program = "🥅 Beginner Program"
    elif "Есть опыт" in experience:
        recommended_program = "⚡ Intermediate Program"
    elif "Продвинутый" in experience:
        recommended_program = "🏆 Advanced Program"
    else:
        recommended_program = "🏆 Advanced Program"
    
    completion_text = f"""
✅ *Регистрация завершена успешно!*

📋 *Ваши данные:*
👤 Имя: {user_data['name']}
🎂 Возраст: {user_data['age']} лет
📱 Телефон: {user_data['phone']}
🏒 Уровень: {user_data['experience']}

🎯 *Рекомендуемая программа:* {recommended_program}

📞 *Что дальше?*
Наш менеджер свяжется с вами в течение 24 часов для подтверждения записи и выбора удобного времени тренировок.

📞 *Контакт:* +971 50 859 9547

💬 Если у вас есть вопросы, напишите их в этом чате!
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        completion_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel registration."""
    await update.message.reply_text(
        "Регистрация отменена. Вы можете вернуться к ней в любое время! 👋"
    )
    return ConversationHandler.END

async def info_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /info and /schedule commands."""
    message = """
📍 *Локация:*
Galaxy Hockey Academy  
Sport Society Mall, район Мердив, Дубай 🇦🇪

📆 *Расписание тренировок:*

*Вторник и Четверг:*
• 🧒 Ю9 и Ю12 — лёд в *19:45*  
• 🧑 Ю15 и Ю18 — лёд в *20:45*

*Воскресенье:*
• 🧒 Ю9 и Ю12 — лёд в *08:00*  
• 🧑 Ю15 и Ю18 — лёд в *09:00*

🧢 *Магазин Galaxy:*
У нас вы можете приобрести фирменную хоккейную экипировку: клюшки, форму, шлемы, худи и многое другое.  
*Скоро прямо здесь будет доступна онлайн‑покупка в Telegram!*

📞 *Контакт:* +971 50 859 9547  
📸 *Instagram:* [galaxy_hockey_academy](https://www.instagram.com/galaxy_hockey_academy?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==)

*Galaxy — сильнейшая хоккейная академия в Персидском заливе!*
    """
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get user's chat ID."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    message = f"""
🆔 *Ваша информация:*

👤 *Имя:* {user.first_name} {user.last_name or ''}
👨‍💻 *Username:* @{user.username or 'отсутствует'}
🆔 *Chat ID:* `{chat_id}`
📱 *User ID:* `{user.id}`

📋 *Для настройки админа скопируйте Chat ID*
    """
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def admin_registrations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all registrations (admin only)."""
    user_id = str(update.effective_user.id)
    
    # Check if user is admin
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    if not user_registrations:
        await update.message.reply_text("📋 Регистраций пока нет.")
        return
    
    message = "📊 *ВСЕ РЕГИСТРАЦИИ GALAXY HOCKEY ACADEMY*\n\n"
    
    count = 0
    for user_id, data in user_registrations.items():
        count += 1
        message += f"*#{count}*\n"
        message += f"👤 {data.get('name', 'Неизвестно')}\n"
        message += f"🎂 {data.get('age', 'Неизвестно')} лет\n"
        message += f"📱 {data.get('phone', 'Неизвестно')}\n"
        message += f"🏒 {data.get('experience', 'Неизвестно')}\n"
        message += f"📅 {data.get('registration_date', 'Неизвестно')}\n"
        message += f"👨‍💻 @{data.get('telegram_username', 'без username')}\n"
        message += "➖➖➖➖➖➖➖➖➖➖\n\n"
    
    message += f"📈 *Всего регистраций:* {count}"
    
    # Split message if too long
    if len(message) > 4000:
        parts = []
        current_part = "📊 *ВСЕ РЕГИСТРАЦИИ GALAXY HOCKEY ACADEMY*\n\n"
        
        for user_id, data in user_registrations.items():
            entry = f"👤 {data.get('name', 'Неизвестно')} | 🎂 {data.get('age', 'Неизвестно')} | 📱 {data.get('phone', 'Неизвестно')}\n"
            
            if len(current_part + entry) > 4000:
                parts.append(current_part)
                current_part = entry
            else:
                current_part += entry
        
        if current_part:
            parts.append(current_part)
        
        for part in parts:
            await update.message.reply_text(part, parse_mode='Markdown')
    else:
        await update.message.reply_text(message, parse_mode='Markdown')

# SHOP FUNCTIONS

async def show_shop_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show shop categories."""
    user_id = update.effective_user.id
    cart_count = len(user_carts.get(str(user_id), {}))
    
    shop_text = f"""
🛒 *Магазин Galaxy Hockey Academy*

Добро пожаловать в наш онлайн-магазин! 
Здесь вы найдете лучшую хоккейную экипировку и фирменную одежду Galaxy.

🎯 *Категории товаров:*
    """
    
    keyboard = []
    for category in SHOP_CATALOG.keys():
        callback_data = f"shop_category_{category.replace(' ', '_')}"
        keyboard.append([InlineKeyboardButton(category, callback_data=callback_data)])
    
    # Cart and back buttons
    cart_text = f"🛒 Корзина ({cart_count})" if cart_count > 0 else "🛒 Корзина"
    keyboard.append([
        InlineKeyboardButton(cart_text, callback_data='view_cart'),
        InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_main')
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=shop_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def show_category_items(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    """Show items in a category."""
    if category not in SHOP_CATALOG:
        await update.callback_query.answer("Категория не найдена!")
        return
    
    items = SHOP_CATALOG[category]
    category_text = f"🛍️ *{category}*\n\n"
    
    keyboard = []
    for item_name, item_info in items.items():
        price = item_info['price']
        stock = item_info['stock']
        status = "✅" if stock > 0 else "❌ Нет в наличии"
        
        item_text = f"{item_name} - {price} AED {status}"
        callback_data = f"shop_item_{category}|{item_name}"
        keyboard.append([InlineKeyboardButton(item_text, callback_data=callback_data)])
    
    keyboard.append([
        InlineKeyboardButton("🔙 К категориям", callback_data='back_to_shop'),
        InlineKeyboardButton("🛒 Корзина", callback_data='view_cart')
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=category_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def show_item_details(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, item_name: str) -> None:
    """Show item details."""
    if category not in SHOP_CATALOG or item_name not in SHOP_CATALOG[category]:
        await update.callback_query.answer("Товар не найден!")
        return
    
    item_info = SHOP_CATALOG[category][item_name]
    
    item_text = f"""
🏷️ *{item_name}*

📝 *Описание:* {item_info['description']}
💰 *Цена:* {item_info['price']} AED
📦 *В наличии:* {item_info['stock']} шт.
    """
    
    keyboard = []
    if item_info['stock'] > 0:
        callback_data = f"add_to_cart_{category}|{item_name}"
        keyboard.append([InlineKeyboardButton("🛒 Добавить в корзину", callback_data=callback_data)])
    
    category_callback = f"shop_category_{category.replace(' ', '_')}"
    keyboard.append([
        InlineKeyboardButton(f"🔙 К {category}", callback_data=category_callback),
        InlineKeyboardButton("🛒 Корзина", callback_data='view_cart')
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=item_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, item_name: str) -> None:
    """Add item to cart."""
    user_id = str(update.effective_user.id)
    
    if category not in SHOP_CATALOG or item_name not in SHOP_CATALOG[category]:
        await update.callback_query.answer("Товар не найден!")
        return
    
    item_info = SHOP_CATALOG[category][item_name]
    
    if item_info['stock'] <= 0:
        await update.callback_query.answer("Товар закончился!")
        return
    
    if user_id not in user_carts:
        user_carts[user_id] = {}
    
    cart_key = f"{category}|{item_name}"
    if cart_key in user_carts[user_id]:
        user_carts[user_id][cart_key]['quantity'] += 1
    else:
        user_carts[user_id][cart_key] = {
            'category': category,
            'item_name': item_name,
            'price': item_info['price'],
            'quantity': 1
        }
    
    await update.callback_query.answer(f"✅ {item_name} добавлен в корзину!")
    
    # Return to item details
    await show_item_details(update, context, category, item_name)

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's cart."""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_carts or not user_carts[user_id]:
        cart_text = "🛒 *Ваша корзина пуста*\n\nДобавьте товары из каталога!"
        keyboard = [[InlineKeyboardButton("🛍️ К покупкам", callback_data='back_to_shop')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=cart_text, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
        return
    
    cart = user_carts[user_id]
    cart_text = "🛒 *Ваша корзина:*\n\n"
    total = 0
    
    keyboard = []
    for cart_key, item in cart.items():
        item_total = item['price'] * item['quantity']
        total += item_total
        
        cart_text += f"• {item['item_name']}\n"
        cart_text += f"  💰 {item['price']} AED × {item['quantity']} = {item_total} AED\n\n"
        
        # Remove button for each item
        remove_callback = f"remove_from_cart_{item['category']}|{item['item_name']}"
        keyboard.append([InlineKeyboardButton(f"❌ Убрать {item['item_name']}", callback_data=remove_callback)])
    
    cart_text += f"💳 *Итого: {total} AED*"
    
    # Checkout and navigation buttons
    keyboard.append([InlineKeyboardButton("💳 Оформить заказ", callback_data='checkout')])
    keyboard.append([
        InlineKeyboardButton("🛍️ Продолжить покупки", callback_data='back_to_shop'),
        InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_main')
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=cart_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, item_name: str) -> None:
    """Remove item from cart."""
    user_id = str(update.effective_user.id)
    cart_key = f"{category}|{item_name}"
    
    if user_id in user_carts and cart_key in user_carts[user_id]:
        if user_carts[user_id][cart_key]['quantity'] > 1:
            user_carts[user_id][cart_key]['quantity'] -= 1
        else:
            del user_carts[user_id][cart_key]
        
        await update.callback_query.answer(f"✅ {item_name} убран из корзины!")
    
    # Refresh cart view
    await show_cart(update, context)

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process checkout."""
    user_id = str(update.effective_user.id)
    user_info = update.effective_user
    
    if user_id not in user_carts or not user_carts[user_id]:
        await update.callback_query.answer("Корзина пуста!")
        return
    
    cart = user_carts[user_id]
    order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
    
    # Calculate total
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    
    # Create order
    order = {
        'order_id': order_id,
        'user_id': user_id,
        'user_info': {
            'username': user_info.username or 'без username',
            'first_name': user_info.first_name,
            'last_name': user_info.last_name or ''
        },
        'items': cart.copy(),
        'total': total,
        'status': 'новый',
        'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save order
    if user_id not in user_orders:
        user_orders[user_id] = []
    user_orders[user_id].append(order)
    save_orders()
    
    # Clear cart
    user_carts[user_id] = {}
    
    # Notify admin about new order
    await notify_admin_order(context, order)
    
    # Show order confirmation
    order_text = f"""
✅ *Заказ успешно оформлен!*

📋 *Номер заказа:* {order_id}
💳 *Сумма:* {total} AED
📅 *Дата:* {order['order_date']}

📞 *Что дальше?*
Наш менеджер свяжется с вами для подтверждения заказа и договоренности о доставке.

📱 *Контакт:* +971 50 859 9547

🎯 *Способы получения:*
• 📍 Самовывоз из Sport Society Mall
• 🚚 Доставка по Дубаю (по договоренности)

Спасибо за покупку в Galaxy Hockey Academy! 🏒
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=order_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def notify_admin_order(context, order):
    """Notify admin about new order."""
    if ADMIN_CHAT_ID != "YOUR_ADMIN_CHAT_ID":
        items_text = ""
        for item in order['items'].values():
            items_text += f"• {item['item_name']} × {item['quantity']} = {item['price'] * item['quantity']} AED\n"
        
        notification = f"""
🛒 *НОВЫЙ ЗАКАЗ В GALAXY SHOP* 🛒

📋 *Заказ:* {order['order_id']}
👤 *Покупатель:* @{order['user_info']['username']} ({order['user_info']['first_name']} {order['user_info']['last_name']})

📦 *Товары:*
{items_text}
💳 *Итого:* {order['total']} AED

📅 *Дата заказа:* {order['order_date']}
📱 *Telegram ID:* {order['user_id']}

❗ Свяжитесь с покупателем для подтверждения заказа!
        """
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=notification,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о заказе: {e}")

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any text messages not in conversation."""
    user_message = update.message.text.lower()
    
    # Simple AI-like responses for common questions
    if any(word in user_message for word in ['привет', 'здравствуйте', 'добрый день']):
        await update.message.reply_text(
            "Привет! 👋 Добро пожаловать в Galaxy Hockey Academy!\n"
            "Используйте /start чтобы открыть главное меню."
        )
    elif any(word in user_message for word in ['цена', 'стоимость', 'сколько стоит']):
        await update.message.reply_text(
            "💰 Наши цены:\n"
            "🥅 Beginners - 1200 AED\n"
            "⚡ Intermediate - 1500 AED\n"
            "🏆 Advanced - 2000 AED\n"
            "👨‍👩‍👧‍👦 Family Package - 2800 AED\n\n"
            "Для подробной информации используйте /start → Программы обучения"
        )
    elif any(word in user_message for word in ['время', 'расписание', 'когда']):
        await update.message.reply_text(
            "📅 Тренировки проходят:\n"
            "Вторник и Четверг в 19:45 и 20:45\n"
            "Воскресенье в 08:00 и 09:00\n\n"
            "Используйте /schedule для полного расписания"
        )
    elif any(word in user_message for word in ['где', 'адрес', 'локация']):
        await update.message.reply_text(
            "📍 Мы находимся в Sport Society Mall, район Мердив, Дубай 🇦🇪\n"
            "📞 Контакт: +971 50 859 9547\n"
            "📸 Instagram: galaxy_hockey_academy\n\n"
            "Используйте /info для подробной информации"
        )
    else:
        await update.message.reply_text(
            "Спасибо за ваше сообщение! 💬\n"
            "Наш менеджер ответит вам в рабочее время.\n\n"
            "А пока используйте /start для доступа к информации об академии! 🏒"
        )

def main() -> None:
    """Start the bot."""
    # Load existing registrations and orders
    load_registrations()
    load_orders()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for registration
    registration_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_registration, pattern="^register$")],
        states={
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_age)],
            REGISTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
            REGISTER_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_experience)],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info_schedule_command))
    application.add_handler(CommandHandler("schedule", info_schedule_command))
    application.add_handler(CommandHandler("get_my_id", get_my_id))
    application.add_handler(CommandHandler("admin_registrations", admin_registrations))
    application.add_handler(registration_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # Run the bot
    print("🏒 Galaxy Hockey Bot запущен!")
    print("Нажмите Ctrl+C для остановки")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()