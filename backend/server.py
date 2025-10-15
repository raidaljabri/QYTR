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
    
    from reportlab.platypus import PageTemplate, Frame, PageBreak, KeepTogether
    from reportlab.platypus.doctemplate import BaseDocTemplate
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    
    # Create PDF that matches the preview layout exactly
    buffer = BytesIO()
    
    class QuoteDocTemplate(BaseDocTemplate):
        def __init__(self, filename, **kwargs):
            super().__init__(filename, **kwargs)
            
            # Define frame with margins similar to preview
            margin = 16 * mm
            frame = Frame(
                margin, margin, 
                A4[0] - 2*margin, A4[1] - 2*margin,
                leftPadding=0, rightPadding=0, 
                topPadding=0, bottomPadding=0,
                showBoundary=0
            )
            
            template = PageTemplate(id='normal', frames=[frame], 
                                  onPage=self.add_page_decoration)
            self.addPageTemplates([template])
        
        def add_page_decoration(self, canvas, doc):
            """Add page decorations and spacing"""
            # Add 10mm spacing between pages
            if doc.page > 1:
                canvas.translate(0, 10*mm)
    
    doc = QuoteDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Styles matching the preview
    title_style = ParagraphStyle(
        'TitleArabic',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=30,
        fontName='Helvetica-Bold',
        textColor=colors.black
    )
    
    company_title_style = ParagraphStyle(
        'CompanyTitle',
        parent=styles['Heading2'],
        alignment=TA_RIGHT,
        fontSize=16,
        spaceAfter=8,
        fontName='Helvetica-Bold',
        textColor=colors.black
    )
    
    normal_style = ParagraphStyle(
        'NormalArabic',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
        fontSize=10,
        spaceAfter=6,
        fontName='Helvetica',
        textColor=colors.black
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        alignment=TA_RIGHT,
        fontSize=14,
        spaceAfter=15,
        fontName='Helvetica-Bold',
        textColor=colors.blue
    )
    
    # === HEADER SECTION - exactly like preview ===
    header_elements = []
    
    # Header with logo and company info (simulate the preview layout)
    header_data = [
        ['', f'شركة {company.name_ar}', ''],
        ['', f'{company.description_ar}', ''],
        ['', f'{company.name_en}', ''],
        ['', '', f'عرض سعر رقم {quote_obj.quote_number}'],
        ['', '', f'التاريخ: {quote_obj.created_date.strftime("%B %d, %Y")}']
    ]
    
    header_table = Table(header_data, colWidths=[40*mm, 120*mm, 40*mm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),     # Logo area
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # Company info center
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),    # Quote info right
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (1, 0), 16),
        ('FONTNAME', (1, 1), (1, 2), 'Helvetica'),
        ('FONTSIZE', (1, 1), (1, 2), 10),
        ('FONTNAME', (2, 2), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 2), (2, -1), 12),
    ]))
    
    header_elements.append(header_table)
    header_elements.append(Spacer(1, 20))
    
    # Company and Customer info side by side - exactly like preview
    info_data = [
        ['Seller / المورد', 'Customer / العميل'],
        [f'الشركة: {company.name_ar}', f'العميل: {quote_obj.customer.name}'],
        [f'الرقم الضريبي: {company.tax_number}', f'الرقم الضريبي: {quote_obj.customer.tax_number or "غير محدد"}'],
        [f'الشارع: {company.street}', f'الشارع: {quote_obj.customer.street or "غير محدد"}'],
        [f'الحي: {company.neighborhood}', f'الحي: {quote_obj.customer.neighborhood or "غير محدد"}'],
        [f'المدينة: {company.city}', f'المدينة: {quote_obj.customer.city or "غير محدد"}'],
        [f'الدولة: {company.country}', f'الدولة: {quote_obj.customer.country or "غير محدد"}'],
        [f'السجل التجاري: {company.commercial_registration}', f'السجل التجاري: {quote_obj.customer.commercial_registration or "غير محدد"}'],
        [f'المبنى: {company.building}', f'المبنى: {quote_obj.customer.building or "غير محدد"}'],
        [f'الرمز البريدي: {company.postal_code}', f'الرمز البريدي: {quote_obj.customer.postal_code or "غير محدد"}'],
        [f'الرقم الإضافي: {company.additional_number}', f'الرقم الإضافي: {quote_obj.customer.additional_number or "غير محدد"}'],
        ['', f'رقم الهاتف: {quote_obj.customer.phone or "غير محدد"}']
    ]
    
    info_table = Table(info_data, colWidths=[95*mm, 95*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    header_elements.append(info_table)
    header_elements.append(Spacer(1, 20))
    
    # Project details
    project_elements = []
    project_elements.append(Paragraph("Project details / تفاصيل المشروع", section_header_style))
    
    project_data = [
        ['وصف المشروع:', quote_obj.project_description],
        ['الموقع:', quote_obj.location]
    ]
    
    project_table = Table(project_data, colWidths=[40*mm, 150*mm])
    project_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    project_elements.append(project_table)
    header_elements.extend(project_elements)
    
    elements.append(KeepTogether(header_elements))
    
    # === ITEMS TABLE - matches preview exactly ===
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Price table / جدول الأسعار", section_header_style))
    
    # Build complete items table (split automatically by ReportLab if needed)
    items_data = [['الرقم التسلسلي', 'الوصف', 'الكمية', 'الوحدة', 'سعر الوحدة', 'السعر الإجمالي']]
    
    for i, item in enumerate(quote_obj.items, 1):
        items_data.append([
            str(i),
            item.description,
            f"{item.quantity:g}",
            item.unit,
            f"{item.unit_price:,.2f}",
            f"{item.total_price:,.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[20*mm, 80*mm, 25*mm, 25*mm, 30*mm, 30*mm])
    items_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        
        # Alignment
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),    # Serial number
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),     # Description
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),   # Numbers
        
        # Borders and spacing
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    # Split table if too long for page
    items_per_page = 15
    if len(quote_obj.items) > items_per_page:
        # Split into chunks
        for i in range(0, len(quote_obj.items), items_per_page):
            chunk_data = [items_data[0]]  # Header
            chunk_items = items_data[1 + i:1 + i + items_per_page]
            chunk_data.extend(chunk_items)
            
            chunk_table = Table(chunk_data, colWidths=[20*mm, 80*mm, 25*mm, 25*mm, 30*mm, 30*mm])
            chunk_table.setStyle(items_table._cellStyles)
            
            elements.append(KeepTogether([chunk_table]))
            
            if i + items_per_page < len(quote_obj.items):
                elements.append(Spacer(1, 10*mm))  # 10mm between table chunks
    else:
        elements.append(items_table)
    
    # === TOTALS SECTION - matches preview ===
    elements.append(Spacer(1, 20))
    
    totals_data = [
        ['المجموع الفرعي:', f'{quote_obj.subtotal:,.2f} ريال'],
        ['ضريبة القيمة المضافة (15%):', f'{quote_obj.tax_amount:,.2f} ريال'],
        ['المبلغ الإجمالي:', f'{quote_obj.total_amount:,.2f} ريال']
    ]
    
    totals_table = Table(totals_data, colWidths=[80*mm, 60*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 11),
        ('FONTSIZE', (0, -1), (-1, -1), 14),  # Total row larger
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.darkgreen),
    ]))
    
    # Right-align the totals table
    totals_container = Table([[totals_table]], colWidths=[190*mm])
    totals_container.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(KeepTogether([totals_container]))
    
    # === SIGNATURE SECTION - matches preview ===
    elements.append(Spacer(1, 40))
    
    signature_data = [
        ['التوقيع والختم', 'تاريخ الموافقة'],
        ['', ''],
        ['', ''],
        ['', '']
    ]
    
    signature_table = Table(signature_data, colWidths=[95*mm, 95*mm], 
                           rowHeights=[15*mm, 25*mm, 25*mm, 15*mm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
    ]))
    
    elements.append(KeepTogether([signature_table]))
    
    # Contact info footer - like preview
    if quote_obj.notes:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("ملاحظات", section_header_style))
        elements.append(Paragraph(quote_obj.notes, normal_style))
    
    # Footer with company contact
    elements.append(Spacer(1, 30))
    footer_text = f"""
    <b>معلومات الاتصال</b><br/>
    البريد الإلكتروني: {company.email}<br/>
    {company.neighborhood}, {company.city}<br/>
    جوال: {company.phone1} | جوال آخر: {company.phone2 or ''} | جوال إضافي: {company.phone3 or ''}
    """
    
    footer_para = Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=normal_style,
        alignment=TA_CENTER,
        fontSize=9,
        textColor=colors.grey
    ))
    
    elements.append(footer_para)
    
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

