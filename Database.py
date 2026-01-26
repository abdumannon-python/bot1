import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        # DictCursor ma'lumotlarni lug'at (dict) ko'rinishida olishga yordam beradi
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)
        self.create_tables()

    def create_tables(self):
        """Jadvallarni yaratish"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS Users (
                id SERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                full_name VARCHAR(100),
                username VARCHAR(100),
                phone VARCHAR(20),
                role VARCHAR(20) DEFAULT 'customer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                razmer VARCHAR(50),
                price DECIMAL(12, 2) NOT NULL,
                image_id VARCHAR(255),
                stock_quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        for query in queries:
            self.cursor.execute(query)
        self.conn.commit()

    # --- Users Metodlari ---
    def add_user(self, user_id, full_name, username, role='customer'):
        query = """
        INSERT INTO Users (user_id, full_name, username, role)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
        full_name = EXCLUDED.full_name,
        username = EXCLUDED.username;
        """
        self.cursor.execute(query, (user_id, full_name, username, role))
        self.conn.commit()

    def get_user_role(self, user_id):
        query = "SELECT role FROM Users WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        if result:
            return result['role']  # Masalan: 'admin', 'kuryer' yoki 'customer'
        return None
    # --- Products Metodlari ---
    def add_product(self, name, razmer, price, image_id, stock):
        query = """
        INSERT INTO Products (name, razmer, price, image_id, stock_quantity)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        self.cursor.execute(query, (name, razmer, price, image_id, stock))
        new_id=self.cursor.fetchone()[0]
        self.conn.commit()
        return new_id

    def get_all_products(self):
        """Sotuvda bor mahsulotlarni olish"""
        self.cursor.execute("SELECT * FROM Products WHERE stock_quantity > 0")
        return self.cursor.fetchall()

    def search_products(self, search_query):
        """Nomi bo'yicha qidirish"""
        query = "SELECT * FROM Products WHERE name ILIKE %s AND stock_quantity > 0"
        self.cursor.execute(query, (f'%{search_query}%',))
        return self.cursor.fetchall()

    def get_all_products(self):
        self.cursor.execute("SELECT * FROM Products ORDER BY id DESC")
        return self.cursor.fetchall()

    def delete_product(self, product_id):
        self.cursor.execute("DELETE FROM Products WHERE id = %s", (product_id,))
        self.conn.commit()

    def update_stock(self, product_id, new_stock):
        query = "UPDATE Products SET stock_quantity = %s WHERE id = %s"
        self.cursor.execute(query, (new_stock, product_id))
        self.conn.commit()

    def get_active_products(self):
        self.cursor.execute("SELECT * FROM Products WHERE stock_quantity > 0 ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_product_by_id(self, product_id):
        self.cursor.execute("SELECT * FROM Products WHERE id = %s and stock_quantity > 0" , (product_id,))
        return self.cursor.fetchone()
    def __del__(self):
        self.cursor.close()
        self.conn.close()