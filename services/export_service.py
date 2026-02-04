import io
import csv
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

class ExportService:
    @staticmethod
    def generate_csv(data, headers):
        """
        Generates a CSV string from a list of lists.
        :param data: List of lists (rows)
        :param headers: List of strings (header row)
        :return: bytes (CSV content encoded in utf-8)
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write Header
        writer.writerow(headers)

        # Write Rows
        for row in data:
            writer.writerow(row)

        output.seek(0)
        # Add BOM for Excel compatibility with UTF-8
        return b'\xef\xbb\xbf' + output.getvalue().encode('utf-8')

    @staticmethod
    def generate_pdf(data, headers, title, subtitle=None):
        """
        Generates a PDF bytes from a list of lists.
        :param data: List of lists (rows)
        :param headers: List of strings (header row)
        :param title: Title of the document
        :return: bytes (PDF content)
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()

        # Header with Logo (if possible, but text for now as per requirement "SGI-GP RDC")
        elements.append(Paragraph("SGI-GP RDC - Système de Gestion Intégrée", styles['Title']))
        elements.append(Paragraph(f"{title}", styles['Heading2']))
        if subtitle:
            elements.append(Paragraph(subtitle, styles['Normal']))
        elements.append(Paragraph(f"Date de l'export: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Table Data
        # Ensure data strings are cleaned for PDF (e.g. None -> "")
        cleaned_data = []
        for row in data:
            cleaned_row = [str(cell) if cell is not None else "" for cell in row]
            cleaned_data.append(cleaned_row)

        table_data = [headers] + cleaned_data

        # Create Table
        # Auto-calculate column widths if needed, but standard Table usually adapts.
        # If too many columns, might need adjustments. For now, standard Table.
        t = Table(table_data)

        # Style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.6)), # Dark Blue Header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])

        t.setStyle(style)

        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
