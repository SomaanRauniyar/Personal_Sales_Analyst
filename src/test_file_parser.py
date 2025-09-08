import unittest
from file_parser import parse_csv

class TestCSVParser(unittest.TestCase):
    def test_csv_to_dicts(self):
        import io
        csv_content = (
            "month_number,facecream,facewash\n"
            "1,2500,1500\n"
            "2,2630,1200\n"
        )
        buf = io.StringIO(csv_content)
        rows = parse_csv(buf)
        self.assertIsInstance(rows, list)
        self.assertIsInstance(rows[0], dict)
        self.assertEqual(rows[0]["month_number"], 1)  # or "1" if your parser outputs str, adjust accordingly
        self.assertIn("facecream", rows[0])
    def test_empty_csv(self):
        import io
        buf = io.StringIO("month_number,facecream,facewash\n")
        rows = parse_csv(buf)
        self.assertEqual(rows, [])
