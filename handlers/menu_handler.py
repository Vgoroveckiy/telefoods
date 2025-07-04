"""
Обработчик меню для Telegram-бота TeleFood.

Этот модуль содержит класс MenuHandler, отвечающий за отображение меню
с категориями и товарами, а также кнопками для добавления товаров в корзину.
"""

from telebot import types

from database import SessionLocal
from services import get_all_categories, get_products_by_category


class MenuHandler:
    """
    Обработчик меню: выводит список категорий и товаров с кнопками добавления в корзину.
    """

    def __init__(self, bot):
        self.bot = bot

    def show_menu(self, message):
        """Отображает меню с категориями и товарами."""
        with SessionLocal() as db:
            categories = get_all_categories(db)
            for cat in categories:
                products = get_products_by_category(db, cat.id)
                if not products:
                    continue
                text = f"<b>{cat.name}</b>\n"
                markup = types.InlineKeyboardMarkup()
                for prod in products:
                    price = f"{prod.cost:.2f}" if prod.cost else "-"
                    text += f"{prod.name}: {price}₽\n"
                    markup.add(
                        types.InlineKeyboardButton(
                            f"➕ {prod.name}", callback_data=f"add_{prod.id}"
                        )
                    )
                self.bot.send_message(
                    message.chat.id, text, parse_mode="HTML", reply_markup=markup
                )
