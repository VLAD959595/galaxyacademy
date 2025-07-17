#!/bin/bash

echo "🏒 Galaxy Hockey Academy Telegram Bot Setup 🏒"
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Пожалуйста, установите Python 3.8 или выше."
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "hockey_bot_env" ]; then
    echo "🔧 Создаем виртуальную среду..."
    python3 -m venv hockey_bot_env
fi

# Activate virtual environment
echo "🔌 Активируем виртуальную среду..."
source hockey_bot_env/bin/activate

# Upgrade pip in virtual environment
echo "📦 Обновляем pip..."
pip install --upgrade pip

echo "📦 Устанавливаем зависимости..."
pip install -r requirements.txt

echo "🚀 Запускаем бота..."
python hockey_bot.py