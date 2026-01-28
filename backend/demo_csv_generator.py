"""
Demo CSV Generator for InvoiceFlow
Generates sample CSV files in various accounting software formats
to test the 180+ column mapping feature
"""

import csv
import random
from datetime import datetime, timedelta
from io import StringIO
from typing import List, Dict, Tuple

# Sample data pools
COMPANY_NAMES = [
    "Acme Corp", "TechStart Inc", "Global Systems LLC", "Digital Solutions",
    "CloudNine Services", "DataDrive Co", "InnovateTech", "SmartBiz Solutions",
    "CyberShield Security", "NetWorks Pro", "CodeCraft Studios", "ByteSize IT",
    "Quantum Computing Ltd", "FutureTech Inc", "Alpha Systems", "Beta Software",
    "Gamma Industries", "Delta Consulting", "Epsilon Enterprises", "Zeta Holdings"
]

FIRST_NAMES = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", "James", "Jennifer"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

SERVICES = [
    ("Network Setup", 150.00, 500.00),
    ("Server Maintenance", 100.00, 300.00),
    ("Cloud Migration", 200.00, 1000.00),
    ("Security Audit", 250.00, 750.00),
    ("Software Installation", 75.00, 200.00),
    ("Data Backup Service", 50.00, 150.00),
    ("Help Desk Support", 45.00, 120.00),
    ("Hardware Repair", 80.00, 350.00),
    ("VoIP Setup", 125.00, 400.00),
    ("Firewall Configuration", 175.00, 450.00),
    ("Email Migration", 100.00, 300.00),
    ("Antivirus Setup", 50.00, 100.00),
    ("Wireless Network Setup", 150.00, 400.00),
    ("Database Administration", 200.00, 600.00),
    ("Custom Development", 150.00, 500.00)
]

ADDRESSES = [
    ("123 Main St", "New York", "NY", "10001"),
    ("456 Oak Ave", "Los Angeles", "CA", "90001"),
    ("789 Elm St", "Chicago", "IL", "60601"),
    ("321 Pine Rd", "Houston", "TX", "77001"),
    ("654 Maple Dr", "Phoenix", "AZ", "85001"),
    ("987 Cedar Ln", "Philadelphia", "PA", "19101"),
    ("147 Birch Blvd", "San Antonio", "TX", "78201"),
    ("258 Willow Way", "San Diego", "CA", "92101"),
    ("369 Spruce St", "Dallas", "TX", "75201"),
    ("741 Ash Ave", "San Jose", "CA", "95101"),
    ("852 Cherry Ct", "Austin", "TX", "78701"),
    ("963 Walnut Pl", "Jacksonville", "FL", "32201"),
    ("159 Hickory Rd", "Fort Worth", "TX", "76101"),
    ("267 Poplar Dr", "Columbus", "OH", "43201"),
    ("378 Sycamore St", "Charlotte", "NC", "28201")
]

# CSV Format Templates
CSV_FORMATS = {
    "quickbooks_online": {
        "name": "QuickBooks Online",
        "columns": {
            "invoice_number": "Invoice #",
            "invoice_date": "Date",
            "due_date": "Due Date",
            "client_name": "Customer",
            "client_email": "Customer Email",
            "client_address": "Billing Address",
            "description": "Product/Service",
            "quantity": "Qty",
            "rate": "Rate",
            "amount": "Amount",
            "tax_rate": "Tax Rate",
            "tax_amount": "Tax",
            "total": "Total",
            "notes": "Message"
        },
        "date_format": "%m/%d/%Y"
    },
    "quickbooks_desktop": {
        "name": "QuickBooks Desktop",
        "columns": {
            "invoice_number": "Ref Number",
            "invoice_date": "Trans Date",
            "due_date": "Terms Date",
            "client_name": "Customer:Company",
            "client_email": "Customer:Email",
            "client_address": "Bill Addr Line 1",
            "description": "Item Description",
            "quantity": "Quantity",
            "rate": "Sales Price",
            "amount": "Line Total",
            "tax_rate": "Sales Tax Rate",
            "tax_amount": "Sales Tax",
            "total": "Balance Due",
            "notes": "Memo"
        },
        "date_format": "%m/%d/%Y"
    },
    "xero": {
        "name": "Xero",
        "columns": {
            "invoice_number": "Invoice ID",
            "invoice_date": "Date Created",
            "due_date": "Due Date",
            "client_name": "Contact Name",
            "client_email": "Contact Email",
            "client_address": "Address",
            "description": "Description",
            "quantity": "Quantity",
            "rate": "Unit Cost",
            "amount": "Line Amount",
            "tax_rate": "Tax Rate",
            "tax_amount": "Tax Amount",
            "total": "Total",
            "notes": "Notes"
        },
        "date_format": "%Y-%m-%d"
    },
    "harvest": {
        "name": "Harvest",
        "columns": {
            "invoice_number": "Invoice Code",
            "invoice_date": "Issued Date",
            "due_date": "Due By",
            "client_name": "Company",
            "client_email": "Email",
            "client_address": "Street Address",
            "description": "Task Name",
            "quantity": "Hours",
            "rate": "Hourly Rate",
            "amount": "Amount",
            "tax_rate": "Tax %",
            "tax_amount": "Tax",
            "total": "Grand Total",
            "notes": "Notes"
        },
        "date_format": "%B %d, %Y"
    },
    "freshbooks": {
        "name": "FreshBooks",
        "columns": {
            "invoice_number": "Invoice Number",
            "invoice_date": "Issue Date",
            "due_date": "Payment Due",
            "client_name": "Client Name",
            "client_email": "Client Email",
            "client_address": "Client Address",
            "description": "Item",
            "quantity": "Units",
            "rate": "Price",
            "amount": "Line Amount",
            "tax_rate": "Tax Percent",
            "tax_amount": "Tax Amount",
            "total": "Amount Due",
            "notes": "Comments"
        },
        "date_format": "%d/%m/%Y"
    },
    "wave": {
        "name": "Wave",
        "columns": {
            "invoice_number": "Invoice Identifier",
            "invoice_date": "Created Date",
            "due_date": "Payment Date",
            "client_name": "Business Name",
            "client_email": "Primary Email",
            "client_address": "Billing Address",
            "description": "Service Description",
            "quantity": "Qty",
            "rate": "Unit Price",
            "amount": "Extended Amount",
            "tax_rate": "Tax Rate %",
            "tax_amount": "Tax Total",
            "total": "Invoice Total",
            "notes": "Customer Message"
        },
        "date_format": "%m-%d-%Y"
    },
    "generic": {
        "name": "Generic CSV",
        "columns": {
            "invoice_number": "Invoice No",
            "invoice_date": "Invoice Date",
            "due_date": "Due Date",
            "client_name": "Client",
            "client_email": "Email",
            "client_address": "Address",
            "description": "Description",
            "quantity": "Qty",
            "rate": "Rate",
            "amount": "Amount",
            "tax_rate": "Tax Rate",
            "tax_amount": "Tax",
            "total": "Total",
            "notes": "Notes"
        },
        "date_format": "%Y-%m-%d"
    }
}


