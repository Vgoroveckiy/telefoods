"""
Конфигурационные настройки для приложения Telegram-бота TeleFood.

Этот файл централизует константы, переменные окружения и другие настройки конфигурации,
используемые в приложении, для улучшения поддерживаемости и удобства обновлений.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Telegram Bot API Token
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Menu Constants for Bot Interface
MENU = {"menu": "🍽️ Меню", "cart": "🛒 Корзина", "orders": "📦 Мои заказы"}
