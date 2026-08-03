from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.business import (
    Product, RetailerInventory, SaleRecord, BusinessExpense,
    InvoiceRecord, QuotationRecord, ReceiptRecord, BusinessCardProfile
)

# --- Products ---
def create_product(db: Session, product_data: dict, user_id: int = 1, owner_type: str = "Manufacturer"):
    visibility = "Global" if owner_type == "Manufacturer" else "Private"
    product_data.pop("initial_stock", None)
    product_data.pop("reminder_stock", None)
    if "gst_id" in product_data and product_data["gst_id"]:
        from models.business import GSTMaster
        gst_master = db.query(GSTMaster).filter(GSTMaster.id == product_data["gst_id"]).first()
        if gst_master:
            product_data["gst_rate"] = gst_master.gst_rate
            
    db_product = Product(**product_data, creator_id=user_id, owner_type=owner_type, visibility=visibility)
    try:
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError:
        db.rollback()
        raise ValueError("Barcode already exists")

def lookup_product(db: Session, barcode: str, user_id: int):
    # 1. Search private products owned by user
    product = db.query(Product).filter(
        Product.barcode == barcode, 
        Product.visibility == "Private", 
        Product.creator_id == user_id
    ).first()
    
    if product:
        return product
        
    # 2. Search global products
    product = db.query(Product).filter(
        Product.barcode == barcode, 
        Product.visibility == "Global"
    ).first()
    
    return product

# --- Inventory ---
def add_to_inventory(db: Session, inv_data: dict, retailer_id: int):
    # Find existing inventory link
    product = db.query(Product).filter(Product.barcode == inv_data["barcode"]).first()
    if not product:
        raise ValueError("Product not found")
        
    db_inv = db.query(RetailerInventory).filter(
        RetailerInventory.retailer_id == retailer_id,
        RetailerInventory.product_id == product.id
    ).first()

    if db_inv:
        # Update existing
        db_inv.available_stock += inv_data.get("available_stock", 0)
        db_inv.purchase_price = inv_data.get("purchase_price", db_inv.purchase_price)
        db_inv.selling_price = inv_data.get("selling_price", db_inv.selling_price)
        db_inv.reminder_stock = inv_data.get("reminder_stock", db_inv.reminder_stock)
    else:
        db_inv = RetailerInventory(
            retailer_id=retailer_id,
            product_id=product.id,
            available_stock=inv_data.get("available_stock", 0),
            purchase_price=inv_data.get("purchase_price", 0.0),
            selling_price=inv_data.get("selling_price", 0.0),
            reminder_stock=inv_data.get("reminder_stock", 0)
        )
        db.add(db_inv)
        
    db.commit()
    db.refresh(db_inv)
    return db_inv

def get_inventory(db: Session, user_id: int = 1):
    # Return retailer's inventory joined with Product
    return db.query(RetailerInventory).filter(RetailerInventory.retailer_id == user_id).all()

# --- Sales ---
def create_sale_record(db: Session, sale_data: dict, user_id: int = 1):
    db_sale = SaleRecord(**sale_data, user_id=user_id)
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale

def get_sales(db: Session, user_id: int = 1):
    return db.query(SaleRecord).filter(SaleRecord.user_id == user_id).all()

# --- Expenses ---
def create_expense(db: Session, expense_data: dict, user_id: int = 1):
    db_expense = BusinessExpense(**expense_data, user_id=user_id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def get_expenses(db: Session, user_id: int = 1):
    return db.query(BusinessExpense).filter(BusinessExpense.user_id == user_id).all()

# --- Documents (Invoice, Quote, Receipt) ---
def create_invoice_record(db: Session, invoice_data: dict, user_id: int = 1):
    existing = db.query(InvoiceRecord).filter(InvoiceRecord.invoice_number == invoice_data["invoice_number"], InvoiceRecord.user_id == user_id).first()
    if existing:
        return existing
        
    db_record = InvoiceRecord(**invoice_data, user_id=user_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def create_quotation_record(db: Session, quote_data: dict, user_id: int = 1):
    db_record = QuotationRecord(**quote_data, user_id=user_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def create_receipt_record(db: Session, receipt_data: dict, user_id: int = 1):
    db_record = ReceiptRecord(**receipt_data, user_id=user_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

# --- Business Card ---
def upsert_business_card(db: Session, card_data: dict, user_id: int = 1):
    valid_keys = {"name", "job_title", "company_name", "phone", "email", "website", "address"}
    filtered_data = {k: v for k, v in card_data.items() if k in valid_keys}

    card = db.query(BusinessCardProfile).filter(BusinessCardProfile.user_id == user_id).first()
    if card:
        for k, v in filtered_data.items():
            setattr(card, k, v)
    else:
        card = BusinessCardProfile(**filtered_data, user_id=user_id)
        db.add(card)
    db.commit()
    db.refresh(card)
    return card
