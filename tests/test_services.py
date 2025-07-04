"""
Модульные тесты для модуля services в приложении TeleFood.

Этот файл содержит тесты для критически важных функций, связанных с управлением пользователями,
операциями с корзиной, обработкой заказов и другой бизнес-логикой.
"""

import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Cart, Order, Product, ProductType, User
from services import (
    add_product_to_cart,
    add_review_to_order,
    checkout_cart,
    create_user_if_not_exists,
    get_all_categories,
    get_cart,
    get_orders_by_user,
    get_products_by_category,
)


class TestServices(unittest.TestCase):
    """
    Класс тестовых случаев для функций модуля services.
    """

    @classmethod
    def setUpClass(cls):
        """
        Настройка базы данных SQLite в памяти для тестирования.
        Выполняется один раз перед всеми тестами в классе.
        """
        # Use an in-memory SQLite database for testing
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        cls.Session = sessionmaker(bind=cls.engine)
        # Create all tables
        Base.metadata.create_all(cls.engine)

        # Populate with test data
        with cls.Session() as db:
            # Add test users
            user1 = User(id=1001, name="TestUser1", description="Test User 1")
            user2 = User(id=1002, name="TestUser2", description="Test User 2")
            db.add_all([user1, user2])
            db.commit()

            # Add test product types (categories)
            cat1 = ProductType(id=1, name="Pizza", description="Pizza category")
            cat2 = ProductType(id=2, name="Sushi", description="Sushi category")
            db.add_all([cat1, cat2])
            db.commit()

            # Add test products
            prod1 = Product(
                id=1,
                name="Margherita",
                cost=10.99,
                product_type=1,
                description="Classic pizza",
            )
            prod2 = Product(
                id=2,
                name="Pepperoni",
                cost=12.99,
                product_type=1,
                description="Pepperoni pizza",
            )
            prod3 = Product(
                id=3,
                name="Salmon Roll",
                cost=8.99,
                product_type=2,
                description="Sushi with salmon",
            )
            db.add_all([prod1, prod2, prod3])
            db.commit()

            # Add test carts
            cart1 = Cart(user_id=1001, content={"products": []})
            cart2 = Cart(user_id=1002, content={"products": [1, 2]})
            db.add_all([cart1, cart2])
            db.commit()

            # Add test orders
            order1 = Order(
                user_id=1001, content={"products": [1, 1, 3]}, review="Great food!"
            )
            order2 = Order(user_id=1001, content={"products": [2]}, review="")
            db.add_all([order1, order2])
            db.commit()

    @classmethod
    def tearDownClass(cls):
        """
        Очистка базы данных в памяти после всех тестов.
        Выполняется один раз после всех тестов в классе.
        """
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        """
        Настройка новой сессии базы данных для каждого теста и сброс состояния базы данных.
        Выполняется перед каждым отдельным тестовым методом.
        """
        self.db = self.Session()
        # Reset relevant tables to initial state before each test for isolation
        self.db.query(Order).delete()
        self.db.query(Cart).delete()
        self.db.query(User).delete()
        self.db.commit()
        # Re-populate with initial test data
        user1 = User(id=1001, name="TestUser1", description="Test User 1")
        user2 = User(id=1002, name="TestUser2", description="Test User 2")
        self.db.add_all([user1, user2])
        self.db.commit()
        cart1 = Cart(user_id=1001, content={"products": []})
        cart2 = Cart(user_id=1002, content={"products": [1, 2]})
        self.db.add_all([cart1, cart2])
        self.db.commit()
        order1 = Order(
            user_id=1001, content={"products": [1, 1, 3]}, review="Great food!"
        )
        order2 = Order(user_id=1001, content={"products": [2]}, review="")
        self.db.add_all([order1, order2])
        self.db.commit()

    def tearDown(self):
        """
        Закрытие сессии базы данных после каждого теста.
        Выполняется после каждого отдельного тестового метода.
        """
        self.db.close()

    def test_create_user_if_not_exists_new_user(self):
        """
        Тестирование создания нового пользователя, если пользователь не существует в базе данных.
        """
        user_id, user_name = create_user_if_not_exists(self.db, 1003, "TestUser3")
        self.assertEqual(user_id, 1003)
        self.assertEqual(user_name, "TestUser3")
        user = self.db.query(User).filter_by(id=1003).first()
        self.assertIsNotNone(user, "User with ID 1003 should be created")
        if user is not None:
            self.assertEqual(user.name, "TestUser3")
        # Check if a cart was created for the new user
        cart = self.db.query(Cart).filter_by(user_id=1003).first()
        self.assertIsNotNone(cart, "Cart for user 1003 should be created")
        if cart is not None:
            self.assertEqual(cart.content, {"products": []})

    def test_create_user_if_not_exists_existing_user(self):
        """
        Тестирование получения существующего пользователя и обновления его имени, если оно изменилось.
        """
        user_id, user_name = create_user_if_not_exists(self.db, 1001, "UpdatedUser1")
        self.assertEqual(user_id, 1001)
        self.assertEqual(user_name, "UpdatedUser1")
        user = self.db.query(User).filter_by(id=1001).first()
        self.assertIsNotNone(user, "User with ID 1001 should exist")
        if user is not None:
            self.assertEqual(user.name, "UpdatedUser1")

    def test_get_all_categories(self):
        """
        Тестирование получения всех категорий продуктов из базы данных.
        """
        categories = get_all_categories(self.db)
        self.assertEqual(len(categories), 2, "Should have 2 categories")
        if categories:
            self.assertEqual(categories[0].name, "Pizza")
            if len(categories) > 1:
                self.assertEqual(categories[1].name, "Sushi")

    def test_get_products_by_category(self):
        """
        Тестирование получения продуктов для конкретной категории.
        """
        pizza_products = get_products_by_category(self.db, 1)
        sushi_products = get_products_by_category(self.db, 2)
        self.assertEqual(len(pizza_products), 2, "Should have 2 pizza products")
        self.assertEqual(len(sushi_products), 1, "Should have 1 sushi product")
        if pizza_products:
            self.assertEqual(pizza_products[0].name, "Margherita")
        if sushi_products:
            self.assertEqual(sushi_products[0].name, "Salmon Roll")

    def test_get_cart(self):
        """
        Тестирование получения корзины пользователя из базы данных.
        """
        cart = get_cart(self.db, 1001)
        self.assertIsNotNone(cart, "Cart should exist for user 1001")
        if cart is not None:
            self.assertEqual(cart.user_id, 1001)
            self.assertEqual(cart.content, {"products": []})

    def test_add_product_to_cart(self):
        """
        Тестирование добавления продукта в корзину пользователя.
        """
        add_product_to_cart(self.db, 1001, 3)
        cart = get_cart(self.db, 1001)
        self.assertIsNotNone(cart, "Cart should exist for user 1001")
        if cart is not None:
            self.assertEqual(cart.content, {"products": [3]})

    def test_checkout_cart_empty(self):
        """
        Тестирование оформления заказа с пустой корзиной, ожидается, что заказ не будет создан.
        """
        # Ensure the cart is empty for user 1001
        cart = get_cart(self.db, 1001)
        self.assertIsNotNone(cart, "Cart should exist for user 1001")
        if cart is not None:
            self.assertEqual(
                cart.content, {"products": []}, "Cart should be empty initially"
            )
        order = checkout_cart(self.db, 1001)
        self.assertIsNone(order, "No order should be created for an empty cart")

    def test_checkout_cart_non_empty(self):
        """
        Тестирование оформления заказа с непустой корзиной, ожидается, что заказ будет создан.
        """
        order = checkout_cart(self.db, 1002)
        self.assertIsNotNone(order, "Order should be created for non-empty cart")
        if order is not None:
            self.assertEqual(order.user_id, 1002)
            self.assertEqual(order.content, {"products": [1, 2]})
        # Check if cart is cleared after checkout
        cart = get_cart(self.db, 1002)
        self.assertIsNotNone(cart, "Cart should exist for user 1002")
        if cart is not None:
            self.assertEqual(cart.content, {"products": []})

    def test_get_orders_by_user(self):
        """
        Тестирование получения всех заказов для конкретного пользователя.
        """
        orders = get_orders_by_user(self.db, 1001)
        self.assertEqual(len(orders), 2, "User 1001 should have 2 orders")
        if orders:
            self.assertEqual(orders[0].user_id, 1001)

    def test_add_review_to_order(self):
        """
        Тестирование добавления отзыва к существующему заказу.
        """
        add_review_to_order(self.db, 2, "Very tasty!")
        order = self.db.query(Order).get(2)
        self.assertIsNotNone(order, "Order with ID 2 should exist")
        if order is not None:
            self.assertEqual(order.review, "Very tasty!")


if __name__ == "__main__":
    unittest.main()
