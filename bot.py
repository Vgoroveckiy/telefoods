"""
Основной скрипт для Telegram-бота TeleFood.

Этот скрипт инициализирует Telegram-бота, настраивает обработчики для взаимодействия с пользователем
и запускает цикл опроса бота для обработки входящих сообщений и callback-запросов.
"""

import logging

import telebot
from telebot import types

from config import API_TOKEN, MENU
from database import SessionLocal
from handlers.cart_handler import CartHandler
from handlers.feedback_handler import FeedbackHandler
from handlers.menu_handler import MenuHandler
from handlers.order_handler import OrderHandler
from services import create_user_if_not_exists

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("telefood_bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger("TeleFoodBot")


class TeleFoodBot:
    """
    Основной класс Telegram-бота TeleFood.

    Этот класс отвечает за инициализацию бота, настройку пользовательского интерфейса (меню),
    агрегацию всех обработчиков для различных функций бота (меню, корзина, заказы, отзывы)
    и регистрацию хендлеров для обработки входящих сообщений и callback-запросов от пользователей.
    """

    def __init__(self, token):
        """
        Инициализирует бот с указанным токеном и настраивает обработчики.

        Args:
            token (str): Токен API Telegram бота.
        """
        self.bot = telebot.TeleBot(token)
        self.user_states = {}
        self.main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        self.main_menu.add(MENU["menu"], MENU["cart"])
        self.main_menu.add(MENU["orders"])
        # Handlers
        self.menu_handler = MenuHandler(self.bot)
        self.cart_handler = CartHandler(self.bot, self.main_menu)
        self.order_handler = OrderHandler(self.bot, self.main_menu)
        self.feedback_handler = FeedbackHandler(
            self.bot, self.main_menu, self.user_states
        )
        self.register_handlers()
        logger.info("TeleFoodBot initialized")

    def register_handlers(self):
        """
        Регистрирует все хендлеры сообщений и callback-кнопок для обработки пользовательских взаимодействий.

        Этот метод настраивает обработчики для команд (например, /start), текстовых сообщений
        (например, выбор пунктов меню), и callback-запросов от интерактивных кнопок (например,
        добавление товара в корзину, оформление заказа, оставление отзыва). Каждый хендлер
        делегирует выполнение соответствующему классу-обработчику (MenuHandler, CartHandler и т.д.),
        обеспечивая модульность и разделение ответственности.
        """

        @self.bot.message_handler(commands=["start"])
        def handle_start(message):
            user_id, user_name = create_user_if_not_exists(
                SessionLocal(), message.from_user.id, message.from_user.first_name
            )
            self.bot.send_message(
                message.chat.id,
                f"Добро пожаловать, {user_name}, в TeleFood!",
                reply_markup=self.main_menu,
            )
            logger.info(f"User {user_name} (ID: {user_id}) started the bot")

        @self.bot.message_handler(func=lambda m: m.text == MENU["menu"])
        def handle_menu(message):
            logger.info(f"User {message.from_user.id} accessed menu")
            self.menu_handler.show_menu(message)

        @self.bot.message_handler(func=lambda m: m.text == MENU["cart"])
        def handle_cart(message):
            logger.info(f"User {message.from_user.id} accessed cart")
            self.cart_handler.show_cart(message)

        @self.bot.message_handler(func=lambda m: m.text == MENU["orders"])
        def handle_orders(message):
            logger.info(f"User {message.from_user.id} accessed orders")
            self.order_handler.show_orders(message)

        @self.bot.message_handler(
            func=lambda m: self.user_states.get(m.chat.id) == "awaiting_feedback"
        )
        def save_feedback(message):
            logger.info(f"User {message.from_user.id} provided feedback")
            self.feedback_handler.save_feedback(message)

        @self.bot.message_handler(func=lambda m: m.text.startswith("Отзыв "))
        def handle_review(message):
            logger.info(f"User {message.from_user.id} initiated review")
            self.feedback_handler.handle_review(message)

        @self.bot.message_handler(
            func=lambda m: self.user_states.get(m.chat.id, "").startswith("review_")
        )
        def save_review(message):
            logger.info(f"User {message.from_user.id} saved review")
            self.feedback_handler.save_review(message)

        @self.bot.callback_query_handler(func=lambda c: c.data == "clear_cart")
        def clear_cart(call):
            logger.info(f"User {call.from_user.id} cleared cart")
            self.cart_handler.clear_cart(call)

        @self.bot.callback_query_handler(func=lambda c: c.data == "checkout")
        def checkout(call):
            logger.info(f"User {call.from_user.id} initiated checkout")
            self.cart_handler.checkout(call)

        @self.bot.callback_query_handler(func=lambda c: c.data.startswith("add_"))
        def add_to_cart(call):
            logger.info(f"User {call.from_user.id} added item to cart")
            self.cart_handler.add_to_cart(call)

        @self.bot.callback_query_handler(
            func=lambda c: c.data.startswith("pay_online_")
        )
        def pay_online(call):
            logger.info(f"User {call.from_user.id} selected online payment")
            self.cart_handler.pay_online(call)

        @self.bot.callback_query_handler(func=lambda c: c.data.startswith("pay_cash_"))
        def pay_cash(call):
            logger.info(f"User {call.from_user.id} selected cash payment")
            self.cart_handler.pay_cash(call)

        @self.bot.callback_query_handler(func=lambda c: c.data.startswith("review_"))
        def review_callback(call):
            logger.info(f"User {call.from_user.id} initiated review")
            self.feedback_handler.review_callback(call)

    def run(self):
        """
        Запускает бесконечный цикл опроса для обработки входящих сообщений и callback-запросов.

        Этот метод инициирует работу бота, позволяя ему непрерывно обрабатывать пользовательские
        взаимодействия. В случае возникновения ошибки в процессе опроса, метод логирует ошибку
        и пытается перезапустить цикл опроса для обеспечения непрерывной работы бота.
        """
        logger.info("Bot started polling...")
        try:
            self.bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Polling error: {str(e)}")
            # Можно добавить перезапуск или уведомление администратора
            self.run()  # Попытка перезапуска в случае ошибки


if __name__ == "__main__":
    bot = TeleFoodBot(API_TOKEN)
    bot.run()
