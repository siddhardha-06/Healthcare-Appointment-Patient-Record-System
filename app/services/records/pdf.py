"""Prescription PDF (HAP-F-042) using ReportLab."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

CLINIC = "HAP Clinic – Healthcare Appointment & Patient Record System"


def prescription_pdf(rx: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm,
                            title=f"Prescription {rx['prescription_id']}")
    st = getSampleStyleSheet()
    story = [Paragraph(CLINIC, st["Title"]),
             Paragraph(f"<b>Doctor:</b> {rx['doctor']} &nbsp;&nbsp; <b>Date:</b> {rx['date']:%d-%m-%Y}", st["Normal"]),
             Paragraph(f"<b>Patient:</b> {rx['patient_name']} &nbsp;&nbsp; <b>MRN:</b> {rx['patient_mrn']}", st["Normal"]),
             Spacer(1, 6 * mm)]
    rows = [["#", "Medicine", "Dosage", "Frequency", "Days", "Instructions"]]
    for i, it in enumerate(rx["items"], 1):
        rows.append([str(i), it["medicine"], it["dosage"], it["frequency"], str(it["duration_days"]), it.get("instructions") or ""])
    table = Table(rows, colWidths=[8 * mm, 45 * mm, 25 * mm, 32 * mm, 12 * mm, 52 * mm], repeatRows=1)
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBE5F1")),
                               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [table, Spacer(1, 12 * mm), Paragraph("Signature: ____________________", st["Normal"])]
    doc.build(story)
    return buf.getvalue()
