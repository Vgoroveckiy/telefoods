"""
Обработчик обратной связи для Telegram-бота TeleFood.

Этот модуль содержит класс FeedbackHandler, отвечающий за обработку обратной связи
пользователей и отзывов о заказах.
"""

from telebot import types

from database import SessionLocal
from services import add_review_to_order


class FeedbackHandler:
    """
    Обработчик обратной связи и отзывов по заказам.
    """

    def __init__(self, bot, main_menu, user_states):
        self.bot = bot
        self.main_menu = main_menu
        self.user_states = user_states

    def handle_feedback(self, message):
        """Запрашивает у пользователя текст обратной связи."""
        self.bot.send_message(
            message.chat.id, "Напишите ваш отзыв. Он будет отправлен администратору."
        )
        self.user_states[message.chat.id] = "awaiting_feedback"

    def save_feedback(self, message):
        """Сохраняет обратную связь пользователя."""
        text = message.text
        self.user_states.pop(message.chat.id)
        self.bot.send_message(
            message.chat.id, "Спасибо за отзыв!", reply_markup=self.main_menu
        )

    def handle_review(self, message):
        """Запрашивает отзыв по заказу."""
        try:
            order_id = int(message.text.split()[1])
            self.user_states[message.chat.id] = f"review_{order_id}"
            self.bot.send_message(
                message.chat.id, f"Напишите отзыв для заказа №{order_id}:"
            )
        except:
            self.bot.send_message(message.chat.id, "Формат: Отзыв <номер_заказа>")

    def save_review(self, message):
        """Сохраняет отзыв пользователя по заказу."""
        order_id = int(self.user_states.pop(message.chat.id).split("_")[1])
        review_text = message.text
        with SessionLocal() as db:
            add_review_to_order(db, order_id, review_text)
        self.bot.send_message(
            message.chat.id, "Спасибо за отзыв!", reply_markup=self.main_menu
        )

    def review_callback(self, call):
        """Обрабатывает callback для начала написания отзыва к заказу."""
        order_id = int(call.data.split("_")[1])
        self.user_states[call.message.chat.id] = f"review_{order_id}"
        self.bot.send_message(
            call.message.chat.id, f"Напишите отзыв для заказа №{order_id}:"
        )
        self.bot.answer_callback_query(call.id)
