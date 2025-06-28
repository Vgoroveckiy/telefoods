from typing import List, Optional

from sqlalchemy.orm import Session

from models import Cart, Order, Product, ProductType, User


def create_user_if_not_exists(db: Session, tg_id: str) -> User:
    """Получить или создать пользователя по телеграмм ID.
    :param db: SQLAlchemy сессия
    :param tg_id: ID пользователя Telegram
    :return: Объект User
    """
    user = db.query(User).filter_by(name=tg_id).first()
    if not user:
        user = User(name=tg_id, description="")
        db.add(user)
        db.commit()
        db.refresh(user)
        cart = Cart(user_id=user.id, content={"products": []})
        db.add(cart)
        db.commit()
    return user


def get_all_categories(db: Session) -> List[ProductType]:
    """Получить все категории из базы данных.
    :param db: SQLAlchemy сессия
    :return: Список объектов ProductType, отсортированных по имени
    """
    return db.query(ProductType).order_by(ProductType.name).all()


def get_products_by_category(db: Session, category_id: int) -> List[Product]:
    """Получить все продукты в категории.
    :param db: SQLAlchemy сессия
    :param category_id: ID ProductType (категории)
    :return: Список объектов Product, отсортированных по имени
    """
    return db.query(Product).filter(Product.product_type == category_id).all()


def get_cart(db: Session, user_id: int) -> Optional[Cart]:
    """Получить корзину пользователя из базы данных.

    :param db: сессия SQLAlchemy
    :param user_id: ID пользователя для получения корзины
    :return: объект Cart, если он существует, иначе None
    """
    return db.query(Cart).filter(Cart.user_id == user_id).first()


def add_product_to_cart(db: Session, user_id: int, product_id: int):
    """Добавляет продукт в корзину пользователя.
    :param db: SQLAlchemy сессия
    :param user_id: ID пользователя для которого добавляется товар в корзину
    :param product_id: ID товара который нужно добавить в корзину
    """
    cart = get_cart(db, user_id)
    if cart:
        cart.content.setdefault("products", []).append(product_id)
        db.commit()


def checkout_cart(db: Session, user_id: int) -> Optional[Order]:
    """Оформляет заказ из корзины пользователя и возвращает его, или возвращает None, если корзина пуста или не найдена.
    :param db: SQLAlchemy session
    :param user_id: ID пользователя для оформления корзины
    :return: Объект Order, если он был создан, иначе None
    """
    cart = get_cart(db, user_id)
    print(f"[checkout_cart] Корзина до оформления: {cart.content if cart else None}")
    if cart and cart.content.get("products"):
        order = Order(user_id=user_id, content=cart.content.copy())
        cart.content = {"products": []}
        db.add(order)
        db.commit()
        db.refresh(order)
        print(
            f"[checkout_cart] Заказ создан: {order.id}, корзина после оформления: {cart.content}"
        )
        return order
    print("[checkout_cart] Заказ не создан: корзина пуста или не найдена")
    return None


def get_orders_by_user(db: Session, user_id: int) -> List[Order]:
    """Получение всех заказов для конкретного пользователя из базы данных.

    :param db: сессия SQLAlchemy
    :param user_id: ID пользователя, чьи заказы нужно получить
    :return: Список объектов Order, связанных с пользователем, отсортированный по ID заказа в порядке убывания
    """

    return (
        db.query(Order).filter(Order.user_id == user_id).order_by(Order.id.desc()).all()
    )


def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
    """Получить заказ по его ID из базы данных.
    :param db: SQLAlchemy сессия
    :param order_id: ID заказа для получения
    :return: Объект Order, если он существует, иначе None
    """
    return db.query(Order).get(order_id)


def add_review_to_order(db: Session, order_id: int, text: str):
    """Добавьте отзыв к заказу в базе данных.

    :param db: Сессия SQLAlchemy
    :param order_id: ID Заказа для добавления отзыва
    :param text: Текст отзыва для добавления
    :return: None
    """
    order = db.query(Order).get(order_id)
    if order:
        order.review = text
        db.commit()


def get_menu_messages(db) -> list:
    """
    Возвращает список кортежей (текст, product_id) для меню.
    text — строка для отправки пользователю,
    product_id — id товара (для callback-кнопки).
    """
    messages = []
    categories = get_all_categories(db)
    for cat in categories:
        products = get_products_by_category(db, cat.id)
        if not products:
            continue
        for prod in products:
            price = f"{prod.cost:.2f}" if prod.cost else "-"
            text = f"<b>{cat.name}</b>\n{prod.name}: {price}₽"
            messages.append((text, prod.id))
    return messages
