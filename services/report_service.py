"""
Automated Reporting Service for FactoryTwin 
Generates Excel-compatible CSV reports and styled PDF executive reports with ReportLab.
Includes metadata, date range filters, summary statistics, and audit logging into report_events.
"""

import csv
import io
import os
import logging
from datetime import datetime
from pathlib import Path
from database import get_db_connection
from config import Config

# ReportLab Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

class NumberedCanvas(canvas.Canvas):
    """Custom canvas that adds two-pass page numbering ('Page X of Y') and footer."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Footer line
        page_width, page_height = self._pagesize
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 30, page_width - 40, 30)

        # Footer text
        self.drawString(40, 18, f"FactoryTwin  - Confidential Factory Operations Report | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_width - 40, 18, page_text)
        self.restoreState()


def fetch_report_data(report_type: str, start_date: str = None, end_date: str = None,
                      machine_id: str = None, status: str = None, severity: str = None):
    """Query database based on report type and applied filters."""
    conn = get_db_connection()
    cursor = conn.cursor()

    params = []
    base_conditions = ["1=1"]

    if start_date:
        base_conditions.append("timestamp >= ?")
        params.append(f"{start_date} 00:00:00")
    if end_date:
        base_conditions.append("timestamp <= ?")
        params.append(f"{end_date} 23:59:59")
    if machine_id and machine_id != "ALL":
        base_conditions.append("machine_id = ?")
        params.append(machine_id)

    where_clause = " AND ".join(base_conditions)

    if report_type == "telemetry":
        query = f"""
            SELECT id, message_id, machine_id, timestamp, temperature, vibration, speed, load, status, production_count, data_source
            FROM telemetry
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT 500
        """
        cursor.execute(query, params)
        headers = ["ID", "Message ID", "Machine", "Timestamp", "Temp (°C)", "Vib (mm/s)", "RPM", "Load (%)", "Status", "Units", "Source"]
        rows = [list(r) for r in cursor.fetchall()]

    elif report_type == "production":
        query = f"""
            SELECT machine_id, MAX(production_count) - MIN(production_count) as cycle_output,
                   MAX(production_count) as current_total, AVG(speed) as avg_speed, AVG(load) as avg_load, COUNT(*) as reading_count
            FROM telemetry
            WHERE {where_clause}
            GROUP BY machine_id
        """
        cursor.execute(query, params)
        headers = ["Machine ID", "Period Net Output (Units)", "Cumulative Total", "Average RPM", "Average Load (%)", "Sample Count"]
        rows = []
        for r in cursor.fetchall():
            rows.append([
                r["machine_id"],
                r["cycle_output"] or 0,
                r["current_total"] or 0,
                round(r["avg_speed"] or 0.0, 1),
                round(r["avg_load"] or 0.0, 1),
                r["reading_count"] or 0
            ])

    elif report_type == "status_history":
        query = f"""
            SELECT id, machine_id, old_status, new_status, reason, timestamp
            FROM machine_status_history
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT 200
        """
        cursor.execute(query, params)
        headers = ["ID", "Machine ID", "Previous Status", "New Status", "Transition Reason", "Timestamp"]
        rows = [list(r) for r in cursor.fetchall()]

    elif report_type == "anomaly":
        query = f"""
            SELECT id, machine_id, timestamp, anomaly_score, is_anomaly, risk_category, detection_method, suggested_action
            FROM anomaly_predictions
            WHERE {where_clause}
        """
        if status and status != "ALL":
            query += " AND risk_category = ?"
            params.append(status)
        query += " ORDER BY timestamp DESC LIMIT 300"

        cursor.execute(query, params)
        headers = ["ID", "Machine", "Timestamp", "Score", "Is Anomaly", "Risk Category", "Method", "Action Recommendation"]
        rows = []
        for r in cursor.fetchall():
            rows.append([
                r["id"],
                r["machine_id"],
                str(r["timestamp"]),
                f"{r['anomaly_score']:.1f}",
                "YES" if r["is_anomaly"] else "NO",
                r["risk_category"],
                r["detection_method"],
                r["suggested_action"] or "N/A"
            ])

    elif report_type == "alerts":
        alert_conditions = ["1=1"]
        alert_params = []
        if start_date:
            alert_conditions.append("timestamp >= ?")
            alert_params.append(f"{start_date} 00:00:00")
        if end_date:
            alert_conditions.append("timestamp <= ?")
            alert_params.append(f"{end_date} 23:59:59")
        if machine_id and machine_id != "ALL":
            alert_conditions.append("machine_id = ?")
            alert_params.append(machine_id)
        if severity and severity != "ALL":
            alert_conditions.append("severity = ?")
            alert_params.append(severity)
        if status and status != "ALL":
            alert_conditions.append("status = ?")
            alert_params.append(status)

        query = f"""
            SELECT id, machine_id, alert_type, severity, message, timestamp, status, acknowledged_by, resolved_by, action_taken
            FROM alerts
            WHERE {" AND ".join(alert_conditions)}
            ORDER BY timestamp DESC
            LIMIT 300
        """
        cursor.execute(query, alert_params)
        headers = ["ID", "Machine", "Alert Type", "Severity", "Message", "Timestamp", "Status", "Ack By", "Resolved By", "Action Taken"]
        rows = [list(r) for r in cursor.fetchall()]

    elif report_type == "daily_summary":
        # Comprehensive aggregate summary
        query = f"""
            SELECT 
                machine_id,
                COUNT(*) as records,
                ROUND(AVG(temperature), 1) as avg_temp,
                ROUND(MAX(temperature), 1) as max_temp,
                ROUND(AVG(vibration), 2) as avg_vib,
                ROUND(MAX(vibration), 2) as max_vib,
                ROUND(AVG(load), 1) as avg_load,
                MAX(production_count) - MIN(production_count) as output_units
            FROM telemetry
            WHERE {where_clause}
            GROUP BY machine_id
        """
        cursor.execute(query, params)
        headers = ["Machine ID", "Samples", "Avg Temp (°C)", "Max Temp (°C)", "Avg Vib (mm/s)", "Max Vib (mm/s)", "Avg Load (%)", "Net Units"]
        rows = [list(r) for r in cursor.fetchall()]
    else:
        headers = ["Error"]
        rows = [["Unknown report type requested."]]

    conn.close()
    return headers, rows


def generate_csv_report(report_type: str, filters: dict, generated_by: str = "System") -> bytes:
    """Generate Excel-compatible UTF-8 CSV with Byte Order Mark (BOM)."""
    headers, rows = fetch_report_data(
        report_type=report_type,
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
        machine_id=filters.get("machine_id"),
        status=filters.get("status"),
        severity=filters.get("severity")
    )

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    # Metadata Header Block
    writer.writerow(["# FactoryTwin - Smart Factory Operations Report"])
    writer.writerow(["# Report Type:", report_type.upper()])
    writer.writerow(["# Generated At:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["# Generated By:", generated_by])
    writer.writerow(["# Applied Filters:", str(filters)])
    writer.writerow(["# Total Records:", len(rows)])
    writer.writerow([])  # Blank line separator

    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    csv_data = output.getvalue().encode("utf-8-sig")

    # Log Report Generation Event
    _log_report_event(report_type, "CSV", generated_by, str(filters), len(rows), f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    return csv_data


def generate_pdf_report(report_type: str, filters: dict, generated_by: str = "System") -> bytes:
    """Generate professionally styled executive PDF report using ReportLab."""
    headers, rows = fetch_report_data(
        report_type=report_type,
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
        machine_id=filters.get("machine_id"),
        status=filters.get("status"),
        severity=filters.get("severity")
    )

    pdf_buffer = io.BytesIO()
    # Use landscape for wide tabular reports
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569")
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )
    header_cell_style = ParagraphStyle(
        "TableHeaderCell",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    elements = []

    # Title & Subtitle
    title_text = f"FACTORYTWIN | {report_type.replace('_', ' ').upper()} REPORT"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 4))

    meta_text = (
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"<b>Operator/User:</b> {generated_by} | "
        f"<b>Target Machine:</b> {filters.get('machine_id', 'ALL')} | "
        f"<b>Date Range:</b> {filters.get('start_date', 'All Historical')} to {filters.get('end_date', 'Present')} | "
        f"<b>Records Retrieved:</b> {len(rows)}"
    )
    elements.append(Paragraph(meta_text, subtitle_style))
    elements.append(Spacer(1, 14))

    # Data Table Preparation
    if rows:
        table_data = []
        # Header Row
        header_row = [Paragraph(f"<b>{h}</b>", header_cell_style) for h in headers]
        table_data.append(header_row)

        # Truncate to first 150 rows in PDF for readability
        display_rows = rows[:150]
        for row in display_rows:
            formatted_row = [Paragraph(str(col), cell_style) for col in row]
            table_data.append(formatted_row)

        report_table = Table(table_data, repeatRows=1)
        report_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ]))
        elements.append(report_table)

        if len(rows) > 150:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<i>* Note: Displaying first 150 of {len(rows)} total records in PDF format. For the full dataset, export as CSV.</i>", subtitle_style))
    else:
        empty_msg = Paragraph("<b>No operational records found matching the specified query criteria.</b>", subtitle_style)
        elements.append(empty_msg)

    # Build PDF with custom NumberedCanvas
    doc.build(elements, canvasmaker=NumberedCanvas)
    pdf_bytes = pdf_buffer.getvalue()

    # Log Report Generation Event
    _log_report_event(report_type, "PDF", generated_by, str(filters), len(rows), f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

    return pdf_bytes


def _log_report_event(report_type: str, file_format: str, generated_by: str, filters_applied: str, record_count: int, file_name: str):
    """Save report generation activity into report_events table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO report_events (report_type, file_format, generated_by, filters_applied, record_count, file_name, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (report_type, file_format, generated_by, filters_applied, record_count, file_name, str(Config.GENERATED_REPORTS_DIR / file_name)))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to record report event: {e}")
