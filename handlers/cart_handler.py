"""
Обработчик корзины для Telegram-бота TeleFood.

Этот модуль содержит класс CartHandler, отвечающий за управление корзиной пользователя,
включая отображение содержимого корзины, очистку корзины, оформление заказа и добавление товаров.
"""

from collections import Counter

from telebot import types

from database import SessionLocal
from services import (
    add_product_to_cart,
    checkout_cart,
    create_user_if_not_exists,
    get_all_categories,
    get_cart,
)


class CartHandler:
    """
    Обработчик корзины: показывает корзину, оформляет и очищает её, добавляет товары.
    """

    def __init__(self, bot, main_menu):
        self.bot = bot
        self.main_menu = main_menu

    def show_cart(self, message):
        """Отображает содержимое корзины пользователя."""
        with SessionLocal() as db:
            user_id, user_name = create_user_if_not_exists(
                db, message.from_user.id, message.from_user.first_name
            )
            cart = get_cart(db, user_id)
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
            user_id, user_name = create_user_if_not_exists(
                db, call.from_user.id, call.from_user.first_name
            )
            cart = get_cart(db, user_id)
            if cart:
                cart.content = {"products": []}
                db.commit()
        self.bot.answer_callback_query(call.id, "Корзина очищена.")
        self.bot.send_message(
            call.message.chat.id, "Корзина очищена.", reply_markup=self.main_menu
        )

    def ask_payment_method(self, call, order_id):
        """Отображает выбор способа оплаты с номером заказа."""
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
            user_id, user_name = create_user_if_not_exists(
                db, call.from_user.id, call.from_user.first_name
            )
            order = checkout_cart(db, user_id)
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
            user_id, user_name = create_user_if_not_exists(
                db, call.from_user.id, call.from_user.first_name
            )
            add_product_to_cart(db, user_id, product_id)
        self.bot.answer_callback_query(call.id, "Добавлено в корзину.")
        self.bot.send_message(
            call.message.chat.id,
            "Добавлено. Продолжайте выбор или откройте 🛒 Корзину.",
        )

    def pay_online(self, call):
        """Обрабатывает выбор онлайн-оплаты для заказа."""
        order_id = call.data.split("_")[-1]
        self.bot.answer_callback_query(call.id)
        self.bot.send_message(
            call.message.chat.id,
            f"Вы выбрали оплату онлайн для заказа №{order_id}. (Заглушка)",
        )

    def pay_cash(self, call):
        """Обрабатывает выбор оплаты наличными для заказа."""
        order_id = call.data.split("_")[-1]
        self.bot.answer_callback_query(call.id)
        self.bot.send_message(
            call.message.chat.id,
            f"Вы выбрали оплату наличными для заказа №{order_id}. (Заглушка)",
        )
