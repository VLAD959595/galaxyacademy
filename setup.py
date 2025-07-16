#!/usr/bin/env python3
"""
Скрипт автоматической настройки Telegram бота хоккейной академии
"""

import os
import sys
import sqlite3
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 7):
        print("❌ Требуется Python 3.7 или выше")
        print(f"   Ваша версия: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} - OK")
    return True

def install_requirements():
    """Установка зависимостей"""
    print("📦 Установка зависимостей...")
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Зависимости установлены успешно")
            return True
        else:
            print(f"❌ Ошибка установки зависимостей: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Ошибка установки: {e}")
        return False

def create_env_file():
    """Создание .env файла"""
    if os.path.exists('.env'):
        print("✅ Файл .env уже существует")
        return True
    
    if not os.path.exists('.env.example'):
        print("❌ Файл .env.example не найден")
        return False
    
    try:
        with open('.env.example', 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Файл .env создан из .env.example")
        print("⚠️  ВАЖНО: Отредактируйте .env и укажите ваш BOT_TOKEN")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания .env: {e}")
        return False

def check_bot_token():
    """Проверка токена бота"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        token = os.getenv('BOT_TOKEN', '')
        if token == 'YOUR_BOT_TOKEN_HERE' or not token:
            print("❌ Необходимо указать BOT_TOKEN в файле .env")
            print("   1. Откройте Telegram, найдите @BotFather")
            print("   2. Отправьте /newbot и следуйте инструкциям")
            print("   3. Скопируйте токен в файл .env")
            return False
        
        print("✅ BOT_TOKEN настроен")
        return True
    except ImportError:
        print("❌ python-dotenv не установлен")
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки токена: {e}")
        return False

def check_admin_config():
    """Проверка настройки администраторов"""
    try:
        import config
        if not config.ADMIN_IDS or config.ADMIN_IDS == []:
            print("⚠️  ADMIN_IDS не настроены в config.py")
            print("   1. Узнайте ваш Telegram ID у @userinfobot")
            print("   2. Добавьте ID в config.py в список ADMIN_IDS")
            return False
        
        print(f"✅ Настроено {len(config.ADMIN_IDS)} администратор(ов)")
        return True
    except ImportError:
        print("❌ Файл config.py не найден")
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки админов: {e}")
        return False

def init_database():
    """Инициализация базы данных"""
    try:
        import config
        from hockey_bot_updated import init_db
        
        print("🗄️  Инициализация базы данных...")
        init_db()
        print("✅ База данных создана успешно")
        
        # Проверяем содержимое
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM trainings")
        trainings_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   📊 Тренировок в БД: {trainings_count}")
        print(f"   👥 Пользователей в БД: {users_count}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return False

def run_bot_test():
    """Тест запуска бота"""
    print("🤖 Тестирование бота...")
    try:
        # Пробуем импортировать основные модули
        import config
        from hockey_bot_updated import main
        
        if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ Сначала настройте BOT_TOKEN в .env")
            return False
        
        print("✅ Все модули загружены успешно")
        print("🚀 Готов к запуску!")
        
        # Спрашиваем, запустить ли бота
        while True:
            answer = input("\n🤖 Запустить бота сейчас? (y/n): ").lower().strip()
            if answer in ['y', 'yes', 'да', 'д']:
                print("\n🚀 Запуск бота...")
                print("   Для остановки нажмите Ctrl+C")
                print("   Откройте Telegram и найдите вашего бота")
                print("-" * 50)
                main()
                break
            elif answer in ['n', 'no', 'нет', 'н']:
                print("✅ Настройка завершена!")
                print("   Для запуска выполните: python hockey_bot_updated.py")
                break
            else:
                print("   Введите 'y' для запуска или 'n' для выхода")
        
        return True
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    """Основная функция настройки"""
    print("🏒 Настройка Telegram Бота Хоккейной Академии")
    print("=" * 50)
    
    # Проверки
    checks = [
        ("Версия Python", check_python_version),
        ("Установка зависимостей", install_requirements),
        ("Создание .env файла", create_env_file),
        ("Проверка токена бота", check_bot_token),
        ("Инициализация БД", init_database),
        ("Настройка админов", check_admin_config),
        ("Тестирование бота", run_bot_test),
    ]
    
    for name, check_func in checks:
        print(f"\n📋 {name}...")
        if not check_func():
            print(f"\n❌ Настройка прервана на этапе: {name}")
            print("\n📚 Инструкции:")
            print("   • Полная документация: README.md")
            print("   • Быстрый старт: QUICK_START.md")
            sys.exit(1)
    
    print("\n🎉 Настройка завершена успешно!")
    print("\n📋 Что дальше:")
    print("   • Добавьте ваш Telegram ID в config.py для админ-доступа")
    print("   • Настройте информацию об академии в .env")
    print("   • Запустите бота: python hockey_bot_updated.py")

if __name__ == "__main__":
    main()