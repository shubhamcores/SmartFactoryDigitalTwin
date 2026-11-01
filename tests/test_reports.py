"""
Unit Tests for CSV and PDF Report Generation (P_307)
"""

import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.report_service import generate_csv_report, generate_pdf_report, fetch_report_data
from database import init_db

class TestReports(unittest.TestCase):
    """Test suite for operational report extraction, CSV formatting, and ReportLab PDF output."""

    @classmethod
    def setUpClass(cls):
        init_db(force_recreate=False)

    def test_fetch_report_data_telemetry(self):
        """Verify fetch_report_data returns valid headers and list rows."""
        headers, rows = fetch_report_data(report_type="telemetry")
        self.assertIn("Machine", headers)
        self.assertIn("Timestamp", headers)
        self.assertIsInstance(rows, list)

    def test_generate_csv_report_with_bom(self):
        """Verify CSV export starts with UTF-8 BOM bytes (\\xef\\xbb\\xbf) for Excel compatibility."""
        filters = {"machine_id": "ALL", "start_date": "", "end_date": ""}
        csv_bytes = generate_csv_report("telemetry", filters, generated_by="TestRunner")

        self.assertIsInstance(csv_bytes, bytes)
        self.assertTrue(csv_bytes.startswith(b"\xef\xbb\xbf"), "CSV missing UTF-8 BOM for Excel.")
        csv_text = csv_bytes.decode("utf-8-sig")
        self.assertIn("# Report Type:,TELEMETRY", csv_text)

    def test_generate_pdf_report_valid_header(self):
        """Verify PDF export generates valid binary output starting with PDF magic bytes (%PDF-)."""
        filters = {"machine_id": "ALL", "start_date": "", "end_date": ""}
        pdf_bytes = generate_pdf_report("telemetry", filters, generated_by="TestRunner")

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"), "Generated file does not match PDF binary specification.")
        self.assertGreater(len(pdf_bytes), 1000)

    def test_report_types_coverage(self):
        """Verify all 6 report categories generate without throwing exceptions."""
        categories = ["telemetry", "production", "status_history", "anomaly", "alerts", "daily_summary"]
        filters = {"machine_id": "ALL"}

        for cat in categories:
            headers, rows = fetch_report_data(cat)
            self.assertGreater(len(headers), 0, f"Headers empty for report category: {cat}")
            csv_b = generate_csv_report(cat, filters)
            self.assertGreater(len(csv_b), 100)
            pdf_b = generate_pdf_report(cat, filters)
            self.assertGreater(len(pdf_b), 1000)

if __name__ == "__main__":
    unittest.main()
