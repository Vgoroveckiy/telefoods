import os
from collections import Counter

import telebot
from dotenv import load_dotenv
from telebot import types

from database import SessionLocal
from services import (
    add_product_to_cart,
    add_review_to_order,
    checkout_cart,
    create_user_if_not_exists,
    get_all_categories,
    get_cart,
    get_menu_messages,
    get_orders_by_user,
    get_products_by_category,
)

load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

MENU = {
    "menu": "🍽️ Меню",
    "cart": "🛒 Корзина",
    "orders": "📦 Мои заказы"
}


class MenuHandler:
    """
    Обработчик меню: выводит список категорий и товаров с кнопками добавления в корзину.
    """

    def __init__(self, bot):
        self.bot = bot

    def show_menu(self, message):
        """Показывает меню с категориями и товарами."""
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


class CartHandler:
    """
    Обработчик корзины: показывает корзину, оформляет и очищает её, добавляет товары.
    """

    def __init__(self, bot, main_menu):
        self.bot = bot
        self.main_menu = main_menu

    def show_cart(self, message):
        """Показывает содержимое корзины пользователя."""
        with SessionLocal() as db:
            user = create_user_if_not_exists(db, str(message.from_user.id))
            cart = get_cart(db, user.id)
            if not cart or not cart.content.get("products"):
                self.bot.send_message(
                    message.chat.id, "Корзина пуста.", reply_markup=self.main_menu
                )
                return
            counts = Counter(cart.content["products"])
            text = "<b>Корзина:</b>\n"
            total = 0
            for pid, count in counts.items():
                prod = db.query(get_all_categories.__globals__["Product"]).get(pid)
                if prod:
                    subtotal = prod.cost * count
                    text += f"{prod.name} x{count} = {subtotal:.2f}₽\n"
                    total += subtotal
            text += f"\n<b>Итого: {total:.2f}₽</b>"
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "✅ Оформить заказ", callback_data="checkout"
                ),
                types.InlineKeyboardButton(
                    "🗑 Очистить корзину", callback_data="clear_cart"
                ),
            )
            self.bot.send_message(
                message.chat.id, text, parse_mode="HTML", reply_markup=markup
            )

    def clear_cart(self, call):
        """Очищает корзину пользователя."""
        with SessionLocal() as db:
            user = create_user_if_not_exists(db, str(call.from_user.id))
            cart = get_cart(db, user.id)
            if cart:
                cart.content = {"products": []}
                db.commit()
        self.bot.answer_callback_query(call.id, "Корзина очищена.")
        self.bot.send_message(
            call.message.chat.id, "Корзина очищена.", reply_markup=self.main_menu
        )

    def ask_payment_method(self, call, order_id):
        """Показывает выбор способа оплаты с номером заказа."""
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "💳 Онлайн", callback_data=f"pay_online_{order_id}"
            ),
            types.InlineKeyboardButton(
                "💵 Наличными", callback_data=f"pay_cash_{order_id}"
            ),
        )
        self.bot.send_message(
            call.message.chat.id,
            f"Выберите способ оплаты для заказа №{order_id}:",
            reply_markup=markup,
        )

    def checkout(self, call):
        """Оформляет заказ из корзины пользователя и предлагает выбрать способ оплаты."""
        with SessionLocal() as db:
            user = create_user_if_not_exists(db, str(call.from_user.id))
            order = checkout_cart(db, user.id)
        if order:
            self.bot.send_message(
                call.message.chat.id,
                f"✅ Заказ №{order.id} оформлен!",
                reply_markup=self.main_menu,
            )
            self.ask_payment_method(call, order.id)
        else:
            self.bot.send_message(call.message.chat.id, "Ошибка при оформлении заказа.")

    def add_to_cart(self, call):
        """Добавляет товар в корзину пользователя."""
        product_id = int(call.data.split("_")[1])
        with SessionLocal() as db:
            user = create_user_if_not_exists(db, str(call.from_user.id))
            add_product_to_cart(db, user.id, product_id)
        self.bot.answer_callback_query(call.id, "Добавлено в корзину.")
        self.bot.send_message(
            call.message.chat.id,
            "Добавлено. Продолжайте выбор или откройте 🛒 Корзину.",
        )


