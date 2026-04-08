# core/export_service.py
"""
Unified Export Center Service
Export data in multiple formats (CSV, PDF, JSON, Excel)
"""

import csv
import json
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from decimal import Decimal
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

from django.utils import timezone
from django.template.loader import render_to_string
from django.http import HttpResponse

from .models import Farm, CropSeason, Animal, EquipmentBooking, Transaction


class ExportService:
    """Service for exporting data in various formats"""
    
    EXPORT_FORMATS = ['csv', 'json', 'pdf', 'xlsx', 'html']
    
    DATA_TYPES = [
        ('crops', 'Crop Data'),
        ('livestock', 'Livestock Data'),
        ('equipment', 'Equipment Rentals'),
        ('financial', 'Financial Data'),
        ('labor', 'Labor Records'),
        ('pest_reports', 'Pest Reports'),
        ('insurance', 'Insurance Policies'),
        ('all', 'All Data'),
    ]
    
    @staticmethod
    def export_crops(
        farm: Farm,
        start_date: datetime = None,
        end_date: datetime = None,
        format: str = 'csv'
    ) -> Tuple[HttpResponse, str]:
        """Export crop data"""
        
        if start_date is None:
            start_date = timezone.now() - timedelta(days=365)
        if end_date is None:
            end_date = timezone.now()
        
        crops = CropSeason.objects.filter(
            field__farm=farm,
            planting_date__gte=start_date,
            planting_date__lte=end_date
        ).select_related('crop_type', 'field')
        
        data = []
        for crop in crops:
            data.append({
                'field_name': crop.field.name,
                'crop_type': crop.crop_type.name,
                'variety': crop.variety,
                'season': crop.get_season_display(),
                'planting_date': crop.planting_date.isoformat(),
                'harvest_date': crop.expected_harvest_date.isoformat(),
                'actual_harvest_date': crop.actual_harvest_date.isoformat() if crop.actual_harvest_date else '',
                'status': crop.get_status_display(),
                'estimated_yield_kg': float(crop.estimated_yield_kg or 0),
                'actual_yield_kg': float(crop.actual_yield_kg or 0),
                'estimated_revenue': float(crop.estimated_revenue or 0),
                'actual_revenue': float(crop.actual_revenue or 0),
            })
        
        return ExportService._format_export(data, format, 'crop_data')
    
    @staticmethod
    def export_livestock(
        farm: Farm,
        start_date: datetime = None,
        end_date: datetime = None,
        format: str = 'csv'
    ) -> Tuple[HttpResponse, str]:
        """Export livestock data"""
        
        if start_date is None:
            start_date = timezone.now() - timedelta(days=365)
        if end_date is None:
            end_date = timezone.now()
        
        animals = Animal.objects.filter(
            farm=farm,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('animal_type')
        
        data = []
        for animal in animals:
            data.append({
                'tag_number': animal.tag_number,
                'name': animal.name,
                'species': animal.animal_type.get_species_display(),
                'breed': animal.animal_type.breed,
                'gender': animal.get_gender_display(),
                'birth_date': animal.birth_date.isoformat() if animal.birth_date else '',
                'purchase_date': animal.purchase_date.isoformat() if animal.purchase_date else '',
                'purchase_price': float(animal.purchase_price or 0),
                'weight_kg': float(animal.weight_kg or 0),
                'status': animal.get_status_display(),
                'location': animal.location,
            })
        
        return ExportService._format_export(data, format, 'livestock_data')
    
    @staticmethod
    def export_financial(
        farm: Farm,
        start_date: datetime = None,
        end_date: datetime = None,
        format: str = 'csv'
    ) -> Tuple[HttpResponse, str]:
        """Export financial data"""
        
        if start_date is None:
            start_date = timezone.now() - timedelta(days=365)
        if end_date is None:
            end_date = timezone.now()
        
        transactions = Transaction.objects.filter(
            farm=farm,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('-created_at')
        
        data = []
        total_income = Decimal('0.00')
        total_expense = Decimal('0.00')
        
        for transaction in transactions:
            amount = float(transaction.amount)
            
            if transaction.transaction_type == 'income':
                total_income += transaction.amount
            else:
                total_expense += transaction.amount
            
            data.append({
                'date': transaction.created_at.date().isoformat(),
                'type': transaction.get_transaction_type_display(),
                'category': transaction.get_category_display(),
                'description': transaction.description,
                'amount': amount,
                'notes': transaction.notes,
            })
        
        # Add summary
        data.append({
            'date': '',
            'type': 'SUMMARY',
            'category': '',
            'description': 'Total Income',
            'amount': float(total_income),
            'notes': ''
        })
        data.append({
            'date': '',
            'type': 'SUMMARY',
            'category': '',
            'description': 'Total Expense',
            'amount': float(total_expense),
            'notes': ''
        })
        data.append({
            'date': '',
            'type': 'SUMMARY',
            'category': '',
            'description': 'Net Profit',
            'amount': float(total_income - total_expense),
            'notes': ''
        })
        
        return ExportService._format_export(data, format, 'financial_data')
    
    @staticmethod
    def _format_export(
        data: List[Dict[str, Any]],
        format: str,
        filename_base: str
    ) -> Tuple[HttpResponse, str]:
        """Format data for export in specified format"""
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'csv':
            return ExportService._export_csv(data, f'{filename_base}_{timestamp}.csv')
        
        elif format == 'json':
            return ExportService._export_json(data, f'{filename_base}_{timestamp}.json')
        
        elif format == 'xlsx':
            return ExportService._export_xlsx(data, f'{filename_base}_{timestamp}.xlsx')
        
        elif format == 'pdf':
            return ExportService._export_pdf(data, f'{filename_base}_{timestamp}.pdf')
        
        elif format == 'html':
            return ExportService._export_html(data, f'{filename_base}_{timestamp}.html')
        
        else:
            raise ValueError(f'Unsupported format: {format}')
    
    @staticmethod
    def _export_csv(data: List[Dict], filename: str) -> Tuple[HttpResponse, str]:
        """Export to CSV"""
        
        if not data:
            data = [{}]
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response, filename
    
    @staticmethod
    def _export_json(data: List[Dict], filename: str) -> Tuple[HttpResponse, str]:
        """Export to JSON"""
        
        json_data = json.dumps(data, indent=2, default=str)
        
        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response, filename
    
    @staticmethod
    def _export_xlsx(data: List[Dict], filename: str) -> Tuple[HttpResponse, str]:
        """Export to Excel"""
        
        if not data:
            data = [{}]
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Data'
        
        # Write headers
        headers = list(data[0].keys())
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            cell.font = Font(bold=True, color='FFFFFF')
            cell.alignment = Alignment(horizontal='center')
        
        # Write data
        for row_idx, row_data in enumerate(data, 2):
            for col_idx, header in enumerate(headers, 1):
                value = row_data.get(header, '')
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                if isinstance(value, (int, float)):
                    cell.number_format = '0.00'
        
        # Auto-adjust column widths
        for col in ws.columns:
            max_length = 0
            column_letter = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response, filename
    
    @staticmethod
    def _export_pdf(data: List[Dict], filename: str) -> Tuple[HttpResponse, str]:
        """Export to PDF"""
        
        # Create PDF
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        elements = []
        
        # Title
        styles = getSampleStyleSheet()
        title = Paragraph(f"Farm Report - {timezone.now().date()}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Create table
        if data:
            headers = list(data[0].keys())
            table_data = [headers] + [[str(row.get(h, '')) for h in headers] for row in data]
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
        
        # Build PDF
        doc.build(elements)
        output.seek(0)
        
        response = HttpResponse(output.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response, filename
    
    @staticmethod
    def _export_html(data: List[Dict], filename: str) -> Tuple[HttpResponse, str]:
        """Export to HTML"""
        
        html_content = '<table border="1" cellpadding="5"><tr>'
        
        if data:
            # Headers
            for header in data[0].keys():
                html_content += f'<th>{header}</th>'
            html_content += '</tr>'
            
            # Rows
            for row in data:
                html_content += '<tr>'
                for header in data[0].keys():
                    html_content += f'<td>{row.get(header, "")}</td>'
                html_content += '</tr>'
        
        html_content += '</table>'
        
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response, filename
