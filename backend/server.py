from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import shutil
from openpyxl import Workbook
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Upload directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Models
class CompanyInfo(BaseModel):
    name_ar: str = "شركة مثلث الأنظمة المميزة للمقاولات"
    name_en: str = "MUTHALLATH AL-ANZIMAH AL-MUMAYYIZAH CONTRACTING CO."
    description_ar: str = "تصميم وتصنيع وتوريد وتركيب مظلات الشد الإنشائي والخيام والسواتر"
    description_en: str = "Design, Manufacture, Supply & Installation of Structure Tension Awnings, Tents & Canopies"
    tax_number: str = "311104439400003"
    street: str = "شارع حائل"
    neighborhood: str = "حي البغدادية الغربية"
    country: str = "السعودية"
    city: str = "جدة"
    commercial_registration: str = "4030255240"
    building: str = "8376"
    postal_code: str = "22231"
    additional_number: str = "3842"
    email: str = "info@tsscoksa.com"
    phone1: str = "+966 50 061 2006"
    phone2: str = "055 538 9792"
    phone3: str = "+966 50 336 5527"
    logo_path: Optional[str] = None

class CustomerInfo(BaseModel):
    name: str
    tax_number: Optional[str] = None
    street: Optional[str] = None
    neighborhood: Optional[str] = None
    country: Optional[str] = "السعودية"
    city: Optional[str] = None
    commercial_registration: Optional[str] = None
    building: Optional[str] = None
    postal_code: Optional[str] = None
    additional_number: Optional[str] = None
    phone: Optional[str] = None

class QuoteItem(BaseModel):
    description: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float

class QuoteCreate(BaseModel):
    customer: CustomerInfo
    project_description: str
    location: str
    items: List[QuoteItem]
    subtotal: float
    tax_amount: float
    total_amount: float
    notes: Optional[str] = None

class Quote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quote_number: str
    customer: CustomerInfo
    project_description: str
    location: str
    items: List[QuoteItem]
    subtotal: float
    tax_amount: float
    total_amount: float
    notes: Optional[str] = None
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QuoteUpdate(BaseModel):
    customer: Optional[CustomerInfo] = None
    project_description: Optional[str] = None
    location: Optional[str] = None
    items: Optional[List[QuoteItem]] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    notes: Optional[str] = None

# Utility functions
async def get_next_quote_number():
    """Generate next sequential quote number"""
    last_quote = await db.quotes.find_one(sort=[("created_date", -1)])
    if last_quote:
        try:
            last_number = int(last_quote.get("quote_number", "0"))
            return str(last_number + 1)
        except:
            count = await db.quotes.count_documents({})
            return str(count + 1)
    return "1"

# Routes
@api_router.get("/")
async def root():
    return {"message": "Quote Management System API"}

# Company routes
@api_router.get("/company", response_model=CompanyInfo)
async def get_company_info():
    company = await db.company.find_one({})
    if not company:
        # Create default company info
        default_company = CompanyInfo()
        await db.company.insert_one(default_company.dict())
        return default_company
    return CompanyInfo(**company)

@api_router.put("/company", response_model=CompanyInfo)
async def update_company_info(company: CompanyInfo):
    company_dict = company.dict()
    company_dict["updated_date"] = datetime.now(timezone.utc).isoformat()
    
    await db.company.delete_many({})  # Remove old company info
    await db.company.insert_one(company_dict)
    return company