class OrderHandler:
    """
    Обработчик заказов: показывает список заказов пользователя.
    """

    def __init__(self, bot, main_menu):
        self.bot = bot
        self.main_menu = main_menu

    def show_orders(self, message):
        """Показывает все оформленные заказы пользователя."""
        with SessionLocal() as db:
            user = create_user_if_not_exists(db, str(message.from_user.id))
            orders = get_orders_by_user(db, user.id)
            if not orders:
                self.bot.send_message(message.chat.id, "У вас нет заказов.")
                return
            for order in orders:
                counts = Counter(order.content.get("products", []))
                text = f"<b>Заказ №{order.id}</b>\n"
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
                    text += f"�� <b>Отзыв:</b>\n<i>отсутствует</i>\n"
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("✍️ Оставить отзыв", callback_data=f"review_{order.id}"))
                self.bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


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
        order_id = int(self.user_states.pop(message.chat.id).split('_')[1])
        review_text = message.text
        with SessionLocal() as db:
            add_review_to_order(db, order_id, review_text)
        self.bot.send_message(message.chat.id, "Спасибо за отзыв!", reply_markup=self.main_menu)


class TeleFoodBot:
    """
    Основной класс Telegram-бота. Агрегирует все обработчики и регистрирует хендлеры.
    """

    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.user_states = {}
        self.main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        self.main_menu.add(MENU['menu'], MENU['cart'])
        self.main_menu.add(MENU['orders'])
        # Handlers
        self.menu_handler = MenuHandler(self.bot)
        self.cart_handler = CartHandler(self.bot, self.main_menu)
        self.order_handler = OrderHandler(self.bot, self.main_menu)
        self.feedback_handler = FeedbackHandler(self.bot, self.main_menu, self.user_states)
        self.register_handlers()

    def register_handlers(self):
        """Регистрирует все хендлеры сообщений и callback-кнопок."""
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            create_user_if_not_exists(SessionLocal(), str(message.from_user.id))
            self.bot.send_message(message.chat.id, "Добро пожаловать в TeleFood!", reply_markup=self.main_menu)
            self.menu_handler.show_menu(message)

        @self.bot.message_handler(func=lambda m: m.text == MENU['menu'])
        def handle_menu(message):
            self.menu_handler.show_menu(message)

        @self.bot.message_handler(func=lambda m: m.text == MENU['cart'])
        def handle_cart(message):
            self.cart_handler.show_cart(message)

        @self.bot.message_handler(func=lambda m: m.text == MENU['orders'])
        def handle_orders(message):
            self.order_handler.show_orders(message)

        @self.bot.message_handler(func=lambda m: self.user_states.get(m.chat.id) == 'awaiting_feedback')
        def save_feedback(message):
            self.feedback_handler.save_feedback(message)

        @self.bot.message_handler(func=lambda m: m.text.startswith("Отзыв "))
        def handle_review(message):
            self.feedback_handler.handle_review(message)

        @self.bot.message_handler(func=lambda m: self.user_states.get(m.chat.id, '').startswith('review_'))
        def save_review(message):
            self.feedback_handler.save_review(message)

        @self.bot.callback_query_handler(func=lambda c: c.data == "clear_cart")
        def clear_cart(call):
            self.cart_handler.clear_cart(call)

        @self.bot.callback_query_handler(func=lambda c: c.data == "checkout")
        def checkout(call):
            self.cart_handler.checkout(call)

        @self.bot.callback_query_handler(func=lambda c: c.data.startswith("add_"))
        def add_to_cart(call):
            self.cart_handler.add_to_cart(call)

        @self.bot.callback_query_handler(func=lambda c: c.data.startswith("pay_online_"))
        def pay_online(call):
            order_id = call.data.split("_")[-1]
            self.bot.answer_callback_query(call.id)
            self.bot.send_message(call.message.chat.id, f"Вы выбрали оплату онлайн для заказа №{order_id}. (Заглушка)")

        @self.bot.callback_query_handler(func=lambda c: c.data.startswith("pay_cash_"))
        def pay_cash(call):
            order_id = call.data.split("_")[-1]
            self.bot.answer_callback_query(call.id)
            self.bot.send_message(call.message.chat.id, f"Вы выбрали оплату наличными для заказа №{order_id}. (Заглушка)")

        @self.bot.callback_query_handler(func=lambda c: c.data.startswith("review_"))
        def review_callback(call):
            order_id = int(call.data.split("_")[1])
            self.feedback_handler.user_states[call.message.chat.id] = f"review_{order_id}"
            self.bot.send_message(call.message.chat.id, f"Напишите отзыв для заказа №{order_id}:")
            self.bot.answer_callback_query(call.id)

    def run(self):
        print("Бот запущен...")
        self.bot.polling(none_stop=True)


if __name__ == "__main__":
    TeleFoodBot(API_TOKEN).run()
