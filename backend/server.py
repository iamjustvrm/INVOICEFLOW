from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
import shutil

# Import custom modules
from models import (
    User, UserCreate, UserLogin, Organization, Branding,
    Upload, Invoice, TaxRate, TaxExemption, UploadStatus, InvoiceStatus
)
from auth import (
    get_password_hash, verify_password, create_access_token, get_current_user
)
from csv_parser import CSVParser
from pdf_generator import PDFGenerator
from tax_service import TaxService


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'invoiceflow')]

# Create uploads and pdfs directories
UPLOADS_DIR = ROOT_DIR / 'uploads'
PDFS_DIR = ROOT_DIR / 'pdfs'
UPLOADS_DIR.mkdir(exist_ok=True)
PDFS_DIR.mkdir(exist_ok=True)

# Initialize services
csv_parser = CSVParser()
pdf_generator = PDFGenerator()
tax_service = TaxService()

# Create the main app
app = FastAPI(title="InvoiceFlow API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create organization if provided
    organization_id = None
    if user_data.organization_name:
        org = Organization(
            name=user_data.organization_name,
            owner_id=""  # Will update after user creation
        )
        org_dict = org.model_dump()
        org_dict['created_at'] = org_dict['created_at'].isoformat()
        await db.organizations.insert_one(org_dict)
        organization_id = org.id
    
    # Create user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        organization_id=organization_id,
        role="owner" if organization_id else "member"
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    await db.users.insert_one(user_dict)
    
    # Update organization owner
    if organization_id:
        await db.organizations.update_one(
            {"id": organization_id},
            {"$set": {"owner_id": user.id}}
        )
        
        # Create default branding
        branding = Branding(organization_id=organization_id)
        branding_dict = branding.model_dump()
        branding_dict['created_at'] = branding_dict['created_at'].isoformat()
        await db.branding.insert_one(branding_dict)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "organization_id": organization_id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": organization_id
        }
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(credentials.password, user_doc['hashed_password']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user_doc['id'],
            "email": user_doc['email'],
            "organization_id": user_doc.get('organization_id')
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_doc['id'],
            "email": user_doc['email'],
            "full_name": user_doc['full_name'],
            "organization_id": user_doc.get('organization_id')
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user_doc = await db.users.find_one({"id": current_user['user_id']}, {"_id": 0, "hashed_password": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    return user_doc


# ==================== UPLOAD & CSV PROCESSING ROUTES ====================

@api_router.post("/uploads")
async def upload_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get('organization_id'):
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    
    # Save file
    file_path = UPLOADS_DIR / f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create upload record
    upload = Upload(
        organization_id=current_user['organization_id'],
        user_id=current_user['user_id'],
        filename=file.filename,
        file_path=str(file_path),
        file_size=os.path.getsize(file_path),
        status=UploadStatus.PROCESSING
    )
    
    upload_dict = upload.model_dump()
    upload_dict['created_at'] = upload_dict['created_at'].isoformat()
    await db.uploads.insert_one(upload_dict)
    
    # Parse CSV
    try:
        invoices_data, error = csv_parser.parse_csv(str(file_path))
        
        if error:
            # Update upload status
            await db.uploads.update_one(
                {"id": upload.id},
                {"$set": {"status": UploadStatus.FAILED.value, "error_message": error}}
            )
            raise HTTPException(status_code=400, detail=error)
        
        # Save invoices to database
        invoices_saved = 0
        for invoice_data in invoices_data:
            invoice = Invoice(
                organization_id=current_user['organization_id'],
                upload_id=upload.id,
                **invoice_data
            )
            invoice_dict = invoice.model_dump()
            invoice_dict['created_at'] = invoice_dict['created_at'].isoformat()
            invoice_dict['updated_at'] = invoice_dict['updated_at'].isoformat()
            invoice_dict['invoice_date'] = invoice_dict['invoice_date'].isoformat() if invoice_dict.get('invoice_date') else None
            invoice_dict['due_date'] = invoice_dict['due_date'].isoformat() if invoice_dict.get('due_date') else None
            await db.invoices.insert_one(invoice_dict)
            invoices_saved += 1
        
        # Update upload status
        await db.uploads.update_one(
            {"id": upload.id},
            {"$set": {"status": UploadStatus.COMPLETED.value, "invoices_count": invoices_saved}}
        )
        
        return {
            "upload_id": upload.id,
            "filename": file.filename,
            "invoices_count": invoices_saved,
            "status": "completed"
        }
        
    except Exception as e:
        await db.uploads.update_one(
            {"id": upload.id},
            {"$set": {"status": UploadStatus.FAILED.value, "error_message": str(e)}}
        )
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@api_router.get("/uploads")
async def get_uploads(current_user: dict = Depends(get_current_user)):
    if not current_user.get('organization_id'):
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    uploads = await db.uploads.find(
        {"organization_id": current_user['organization_id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return uploads


# ==================== INVOICE ROUTES ====================

@api_router.get("/invoices")
async def get_invoices(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get('organization_id'):
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    query = {"organization_id": current_user['organization_id']}
    if status:
        query["status"] = status
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return invoices

@api_router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "organization_id": current_user['organization_id']},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@api_router.put("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: str,
    invoice_update: dict,
    current_user: dict = Depends(get_current_user)
):
    # Remove fields that shouldn't be updated
    invoice_update.pop('id', None)
    invoice_update.pop('organization_id', None)
    invoice_update.pop('created_at', None)
    
    invoice_update['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.invoices.update_one(
        {"id": invoice_id, "organization_id": current_user['organization_id']},
        {"$set": invoice_update}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {"message": "Invoice updated successfully"}

@api_router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.invoices.delete_one(
        {"id": invoice_id, "organization_id": current_user['organization_id']}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {"message": "Invoice deleted successfully"}


# ==================== PDF GENERATION ROUTES ====================

@api_router.post("/pdf/generate/{invoice_id}")
async def generate_pdf(invoice_id: str, current_user: dict = Depends(get_current_user)):
    # Get invoice
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "organization_id": current_user['organization_id']},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get branding
    branding = await db.branding.find_one(
        {"organization_id": current_user['organization_id']},
        {"_id": 0}
    )
    if not branding:
        branding = {"primary_color": "#3B82F6", "logo_url": None}
    
    # Generate PDF
    pdf_filename = f"invoice_{invoice_id}.pdf"
    pdf_path = PDFS_DIR / pdf_filename
    
    success = pdf_generator.generate_pdf(invoice, branding, str(pdf_path))
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to generate PDF")
    
    # Update invoice with PDF URL
    pdf_url = f"/api/pdf/download/{pdf_filename}"
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"pdf_url": pdf_url, "status": InvoiceStatus.SENT.value}}
    )
    
    return {"pdf_url": pdf_url, "message": "PDF generated successfully"}

@api_router.get("/pdf/download/{filename}")
async def download_pdf(filename: str, current_user: dict = Depends(get_current_user)):
    pdf_path = PDFS_DIR / filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(pdf_path, media_type="application/pdf", filename=filename)


# ==================== TAX ROUTES ====================

@api_router.post("/tax/calculate")
async def calculate_tax(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    amount = data.get('amount', 0)
    state_code = data.get('state_code')
    client_address = data.get('client_address')
    
    tax_info = tax_service.calculate_tax(amount, state_code, client_address)
    return tax_info


# ==================== BRANDING ROUTES ====================

@api_router.get("/branding")
async def get_branding(current_user: dict = Depends(get_current_user)):
    if not current_user.get('organization_id'):
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    branding = await db.branding.find_one(
        {"organization_id": current_user['organization_id']},
        {"_id": 0}
    )
    
    if not branding:
        # Create default branding
        branding = Branding(organization_id=current_user['organization_id'])
        branding_dict = branding.model_dump()
        branding_dict['created_at'] = branding_dict['created_at'].isoformat()
        await db.branding.insert_one(branding_dict)
        return branding_dict
    
    return branding

@api_router.put("/branding")
async def update_branding(
    branding_update: dict,
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get('organization_id'):
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    result = await db.branding.update_one(
        {"organization_id": current_user['organization_id']},
        {"$set": branding_update}
    )
    
    return {"message": "Branding updated successfully"}


# ==================== DASHBOARD STATS ====================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    if not current_user.get('organization_id'):
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    org_id = current_user['organization_id']
    
    # Get counts
    total_invoices = await db.invoices.count_documents({"organization_id": org_id})
    draft_invoices = await db.invoices.count_documents({"organization_id": org_id, "status": "draft"})
    sent_invoices = await db.invoices.count_documents({"organization_id": org_id, "status": "sent"})
    paid_invoices = await db.invoices.count_documents({"organization_id": org_id, "status": "paid"})
    
    # Calculate totals
    invoices = await db.invoices.find({"organization_id": org_id}, {"_id": 0, "total": 1}).to_list(10000)
    total_revenue = sum(inv.get('total', 0) for inv in invoices)
    
    return {
        "total_invoices": total_invoices,
        "draft_invoices": draft_invoices,
        "sent_invoices": sent_invoices,
        "paid_invoices": paid_invoices,
        "total_revenue": total_revenue
    }


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