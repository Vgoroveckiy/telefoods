"""
Обработчик заказов для Telegram-бота TeleFood.

Этот модуль содержит класс OrderHandler, отвечающий за управление и отображение
заказов пользователя.
"""

import datetime
from collections import Counter

from telebot import types

from database import SessionLocal
from services import create_user_if_not_exists, get_all_categories, get_orders_by_user


class OrderHandler:
    """
    Обработчик заказов: показывает список заказов пользователя.
    """

    def __init__(self, bot, main_menu):
        self.bot = bot
        self.main_menu = main_menu

    def show_orders(self, message):
        """Отображает все оформленные заказы пользователя."""
        with SessionLocal() as db:
            user_id, user_name = create_user_if_not_exists(
                db, message.from_user.id, message.from_user.first_name
            )
            orders = get_orders_by_user(db, user_id)
            if not orders:
                self.bot.send_message(message.chat.id, "У вас нет заказов.")
                return
            for order in orders:
                counts = Counter(order.content.get("products", []))
                created_at_str = "неизвестно"
                if order.created_at:
                    try:
                        # Convert UTC to Moscow time (UTC+3)
                        moscow_time = order.created_at.replace(
                            tzinfo=datetime.timezone.utc
                        ).astimezone(datetime.timezone(datetime.timedelta(hours=3)))
                        created_at_str = moscow_time.strftime("%d.%m.%Y %H:%M")
                    except (AttributeError, ValueError):
                        pass
                text = f"<b>Заказ №{order.id}</b> от {created_at_str} (мск)\n"
                total = 0
                for pid, count in counts.items():
                    prod = db.query(get_all_categories.__globals__["Product"]).get(pid)
                    if prod:
                        subtotal = prod.cost * count
                        text += f"{prod.name} x{count} = {subtotal:.2f}₽\n"
                        total += subtotal
                text += f"Итого: {total:.2f}₽\n"
                if order.review:
                    text += f"💬 <b>Отзыв:</b>\n<i>«{order.review}»</i>\n"
                else:
                    text += f" <b>Отзыв:</b>\n<i>отсутствует</i>\n"
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "✍️ Оставить отзыв", callback_data=f"review_{order.id}"
                    )
                )
                self.bot.send_message(
                    message.chat.id, text, parse_mode="HTML", reply_markup=markup
                )
