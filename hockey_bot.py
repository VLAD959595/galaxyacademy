import logging
import os
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

# Conversation states
REGISTER_NAME, REGISTER_AGE, REGISTER_PHONE, REGISTER_EXPERIENCE = range(4)

# Store user registrations (in production, use a proper database)
user_registrations = {}

class HockeyBot:
    def __init__(self):
        self.training_schedule = {
            "Monday": "16:00-17:30 - Beginners, 18:00-19:30 - Advanced",
            "Tuesday": "16:00-17:30 - Intermediate, 18:00-19:30 - Pro Training",
            "Wednesday": "16:00-17:30 - Youth Team, 18:00-19:30 - Adult League",
            "Thursday": "16:00-17:30 - Beginners, 18:00-19:30 - Skills Training",
            "Friday": "16:00-17:30 - Free Skating, 18:00-19:30 - Scrimmage",
            "Saturday": "10:00-11:30 - Kids Program, 14:00-15:30 - All Levels",
            "Sunday": "10:00-11:30 - Family Skating, 14:00-15:30 - Tournament Prep"
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
    elif query.data.startswith('program_'):
        await show_program_details(update, context, query.data.split('_')[1])

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show training schedule."""
    bot = HockeyBot()
    
    schedule_text = "📅 *Расписание тренировок Galaxy Hockey Academy*\n\n"
    
    for day, times in bot.training_schedule.items():
        schedule_text += f"*{day}:*\n{times}\n\n"
    
    schedule_text += "⏰ Все время указано по Дубаю (GST)\n"
    schedule_text += "📍 Локация: Dubai Ice Rink, Dubai Mall\n\n"
    schedule_text += "_Для записи на конкретное время, используйте кнопку 'Записаться на тренировку'_"
    
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_main')]]
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
📍 Адрес: Dubai Ice Rink, Dubai Mall, Downtown Dubai

📱 Телефон: +971 4 448 5111
📧 Email: info@galaxyhockey.ae
🌐 Веб-сайт: www.galaxyhockey.ae

🕐 *Часы работы:*
Понедельник - Пятница: 15:00 - 22:00
Суббота - Воскресенье: 10:00 - 22:00

🚗 *Как добраться:*
• Метро: Станция Burj Khalifa/Dubai Mall
• Парковка: Бесплатная парковка в Dubai Mall
• Такси: До Dubai Mall

💬 *Связаться с нами прямо сейчас:*
Напишите нам в этом чате, и мы ответим в рабочее время!
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
    experience = update.message.text
    user_registrations[user_id]['experience'] = experience
    user_registrations[user_id]['registration_date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Get user data
    user_data = user_registrations[user_id]
    
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
            "📅 Мы работаем:\n"
            "Пн-Пт: 15:00-22:00\n"
            "Сб-Вс: 10:00-22:00\n\n"
            "Для полного расписания тренировок используйте /start → Расписание"
        )
    elif any(word in user_message for word in ['где', 'адрес', 'локация']):
        await update.message.reply_text(
            "📍 Мы находимся в Dubai Ice Rink, Dubai Mall\n"
            "🚇 Ближайшее метро: Burj Khalifa/Dubai Mall\n"
            "🚗 Бесплатная парковка в Dubai Mall\n\n"
            "Подробная информация: /start → Контакты"
        )
    else:
        await update.message.reply_text(
            "Спасибо за ваше сообщение! 💬\n"
            "Наш менеджер ответит вам в рабочее время.\n\n"
            "А пока используйте /start для доступа к информации об академии! 🏒"
        )

def main() -> None:
    """Start the bot."""
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
    application.add_handler(registration_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # Run the bot
    print("🏒 Galaxy Hockey Bot запущен!")
    print("Нажмите Ctrl+C для остановки")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()