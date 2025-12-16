"""Example: Creating a sample database with test data."""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def create_sample_database():
    """Create a sample database with sample e-commerce data."""
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect("data/analytics.db")
    cursor = conn.cursor()
    
    # Create tables
    print("Creating tables...")
    
    # Customers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        country TEXT,
        signup_date DATE
    )
    """)
    
    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT,
        price DECIMAL(10, 2)
    )
    """)
    
    # Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        order_date DATE,
        total_amount DECIMAL(10, 2),
        status TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
    """)
    
    # Order items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        unit_price DECIMAL(10, 2),
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """)
    
    # Generate sample data
    print("Generating sample data...")
    
    # Customers
    customers_data = []
    countries = ["USA", "UK", "Canada", "Germany", "France", "Australia"]
    for i in range(1, 101):
        signup_date = datetime.now() - timedelta(days=np.random.randint(1, 730))
        customers_data.append((
            i,
            f"Customer {i}",
            f"customer{i}@example.com",
            np.random.choice(countries),
            signup_date.strftime("%Y-%m-%d")
        ))
    
    cursor.executemany("""
    INSERT OR REPLACE INTO customers (customer_id, name, email, country, signup_date)
    VALUES (?, ?, ?, ?, ?)
    """, customers_data)
    
    # Products
    products_data = []
    categories = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports"]
    for i in range(1, 51):
        products_data.append((
            i,
            f"Product {i}",
            np.random.choice(categories),
            round(np.random.uniform(10, 500), 2)
        ))
    
    cursor.executemany("""
    INSERT OR REPLACE INTO products (product_id, product_name, category, price)
    VALUES (?, ?, ?, ?)
    """, products_data)
    
    # Orders and order items
    orders_data = []
    order_items_data = []
    order_item_id = 1
    
    for order_id in range(1, 501):
        customer_id = np.random.randint(1, 101)
        order_date = datetime.now() - timedelta(days=np.random.randint(1, 365))
        status = np.random.choice(["completed", "pending", "cancelled"], p=[0.8, 0.15, 0.05])
        
        # Generate order items
        num_items = np.random.randint(1, 6)
        order_total = 0
        
        for _ in range(num_items):
            product_id = np.random.randint(1, 51)
            quantity = np.random.randint(1, 5)
            
            # Get product price
            cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
            unit_price = cursor.fetchone()[0]
            
            order_total += unit_price * quantity
            
            order_items_data.append((
                order_item_id,
                order_id,
                product_id,
                quantity,
                unit_price
            ))
            order_item_id += 1
        
        orders_data.append((
            order_id,
            customer_id,
            order_date.strftime("%Y-%m-%d"),
            round(order_total, 2),
            status
        ))
    
    cursor.executemany("""
    INSERT OR REPLACE INTO orders (order_id, customer_id, order_date, total_amount, status)
    VALUES (?, ?, ?, ?, ?)
    """, orders_data)
    
    cursor.executemany("""
    INSERT OR REPLACE INTO order_items (order_item_id, order_id, product_id, quantity, unit_price)
    VALUES (?, ?, ?, ?, ?)
    """, order_items_data)
    
    # Commit and close
    conn.commit()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Sample Database Created Successfully!")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    print(f"Customers: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"Products: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    print(f"Orders: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM order_items")
    print(f"Order Items: {cursor.fetchone()[0]}")
    
    print(f"\nDatabase location: data/analytics.db")
    print("=" * 60)
    
    conn.close()


if __name__ == "__main__":
    create_sample_database()
