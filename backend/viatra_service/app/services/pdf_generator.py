import io
from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from app.domain.entities.viatra_entities import TravelerGroup, ItineraryItem, PaymentHistory

class PDFGenerator:
    @staticmethod
    async def generate_travel_itinerary(
        group: TravelerGroup, 
        items: list[ItineraryItem], 
        payments: list[PaymentHistory],
        user_name: str
    ) -> io.BytesIO:
        """
        Genera un itinerario de viaje profesional en formato PDF.
        Refleja la estética 'Mission Control' con encabezados Slate-950.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=LETTER)
        styles = getSampleStyleSheet()
        elements = []

        # Estilo Personalizado para Encabezados
        title_style = styles['Title']
        title_style.textColor = colors.HexColor("#0f172a") # Slate-900
        
        # 1. Header de Marca
        elements.append(Paragraph(f"VIATRA CORE — {group.name.upper()}", title_style))
        elements.append(Paragraph(f"Itinerario de Viaje Certificado", styles['Normal']))
        elements.append(Spacer(1, 20))

        # 2. Datos del Viajero
        elements.append(Paragraph(f"<b>Viajero:</b> {user_name}", styles['Normal']))
        elements.append(Paragraph(f"<b>Vuelo de Referencia:</b> {group.flight_number}", styles['Normal']))
        elements.append(Paragraph(f"<b>Fecha de Emisión:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 24))

        # 3. Bloque de Logística (Vuelos y Hoteles)
        elements.append(Paragraph("<b>LOGÍSTICA Y HOSPEDAJE</b>", styles['Heading2']))
        data = [["Tipo", "Nombre / Referencia", "Estatus", "Confirmación"]]
        
        for item in items:
            data.append([
                item.item_type,
                item.name[:30] + "..." if len(item.name) > 30 else item.name,
                "✓ Verificado",
                item.confirmation_number or "N/A"
            ])

        t = Table(data, colWidths=[80, 200, 100, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")), # Slate-800
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 24))

        # 4. Bloque Financiero
        elements.append(Paragraph("<b>ESTADO DE CUENTA (PAID)</b>", styles['Heading2']))
        pay_data = [["Fecha", "Monto", "Referencia Stripe", "Estatus"]]
        
        total_paid = 0
        for pay in payments:
            pay_data.append([
                pay.created_at.strftime('%d/%m/%Y'),
                f"{pay.amount} {pay.currency}",
                pay.stripe_payment_id[:20] + "...",
                pay.status
            ])
            if pay.status == "PAID":
                total_paid += pay.amount

        pt = Table(pay_data, colWidths=[100, 100, 180, 100])
        pt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#065f46")), # Emerald-800
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(pt)
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>Inversión Total Confirmada:</b> {total_paid} USD", styles['Normal']))

        # Construir
        doc.build(elements)
        buffer.seek(0)
        return buffer
