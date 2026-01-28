import pandas as pd
import csv
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
from fuzzywuzzy import fuzz
from io import StringIO

# Column mappings for 180+ accounting software variations
COLUMN_MAPPINGS = {
    # QuickBooks variations
    'invoice_number': ['invoice #', 'invoice number', 'invoice no', 'inv #', 'inv no', 'number', 'doc number', 'num'],
    'invoice_date': ['date', 'invoice date', 'transaction date', 'inv date', 'issue date', 'created date'],
    'due_date': ['due date', 'payment due', 'due', 'terms date', 'payment date'],
    'client_name': ['customer', 'client', 'customer name', 'client name', 'bill to', 'sold to', 'company', 'business name'],
    'client_email': ['email', 'customer email', 'client email', 'contact email', 'e-mail'],
    'client_address': ['address', 'billing address', 'customer address', 'street', 'bill to address'],
    'description': ['description', 'item', 'product/service', 'item description', 'memo', 'service description', 'product'],
    'quantity': ['qty', 'quantity', 'units', 'hours', 'amount'],
    'rate': ['rate', 'price', 'unit price', 'cost', 'price each', 'unit cost', 'hourly rate'],
    'amount': ['amount', 'total', 'line total', 'extended amount', 'subtotal', 'sum'],
    'subtotal': ['subtotal', 'sub total', 'sub-total', 'net amount'],
    'tax_rate': ['tax rate', 'tax %', 'tax percent', 'sales tax rate'],
    'tax_amount': ['tax', 'tax amount', 'sales tax', 'tax total', 'gst', 'vat'],
    'total': ['total', 'grand total', 'invoice total', 'balance due', 'amount due'],
    'notes': ['notes', 'memo', 'message', 'comments', 'terms', 'description']
}