# Word export route - matches preview layout
@api_router.get("/quotes/{quote_id}/export/word")
async def export_quote_word(quote_id: str):
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote_obj = Quote(**quote)
    company = await get_company_info()
    
    from docx import Document
    from docx.shared import Inches, Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_ALIGN_VERTICAL
    from docx.oxml.ns import nsdecls
    from docx.oxml import parse_xml
    
    # Create Word document with RTL support
    doc = Document()
    
    # Set page layout to A4
    sections = doc.sections
    for section in sections:
        section.page_height = Inches(11.69)
        section.page_width = Inches(8.27)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
    
    # === HEADER SECTION - matches preview ===
    
    # Company header table (logo area, company info, quote info)
    header_table = doc.add_table(rows=3, cols=3)
    header_table.columns[0].width = Inches(1.5)  # Logo area
    header_table.columns[1].width = Inches(4.5)  # Company info
    header_table.columns[2].width = Inches(1.5)  # Quote info
    
    # Company name and info (center column)
    header_table.cell(0, 1).text = f'شركة {company.name_ar}'
    header_table.cell(0, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    header_table.cell(0, 1).paragraphs[0].runs[0].font.size = Pt(16)
    header_table.cell(0, 1).paragraphs[0].runs[0].font.bold = True
    
    header_table.cell(1, 1).text = company.description_ar
    header_table.cell(1, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    header_table.cell(1, 1).paragraphs[0].runs[0].font.size = Pt(10)
    
    header_table.cell(2, 1).text = company.name_en
    header_table.cell(2, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    header_table.cell(2, 1).paragraphs[0].runs[0].font.size = Pt(9)
    
    # Quote number and date (right column)
    header_table.cell(0, 2).text = f'عرض سعر رقم {quote_obj.quote_number}'
    header_table.cell(0, 2).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_table.cell(0, 2).paragraphs[0].runs[0].font.size = Pt(12)
    header_table.cell(0, 2).paragraphs[0].runs[0].font.bold = True
    
    header_table.cell(1, 2).text = f'التاريخ: {quote_obj.created_date.strftime("%B %d, %Y")}'
    header_table.cell(1, 2).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_table.cell(1, 2).paragraphs[0].runs[0].font.size = Pt(10)
    
    # Remove borders from header table
    for row in header_table.rows:
        for cell in row.cells:
            cell._element.get_or_add_tcPr().append(
                parse_xml(r'<w:tcBorders %s><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>' % nsdecls('w'))
            )
    
    doc.add_paragraph()
    
    # === COMPANY AND CUSTOMER INFO TABLE - exactly like preview ===
    
    info_table = doc.add_table(rows=13, cols=2)
    info_table.style = 'Table Grid'
    
    # Header row
    info_table.cell(0, 0).text = 'Seller / المورد'
    info_table.cell(0, 1).text = 'Customer / العميل'
    
    # Style header row
    for i in range(2):
        cell = info_table.cell(0, i)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.size = Pt(11)
        # Add blue background
        shading = parse_xml(r'<w:shd {} w:fill="D6EAF8"/>'.format(nsdecls('w')))
        cell._element.get_or_add_tcPr().append(shading)
    
    # Data rows - matching preview layout exactly
    company_data = [
        (f'الشركة: {company.name_ar}', f'العميل: {quote_obj.customer.name}'),
        (f'الرقم الضريبي: {company.tax_number}', f'الرقم الضريبي: {quote_obj.customer.tax_number or "غير محدد"}'),
        (f'الشارع: {company.street}', f'الشارع: {quote_obj.customer.street or "غير محدد"}'),
        (f'الحي: {company.neighborhood}', f'الحي: {quote_obj.customer.neighborhood or "غير محدد"}'),
        (f'المدينة: {company.city}', f'المدينة: {quote_obj.customer.city or "غير محدد"}'),
        (f'الدولة: {company.country}', f'الدولة: {quote_obj.customer.country or "غير محدد"}'),
        (f'السجل التجاري: {company.commercial_registration}', f'السجل التجاري: {quote_obj.customer.commercial_registration or "غير محدد"}'),
        (f'المبنى: {company.building}', f'المبنى: {quote_obj.customer.building or "غير محدد"}'),
        (f'الرمز البريدي: {company.postal_code}', f'الرمز البريدي: {quote_obj.customer.postal_code or "غير محدد"}'),
        (f'الرقم الإضافي: {company.additional_number}', f'الرقم الإضافي: {quote_obj.customer.additional_number or "غير محدد"}'),
        ('', f'رقم الهاتف: {quote_obj.customer.phone or "غير محدد"}'),
        ('', '')
    ]
    
    for i, (company_text, customer_text) in enumerate(company_data, 1):
        info_table.cell(i, 0).text = company_text
        info_table.cell(i, 1).text = customer_text
        
        # Right-align text
        info_table.cell(i, 0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        info_table.cell(i, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # Font size
        info_table.cell(i, 0).paragraphs[0].runs[0].font.size = Pt(9)
        info_table.cell(i, 1).paragraphs[0].runs[0].font.size = Pt(9)
    
    doc.add_paragraph()
    
    # === PROJECT DETAILS ===
    project_heading = doc.add_heading('Project details / تفاصيل المشروع', level=2)
    project_heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    project_heading.runs[0].font.color.rgb = RGBColor(0, 100, 200)  # Blue color
    
    # Project info table
    project_table = doc.add_table(rows=2, cols=2)
    project_table.columns[0].width = Inches(1.5)
    project_table.columns[1].width = Inches(5)
    
    project_table.cell(0, 0).text = 'وصف المشروع:'
    project_table.cell(0, 1).text = quote_obj.project_description
    project_table.cell(1, 0).text = 'الموقع:'
    project_table.cell(1, 1).text = quote_obj.location
    
    # Style project table
    for row in project_table.rows:
        row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        row.cells[0].paragraphs[0].runs[0].font.size = Pt(10)
        row.cells[1].paragraphs[0].runs[0].font.size = Pt(10)
    
    # Remove borders from project table
    for row in project_table.rows:
        for cell in row.cells:
            cell._element.get_or_add_tcPr().append(
                parse_xml(r'<w:tcBorders %s><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>' % nsdecls('w'))
            )
    
    doc.add_paragraph()
    
    # === ITEMS TABLE - exactly like preview ===
    items_heading = doc.add_heading('Price table / جدول الأسعار', level=2)
    items_heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    items_heading.runs[0].font.color.rgb = RGBColor(0, 100, 200)  # Blue color
    
    # Calculate if we need page breaks (approximately 20 items per page)
    items_per_page = 20
    total_items = len(quote_obj.items)
    
    if total_items > items_per_page:
        # Split into chunks for page breaks
        for chunk_start in range(0, total_items, items_per_page):
            chunk_end = min(chunk_start + items_per_page, total_items)
            
            # Create table for this chunk
            items_table = doc.add_table(rows=1, cols=6)
            items_table.style = 'Table Grid'
            
            # Header row
            headers = items_table.rows[0].cells
            headers[0].text = 'الرقم التسلسلي'
            headers[1].text = 'الوصف'
            headers[2].text = 'الكمية'
            headers[3].text = 'الوحدة'
            headers[4].text = 'سعر الوحدة'
            headers[5].text = 'السعر الإجمالي'
            
            # Style header
            for cell in headers:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                cell.paragraphs[0].runs[0].font.bold = True
                cell.paragraphs[0].runs[0].font.size = Pt(10)
                # Gray background for header
                shading = parse_xml(r'<w:shd {} w:fill="808080"/>'.format(nsdecls('w')))
                cell._element.get_or_add_tcPr().append(shading)
                cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)  # White text
            
            # Add items for this chunk
            for i in range(chunk_start, chunk_end):
                item = quote_obj.items[i]
                row_cells = items_table.add_row().cells
                row_cells[0].text = str(i + 1)
                row_cells[1].text = item.description
                row_cells[2].text = f"{item.quantity:g}"
                row_cells[3].text = item.unit
                row_cells[4].text = f"{item.unit_price:,.2f}"
                row_cells[5].text = f"{item.total_price:,.2f}"
                
                # Style data cells
                row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
                for j in range(2, 6):
                    row_cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # Font size for data
                for cell in row_cells:
                    cell.paragraphs[0].runs[0].font.size = Pt(9)
            
            # Add page break if not the last chunk
            if chunk_end < total_items:
                doc.add_page_break()
    else:
        # Single table for all items
        items_table = doc.add_table(rows=1, cols=6)
        items_table.style = 'Table Grid'
        
        # Header row
        headers = items_table.rows[0].cells
        headers[0].text = 'الرقم التسلسلي'
        headers[1].text = 'الوصف'
        headers[2].text = 'الكمية'
        headers[3].text = 'الوحدة'
        headers[4].text = 'سعر الوحدة'
        headers[5].text = 'السعر الإجمالي'
        
        # Style header
        for cell in headers:
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cell.paragraphs[0].runs[0].font.bold = True
            cell.paragraphs[0].runs[0].font.size = Pt(10)
            shading = parse_xml(r'<w:shd {} w:fill="808080"/>'.format(nsdecls('w')))
            cell._element.get_or_add_tcPr().append(shading)
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        
        # Add all items
        for i, item in enumerate(quote_obj.items, 1):
            row_cells = items_table.add_row().cells
            row_cells[0].text = str(i)
            row_cells[1].text = item.description
            row_cells[2].text = f"{item.quantity:g}"
            row_cells[3].text = item.unit
            row_cells[4].text = f"{item.unit_price:,.2f}"
            row_cells[5].text = f"{item.total_price:,.2f}"
            
            # Style data cells
            row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
            for j in range(2, 6):
                row_cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            for cell in row_cells:
                cell.paragraphs[0].runs[0].font.size = Pt(9)
    
    doc.add_paragraph()
    
    # === TOTALS SECTION - matches preview ===
    
    totals_table = doc.add_table(rows=3, cols=2)
    totals_table.style = 'Table Grid'
    totals_table.columns[0].width = Inches(3)
    totals_table.columns[1].width = Inches(2.5)
    
    totals_data = [
        ('المجموع الفرعي:', f'{quote_obj.subtotal:,.2f} ريال'),
        ('ضريبة القيمة المضافة (15%):', f'{quote_obj.tax_amount:,.2f} ريال'),
        ('المبلغ الإجمالي:', f'{quote_obj.total_amount:,.2f} ريال')
    ]
    
    for i, (desc, amount) in enumerate(totals_data):
        totals_table.cell(i, 0).text = desc
        totals_table.cell(i, 1).text = amount
        
        # Right align
        totals_table.cell(i, 0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        totals_table.cell(i, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # Font styling
        totals_table.cell(i, 0).paragraphs[0].runs[0].font.bold = True
        totals_table.cell(i, 1).paragraphs[0].runs[0].font.bold = True
        totals_table.cell(i, 0).paragraphs[0].runs[0].font.size = Pt(11)
        totals_table.cell(i, 1).paragraphs[0].runs[0].font.size = Pt(11)
        
        # Highlight total row
        if i == 2:  # Total row
            totals_table.cell(i, 0).paragraphs[0].runs[0].font.size = Pt(13)
            totals_table.cell(i, 1).paragraphs[0].runs[0].font.size = Pt(13)
            # Gray background for total
            for j in range(2):
                shading = parse_xml(r'<w:shd {} w:fill="E8E8E8"/>'.format(nsdecls('w')))
                totals_table.cell(i, j)._element.get_or_add_tcPr().append(shading)
    
    # Right-align totals table
    totals_table.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    doc.add_paragraph()
    
    # === SIGNATURE SECTION - matches preview ===
    
    signature_heading = doc.add_heading('التوقيع والختم', level=2)
    signature_heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    signature_table = doc.add_table(rows=4, cols=2)
    signature_table.style = 'Table Grid'
    
    # Header row
    signature_table.cell(0, 0).text = 'التوقيع والختم'
    signature_table.cell(0, 1).text = 'تاريخ الموافقة'
    
    # Style header
    for i in range(2):
        cell = signature_table.cell(0, i)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.size = Pt(12)
        shading = parse_xml(r'<w:shd {} w:fill="E8E8E8"/>'.format(nsdecls('w')))
        cell._element.get_or_add_tcPr().append(shading)
    
    # Empty rows for signatures
    for i in range(1, 4):
        for j in range(2):
            signature_table.cell(i, j).text = ""
    
    # Notes section if exists
    if quote_obj.notes:
        doc.add_paragraph()
        notes_heading = doc.add_heading('ملاحظات', level=2)
        notes_heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        notes_para = doc.add_paragraph(quote_obj.notes)
        notes_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    # Contact footer
    doc.add_paragraph()
    footer_heading = doc.add_heading('معلومات الاتصال', level=3)
    footer_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    contact_text = f"""البريد الإلكتروني: {company.email}
{company.neighborhood}, {company.city}
جوال: {company.phone1} | جوال آخر: {company.phone2 or ''} | جوال إضافي: {company.phone3 or ''}"""
    
    contact_para = doc.add_paragraph(contact_text)
    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_para.runs[0].font.size = Pt(9)
    
    # Save document
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="quote_{quote_obj.quote_number}.docx"'
    }
    
    return StreamingResponse(
        BytesIO(buffer.read()),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
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