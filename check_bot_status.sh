#!/bin/bash

# 🏒 Galaxy Hockey Bot Status Checker
# Быстрая проверка статуса бота

echo "🔍 Проверка статуса Galaxy Hockey Bot..."
echo "========================================="

if pgrep -f "hockey_bot.py" > /dev/null; then
    PID=$(pgrep -f "hockey_bot.py")
    UPTIME=$(ps -o etime= -p $PID | tr -d ' ')
    echo "✅ Бот РАБОТАЕТ"
    echo "📋 PID: $PID"
    echo "⏰ Время работы: $UPTIME"
    echo "🗂️ Файлы:"
    echo "   - Регистрации: $([ -f registrations.json ] && echo "✅ Найден" || echo "❌ Не найден")"
    echo "   - Заказы: $([ -f orders.json ] && echo "✅ Найден" || echo "❌ Не найден")"
    echo "📊 Статистика:"
    echo "   - Регистраций: $([ -f registrations.json ] && jq '. | length' registrations.json 2>/dev/null || echo "0")"
    echo "   - Заказов: $([ -f orders.json ] && jq '. | length' orders.json 2>/dev/null || echo "0")"
else
    echo "❌ Бот НЕ РАБОТАЕТ!"
    echo "🔧 Для запуска используйте: ./start_bot.sh"
    echo "🔄 Для авто-перезапуска: ./monitor_bot.sh"
fi

echo "========================================="
echo "📅 Проверка выполнена: $(date)"

# Показать последние 5 строк лога
if [ -f "bot_monitor.log" ]; then
    echo ""
    echo "📊 Последние записи лога:"
    tail -n 5 bot_monitor.log
fi