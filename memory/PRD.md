# InvoiceFlow - Product Requirements Document

## Overview
InvoiceFlow is a SaaS product for smart invoice automation targeting Managed Service Providers (MSPs). It processes CSV/Excel files from accounting software (QuickBooks, Xero, Harvest, FreshBooks, Wave), generates branded PDF invoices, and handles tax calculations.

## Core Features

### 1. Smart CSV/Excel Processing
- **Status:** ✅ IMPLEMENTED
- Parse 180+ column variations from accounting software using fuzzy matching
- Multi-invoice splitting from single files
- Automatic date and number format detection
- Error recovery with AI-driven repair suggestions (planned)

### 2. Branded PDF Generation
- **Status:** ✅ BASIC IMPLEMENTED
- Generate invoices from uploaded data
- Basic branding support (logo upload)
- Single template currently available

### 3. Automated Tax Calculation
- **Status:** ✅ IMPLEMENTED (Fallback Database)
- US state tax rates database (50 states + DC)
- Intelligent state extraction from addresses
- **Note:** TaxJar API integration is PLANNED but uses fallback database

### 4. Multi-tenancy & Authentication
- **Status:** ✅ IMPLEMENTED
- JWT-based authentication
- Role-based access control
- Organization-based data isolation

### 5. Invoice Management
- **Status:** ✅ IMPLEMENTED
- CRUD operations for invoices
- Status tracking (draft, sent, paid, cancelled)
- PDF download with authentication

## Technical Architecture

### Backend (FastAPI)
- `/app/backend/server.py` - Main API routes
- `/app/backend/auth.py` - JWT authentication
- `/app/backend/csv_parser_v2.py` - CSV parsing (180+ column mappings)
- `/app/backend/pdf_generator.py` - PDF generation
- `/app/backend/tax_service.py` - Tax calculations
- `/app/backend/models.py` - Pydantic models

### Frontend (React)
- `/app/frontend/src/pages/` - Page components
- `/app/frontend/src/contexts/AuthContext.js` - Auth state
- `/app/frontend/src/api/index.js` - API client

### Database (MongoDB)
- Collections: users, organizations, invoices, uploads, branding

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User login |
| `/api/auth/register` | POST | User registration |
| `/api/auth/me` | GET | Get current user |
| `/api/uploads` | POST | Upload CSV/Excel |
| `/api/uploads` | GET | List uploads |
| `/api/invoices` | GET | List invoices |
| `/api/invoices/{id}` | GET/PUT/DELETE | Invoice CRUD |
| `/api/pdf/generate/{id}` | POST | Generate PDF |
| `/api/pdf/download/{filename}` | GET | Download PDF |
| `/api/tax/calculate` | POST | Calculate tax |
| `/api/branding` | GET/PUT | Branding settings |
| `/api/branding/logo` | POST/GET | Logo upload/retrieve |
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/api/health` | GET | Health check |

## Test Credentials
- Email: `demo@invoiceflow.com`
- Password: `demo123`

## What's Implemented (as of Jan 28, 2025)

### Completed
- ✅ User authentication (login/register/JWT)
- ✅ CSV Parser v2 with 180+ column mappings
- ✅ Fuzzy matching for column detection
- ✅ Invoice CRUD operations
- ✅ PDF generation and download
- ✅ Tax calculation with state extraction
- ✅ Branding (logo upload)
- ✅ Dashboard statistics
- ✅ Health check endpoint
- ✅ Data-testid attributes for testing

### Bug Fixes Applied
- ✅ Fixed backend startup (CSVParser → CSVParserV2)
- ✅ Fixed CSV parser return value handling (3-tuple)
- ✅ Fixed tax service state extraction (word boundary matching)

## Backlog (Priority Order)

### P0 - Critical
- [ ] TaxJar API integration (currently using fallback database)

### P1 - High Priority
- [ ] Multiple PDF templates (5 professional designs)
- [ ] PDF pagination for large invoices
- [ ] Batch processing for 100+ invoices
- [ ] Email integration (Resend API)

### P2 - Medium Priority
- [ ] QuickBooks OAuth integration
- [ ] Tax exemption certificate management
- [ ] Audit trail / version history
- [ ] Excel export (QuickBooks format)

### P3 - Future
- [ ] Client portal
- [ ] Payment tracking (Stripe integration)
- [ ] Advanced analytics dashboard

## Mocked/Placeholder Features
- **Tax Calculation:** Uses hardcoded US state tax rates instead of TaxJar API
- **Email:** Not yet implemented
- **QuickBooks Integration:** Not yet implemented
