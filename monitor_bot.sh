#!/bin/bash

# 🏒 Galaxy Hockey Bot Monitor & Auto-Restart Script
# Скрипт автоматического мониторинга и перезапуска бота

LOG_FILE="/workspace/bot_monitor.log"
BOT_DIR="/workspace"
BOT_SCRIPT="hockey_bot.py"

# Функция логирования
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Проверка работает ли бот
check_bot() {
    pgrep -f "$BOT_SCRIPT" > /dev/null
    return $?
}

# Запуск бота
start_bot() {
    cd "$BOT_DIR"
    source hockey_bot_env/bin/activate
    nohup python "$BOT_SCRIPT" > bot_output.log 2>&1 &
    sleep 3
    if check_bot; then
        log_message "✅ Бот успешно запущен"
        # Отправка уведомления админу о перезапуске
        curl -s -X POST "https://api.telegram.org/bot8063979941:AAHaqabigWgdIoVF-XDNmxXTY1WdYE9oUVE/sendMessage" \
        -d chat_id=7691112715 \
        -d text="🔄 Galaxy Hockey Bot автоматически перезапущен! ✅"
    else
        log_message "❌ Ошибка запуска бота"
        # Отправка уведомления об ошибке
        curl -s -X POST "https://api.telegram.org/bot8063979941:AAHaqabigWgdIoVF-XDNmxXTY1WdYE9oUVE/sendMessage" \
        -d chat_id=7691112715 \
        -d text="🚨 ОШИБКА: Galaxy Hockey Bot не удалось запустить!"
    fi
}

# Основная логика мониторинга
main() {
    log_message "🔍 Проверка статуса Galaxy Hockey Bot..."
    
    if check_bot; then
        log_message "✅ Бот работает нормально"
    else
        log_message "❌ Бот не работает! Начинаем перезапуск..."
        start_bot
    fi
}

# Запуск мониторинга
main

# Ежедневная очистка старых логов (оставляем только последние 100 строк)
tail -n 100 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"