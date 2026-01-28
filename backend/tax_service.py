from typing import Dict, Optional, List
import json
from pathlib import Path

class TaxService:
    def __init__(self):
        self.tax_rates_db = self._load_tax_rates()
    
    def _load_tax_rates(self) -> Dict[str, float]:
        """Load fallback tax rates database"""
        # Simplified US state tax rates (as of 2024)
        # In production, this would be loaded from MongoDB
        return {
            'AL': 4.00, 'AK': 0.00, 'AZ': 5.60, 'AR': 6.50, 'CA': 7.25,
            'CO': 2.90, 'CT': 6.35, 'DE': 0.00, 'FL': 6.00, 'GA': 4.00,
            'HI': 4.00, 'ID': 6.00, 'IL': 6.25, 'IN': 7.00, 'IA': 6.00,
            'KS': 6.50, 'KY': 6.00, 'LA': 4.45, 'ME': 5.50, 'MD': 6.00,
            'MA': 6.25, 'MI': 6.00, 'MN': 6.88, 'MS': 7.00, 'MO': 4.23,
            'MT': 0.00, 'NE': 5.50, 'NV': 6.85, 'NH': 0.00, 'NJ': 6.63,
            'NM': 5.13, 'NY': 4.00, 'NC': 4.75, 'ND': 5.00, 'OH': 5.75,
            'OK': 4.50, 'OR': 0.00, 'PA': 6.00, 'RI': 7.00, 'SC': 6.00,
            'SD': 4.50, 'TN': 7.00, 'TX': 6.25, 'UT': 6.10, 'VT': 6.00,
            'VA': 5.30, 'WA': 6.50, 'WV': 6.00, 'WI': 5.00, 'WY': 4.00,
            'DC': 6.00
        }
    
    def extract_state_from_address(self, address: Optional[str]) -> Optional[str]:
        """Extract state code from address string"""
        if not address:
            return None
        
        address = address.upper()
        
        # Look for state codes
        for state_code in self.tax_rates_db.keys():
            if state_code in address:
                return state_code
        
        return None
    
    def calculate_tax(self, amount: float, state_code: Optional[str] = None, 
                     client_address: Optional[str] = None) -> Dict[str, float]:
        """Calculate tax for an invoice"""
        # Try to get state from code or address
        if not state_code and client_address:
            state_code = self.extract_state_from_address(client_address)
        
        # Default to 0% if state not found
        tax_rate = 0.0
        if state_code and state_code in self.tax_rates_db:
            tax_rate = self.tax_rates_db[state_code]
        
        tax_amount = amount * (tax_rate / 100)
        
        return {
            'tax_rate': tax_rate,
            'tax_amount': round(tax_amount, 2),
            'total': round(amount + tax_amount, 2),
            'state': state_code
        }
    
    def check_exemption(self, organization_id: str, client_name: str, 
                       state: str, db) -> bool:
        """Check if client has valid tax exemption"""
        # This would query MongoDB for exemptions
        # Simplified for now
        return False
