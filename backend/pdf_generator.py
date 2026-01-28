from weasyprint import HTML, CSS
from typing import Dict, Any, List
import os
from pathlib import Path

class PDFGenerator:
    def __init__(self):
        self.templates_dir = Path(__file__).parent / 'templates'
        self.templates_dir.mkdir(exist_ok=True)
        
    def generate_invoice_html(self, invoice_data: Dict[str, Any], branding: Dict[str, Any]) -> str:
        """Generate HTML for invoice based on template"""
        template_id = invoice_data.get('template_id', 'modern')
        
        if template_id == 'modern':
            return self._modern_template(invoice_data, branding)
        elif template_id == 'classic':
            return self._classic_template(invoice_data, branding)
        elif template_id == 'minimal':
            return self._minimal_template(invoice_data, branding)
        else:
            return self._modern_template(invoice_data, branding)
    
    def _modern_template(self, invoice: Dict[str, Any], branding: Dict[str, Any]) -> str:
        """Modern professional template"""
        primary_color = branding.get('primary_color', '#3B82F6')
        logo_url = branding.get('logo_url', '')
        
        line_items_html = ''
        for item in invoice.get('line_items', []):
            line_items_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #E5E7EB;">{item['description']}</td>
                <td style="padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: center;">{item['quantity']}</td>
                <td style="padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">${item['rate']:.2f}</td>
                <td style="padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: right; font-weight: 600;">${item['amount']:.2f}</td>
            </tr>
            """
        
        invoice_date = invoice.get('invoice_date', '').strftime('%B %d, %Y') if isinstance(invoice.get('invoice_date'), object) else ''
        due_date = invoice.get('due_date', '').strftime('%B %d, %Y') if invoice.get('due_date') and isinstance(invoice.get('due_date'), object) else 'Upon Receipt'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: 'Helvetica', 'Arial', sans-serif;
                    color: #1F2937;
                    line-height: 1.6;
                }}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 3px solid {primary_color};
                }}
                .logo {{
                    max-width: 200px;
                    max-height: 80px;
                }}
                .invoice-title {{
                    font-size: 36px;
                    font-weight: bold;
                    color: {primary_color};
                }}
                .info-section {{
                    margin-bottom: 30px;
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 30px;
                }}
                .info-box {{
                    background: #F9FAFB;
                    padding: 20px;
                    border-radius: 8px;
                }}
                .info-label {{
                    font-size: 12px;
                    color: #6B7280;
                    text-transform: uppercase;
                    margin-bottom: 5px;
                }}
                .info-value {{
                    font-size: 14px;
                    font-weight: 600;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 30px 0;
                }}
                th {{
                    background: {primary_color};
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                }}
                .totals {{
                    margin-top: 30px;
                    text-align: right;
                }}
                .total-row {{
                    display: flex;
                    justify-content: flex-end;
                    padding: 8px 0;
                }}
                .total-label {{
                    width: 150px;
                    text-align: right;
                    padding-right: 20px;
                }}
                .total-value {{
                    width: 100px;
                    text-align: right;
                    font-weight: 600;
                }}
                .grand-total {{
                    font-size: 20px;
                    color: {primary_color};
                    border-top: 2px solid {primary_color};
                    padding-top: 15px;
                    margin-top: 10px;
                }}
                .notes {{
                    margin-top: 40px;
                    padding: 20px;
                    background: #F9FAFB;
                    border-left: 4px solid {primary_color};
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div>
                    {'<img class="logo" src="' + logo_url + '" />' if logo_url else ''}
                </div>
                <div class="invoice-title">INVOICE</div>
            </div>
            
            <div class="info-section">
                <div class="info-grid">
                    <div class="info-box">
                        <div class="info-label">Invoice Number</div>
                        <div class="info-value">{invoice.get('invoice_number', '')}</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">Invoice Date</div>
                        <div class="info-value">{invoice_date}</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">Bill To</div>
                        <div class="info-value">{invoice.get('client_name', '')}</div>
                        {'<div style="font-size: 12px; color: #6B7280; margin-top: 5px;">' + invoice.get('client_address', '') + '</div>' if invoice.get('client_address') else ''}
                        {'<div style="font-size: 12px; color: #6B7280;">' + invoice.get('client_email', '') + '</div>' if invoice.get('client_email') else ''}
                    </div>
                    <div class="info-box">
                        <div class="info-label">Due Date</div>
                        <div class="info-value">{due_date}</div>
                    </div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th style="text-align: center; width: 80px;">Qty</th>
                        <th style="text-align: right; width: 100px;">Rate</th>
                        <th style="text-align: right; width: 100px;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {line_items_html}
                </tbody>
            </table>
            
            <div class="totals">
                <div class="total-row">
                    <div class="total-label">Subtotal:</div>
                    <div class="total-value">${invoice.get('subtotal', 0):.2f}</div>
                </div>
                {f'<div class="total-row"><div class="total-label">Tax ({invoice.get("tax_rate", 0):.2f}%):</div><div class="total-value">${invoice.get("tax_amount", 0):.2f}</div></div>' if invoice.get('tax_amount', 0) > 0 else ''}
                <div class="total-row grand-total">
                    <div class="total-label">Total:</div>
                    <div class="total-value">${invoice.get('total', 0):.2f}</div>
                </div>
            </div>
            
            {f'<div class="notes"><strong>Notes:</strong><br>{invoice.get("notes", "")}</div>' if invoice.get('notes') else ''}
        </body>
        </html>
        """
        return html
    
    def _classic_template(self, invoice: Dict[str, Any], branding: Dict[str, Any]) -> str:
        """Classic business template"""
        # Similar structure but with classic styling
        return self._modern_template(invoice, branding)  # Simplified for now
    
    def _minimal_template(self, invoice: Dict[str, Any], branding: Dict[str, Any]) -> str:
        """Minimal clean template"""
        # Similar structure but with minimal styling
        return self._modern_template(invoice, branding)  # Simplified for now
    
    def generate_pdf(self, invoice_data: Dict[str, Any], branding: Dict[str, Any], output_path: str) -> bool:
        """Generate PDF from invoice data"""
        try:
            html_content = self.generate_invoice_html(invoice_data, branding)
            HTML(string=html_content).write_pdf(output_path)
            return True
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return False
