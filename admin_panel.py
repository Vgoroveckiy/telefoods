import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.orm import Session
from models import Product, ProductType
from database import SessionLocal


class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление продуктами и типами")
        self.root.geometry("800x600")

        # Раздел "Типы блюд"
        self.setup_types_section()

        # Раздел "Продукты"
        self.setup_products_section()

        # Загрузка данных
        self.load_types()
        self.load_products()

    def setup_types_section(self):
        frame_types = tk.LabelFrame(self.root, text="Типы блюд", padx=10, pady=10)
        frame_types.pack(fill="x", padx=10, pady=5)

        # Поле для ввода нового типа
        self.new_type_entry = tk.Entry(frame_types, width=30)
        self.new_type_entry.pack(side="left", padx=5)

        # Кнопка "Добавить тип"
        tk.Button(
            frame_types,
            text="Добавить тип",
            command=self.add_product_type
        ).pack(side="left", padx=5)

        # Список типов
        self.types_listbox = tk.Listbox(frame_types, width=40, height=5)
        self.types_listbox.pack(side="right", padx=5)

    def setup_products_section(self):
        frame_products = tk.LabelFrame(self.root, text="Продукты", padx=10, pady=10)
        frame_products.pack(fill="both", expand=True, padx=10, pady=5)

        # Таблица продуктов
        columns = ("ID", "Name", "Cost", "Type")
        self.products_tree = ttk.Treeview(
            frame_products,
            columns=columns,
            show="headings",
            height=10
        )

        for col in columns:
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=150, anchor="center")

        self.products_tree.pack(fill="both", expand=True)

        # Поля ввода и кнопки
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

        # Кнопки управления
        btn_frame = tk.Frame(frame_products)
        btn_frame.pack()

        tk.Button(btn_frame, text="Добавить", command=self.add_product).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Обновить", command=self.update_product).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Очистить", command=self.clear_fields).pack(side="left", padx=5)

    def load_types(self):
        db = SessionLocal()
        types = db.query(ProductType).all()
        self.types_listbox.delete(0, tk.END)
        self.product_type_combobox['values'] = []

        for product_type in types:
            self.types_listbox.insert(tk.END, product_type.name)
            self.product_type_combobox['values'] = (*self.product_type_combobox['values'], product_type.name)

        db.close()

    def load_products(self):
        db = SessionLocal()
        products = db.query(Product).join(ProductType).all()
        self.products_tree.delete(*self.products_tree.get_children())

        for product in products:
            self.products_tree.insert("", tk.END, values=(
                product.id,
                product.name,
                f"{product.cost:.2f}",
                product.product_type_rel.name
            ))

        db.close()

    def add_product_type(self):
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

        new_product = Product(
            name=name,
            cost=cost,
            product_type=product_type.id
        )

        db.add(new_product)
        db.commit()
        db.close()

        self.clear_fields()
        self.load_products()
        messagebox.showinfo("Успех", "Продукт добавлен!")

    def update_product(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите продукт для обновления!")
            return

        item = self.products_tree.item(selected[0])
        product_id = item['values'][0]

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
        product = db.query(Product).get(product_id)
        product_type = db.query(ProductType).filter_by(name=type_name).first()

        if not product_type:
            messagebox.showerror("Ошибка", "Выберите существующий тип!")
            db.close()
            return

        product.name = name
        product.cost = cost
        product.product_type = product_type.id

        db.commit()
        db.close()

        self.clear_fields()
        self.load_products()
        messagebox.showinfo("Успех", "Продукт обновлен!")

    def clear_fields(self):
        self.product_name_entry.delete(0, tk.END)
        self.product_cost_entry.delete(0, tk.END)
        self.product_type_combobox.set('')


if __name__ == "__main__":
    root = tk.Tk()
    app = AdminPanel(root)
    root.mainloop()