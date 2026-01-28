"""
CSV Parser v2.0 - Production-Grade Implementation
Supports 180+ column variations from QuickBooks, Xero, Harvest, FreshBooks, Wave
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
from fuzzywuzzy import fuzz
from io import StringIO, BytesIO
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# COLUMN MAPPING DATABASE - 180+ Variations
# ============================================================================

class ColumnMappings:
    """Complete column mapping database for all accounting systems"""
    
    # Invoice Number Variations (QuickBooks, Xero, Harvest, etc.)
    INVOICE_NUMBER = [
        # QuickBooks Online
        'invoice #', 'invoice number', 'invoice no', 'invoicenumber', 'invoice_number',
        # QuickBooks Desktop
        'ref number', 'refnumber', 'ref #', 'ref', 'transaction number', 'trans #',
        'num', 'number', 'doc number', 'docnumber', 'document number',
        # Xero
        'invoice id', 'invoiceid', 'reference', 'invoice reference',
        # Harvest
        'invoice code', 'invoice#', 'id',
        # FreshBooks
        'invoice_id', 'invoicecode',
        # Wave
        'invoice identifier', 'bill number',
        # Generic
        'inv #', 'inv no', 'inv number', 'inv_no', 'inv_num'
    ]
    
    # Invoice Date Variations
    INVOICE_DATE = [
        # QuickBooks
        'date', 'invoice date', 'invoicedate', 'invoice_date', 'trans date',
        'transaction date', 'txn date', 'txndate', 'billing date',
        # Xero
        'date created', 'created date', 'creation date', 'issue date',
        # Harvest
        'sent date', 'issued', 'issued date', 'issued on',
        # Generic
        'inv date', 'inv_date', 'bill date', 'billed date', 'billed on'
    ]
    
    # Due Date Variations
    DUE_DATE = [
        'due date', 'duedate', 'due_date', 'payment due', 'paymentdue',
        'payment due date', 'terms date', 'termsdate', 'due by',
        'payment date', 'paymentdate', 'pay by date', 'expiry date',
        'due on', 'payment deadline', 'term date'
    ]
    
    # Client/Customer Name Variations
    CLIENT_NAME = [
        # QuickBooks
        'customer', 'customer name', 'customername', 'customer_name',
        'client', 'client name', 'clientname', 'client_name',
        'bill to', 'bill_to', 'billto', 'bill to name',
        'sold to', 'sold_to', 'soldto',
        # Xero
        'contact', 'contact name', 'customer/contact',
        # Harvest
        'company', 'company name', 'companyname', 'organization',
        # Generic
        'business name', 'business', 'account', 'account name',
        'customer:company', 'customer company', 'name'
    ]
    
    # Client Email Variations
    CLIENT_EMAIL = [
        'email', 'e-mail', 'email address', 'emailaddress', 'email_address',
        'customer email', 'customeremail', 'customer_email',
        'client email', 'clientemail', 'client_email',
        'contact email', 'contactemail', 'contact_email',
        'bill to email', 'billing email', 'invoice email',
        'primary email', 'email 1', 'email1', 'customer:email'
    ]
    
    # Client Address Variations
    CLIENT_ADDRESS = [
        # Full Address
        'address', 'billing address', 'billingaddress', 'billing_address',
        'bill to address', 'customer address', 'customeraddress',
        'street address', 'street', 'ship to', 'shipto',
        # Address Lines
        'address line 1', 'addressline1', 'address1', 'addr1',
        'address line 2', 'addressline2', 'address2', 'addr2',
        'bill addr line 1', 'billing addr 1',
        # City
        'city', 'billing city', 'customer city', 'town',
        # State
        'state', 'state/province', 'province', 'region',
        'billing state', 'customer state',
        # ZIP
        'zip', 'zip code', 'zipcode', 'postal code', 'postalcode',
        'billing zip', 'customer zip'
    ]
    
    # Line Item Description Variations
    DESCRIPTION = [
        # QuickBooks
        'description', 'item description', 'service description',
        'product/service', 'product_service', 'product or service',
        'item', 'item name', 'itemname', 'item_name',
        'service', 'service name', 'servicename',
        # Xero
        'description & qty', 'description/qty', 'line description',
        # Harvest  
        'task', 'task name', 'activity', 'service item',
        # Generic
        'product', 'product name', 'productname', 'product description',
        'service type', 'memo', 'line item', 'lineitem', 'line_item',
        'details', 'item details', 'notes', 'description/notes',
        'sku', 'sku description', 'class'
    ]
    
    # Quantity Variations
    QUANTITY = [
        'qty', 'quantity', 'units', 'hours', 'amount',
        'qty sold', 'qtysold', 'quantity sold', 'units sold',
        'billable hours', 'billable qty', 'item qty',
        'num', 'count', 'volume', 'billing quantity'
    ]
    
    # Rate/Price Variations
    RATE = [
        # QuickBooks
        'rate', 'price', 'unit price', 'unitprice', 'unit_price',
        'sales price', 'salesprice', 'sales_price',
        # Xero
        'unit cost', 'unitcost', 'unit_cost', 'cost per unit',
        # Harvest
        'hourly rate', 'hourlyrate', 'hourly_rate', 'billing rate',
        # Generic
        'price each', 'priceeach', 'price_each', 'each',
        'cost', 'rate/price', 'rate price', 'charge', 'fee'
    ]
    
    # Line Amount Variations
    AMOUNT = [
        # QuickBooks
        'amount', 'line amount', 'lineamount', 'line_amount',
        'line total', 'linetotal', 'line_total',
        'extended amount', 'extendedamount', 'extended_amount',
        # Xero
        'line amount tax', 'line amount no tax',
        # Generic
        'total', 'subtotal', 'sum', 'price', 'charge',
        'item total', 'net amount', 'line price'
    ]
    
    # Subtotal Variations
    SUBTOTAL = [
        'subtotal', 'sub total', 'sub-total', 'sub_total',
        'net amount', 'netamount', 'net_amount',
        'total before tax', 'amount before tax',
        'taxable amount', 'taxableamount', 'pre-tax total',
        'item total', 'items total', 'line items total'
    ]
    
    # Tax Rate Variations
    TAX_RATE = [
        'tax rate', 'taxrate', 'tax_rate', 'tax %', 'tax percent',
        'tax percentage', 'sales tax rate', 'salestaxrate',
        'gst rate', 'vat rate', 'tax code rate',
        'rate of tax', 'tax rate %', 'rate %'
    ]
    
    # Tax Amount Variations
    TAX_AMOUNT = [
        # QuickBooks
        'tax', 'tax amount', 'taxamount', 'tax_amount',
        'sales tax', 'salestax', 'sales_tax',
        # International
        'gst', 'gst amount', 'vat', 'vat amount',
        # Generic
        'tax total', 'taxtotal', 'total tax',
        'tax charged', 'tax applied', 'tax value'
    ]
    
    # Total Amount Variations  
    TOTAL = [
        'total', 'grand total', 'grandtotal', 'grand_total',
        'invoice total', 'invoicetotal', 'invoice_total',
        'amount due', 'amountdue', 'amount_due',
        'balance', 'balance due', 'balancedue',
        'total amount', 'totalamount', 'final total',
        'amount owing', 'total with tax', 'final amount'
    ]
    
    # Terms Variations
    TERMS = [
        'terms', 'payment terms', 'paymentterms', 'payment_terms',
        'term', 'due terms', 'invoice terms', 'billing terms',
        'net terms', 'due net', 'payment method'
    ]
    
    # Notes/Memo Variations
    NOTES = [
        'notes', 'memo', 'message', 'customer message', 'customermessage',
        'comments', 'description', 'remarks', 'note to customer',
        'invoice message', 'invoice note', 'additional info',
        'special instructions', 'instructions'
    ]
    
    # Currency Variations
    CURRENCY = [
        'currency', 'currency code', 'currencycode', 'curr',
        'transaction currency', 'billing currency',
        'home currency', 'foreign currency'
    ]
    
    # Status Variations
    STATUS = [
        'status', 'invoice status', 'payment status', 'paymentstatus',
        'paid status', 'state', 'condition', 'paid/unpaid',
        'open/closed', 'sent/unsent'
    ]
    
    # PO Number Variations
    PO_NUMBER = [
        'po #', 'po number', 'ponumber', 'po_number',
        'purchase order', 'purchase order #', 'p.o. number',
        'po', 'purchase order number', 'client po'
    ]
    
    @classmethod
    def get_all_mappings(cls) -> Dict[str, List[str]]:
        """Return all column mappings as a dictionary"""
        return {
            'invoice_number': cls.INVOICE_NUMBER,
            'invoice_date': cls.INVOICE_DATE,
            'due_date': cls.DUE_DATE,
            'client_name': cls.CLIENT_NAME,
            'client_email': cls.CLIENT_EMAIL,
            'client_address': cls.CLIENT_ADDRESS,
            'description': cls.DESCRIPTION,
            'quantity': cls.QUANTITY,
            'rate': cls.RATE,
            'amount': cls.AMOUNT,
            'subtotal': cls.SUBTOTAL,
            'tax_rate': cls.TAX_RATE,
            'tax_amount': cls.TAX_AMOUNT,
            'total': cls.TOTAL,
            'terms': cls.TERMS,
            'notes': cls.NOTES,
            'currency': cls.CURRENCY,
            'status': cls.STATUS,
            'po_number': cls.PO_NUMBER
        }


# ============================================================================
# FUZZY MATCHING ENGINE
# ============================================================================

class FuzzyMatcher:
    """Advanced fuzzy matching with multiple strategies"""
    
    @staticmethod
    def levenshtein_match(col_name: str, targets: List[str], threshold: int = 70) -> Optional[str]:
        """Match using Levenshtein distance"""
        col_lower = col_name.lower().strip()
        best_match = None
        best_score = 0
        
        for target in targets:
            score = fuzz.ratio(col_lower, target.lower())
            if score > best_score and score >= threshold:
                best_score = score
                best_match = target
        
        return best_match if best_score >= threshold else None
    
    @staticmethod
    def partial_match(col_name: str, targets: List[str], threshold: int = 80) -> Optional[str]:
        """Match using partial string matching"""
        col_lower = col_name.lower().strip()
        best_match = None
        best_score = 0
        
        for target in targets:
            score = fuzz.partial_ratio(col_lower, target.lower())
            if score > best_score and score >= threshold:
                best_score = score
                best_match = target
        
        return best_match if best_score >= threshold else None
    
    @staticmethod
    def token_sort_match(col_name: str, targets: List[str], threshold: int = 75) -> Optional[str]:
        """Match using token sort (order-independent)"""
        col_lower = col_name.lower().strip()
        best_match = None
        best_score = 0
        
        for target in targets:
            score = fuzz.token_sort_ratio(col_lower, target.lower())
            if score > best_score and score >= threshold:
                best_score = score
                best_match = target
        
        return best_match if best_score >= threshold else None
    
    @classmethod
    def best_match(cls, col_name: str, targets: List[str]) -> Optional[Tuple[str, int]]:
        """
        Find best match using multiple strategies
        Returns: (matched_target, confidence_score)
        """
        # Strategy 1: Exact match
        col_lower = col_name.lower().strip()
        for target in targets:
            if col_lower == target.lower():
                return (target, 100)
        
        # Strategy 2: Levenshtein
        lev_match = cls.levenshtein_match(col_name, targets, threshold=70)
        lev_score = fuzz.ratio(col_lower, lev_match.lower()) if lev_match else 0
        
        # Strategy 3: Partial
        partial_match = cls.partial_match(col_name, targets, threshold=80)
        partial_score = fuzz.partial_ratio(col_lower, partial_match.lower()) if partial_match else 0
        
        # Strategy 4: Token sort
        token_match = cls.token_sort_match(col_name, targets, threshold=75)
        token_score = fuzz.token_sort_ratio(col_lower, token_match.lower()) if token_match else 0
        
        # Choose best strategy
        strategies = [
            (lev_match, lev_score),
            (partial_match, partial_score),
            (token_match, token_score)
        ]
        
        best = max(strategies, key=lambda x: x[1])
        return best if best[1] >= 70 else (None, 0)


# ============================================================================
# CSV PARSER V2.0
# ============================================================================

class CSVParserV2:
    """Production-grade CSV parser with 180+ column support"""
    
    def __init__(self):
        self.mappings = ColumnMappings.get_all_mappings()
        self.fuzzy_matcher = FuzzyMatcher()
        self.used_columns = set()
    
    def detect_column_mapping(self, df_columns: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Detect which columns in CSV correspond to our fields
        Returns: {standard_field: {csv_column: str, confidence: int}}
        """
        mapping = {}
        self.used_columns = set()
        
        for standard_field, variations in self.mappings.items():
            best_col = None
            best_score = 0
            
            for col in df_columns:
                if col in self.used_columns:
                    continue
                
                match_result = self.fuzzy_matcher.best_match(col, variations)
                if match_result and match_result[1] > best_score:
                    best_col = col
                    best_score = match_result[1]
            
            if best_col and best_score >= 70:
                mapping[standard_field] = {
                    'csv_column': best_col,
                    'confidence': best_score
                }
                self.used_columns.add(best_col)
                logger.info(f"Mapped {standard_field} → {best_col} (confidence: {best_score}%)")
        
        return mapping
    
    def parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse dates with multiple format detection"""
        if pd.isna(date_value) or date_value is None:
            return None
        
        if isinstance(date_value, datetime):
            return date_value
        
        date_str = str(date_value).strip()
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%m/%d/%Y', '%m/%d/%y',  # US: 01/15/2024, 01/15/24
            '%d/%m/%Y', '%d/%m/%y',  # EU: 15/01/2024, 15/01/24
            '%Y-%m-%d', '%Y/%m/%d',  # ISO: 2024-01-15, 2024/01/15
            '%m-%d-%Y', '%d-%m-%Y',  # Dash: 01-15-2024, 15-01-2024
            '%B %d, %Y',             # January 15, 2024
            '%b %d, %Y',             # Jan 15, 2024
            '%d %B %Y',              # 15 January 2024
            '%d %b %Y',              # 15 Jan 2024
            '%Y%m%d',                # 20240115
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try pandas parser as fallback
        try:
            return pd.to_datetime(date_str)
        except:
            logger.warning(f"Could not parse date: {date_str}")
            return None
    
    def parse_number(self, num_value: Any) -> float:
        """Parse numbers with currency symbol and format handling"""
        if pd.isna(num_value) or num_value is None:
            return 0.0
        
        if isinstance(num_value, (int, float)):
            return float(num_value)
        
        # Clean the string
        cleaned = str(num_value).strip()
        
        # Remove currency symbols and common formatting
        cleaned = re.sub(r'[$£€¥₹,\s]', '', cleaned)
        
        # Handle negative numbers in parentheses: (1234.56) → -1234.56
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        
        # Handle European format: 1.234,56 → 1234.56
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rindex(',') > cleaned.rindex('.'):
                # European format
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US format
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Check if it's decimal separator or thousands
            parts = cleaned.split(',')
            if len(parts[-1]) == 2:
                # Likely European decimal: 1234,56
                cleaned = cleaned.replace(',', '.')
            else:
                # Thousands separator: 1,234
                cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            logger.warning(f"Could not parse number: {num_value}")
            return 0.0
    
    def split_invoices(self, df: pd.DataFrame, mapping: Dict[str, Dict]) -> List[pd.DataFrame]:
        """
        Split multi-invoice CSV into individual invoice DataFrames
        Handles same invoice number with different dates
        """
        if 'invoice_number' not in mapping:
            # Single invoice file
            return [df]
        
        invoice_col = mapping['invoice_number']['csv_column']
        
        # Create composite key: invoice_number + invoice_date (if available)
        if 'invoice_date' in mapping:
            date_col = mapping['invoice_date']['csv_column']
            df['_composite_key'] = df.apply(
                lambda row: f"{row[invoice_col]}_{row[date_col]}" 
                if pd.notna(row[invoice_col]) else None,
                axis=1
            )
            group_col = '_composite_key'
        else:
            group_col = invoice_col
        
        # Group by invoice
        invoice_groups = []
        for key, group in df.groupby(group_col):
            if pd.notna(key) and str(key).strip():
                invoice_groups.append(group.copy())
        
        return invoice_groups
    
    def parse_invoice_group(self, df: pd.DataFrame, mapping: Dict[str, Dict]) -> Optional[Dict[str, Any]]:
        """Parse a single invoice from grouped DataFrame"""
        if df.empty:
            return None
        
        first_row = df.iloc[0]
        
        # Extract invoice-level fields
        invoice_number = self._get_field(first_row, mapping, 'invoice_number', 
                                        default=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        invoice_date = self._get_date_field(first_row, mapping, 'invoice_date', 
                                            default=datetime.now())
        
        due_date = self._get_date_field(first_row, mapping, 'due_date')
        
        client_name = self._get_field(first_row, mapping, 'client_name', 
                                      default='Unknown Client')
        
        client_email = self._get_field(first_row, mapping, 'client_email')
        client_address = self._get_field(first_row, mapping, 'client_address')
        terms = self._get_field(first_row, mapping, 'terms')
        notes = self._get_field(first_row, mapping, 'notes')
        po_number = self._get_field(first_row, mapping, 'po_number')
        currency = self._get_field(first_row, mapping, 'currency', default='USD')
        status = self._get_field(first_row, mapping, 'status', default='draft')
        
        # Parse line items
        line_items = []
        for _, row in df.iterrows():
            description = self._get_field(row, mapping, 'description')
            if not description:
                continue  # Skip rows without description
            
            quantity = self._get_number_field(row, mapping, 'quantity', default=1.0)
            rate = self._get_number_field(row, mapping, 'rate', default=0.0)
            amount = self._get_number_field(row, mapping, 'amount', default=0.0)
            
            # Calculate amount if not provided
            if amount == 0.0 and quantity > 0 and rate > 0:
                amount = quantity * rate
            
            line_items.append({
                'description': description,
                'quantity': quantity,
                'rate': rate,
                'amount': amount
            })
        
        if not line_items:
            logger.warning(f"No line items found for invoice {invoice_number}")
            return None
        
        # Calculate totals
        subtotal = sum(item['amount'] for item in line_items)
        
        # Get tax from CSV or calculate
        tax_amount = self._get_number_field(first_row, mapping, 'tax_amount', default=0.0)
        tax_rate = self._get_number_field(first_row, mapping, 'tax_rate', default=0.0)
        
        # Calculate missing tax values
        if tax_amount > 0 and tax_rate == 0 and subtotal > 0:
            tax_rate = (tax_amount / subtotal) * 100
        elif tax_rate > 0 and tax_amount == 0:
            tax_amount = subtotal * (tax_rate / 100)
        
        total = subtotal + tax_amount
        
        return {
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'due_date': due_date,
            'client_name': client_name,
            'client_email': client_email,
            'client_address': client_address,
            'line_items': line_items,
            'subtotal': subtotal,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total': total,
            'terms': terms,
            'notes': notes,
            'po_number': po_number,
            'currency': currency,
            'status': status
        }
    
    def _get_field(self, row, mapping: Dict, field: str, default: Any = None) -> Any:
        """Safely get field value from row"""
        if field not in mapping:
            return default
        
        col = mapping[field]['csv_column']
        value = row.get(col)
        
        if pd.isna(value) or value is None:
            return default
        
        return str(value).strip() if value else default
    
    def _get_date_field(self, row, mapping: Dict, field: str, default: Any = None) -> Any:
        """Get and parse date field"""
        if field not in mapping:
            return default
        
        col = mapping[field]['csv_column']
        value = row.get(col)
        
        parsed = self.parse_date(value)
        return parsed if parsed else default
    
    def _get_number_field(self, row, mapping: Dict, field: str, default: float = 0.0) -> float:
        """Get and parse number field"""
        if field not in mapping:
            return default
        
        col = mapping[field]['csv_column']
        value = row.get(col)
        
        return self.parse_number(value)
    
    def parse_csv(self, file_path: str) -> Tuple[List[Dict[str, Any]], Optional[str], Dict[str, Any]]:
        """
        Main parsing function
        Returns: (invoices, error_message, metadata)
        """
        try:
            # Determine file type
            file_ext = file_path.lower().split('.')[-1]
            
            # Read file
            if file_ext == 'csv':
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='latin-1')
                except Exception as e:
                    df = pd.read_csv(file_path, encoding='cp1252')
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path, engine='openpyxl')
            else:
                return [], f"Unsupported file type: {file_ext}", {}
            
            if df.empty:
                return [], "File is empty", {}
            
            logger.info(f"Read {len(df)} rows, {len(df.columns)} columns")
            
            # Detect column mapping
            mapping = self.detect_column_mapping(df.columns.tolist())
            
            if not mapping:
                return [], "Could not detect any recognizable columns. Please check your CSV format.", {}
            
            # Log mapping results
            mapped_fields = list(mapping.keys())
            confidence_scores = {k: v['confidence'] for k, v in mapping.items()}
            
            logger.info(f"Mapped {len(mapping)} fields: {mapped_fields}")
            
            # Split into individual invoices
            invoice_groups = self.split_invoices(df, mapping)
            logger.info(f"Found {len(invoice_groups)} invoice groups")
            
            # Parse each invoice
            invoices = []
            for group in invoice_groups:
                invoice_data = self.parse_invoice_group(group, mapping)
                if invoice_data:
                    invoices.append(invoice_data)
            
            if not invoices:
                return [], "No valid invoices found in file", {}
            
            metadata = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'mapped_fields': mapped_fields,
                'confidence_scores': confidence_scores,
                'invoices_found': len(invoices),
                'avg_confidence': sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
            }
            
            return invoices, None, metadata
            
        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}", exc_info=True)
            return [], f"Error parsing file: {str(e)}", {}
