import aiosqlite
import json
from typing import Optional, List, Dict, Any
from config import DB_NAME

class Database:
    def __init__(self):
        self.db_name = DB_NAME

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_name) as db:
            # Таблица товаров
            await db.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    image_url TEXT,
                    category TEXT,
                    stock INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица категорий
            await db.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')
            
            # Таблица корзины
            await db.execute('''
                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    UNIQUE(user_id, product_id)
                )
            ''')
            
            # Таблица заказов
            await db.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    items TEXT NOT NULL,
                    total_price REAL NOT NULL,
                    phone TEXT,
                    address TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Добавляем категории по умолчанию (без "Комнатные растения")
            categories = ['Букеты', 'Розы', 'Тюльпаны', 'Подарки']
            for category in categories:
                await db.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (category,))
            
            await db.commit()

    # Методы для работы с товарами
    async def add_product(self, name: str, description: str, price: float, 
                         image_url: str, category: str, stock: int = 0) -> int:
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
                INSERT INTO products (name, description, price, image_url, category, stock)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, description, price, image_url, category, stock))
            await db.commit()
            return cursor.lastrowid

    async def get_all_products(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM products ORDER BY created_at DESC') as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM products WHERE id = ?', (product_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_product_stock(self, product_id: int, stock: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE products SET stock = ? WHERE id = ?', (stock, product_id))
            await db.commit()

    async def update_product_price(self, product_id: int, price: float):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE products SET price = ? WHERE id = ?', (price, product_id))
            await db.commit()

    async def delete_product(self, product_id: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('DELETE FROM products WHERE id = ?', (product_id,))
            await db.commit()

    # Методы для работы с корзиной
    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT INTO cart (user_id, product_id, quantity) 
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, product_id) 
                DO UPDATE SET quantity = quantity + ?
            ''', (user_id, product_id, quantity, quantity))
            await db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT c.*, p.name, p.price, p.image_url 
                FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
            ''', (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def remove_from_cart(self, user_id: int, product_id: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?', 
                           (user_id, product_id))
            await db.commit()

    async def clear_cart(self, user_id: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
            await db.commit()

    async def update_cart_quantity(self, user_id: int, product_id: int, quantity: int):
        async with aiosqlite.connect(self.db_name) as db:
            if quantity <= 0:
                await self.remove_from_cart(user_id, product_id)
            else:
                await db.execute('''
                    UPDATE cart SET quantity = ? 
                    WHERE user_id = ? AND product_id = ?
                ''', (quantity, user_id, product_id))
                await db.commit()

    # Методы для работы с заказами
    async def create_order(self, user_id: int, items: List[Dict], total_price: float, 
                          phone: str, address: str) -> int:
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
                INSERT INTO orders (user_id, items, total_price, phone, address)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, json.dumps(items), total_price, phone, address))
            await db.commit()
            return cursor.lastrowid

    async def get_categories(self) -> List[str]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT name FROM categories ORDER BY name') as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM products WHERE category = ?', (category,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]