from sqlalchemy.orm import Session
from models import User, Product, ProductType, Order

# Получить все категории блюд
def get_all_categories(db: Session):
    return db.query(ProductType).all()

# Получить все блюда по id категории
def get_products_by_category(db: Session, category_id: int):
    return db.query(Product).filter(Product.product_type == category_id).all()

# Получить пользователя по tg_id (name)
def get_user_by_tg_id(db: Session, tg_id: str):
    return db.query(User).filter(User.name == tg_id).first()

# Создать пользователя, если не существует
def create_user_if_not_exists(db: Session, tg_id: str, description: str = ""): 
    user = get_user_by_tg_id(db, tg_id)
    if not user:
        user = User(name=tg_id, description=description)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# Получить корзину пользователя (неоформленный заказ)
def get_cart(db: Session, user_id: int):
    return db.query(Order).filter(Order.user_id == user_id, Order.pay_status == False).first()

# Добавить блюдо в корзину (content - список блюд)
def add_product_to_cart(db: Session, user_id: int, product_id: int):
    cart = get_cart(db, user_id)
    if not cart:
        cart = Order(user_id=user_id, content={"products": [product_id]}, pay_status=False)
        db.add(cart)
    else:
        products = cart.content.get("products", [])
        products.append(product_id)
        cart.content["products"] = products
    db.commit()
    db.refresh(cart)
    return cart

# Оформить заказ (установить pay_status=True)
def checkout_cart(db: Session, user_id: int, description: str = ""): 
    cart = get_cart(db, user_id)
    if cart:
        cart.pay_status = True
        cart.description = description
        db.commit()
        db.refresh(cart)
    return cart

# Получить все заказы пользователя
def get_orders_by_user(db: Session, user_id: int):
    return db.query(Order).filter(Order.user_id == user_id, Order.pay_status == True).all()

# Получить заказ по id
def get_order_by_id(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == order_id).first()

# Добавить отзыв к заказу
def add_review_to_order(db: Session, order_id: int, review: str):
    order = get_order_by_id(db, order_id)
    if order:
        order.review = review
        db.commit()
        db.refresh(order)
    return order 