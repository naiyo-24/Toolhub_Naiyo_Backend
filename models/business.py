from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class GSTMaster(Base):
    __tablename__ = "gst_master"
    
    id = Column(Integer, primary_key=True, index=True)
    gst_rate = Column(Float, unique=True, index=True)
    cgst = Column(Float)
    sgst = Column(Float)
    igst = Column(Float)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, index=True)
    owner_type = Column(String, index=True) # 'Manufacturer' or 'Retailer'
    visibility = Column(String, index=True) # 'Global' or 'Private'
    product_type = Column(String, default='Finished Good') # 'Finished Good' or 'Raw Material'
    barcode = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    image_url = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    category = Column(String, nullable=True)
    description = Column(String, nullable=True)
    hsn_code = Column(String, nullable=True)
    gst_rate = Column(Float, default=0.0) # Kept for backward compatibility temporarily
    gst_id = Column(Integer, ForeignKey("gst_master.id"), nullable=True)
    mrp = Column(Float, nullable=True)

    gst_details = relationship("GSTMaster")
    inventories = relationship("RetailerInventory", back_populates="product")

class RetailerInventory(Base):
    __tablename__ = "retailer_inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    retailer_id = Column(Integer, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    available_stock = Column(Integer, default=0)
    purchase_price = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    batch_number = Column(String, nullable=True)
    expiry_date = Column(Date, nullable=True)
    reminder_stock = Column(Integer, default=0)

    product = relationship("Product", back_populates="inventories")
    
class SaleRecord(Base):
    __tablename__ = "sales_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1)
    item_name = Column(String)
    sku = Column(String, nullable=True)
    quantity_sold = Column(Integer)
    unit_price = Column(Float)
    total_amount = Column(Float)
    sale_date = Column(Date)

class BusinessExpense(Base):
    __tablename__ = "business_expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1)
    category = Column(String)
    amount = Column(Float)
    description = Column(String, nullable=True)
    expense_date = Column(Date)
    
class InvoiceRecord(Base):
    __tablename__ = "invoice_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1)
    invoice_number = Column(String, unique=True, index=True)
    invoice_date = Column(Date)
    client_name = Column(String)
    is_gst_invoice = Column(Boolean, default=False)
    pdf_url = Column(String, nullable=True)
    total_amount = Column(Float)
    items_json = Column(JSON) # Store items as JSON array to avoid complex relations for now
    
class QuotationRecord(Base):
    __tablename__ = "quotation_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1)
    quotation_number = Column(String, unique=True, index=True)
    valid_until = Column(Date)
    client_name = Column(String)
    total_amount = Column(Float)
    items_json = Column(JSON)
    
class ReceiptRecord(Base):
    __tablename__ = "receipt_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1)
    receipt_number = Column(String, unique=True, index=True)
    receipt_date = Column(Date)
    received_from = Column(String)
    amount = Column(Float)
    payment_mode = Column(String)
    purpose = Column(String)

class BusinessCardProfile(Base):
    __tablename__ = "business_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, default=1)
    name = Column(String)
    job_title = Column(String)
    company_name = Column(String)
    phone = Column(String)
    email = Column(String)
    website = Column(String, nullable=True)
    address = Column(String)
    card_design_type = Column(String, default="modern")
    custom_message = Column(String, nullable=True)

class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1)
    supplier_name = Column(String)
    invoice_number = Column(String, index=True)
    invoice_date = Column(Date)
    total_amount = Column(Float)
    pdf_url = Column(String, nullable=True)

class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchase_invoices.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    unit_price = Column(Float)
    total_price = Column(Float)

class StockMovement(Base):
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    retailer_id = Column(Integer, index=True)
    movement_type = Column(String) # PURCHASE, SALE
    quantity_change = Column(Integer)
    reference_id = Column(String) # Invoice number or receipt number
    date = Column(Date)

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    name = Column(String, index=True)
    phone = Column(String, nullable=True, index=True)
    address = Column(String, nullable=True)
    gstin = Column(String, nullable=True)
    company_name = Column(String, nullable=True)

