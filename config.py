import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Настройки академии
ACADEMY_NAME = os.getenv('ACADEMY_NAME', 'Хоккейная Академия "Ледяные Волки"')
ACADEMY_ADDRESS = os.getenv('ACADEMY_ADDRESS', 'г. Москва, ул. Спортивная, 15')
ACADEMY_PHONE = os.getenv('ACADEMY_PHONE', '+7 (495) 123-45-67')
ACADEMY_EMAIL = os.getenv('ACADEMY_EMAIL', 'info@icewolves.ru')
ACADEMY_WEBSITE = os.getenv('ACADEMY_WEBSITE', 'www.icewolves.ru')

# Настройки базы данных
DB_NAME = os.getenv('DB_NAME', 'hockey_academy.db')

# Настройки уведомлений
REMINDER_HOURS = int(os.getenv('REMINDER_HOURS', 24))

# ID администраторов (добавьте свой Telegram ID)
ADMIN_IDS = [
    # 123456789,  # Замените на ваш Telegram ID
]