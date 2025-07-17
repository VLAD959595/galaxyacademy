#!/bin/bash

# 🏒 Setup Auto-Monitoring for Galaxy Hockey Bot
# Настройка автоматического мониторинга бота

echo "🔧 Настройка автоматического мониторинга Galaxy Hockey Bot..."

# Создаем cron job для проверки каждые 5 минут
(crontab -l 2>/dev/null; echo "*/5 * * * * cd /workspace && /workspace/monitor_bot.sh >> /workspace/cron.log 2>&1") | crontab -

# Создаем cron job для ежедневной проверки в 08:00
(crontab -l 2>/dev/null; echo "0 8 * * * cd /workspace && /workspace/check_bot_status.sh >> /workspace/daily_status.log 2>&1") | crontab -

echo "✅ Автоматический мониторинг настроен!"
echo ""
echo "📋 Настроенные задачи:"
echo "   🔄 Каждые 5 минут - проверка и автоперезапуск"
echo "   📊 Каждый день в 08:00 - статус отчет"
echo ""
echo "📁 Лог файлы:"
echo "   📝 Мониторинг: bot_monitor.log"
echo "   📝 Cron задачи: cron.log"
echo "   📝 Ежедневные отчеты: daily_status.log"
echo ""
echo "🔍 Проверить статус: ./check_bot_status.sh"
echo "🔄 Ручной перезапуск: ./monitor_bot.sh"

# Показать текущие cron задачи
echo ""
echo "📅 Текущие cron задачи:"
crontab -l