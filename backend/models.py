from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from enum import Enum

# Enums
class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

class UploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    CANCELLED = "cancelled"

# Base Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    hashed_password: str
    full_name: str
    organization_id: Optional[str] = None
    role: UserRole = UserRole.MEMBER
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Organization(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    owner_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    settings: Dict[str, Any] = Field(default_factory=dict)

class Branding(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    logo_url: Optional[str] = None
    primary_color: str = "#3B82F6"
    secondary_color: str = "#1E40AF"
    font_family: str = "Inter"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Upload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    user_id: str
    filename: str
    file_path: str
    file_size: int
    status: UploadStatus = UploadStatus.PENDING
    invoices_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = 1.0
    rate: float
    amount: float

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    upload_id: str
    invoice_number: str
    invoice_date: datetime
    due_date: Optional[datetime] = None
    
    # Client info
    client_name: str
    client_address: Optional[str] = None
    client_email: Optional[str] = None
    
    # Line items
    line_items: List[InvoiceLineItem] = Field(default_factory=list)
    
    # Amounts
    subtotal: float
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total: float
    
    # Status
    status: InvoiceStatus = InvoiceStatus.DRAFT
    pdf_url: Optional[str] = None
    
    # Metadata
    notes: Optional[str] = None
    template_id: str = "modern"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaxRate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: str
    state_code: str
    zip_code: Optional[str] = None
    city: Optional[str] = None
    tax_rate: float
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaxExemption(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    client_name: str
    certificate_number: str
    state: str
    certificate_url: Optional[str] = None
    expiry_date: Optional[datetime] = None
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
