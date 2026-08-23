from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS customer_number VARCHAR;"))
    db.commit()
    print("Successfully added customer_number column.")
    
    # Also backfill existing rows
    customers = db.execute(text("SELECT id FROM customers WHERE customer_number IS NULL")).fetchall()
    from utils.ids import generate_customer_number
    for c in customers:
        db.execute(text("UPDATE customers SET customer_number = :num WHERE id = :id"), {"num": generate_customer_number(), "id": c[0]})
    db.commit()
    print("Backfilled existing customers.")
except Exception as e:
    print("Error:", e)
finally:
    db.close()
