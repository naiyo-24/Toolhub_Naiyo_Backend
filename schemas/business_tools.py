from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# 1. Invoice Generator & GST Billing
class InvoiceItem(BaseModel):
    description: str
    sku: Optional[str] = None
    quantity: int
    unit: str = Field("Piece", description="Pricing Unit (e.g., Piece, Kg, Box)")
    unit_price: float
    gst_rate: Optional[float] = Field(0.0, description="GST Rate (e.g., 18)")
    hsn_code: Optional[str] = None
    discount_type: Optional[str] = Field(None, description="'PERCENTAGE' or 'AMOUNT'")
    discount_value: Optional[float] = Field(0.0)

class InvoiceRequest(BaseModel):
    company_name: str
    company_address: str
    company_gstin: Optional[str] = None
    company_phone: Optional[str] = None
    company_whatsapp: Optional[str] = None
    company_logo_url: Optional[str] = None
    client_name: str
    client_company_name: Optional[str] = None
    client_address: str
    client_gstin: Optional[str] = None
    client_phone: Optional[str] = None
    client_whatsapp: Optional[str] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_branch: Optional[str] = None
    invoice_number: str
    invoice_date: date = Field(default_factory=date.today)
    items: List[InvoiceItem]
    is_gst_invoice: bool = Field(False, description="True for strict GST tax invoice")
    notes: Optional[str] = None
    pricing_mode: str = Field("EXCLUSIVE")
    invoice_discount_type: Optional[str] = Field(None, description="'PERCENTAGE' or 'AMOUNT'")
    invoice_discount_value: Optional[float] = Field(0.0)

class POSCheckoutRequest(BaseModel):
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_gstin: Optional[str] = None
    receipt_number: str
    receipt_date: date = Field(default_factory=date.today)
    items: List[InvoiceItem]
    payment_mode: str = Field(default="Cash")
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    receipt_size: str = Field(default="Thermal", description="Thermal or A4")
    pricing_mode: str = Field("EXCLUSIVE")
    invoice_discount_type: Optional[str] = Field(None, description="'PERCENTAGE' or 'AMOUNT'")
    invoice_discount_value: Optional[float] = Field(0.0)

# 2. Quotation Gen
class QuotationRequest(BaseModel):
    company_name: str
    company_address: str
    client_name: str
    client_address: str
    quotation_number: str
    valid_until: date
    items: List[InvoiceItem]
    terms_and_conditions: Optional[str] = None

# 3. Receipt Gen
class ReceiptRequest(BaseModel):
    company_name: str
    company_address: str
    receipt_number: str
    receipt_date: date = Field(default_factory=date.today)
    received_from: str
    amount: float
    payment_mode: str = Field(..., description="e.g., Cash, Card, UPI, Bank Transfer")
    transaction_id: Optional[str] = None
    purpose: str

# 4. Business Card
class BusinessCardRequest(BaseModel):
    name: str
    job_title: str
    company_name: str
    phone: str
    email: str
    website: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None

# 5. Master Product Catalog & Retailer Inventory
class GSTMasterResponse(BaseModel):
    id: int
    gst_rate: float
    cgst: float
    sgst: float
    igst: float

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    product_type: Optional[str] = 'Finished Good'
    hsn_code: Optional[str] = None
    gst_rate: float = Field(0.0)
    gst_id: Optional[int] = None
    mrp: Optional[float] = None
    description: Optional[str] = None
    barcode: Optional[str] = None
    initial_stock: Optional[int] = 0
    reminder_stock: Optional[int] = 0

class ProductResponse(BaseModel):
    id: int
    creator_id: int
    owner_type: str
    visibility: str
    product_type: str
    barcode: str
    name: str
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    hsn_code: Optional[str] = None
    gst_rate: float
    gst_id: Optional[int] = None
    gst_details: Optional[GSTMasterResponse] = None
    mrp: Optional[float] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class InventoryAdd(BaseModel):
    barcode: str
    purchase_price: float = Field(0.0)
    selling_price: float = Field(0.0)
    available_stock: int = Field(0)
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    initial_stock: Optional[int] = 0
    reminder_stock: Optional[int] = 0

class InventoryResponse(BaseModel):
    id: int
    retailer_id: int
    product_id: int
    available_stock: int
    purchase_price: float
    selling_price: float
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

# 6. Sales Tracker
class SaleRecord(BaseModel):
    item_name: str
    sku: Optional[str] = None
    quantity_sold: int
    unit_price: float
    sale_date: date = Field(default_factory=date.today)

class SalesTrackerRequest(BaseModel):
    sales: List[SaleRecord]

# 7. Expense Manager
class BusinessExpense(BaseModel):
    category: str = Field(..., description="e.g., COGS, Utilities, Payroll, Marketing, Rent")
    amount: float
    description: Optional[str] = None

class ExpenseManagerRequest(BaseModel):
    expenses: List[BusinessExpense]

# 8. Profit Calculator
class ProfitCalculatorRequest(BaseModel):
    total_revenue: float
    cost_of_goods_sold: float = Field(..., description="Direct costs of producing the goods/services")
    operating_expenses: float = Field(..., description="Indirect costs like rent, utilities, payroll")
    taxes_paid: Optional[float] = 0.0

# 9. Business Analytics
class AnalyticsRequest(BaseModel):
    revenue_this_month: float
    revenue_last_month: float
    expenses_this_month: float
    expenses_last_month: float
    total_customers: int

class PurchaseInvoiceRequest(BaseModel):
    supplier_name: str
    invoice_number: Optional[str] = None
    invoice_date: date
    total_amount: float
    items: List[InvoiceItem]
    pdf_url: Optional[str] = None

class StockMovementResponse(BaseModel):
    id: int
    product_id: int
    retailer_id: int
    movement_type: str
    quantity_change: int
    reference_id: str
    date: date
    
    class Config:
        from_attributes = True
