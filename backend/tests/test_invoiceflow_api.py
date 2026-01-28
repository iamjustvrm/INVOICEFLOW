"""
InvoiceFlow API Tests - Comprehensive Backend Testing
Tests: Auth, Invoices, PDF Generation, Tax Calculation, Branding, Dashboard
"""

import pytest
import requests
import os
import time
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@invoiceflow.com"
TEST_PASSWORD = "demo123"

# For new user registration tests
TEST_NEW_USER_EMAIL = f"TEST_user_{int(time.time())}@invoiceflow.com"
TEST_NEW_USER_PASSWORD = "testpass123"
TEST_NEW_USER_NAME = "Test User"
TEST_ORG_NAME = "Test Organization"


class TestAuthEndpoints:
    """Authentication endpoint tests - Login, Register, Me"""
    
    def test_login_success(self):
        """Test successful login with demo credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Missing access_token in response"
        assert "token_type" in data, "Missing token_type in response"
        assert data["token_type"] == "bearer"
        assert "user" in data, "Missing user in response"
        assert data["user"]["email"] == TEST_EMAIL
        assert "id" in data["user"]
        assert "organization_id" in data["user"]
        print(f"✓ Login successful for {TEST_EMAIL}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        print("✓ Invalid credentials correctly rejected")
    
    def test_login_missing_fields(self):
        """Test login with missing fields"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL}  # Missing password
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✓ Missing fields correctly rejected")
    
    def test_register_new_user(self):
        """Test user registration"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_NEW_USER_EMAIL,
                "password": TEST_NEW_USER_PASSWORD,
                "full_name": TEST_NEW_USER_NAME,
                "organization_name": TEST_ORG_NAME
            }
        )
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_NEW_USER_EMAIL
        assert data["user"]["full_name"] == TEST_NEW_USER_NAME
        assert data["user"]["organization_id"] is not None
        print(f"✓ Registration successful for {TEST_NEW_USER_EMAIL}")
    
    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_EMAIL,  # Already exists
                "password": "somepass",
                "full_name": "Duplicate User",
                "organization_name": "Dup Org"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        assert "already registered" in data["detail"].lower()
        print("✓ Duplicate email correctly rejected")
    
    def test_get_current_user(self):
        """Test GET /api/auth/me endpoint"""
        # First login to get token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Get me failed: {response.text}"
        
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert "id" in data
        assert "full_name" in data
        assert "hashed_password" not in data  # Should be excluded
        print("✓ GET /api/auth/me successful")
    
    def test_get_me_without_token(self):
        """Test GET /api/auth/me without authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthenticated request correctly rejected")


