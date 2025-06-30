import tkinter as tk
from tkinter import messagebox, ttk

from database import SessionLocal
from models import Product, ProductType


class AdminPanel:
    """
    Класс для управления продуктами и их типами в GUI приложении.

    Этот класс реализует интерфейс администратора для добавления, обновления и удаления продуктов и их типов из базы данных.
    """

    def __init__(self, master):
        """
        Инициализация компонентов GUI.

        Создает все необходимые виджеты и устанавливает их параметры. Также проверяет наличие и создает базу данных при необходимости.
        """
        self.master = master
        self.master.title("Управление продуктами и типами")
        self.master.geometry("800x600")

        # Инициализация всех атрибутов UI в __init__
        self.new_type_entry = None
        self.types_listbox = None
        self.products_tree = None
        self.product_name_entry = None
        self.product_cost_entry = None
        self.product_type_combobox = None

        # Проверка БД (теперь static method)
        self._initialize_database()

        self.initialize_ui()

    @staticmethod
    def _initialize_database():
        """
        Проверяет наличие базы данных и создает таблицы при необходимости.

        Создает необходимые таблицы в базе данных, если их еще нет.
        """
        from pathlib import Path

        from database import Base, engine

        db_file = Path("app.db")
        if not db_file.exists():
            Base.metadata.create_all(bind=engine)
            print("БД создана автоматически!")

    def initialize_ui(self):
        """
        Инициализирует все компоненты GUI.

        Создает и размещает на форме все необходимые элементы пользовательского интерфейса.
        """
        self.setup_types_section()
        self.setup_products_section()
        self.load_data()

    def load_data(self):
        """
        Загружает данные при старте.

        Перезагружает список типов и продуктов из базы данных, когда окно открывается.
        """
        self.load_types()
        self.load_products()

    def setup_types_section(self):
        """
        Устанавливает раздел с типами блюд.

        Создает и размещает на форме элементы для ввода нового типа блюда и отображения списка существующих типов.
        """
        frame_types = tk.LabelFrame(self.master, text="Типы блюд", padx=10, pady=10)
        frame_types.pack(fill="x", padx=10, pady=5)

        # Контейнер для поля ввода и кнопки
        input_frame = tk.Frame(frame_types)
        input_frame.pack(side="left", fill="x", expand=True)

        # Поле для ввода нового типа
        self.new_type_entry = tk.Entry(input_frame, width=30)
        self.new_type_entry.pack(side="left", padx=5)

        # Кнопка "Добавить тип"
        tk.Button(input_frame, text="Добавить тип", command=self.add_product_type).pack(
            side="left", padx=5
        )

        # Контейнер для списка и полосы прокрутки
        list_frame = tk.Frame(frame_types)
        list_frame.pack(side="right", fill="both", expand=True)

        # Список типов с прокруткой
        self.types_listbox = tk.Listbox(
            list_frame, width=40, height=5, exportselection=False
        )

        # Вертикальная полоса прокрутки
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.types_listbox.yview
        )
        self.types_listbox.configure(yscrollcommand=scrollbar.set)

        # Размещение списка и полосы прокрутки
        self.types_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_products_section(self):
        """
        Устанавливает раздел с продуктами.

        Создает и размещает на форме элементы для отображения продуктов, их добавления и обновления.
        """
        frame_products = tk.LabelFrame(self.master, text="Продукты", padx=10, pady=10)
        frame_products.pack(fill="both", expand=True, padx=10, pady=5)

        # Создаем фрейм для таблицы и полосы прокрутки
        tree_frame = tk.Frame(frame_products)
        tree_frame.pack(fill="both", expand=True)

        # Таблица продуктов
        columns = ("ID", "Name", "Cost", "Type")
        self.products_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=10,  # Количество отображаемых строк
        )

        # Настройка колонок (как в предыдущем примере)
        self.products_tree.heading("ID", text="ID", anchor="center")
        self.products_tree.heading("Name", text="Name", anchor="w")
        self.products_tree.heading("Cost", text="Cost", anchor="center")
        self.products_tree.heading("Type", text="Type", anchor="w")

        self.products_tree.column("ID", width=50, anchor="center")
        self.products_tree.column("Name", width=200, anchor="w")
        self.products_tree.column("Cost", width=100, anchor="center")
        self.products_tree.column("Type", width=150, anchor="w")

        # Вертикальная полоса прокрутки
        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.products_tree.yview
        )
        self.products_tree.configure(yscrollcommand=scrollbar.set)

        # Размещаем таблицу и полосу прокрутки
        self.products_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        input_frame = tk.Frame(frame_products)
        input_frame.pack(fill="x", pady=10)

        tk.Label(input_frame, text="Название:").grid(row=0, column=0)
        self.product_name_entry = tk.Entry(input_frame, width=30)
        self.product_name_entry.grid(row=0, column=1, padx=5)

        tk.Label(input_frame, text="Цена:").grid(row=0, column=2)
        self.product_cost_entry = tk.Entry(input_frame, width=10)
        self.product_cost_entry.grid(row=0, column=3, padx=5)

        tk.Label(input_frame, text="Тип:").grid(row=0, column=4)
        self.product_type_combobox = ttk.Combobox(input_frame, width=20)
        self.product_type_combobox.grid(row=0, column=5, padx=5)

        btn_frame = tk.Frame(frame_products)
        btn_frame.pack()

        tk.Button(btn_frame, text="Добавить", command=self.add_product).pack(
            side="left", padx=5
        )
        tk.Button(btn_frame, text="Обновить", command=self.update_product).pack(
            side="left", padx=5
        )

    def load_types(self):
        """Загружает все доступные типы продуктов из базы данных и отображает их в списке и комбобоксе."""
        db = SessionLocal()
        types = db.query(ProductType).all()
        self.types_listbox.delete(0, tk.END)
        self.product_type_combobox["values"] = []

        for product_type in types:
            self.types_listbox.insert(tk.END, product_type.name)
            self.product_type_combobox["values"] = (
                *self.product_type_combobox["values"],
                product_type.name,
            )

        db.close()

    def load_products(self):
        """Загружает все доступные продукты из базы данных и отображает их в таблице."""
        db = SessionLocal()
        products = db.query(Product).join(ProductType).all()
        self.products_tree.delete(*self.products_tree.get_children())

        for product in products:
            self.products_tree.insert(
                "",
                tk.END,
                values=(
                    product.id,
                    product.name,
                    f"{product.cost:.2f}",
                    product.type_rel.name,
                ),
            )

        db.close()

    def add_product_type(self):
        """Добавляет новый тип продукта в базу данных и обновляет список типов."""
        type_name = self.new_type_entry.get().strip()
        if not type_name:
            messagebox.showwarning("Ошибка", "Введите название типа!")
            return

        db = SessionLocal()
        new_type = ProductType(name=type_name)
        db.add(new_type)
        db.commit()
        db.close()

        self.new_type_entry.delete(0, tk.END)
        self.load_types()
        messagebox.showinfo("Успех", "Тип добавлен!")

    def add_product(self):
        """Добавляет новый продукт в базу данных и обновляет таблицу продуктов."""
        name = self.product_name_entry.get().strip()
        cost = self.product_cost_entry.get().strip()
        type_name = self.product_type_combobox.get().strip()

        if not all([name, cost, type_name]):
            messagebox.showwarning("Ошибка", "Заполните все поля!")
            return

        try:
            cost = float(cost)
        except ValueError:
            messagebox.showerror("Ошибка", "Цена должна быть числом!")
            return

        db = SessionLocal()
        product_type = db.query(ProductType).filter_by(name=type_name).first()

        if not product_type:
            messagebox.showerror("Ошибка", "Выберите существующий тип!")
            db.close()
            return

        new_product = Product(name=name, cost=cost, product_type=product_type.id)

        db.add(new_product)
        db.commit()
        db.close()

        self.clear_fields()
        self.load_products()
        messagebox.showinfo("Успех", "Продукт добавлен!")

    def update_product(self):
        """Обновляет существующий продукт в базе данных и обновляет таблицу продуктов."""
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите продукт для обновления!")
            return

        item = self.products_tree.item(selected[0])
        product_id = item["values"][0]

        name = self.product_name_entry.get().strip()
        cost = self.product_cost_entry.get().strip()
        type_name = self.product_type_combobox.get().strip()

        if not all([name, cost, type_name]):
            messagebox.showwarning("Ошибка", "Заполните все поля!")
            return

        try:
            cost = float(cost)
        except ValueError:
            messagebox.showerror("Ошибка", "Цена должна быть числом!")
            return

        db = SessionLocal()
        try:
            product = db.get(Product, product_id)
            if not product:
                messagebox.showerror("Ошибка", "Продукт не найден!")
                return

            product_type = db.query(ProductType).filter_by(name=type_name).first()
            if not product_type:
                messagebox.showerror("Ошибка", "Выберите существующий тип!")
                return

            product.name = name
            product.cost = cost
            product.product_type = product_type.id

            db.commit()
            self.load_products()
            messagebox.showinfo("Успех", "Продукт обновлен!")
            self.clear_fields()  # ← Добавляем очистку полей здесь!

        except Exception as e:
            db.rollback()
            messagebox.showerror("Ошибка", f"Ошибка при обновлении: {str(e)}")
        finally:
            db.close()

    def clear_fields(self):
        """Очищает поля ввода для добавления и обновления продуктов."""
        self.product_name_entry.delete(0, tk.END)
        self.product_cost_entry.delete(0, tk.END)
        self.product_type_combobox.set("")


if __name__ == "__main__":
    main_window = tk.Tk()  # Переименовали для ясности
    app = AdminPanel(main_window)
    main_window.mainloop()