def generate_random_email(company_name: str) -> str:
    """Generate a random email based on company name"""
    domain = company_name.lower().replace(" ", "").replace(".", "")[:10]
    first = random.choice(FIRST_NAMES).lower()
    return f"{first}@{domain}.com"


def generate_random_address() -> Tuple[str, str, str, str]:
    """Generate a random address"""
    return random.choice(ADDRESSES)


def generate_line_items(num_items: int) -> List[Dict]:
    """Generate random line items"""
    items = []
    for _ in range(num_items):
        service_name, min_rate, max_rate = random.choice(SERVICES)
        quantity = round(random.uniform(1, 20), 1)
        rate = round(random.uniform(min_rate, max_rate), 2)
        amount = round(quantity * rate, 2)
        items.append({
            "description": service_name,
            "quantity": quantity,
            "rate": rate,
            "amount": amount
        })
    return items


def generate_invoice_data(invoice_num: int, format_key: str) -> List[Dict]:
    """Generate data for a single invoice with multiple line items"""
    fmt = CSV_FORMATS[format_key]
    columns = fmt["columns"]
    date_format = fmt["date_format"]
    
    # Invoice header data
    company = random.choice(COMPANY_NAMES)
    email = generate_random_email(company)
    street, city, state, zip_code = generate_random_address()
    full_address = f"{street}, {city}, {state} {zip_code}"
    
    invoice_date = datetime.now() - timedelta(days=random.randint(1, 30))
    due_date = invoice_date + timedelta(days=random.randint(15, 45))
    
    # Generate line items
    num_items = random.randint(1, 5)
    line_items = generate_line_items(num_items)
    
    # Calculate totals
    subtotal = sum(item["amount"] for item in line_items)
    tax_rate = random.choice([0, 4.0, 5.5, 6.0, 6.25, 7.0, 7.5, 8.0])
    tax_amount = round(subtotal * (tax_rate / 100), 2)
    total = round(subtotal + tax_amount, 2)
    
    # Generate CSV rows
    rows = []
    for i, item in enumerate(line_items):
        row = {
            columns["invoice_number"]: f"INV-{invoice_num:04d}",
            columns["invoice_date"]: invoice_date.strftime(date_format),
            columns["due_date"]: due_date.strftime(date_format),
            columns["client_name"]: company,
            columns["client_email"]: email,
            columns["client_address"]: full_address,
            columns["description"]: item["description"],
            columns["quantity"]: item["quantity"],
            columns["rate"]: f"${item['rate']:.2f}",
            columns["amount"]: f"${item['amount']:.2f}",
            columns["tax_rate"]: f"{tax_rate}%" if i == 0 else "",
            columns["tax_amount"]: f"${tax_amount:.2f}" if i == 0 else "",
            columns["total"]: f"${total:.2f}" if i == 0 else "",
            columns["notes"]: "Thank you for your business!" if i == 0 else ""
        }
        rows.append(row)
    
    return rows


def generate_demo_csv(format_key: str = "quickbooks_online", num_invoices: int = 5) -> Tuple[str, str]:
    """
    Generate a demo CSV file in the specified format
    
    Args:
        format_key: One of the CSV_FORMATS keys
        num_invoices: Number of invoices to generate
    
    Returns:
        Tuple of (csv_content, format_name)
    """
    if format_key not in CSV_FORMATS:
        format_key = "quickbooks_online"
    
    fmt = CSV_FORMATS[format_key]
    columns = fmt["columns"]
    
    # Generate all invoice rows
    all_rows = []
    for i in range(num_invoices):
        invoice_num = 1000 + i
        rows = generate_invoice_data(invoice_num, format_key)
        all_rows.extend(rows)
    
    # Create CSV
    output = StringIO()
    fieldnames = list(columns.values())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_rows)
    
    return output.getvalue(), fmt["name"]


def get_available_formats() -> List[Dict]:
    """Get list of available CSV formats"""
    return [
        {"key": key, "name": fmt["name"]}
        for key, fmt in CSV_FORMATS.items()
    ]


# Quick test
if __name__ == "__main__":
    for format_key in CSV_FORMATS.keys():
        csv_content, format_name = generate_demo_csv(format_key, num_invoices=2)
        print(f"\n{'='*60}")
        print(f"Format: {format_name}")
        print(f"{'='*60}")
        print(csv_content[:500] + "..." if len(csv_content) > 500 else csv_content)