class TestInvoiceEndpoints:
    """Invoice CRUD endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_invoices_list(self):
        """Test GET /api/invoices"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get invoices failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/invoices returned {len(data)} invoices")
        
        # If invoices exist, validate structure
        if len(data) > 0:
            invoice = data[0]
            assert "id" in invoice
            assert "invoice_number" in invoice
            assert "client_name" in invoice
            assert "total" in invoice
            assert "status" in invoice
            print(f"✓ Invoice structure validated: {invoice['invoice_number']}")
    
    def test_get_invoices_by_status(self):
        """Test GET /api/invoices with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            params={"status": "draft"},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        # All returned invoices should have draft status
        for invoice in data:
            assert invoice["status"] == "draft", f"Expected draft, got {invoice['status']}"
        print(f"✓ Status filter working, found {len(data)} draft invoices")
    
    def test_get_single_invoice(self):
        """Test GET /api/invoices/{id}"""
        # First get list to find an invoice ID
        list_response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=self.headers
        )
        invoices = list_response.json()
        
        if len(invoices) == 0:
            pytest.skip("No invoices available for testing")
        
        invoice_id = invoices[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/invoices/{invoice_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get invoice failed: {response.text}"
        
        data = response.json()
        assert data["id"] == invoice_id
        assert "line_items" in data
        assert "subtotal" in data
        assert "total" in data
        print(f"✓ GET /api/invoices/{invoice_id} successful")
    
    def test_get_nonexistent_invoice(self):
        """Test GET /api/invoices/{id} with invalid ID"""
        response = requests.get(
            f"{BASE_URL}/api/invoices/nonexistent-id-12345",
            headers=self.headers
        )
        assert response.status_code == 404
        print("✓ Nonexistent invoice correctly returns 404")
    
    def test_update_invoice(self):
        """Test PUT /api/invoices/{id}"""
        # Get an invoice to update
        list_response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=self.headers
        )
        invoices = list_response.json()
        
        if len(invoices) == 0:
            pytest.skip("No invoices available for testing")
        
        invoice_id = invoices[0]["id"]
        original_notes = invoices[0].get("notes", "")
        
        # Update the invoice
        new_notes = f"TEST_Updated at {datetime.now().isoformat()}"
        response = requests.put(
            f"{BASE_URL}/api/invoices/{invoice_id}",
            json={"notes": new_notes},
            headers=self.headers
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        # Verify update persisted
        get_response = requests.get(
            f"{BASE_URL}/api/invoices/{invoice_id}",
            headers=self.headers
        )
        updated_invoice = get_response.json()
        assert updated_invoice["notes"] == new_notes
        print(f"✓ Invoice {invoice_id} updated successfully")
        
        # Restore original notes
        requests.put(
            f"{BASE_URL}/api/invoices/{invoice_id}",
            json={"notes": original_notes},
            headers=self.headers
        )
    
    def test_invoices_without_auth(self):
        """Test invoices endpoint without authentication"""
        response = requests.get(f"{BASE_URL}/api/invoices")
        assert response.status_code in [401, 403]
        print("✓ Unauthenticated invoice request correctly rejected")


class TestPDFGeneration:
    """PDF generation endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_generate_pdf(self):
        """Test POST /api/pdf/generate/{invoice_id}"""
        # Get an invoice
        list_response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=self.headers
        )
        invoices = list_response.json()
        
        if len(invoices) == 0:
            pytest.skip("No invoices available for PDF generation")
        
        invoice_id = invoices[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/pdf/generate/{invoice_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"PDF generation failed: {response.text}"
        
        data = response.json()
        assert "pdf_url" in data
        assert "message" in data
        assert data["pdf_url"].startswith("/api/pdf/download/")
        print(f"✓ PDF generated: {data['pdf_url']}")
        
        return data["pdf_url"]
    
    def test_download_pdf(self):
        """Test GET /api/pdf/download/{filename}"""
        # First generate a PDF
        list_response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=self.headers
        )
        invoices = list_response.json()
        
        if len(invoices) == 0:
            pytest.skip("No invoices available for PDF download test")
        
        # Find an invoice with PDF or generate one
        invoice_with_pdf = None
        for inv in invoices:
            if inv.get("pdf_url"):
                invoice_with_pdf = inv
                break
        
        if not invoice_with_pdf:
            # Generate PDF first
            invoice_id = invoices[0]["id"]
            gen_response = requests.post(
                f"{BASE_URL}/api/pdf/generate/{invoice_id}",
                headers=self.headers
            )
            pdf_url = gen_response.json()["pdf_url"]
        else:
            pdf_url = invoice_with_pdf["pdf_url"]
        
        # Download the PDF
        response = requests.get(
            f"{BASE_URL}{pdf_url}",
            headers=self.headers
        )
        assert response.status_code == 200, f"PDF download failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 0
        print(f"✓ PDF downloaded successfully ({len(response.content)} bytes)")
    
    def test_generate_pdf_nonexistent_invoice(self):
        """Test PDF generation for nonexistent invoice"""
        response = requests.post(
            f"{BASE_URL}/api/pdf/generate/nonexistent-id-12345",
            headers=self.headers
        )
        assert response.status_code == 404
        print("✓ PDF generation for nonexistent invoice correctly returns 404")


class TestTaxCalculation:
    """Tax calculation endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_calculate_tax_with_state_code(self):
        """Test POST /api/tax/calculate with state code"""
        response = requests.post(
            f"{BASE_URL}/api/tax/calculate",
            json={"amount": 100.00, "state_code": "CA"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Tax calculation failed: {response.text}"
        
        data = response.json()
        assert "tax_rate" in data
        assert "tax_amount" in data
        assert "total" in data
        assert data["tax_rate"] == 7.25  # California rate
        assert data["tax_amount"] == 7.25
        assert data["total"] == 107.25
        print(f"✓ Tax calculated: {data['tax_rate']}% = ${data['tax_amount']}")
    
    def test_calculate_tax_with_address(self):
        """Test tax calculation with client address"""
        response = requests.post(
            f"{BASE_URL}/api/tax/calculate",
            json={
                "amount": 200.00,
                "client_address": "123 Main St, New York, NY 10001"
            },
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "tax_rate" in data
        assert data["state"] == "NY"
        print(f"✓ Tax calculated from address: {data['state']} @ {data['tax_rate']}%")
    
    def test_calculate_tax_no_tax_state(self):
        """Test tax calculation for no-tax state (Oregon)"""
        response = requests.post(
            f"{BASE_URL}/api/tax/calculate",
            json={"amount": 100.00, "state_code": "OR"},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["tax_rate"] == 0.0
        assert data["tax_amount"] == 0.0
        assert data["total"] == 100.00
        print("✓ No-tax state (OR) correctly returns 0% tax")
    
    def test_calculate_tax_unknown_state(self):
        """Test tax calculation with unknown state"""
        response = requests.post(
            f"{BASE_URL}/api/tax/calculate",
            json={"amount": 100.00, "state_code": "XX"},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["tax_rate"] == 0.0  # Default to 0 for unknown
        print("✓ Unknown state correctly defaults to 0% tax")


class TestBrandingEndpoints:
    """Branding endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_branding(self):
        """Test GET /api/branding"""
        response = requests.get(
            f"{BASE_URL}/api/branding",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get branding failed: {response.text}"
        
        data = response.json()
        assert "primary_color" in data
        assert "organization_id" in data
        print(f"✓ Branding retrieved: primary_color={data['primary_color']}")
    
    def test_update_branding(self):
        """Test PUT /api/branding"""
        # Get current branding
        get_response = requests.get(
            f"{BASE_URL}/api/branding",
            headers=self.headers
        )
        original_color = get_response.json().get("primary_color", "#3B82F6")
        
        # Update branding
        new_color = "#FF5733"
        response = requests.put(
            f"{BASE_URL}/api/branding",
            json={"primary_color": new_color},
            headers=self.headers
        )
        assert response.status_code == 200, f"Update branding failed: {response.text}"
        
        # Verify update
        verify_response = requests.get(
            f"{BASE_URL}/api/branding",
            headers=self.headers
        )
        assert verify_response.json()["primary_color"] == new_color
        print(f"✓ Branding updated: primary_color={new_color}")
        
        # Restore original
        requests.put(
            f"{BASE_URL}/api/branding",
            json={"primary_color": original_color},
            headers=self.headers
        )


class TestDashboardStats:
    """Dashboard stats endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_dashboard_stats(self):
        """Test GET /api/dashboard/stats"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get stats failed: {response.text}"
        
        data = response.json()
        assert "total_invoices" in data
        assert "draft_invoices" in data
        assert "sent_invoices" in data
        assert "paid_invoices" in data
        assert "total_revenue" in data
        
        # Validate types
        assert isinstance(data["total_invoices"], int)
        assert isinstance(data["total_revenue"], (int, float))
        
        print(f"✓ Dashboard stats: {data['total_invoices']} invoices, ${data['total_revenue']} revenue")
    
    def test_dashboard_stats_without_auth(self):
        """Test dashboard stats without authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code in [401, 403]
        print("✓ Unauthenticated dashboard request correctly rejected")


class TestUploadEndpoints:
    """Upload endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_uploads(self):
        """Test GET /api/uploads"""
        response = requests.get(
            f"{BASE_URL}/api/uploads",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get uploads failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/uploads returned {len(data)} uploads")
        
        if len(data) > 0:
            upload = data[0]
            assert "id" in upload
            assert "filename" in upload
            assert "status" in upload
    
    def test_upload_csv_file(self):
        """Test POST /api/uploads with CSV file"""
        # Create a simple test CSV
        csv_content = """Invoice Number,Date,Client Name,Description,Quantity,Rate,Amount
TEST-001,2024-01-15,Test Client,Consulting Services,10,150.00,1500.00
TEST-001,2024-01-15,Test Client,Support Hours,5,100.00,500.00"""
        
        files = {
            'file': ('test_invoice.csv', csv_content, 'text/csv')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/uploads",
            files=files,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert "upload_id" in data
        assert "invoices_count" in data
        assert data["status"] == "completed"
        print(f"✓ CSV uploaded: {data['invoices_count']} invoices created")
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        files = {
            'file': ('test.txt', 'invalid content', 'text/plain')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/uploads",
            files=files,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 400
        print("✓ Invalid file type correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