@api_router.post("/company/logo")
async def upload_logo(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"logo_{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update company info with logo path
    await db.company.update_one(
        {},
        {"$set": {"logo_path": f"/api/uploads/{filename}"}},
        upsert=True
    )
    
    return {"logo_path": f"/api/uploads/{filename}"}

@api_router.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

# Quote routes
@api_router.post("/quotes", response_model=Quote)
async def create_quote(quote_data: QuoteCreate):
    quote_number = await get_next_quote_number()
    quote_dict = quote_data.dict()
    quote_dict["id"] = str(uuid.uuid4())
    quote_dict["quote_number"] = quote_number
    quote_dict["created_date"] = datetime.now(timezone.utc).isoformat()
    quote_dict["updated_date"] = datetime.now(timezone.utc).isoformat()
    
    quote_obj = Quote(**quote_dict)
    await db.quotes.insert_one(quote_obj.dict())
    return quote_obj

@api_router.get("/quotes", response_model=List[Quote])
async def get_quotes(skip: int = 0, limit: int = 100):
    quotes = await db.quotes.find().sort("created_date", -1).skip(skip).limit(limit).to_list(limit)
    return [Quote(**quote) for quote in quotes]

@api_router.get("/quotes/{quote_id}", response_model=Quote)
async def get_quote(quote_id: str):
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return Quote(**quote)

@api_router.put("/quotes/{quote_id}", response_model=Quote)
async def update_quote(quote_id: str, quote_update: QuoteUpdate):
    existing_quote = await db.quotes.find_one({"id": quote_id})
    if not existing_quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    update_data = {k: v for k, v in quote_update.dict().items() if v is not None}
    update_data["updated_date"] = datetime.now(timezone.utc).isoformat()
    
    await db.quotes.update_one({"id": quote_id}, {"$set": update_data})
    
    updated_quote = await db.quotes.find_one({"id": quote_id})
    return Quote(**updated_quote)

@api_router.delete("/quotes/{quote_id}")
async def delete_quote(quote_id: str):
    result = await db.quotes.delete_one({"id": quote_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {"message": "Quote deleted successfully"}

# Export routes
@api_router.get("/quotes/{quote_id}/export/excel")
async def export_quote_excel(quote_id: str):
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote_obj = Quote(**quote)
    company = await get_company_info()
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = f"Quote_{quote_obj.quote_number}"
    
    # Headers
    ws.append([f"Quote #{quote_obj.quote_number}"])
    ws.append([f"Company: {company.name_ar}"])
    ws.append([f"Customer: {quote_obj.customer.name}"])
    ws.append([f"Project: {quote_obj.project_description}"])
    ws.append([f"Location: {quote_obj.location}"])
    ws.append([])
    
    # Items table
    ws.append(["#", "Description", "Quantity", "Unit", "Unit Price", "Total"])
    for i, item in enumerate(quote_obj.items, 1):
        ws.append([i, item.description, item.quantity, item.unit, item.unit_price, item.total_price])
    
    ws.append([])
    ws.append(["", "", "", "", "Subtotal:", quote_obj.subtotal])
    ws.append(["", "", "", "", "Tax (15%):", quote_obj.tax_amount])
    ws.append(["", "", "", "", "Total:", quote_obj.total_amount])
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="quote_{quote_obj.quote_number}.xlsx"'
    }
    
    return StreamingResponse(
        BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )

@api_router.get("/quotes/{quote_id}/export/pdf")
async def export_quote_pdf(quote_id: str):
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote_obj = Quote(**quote)
    company = await get_company_info()
    
    # Create PDF with better formatting
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    arabic_style = ParagraphStyle(
        'Arabic',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
        fontSize=10,
        spaceAfter=12,
    )
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=30,
    )
    
    # Header with company info
    if company.logo_path:
        # Note: Logo would need special handling for embedded images
        pass
    
    # Title
    elements.append(Paragraph(f"عرض سعر رقم {quote_obj.quote_number}", title_style))
    elements.append(Spacer(1, 20))
    
    # Company and Customer info in table
    company_customer_data = [
        ['معلومات العميل', 'معلومات الشركة'],
        [f'العميل: {quote_obj.customer.name}', f'الشركة: {company.name_ar}'],
        [f'الهاتف: {quote_obj.customer.phone or "غير محدد"}', f'الرقم الضريبي: {company.tax_number}'],
        [f'المدينة: {quote_obj.customer.city or "غير محدد"}', f'المدينة: {company.city}'],
        ['', f'البريد: {company.email}'],
    ]
    
    company_customer_table = Table(company_customer_data, colWidths=[250, 250])
    company_customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(company_customer_table)
    elements.append(Spacer(1, 20))
    
    # Project info
    elements.append(Paragraph(f"وصف المشروع: {quote_obj.project_description}", arabic_style))
    elements.append(Paragraph(f"الموقع: {quote_obj.location}", arabic_style))
    elements.append(Spacer(1, 20))
    
    # Items table
    items_data = [['السعر الإجمالي', 'سعر الوحدة', 'الوحدة', 'الكمية', 'الوصف', 'م']]
    
    for i, item in enumerate(quote_obj.items, 1):
        items_data.append([
            f"{item.total_price:,.2f}",
            f"{item.unit_price:,.2f}",
            item.unit,
            str(item.quantity),
            item.description,
            str(i)
        ])
    
    items_table = Table(items_data, colWidths=[80, 80, 60, 60, 200, 30])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    # Totals table
    totals_data = [
        ['المبلغ', 'البيان'],
        [f"{quote_obj.subtotal:,.2f} ريال", 'المجموع الفرعي'],
        [f"{quote_obj.tax_amount:,.2f} ريال", 'ضريبة القيمة المضافة (15%)'],
        [f"{quote_obj.total_amount:,.2f} ريال", 'المبلغ الإجمالي'],
    ]
    
    totals_table = Table(totals_data, colWidths=[150, 200])
    totals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(totals_table)
    elements.append(Spacer(1, 40))
    
    # Signature section
    signature_data = [
        ['التاريخ: ________________', 'التوقيع والختم'],
    ]
    
    signature_table = Table(signature_data, colWidths=[200, 200])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 50),
    ]))
    
    elements.append(signature_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="quote_{quote_obj.quote_number}.pdf"'
    }
    
    return StreamingResponse(
        BytesIO(buffer.read()),
        media_type="application/pdf",
        headers=headers
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()