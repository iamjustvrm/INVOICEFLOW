from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from typing import Dict, Any, List
import os
from pathlib import Path
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.templates_dir = Path(__file__).parent / 'templates'
        self.templates_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
    
    def _parse_color(self, color_hex: str):
        """Convert hex color to ReportLab color"""
        try:
            color_hex = color_hex.lstrip('#')
            return colors.HexColor('#' + color_hex)
        except:
            return colors.HexColor('#3B82F6')
    
    def generate_pdf(self, invoice_data: Dict[str, Any], branding: Dict[str, Any], output_path: str) -> bool:
        """Generate PDF from invoice data using ReportLab"""
        try:
            # Create the PDF object
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=inch*0.75,
                leftMargin=inch*0.75,
                topMargin=inch*0.75,
                bottomMargin=inch*0.75,
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Get branding colors
            primary_color = self._parse_color(branding.get('primary_color', '#3B82F6'))
            
            # Add logo if available
            logo_url = branding.get('logo_url')
            if logo_url and logo_url.startswith('/api/'):
                # Convert API path to local file path
                logo_filename = logo_url.split('/')[-1]
                logo_path = Path(__file__).parent / 'uploads' / logo_filename
                if logo_path.exists():
                    try:
                        logo = Image(str(logo_path), width=2*inch, height=0.8*inch)
                        elements.append(logo)
                        elements.append(Spacer(1, 0.2*inch))
                    except:
                        pass  # Skip if logo can't be loaded
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=28,
                textColor=primary_color,
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            elements.append(Paragraph("INVOICE", title_style))
            elements.append(Spacer(1, 0.3*inch))
            
            # Invoice info section
            invoice_date = invoice_data.get('invoice_date', '')
            if isinstance(invoice_date, str):
                try:
                    invoice_date = datetime.fromisoformat(invoice_date).strftime('%B %d, %Y')
                except:
                    invoice_date = str(invoice_date)
            elif hasattr(invoice_date, 'strftime'):
                invoice_date = invoice_date.strftime('%B %d, %Y')
            else:
                invoice_date = str(invoice_date)
            
            due_date = invoice_data.get('due_date', 'Upon Receipt')
            if due_date and due_date != 'Upon Receipt':
                if isinstance(due_date, str):
                    try:
                        due_date = datetime.fromisoformat(due_date).strftime('%B %d, %Y')
                    except:
                        due_date = str(due_date)
                elif hasattr(due_date, 'strftime'):
                    due_date = due_date.strftime('%B %d, %Y')
            
            info_data = [
                ['Invoice Number:', invoice_data.get('invoice_number', '')],
                ['Invoice Date:', invoice_date],
                ['Due Date:', due_date],
                ['', ''],
                ['Bill To:', invoice_data.get('client_name', '')],
            ]
            
            if invoice_data.get('client_address'):
                info_data.append(['Address:', invoice_data.get('client_address', '')])
            if invoice_data.get('client_email'):
                info_data.append(['Email:', invoice_data.get('client_email', '')])
            
            info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.97, 0.98, 0.99)),
                ('PADDING', (0, 0), (-1, -1), 12),
            ]))
            
            elements.append(info_table)
            elements.append(Spacer(1, 0.5*inch))
            
            # Line items table
            line_items_data = [['Description', 'Qty', 'Rate', 'Amount']]
            
            for item in invoice_data.get('line_items', []):
                line_items_data.append([
                    Paragraph(item.get('description', ''), self.styles['Normal']),
                    str(item.get('quantity', 1)),
                    f"${item.get('rate', 0):.2f}",
                    f"${item.get('amount', 0):.2f}"
                ])
            
            line_items_table = Table(
                line_items_data,
                colWidths=[3.5*inch, 0.8*inch, inch, inch]
            )
            
            line_items_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                # Body
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.Color(0.9, 0.9, 0.9)),
                ('TOPPADDING', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ]))
            
            elements.append(line_items_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Totals section
            subtotal = invoice_data.get('subtotal', 0)
            tax_rate = invoice_data.get('tax_rate', 0)
            tax_amount = invoice_data.get('tax_amount', 0)
            total = invoice_data.get('total', 0)
            
            totals_data = [
                ['Subtotal:', f"${subtotal:.2f}"],
            ]
            
            if tax_amount > 0:
                totals_data.append([f'Tax ({tax_rate:.2f}%):', f"${tax_amount:.2f}"])
            
            totals_data.append(['Total:', f"${total:.2f}"])
            
            totals_table = Table(totals_data, colWidths=[4.8*inch, 1.7*inch])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 14),
                ('TEXTCOLOR', (0, -1), (-1, -1), primary_color),
                ('LINEABOVE', (0, -1), (-1, -1), 2, primary_color),
                ('TOPPADDING', (0, -1), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -2), 8),
            ]))
            
            elements.append(totals_table)
            
            # Notes section
            if invoice_data.get('notes'):
                elements.append(Spacer(1, 0.5*inch))
                notes_style = ParagraphStyle(
                    'Notes',
                    parent=self.styles['Normal'],
                    fontSize=10,
                    textColor=colors.grey,
                    leftIndent=10,
                    borderWidth=1,
                    borderColor=primary_color,
                    borderPadding=10,
                    backColor=colors.Color(0.97, 0.98, 0.99)
                )
                elements.append(Paragraph(f"<b>Notes:</b> {invoice_data.get('notes', '')}", notes_style))
            
            # Build PDF
            doc.build(elements)
            return True
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
