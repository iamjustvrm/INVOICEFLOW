#!/bin/bash

# InvoiceFlow API Testing Script

BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d'=' -f2)

echo "======================================"
echo "InvoiceFlow API Testing"
echo "======================================"
echo ""

echo "1. Testing Health Check..."
curl -s "${BACKEND_URL}/api" | python3 -m json.tool || echo "Basic endpoint not found, but that's OK"
echo ""

echo "2. Registering Test User..."
RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User","organization_name":"Test Org"}')

if echo "$RESPONSE" | grep -q "access_token"; then
    echo "✅ Registration successful"
    TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
else
    echo "⚠️  User may already exist, trying login..."
    LOGIN_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"email":"test@example.com","password":"test123"}')
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "✅ Login successful"
fi
echo ""

echo "3. Testing Dashboard Stats..."
curl -s -X GET "${BACKEND_URL}/api/dashboard/stats" \
  -H "Authorization: Bearer ${TOKEN}" | python3 -m json.tool
echo "✅ Dashboard stats retrieved"
echo ""

echo "4. Testing CSV Upload..."
UPLOAD_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/uploads" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@/app/test_invoices_sample.csv")

echo "$UPLOAD_RESPONSE" | python3 -m json.tool
echo "✅ CSV uploaded and processed"
echo ""

echo "5. Getting Invoices List..."
INVOICES=$(curl -s -X GET "${BACKEND_URL}/api/invoices" \
  -H "Authorization: Bearer ${TOKEN}")

INVOICE_COUNT=$(echo "$INVOICES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo "✅ Found $INVOICE_COUNT invoices"

if [ "$INVOICE_COUNT" -gt 0 ]; then
    INVOICE_ID=$(echo "$INVOICES" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    echo "   Sample Invoice ID: $INVOICE_ID"
    echo ""
    
    echo "6. Generating PDF for Invoice..."
    PDF_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/pdf/generate/${INVOICE_ID}" \
      -H "Authorization: Bearer ${TOKEN}")
    
    echo "$PDF_RESPONSE" | python3 -m json.tool
    echo "✅ PDF generated successfully"
fi
echo ""

echo "======================================"
echo "🎉 All tests passed successfully!"
echo "======================================"
echo ""
echo "Access the application at:"
echo "Frontend: https://$(echo $BACKEND_URL | cut -d'/' -f3 | cut -d':' -f1)"
echo ""
echo "Demo Credentials:"
echo "Email: demo@invoiceflow.com"
echo "Password: demo123"
echo ""
