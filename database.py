import csv
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'data' / 'sales.db'
CSV_PATH = ROOT / 'data' / 'sales.csv'


def connect(path=None):
    conn = sqlite3.connect(str(path or DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def initialize(path=None, csv_path=None):
    conn = connect(path)
    conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
      transaction_id TEXT PRIMARY KEY, order_date TEXT, product TEXT, category TEXT,
      region TEXT, sales_channel TEXT, quantity INTEGER, unit_price REAL,
      discount_amount REAL, status TEXT, revenue REAL, exclusion_reason TEXT)''')
    conn.execute('DELETE FROM transactions')
    with open(csv_path or CSV_PATH, newline='', encoding='utf-8-sig') as file:
        for row in csv.DictReader(file):
            reasons = []
            def number(key):
                try:
                    value = row[key].strip()
                    return float(value) if value else None
                except (ValueError, KeyError, AttributeError):
                    return None
            quantity = number('Quantity')
            price = number('Unit_price')
            discount = number('Discount_amount')
            try:
                date = datetime.strptime(row['Order_date'].strip(), '%d-%m-%Y').date().isoformat()
            except (ValueError, KeyError, AttributeError):
                date = None
                reasons.append('invalid date')
            status = (row.get('Status') or '').strip()
            if status != 'Completed': reasons.append('not completed')
            if quantity is None or not quantity.is_integer() or quantity <= 0: reasons.append('invalid quantity')
            if price is None or price < 0: reasons.append('invalid unit price')
            if discount is None or discount < 0: reasons.append('invalid discount')
            for key in ('Transaction_Id', 'Product', 'Category', 'Region', 'Sales_channel'):
                if not (row.get(key) or '').strip(): reasons.append('missing ' + key)
            revenue = None
            if not reasons:
                revenue = quantity * price - discount
                if revenue < 0:
                    reasons.append('discount exceeds gross sales')
                    revenue = None
            try:
                conn.execute('INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
                    row.get('Transaction_Id','').strip(), date,
                    row.get('Product','').strip(), row.get('Category','').strip(),
                    row.get('Region','').strip(), row.get('Sales_channel','').strip(),
                    int(quantity) if quantity is not None and quantity.is_integer() else None,
                    price, discount, status, revenue, '; '.join(reasons) if reasons else None))
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                conn.close()
                raise ValueError('Duplicate or missing transaction ID in CSV') from exc
    conn.commit()
    conn.close()


if __name__ == '__main__':
    initialize()
    print('Database initialized:', DB_PATH)