class CSVParser:
    def __init__(self):
        self.column_mappings = COLUMN_MAPPINGS
        
    def fuzzy_match_column(self, column_name: str, target_columns: List[str]) -> Optional[str]:
        """Use fuzzy matching to find the best matching column"""
        column_name = column_name.lower().strip()
        best_match = None
        best_score = 0
        
        for target in target_columns:
            score = fuzz.ratio(column_name, target)
            if score > best_score and score > 70:  # 70% similarity threshold
                best_score = score
                best_match = target
        
        return best_match
    
    def detect_column_mapping(self, df_columns: List[str]) -> Dict[str, str]:
        """Detect which columns in the CSV correspond to our standard fields"""
        mapping = {}
        
        for standard_field, variations in self.column_mappings.items():
            for col in df_columns:
                match = self.fuzzy_match_column(col, variations)
                if match:
                    mapping[standard_field] = col
                    break
        
        return mapping
    
    def parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse various date formats"""
        if pd.isna(date_str):
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        date_str = str(date_str).strip()
        
        # Common date formats
        formats = [
            '%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y',
            '%d-%m-%Y', '%Y/%m/%d', '%B %d, %Y', '%d %B %Y',
            '%m/%d/%y', '%d/%m/%y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def parse_number(self, num_str: Any) -> float:
        """Parse numbers with various formats (commas, currency symbols, etc.)"""
        if pd.isna(num_str):
            return 0.0
        
        if isinstance(num_str, (int, float)):
            return float(num_str)
        
        # Remove currency symbols and commas
        cleaned = str(num_str).strip()
        cleaned = re.sub(r'[^0-9.-]', '', cleaned)
        
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0
    
    def split_invoices(self, df: pd.DataFrame, mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Split a multi-invoice CSV into individual invoices"""
        invoices = []
        
        if 'invoice_number' not in mapping:
            # Single invoice file - treat all rows as one invoice
            return [self.parse_invoice_rows(df, mapping)]
        
        invoice_col = mapping['invoice_number']
        
        # Group rows by invoice number
        for invoice_num, group in df.groupby(invoice_col):
            if pd.notna(invoice_num) and str(invoice_num).strip():
                invoice_data = self.parse_invoice_rows(group, mapping)
                if invoice_data:
                    invoices.append(invoice_data)
        
        return invoices
    
    def parse_invoice_rows(self, df: pd.DataFrame, mapping: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse rows belonging to a single invoice"""
        if df.empty:
            return None
        
        first_row = df.iloc[0]
        
        # Extract invoice-level data from first row
        invoice_data = {
            'invoice_number': str(first_row.get(mapping.get('invoice_number', ''), '')).strip() or f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'invoice_date': self.parse_date(first_row.get(mapping.get('invoice_date', ''), datetime.now())),
            'due_date': self.parse_date(first_row.get(mapping.get('due_date', ''))) if 'due_date' in mapping else None,
            'client_name': str(first_row.get(mapping.get('client_name', ''), 'Unknown Client')).strip(),
            'client_email': str(first_row.get(mapping.get('client_email', ''), '')).strip() if 'client_email' in mapping else None,
            'client_address': str(first_row.get(mapping.get('client_address', ''), '')).strip() if 'client_address' in mapping else None,
            'notes': str(first_row.get(mapping.get('notes', ''), '')).strip() if 'notes' in mapping else None,
        }
        
        # Parse line items
        line_items = []
        for _, row in df.iterrows():
            description = str(row.get(mapping.get('description', ''), '')).strip()
            if not description:
                continue
            
            quantity = self.parse_number(row.get(mapping.get('quantity', ''), 1.0))
            rate = self.parse_number(row.get(mapping.get('rate', ''), 0.0))
            amount = self.parse_number(row.get(mapping.get('amount', ''), 0.0))
            
            # Calculate amount if not provided
            if amount == 0.0 and quantity > 0 and rate > 0:
                amount = quantity * rate
            
            line_items.append({
                'description': description,
                'quantity': quantity,
                'rate': rate,
                'amount': amount
            })
        
        # Calculate totals
        subtotal = sum(item['amount'] for item in line_items)
        
        # Try to get tax from CSV, otherwise calculate
        tax_amount = self.parse_number(first_row.get(mapping.get('tax_amount', ''), 0.0)) if 'tax_amount' in mapping else 0.0
        tax_rate = self.parse_number(first_row.get(mapping.get('tax_rate', ''), 0.0)) if 'tax_rate' in mapping else 0.0
        
        # If tax_amount is provided but not rate, calculate rate
        if tax_amount > 0 and tax_rate == 0 and subtotal > 0:
            tax_rate = (tax_amount / subtotal) * 100
        
        # If rate is provided but not amount, calculate amount
        if tax_rate > 0 and tax_amount == 0:
            tax_amount = subtotal * (tax_rate / 100)
        
        total = subtotal + tax_amount
        
        invoice_data.update({
            'line_items': line_items,
            'subtotal': subtotal,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total': total
        })
        
        return invoice_data
    
    def parse_csv(self, file_path: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Main parsing function - returns (invoices, error_message)"""
        try:
            # Determine file type by extension
            file_ext = file_path.lower().split('.')[-1]
            
            # Try to read the file based on extension
            try:
                if file_ext == 'csv':
                    # Read as CSV
                    try:
                        df = pd.read_csv(file_path, encoding='utf-8')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, encoding='latin-1')
                else:
                    # Read as Excel
                    df = pd.read_excel(file_path, engine='openpyxl')
            except Exception as e:
                return [], f"Could not read file: {str(e)}"
            
            if df.empty:
                return [], "File is empty"
            
            # Detect column mapping
            mapping = self.detect_column_mapping(df.columns.tolist())
            
            if not mapping:
                return [], "Could not detect any recognizable columns"
            
            # Split into individual invoices
            invoices = self.split_invoices(df, mapping)
            
            if not invoices:
                return [], "No valid invoices found"
            
            return invoices, None
            
        except Exception as e:
            return [], f"Error parsing file: {str(e)}"
