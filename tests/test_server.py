import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from glasshouse.server import create_server, serve_report


class ServerTests(unittest.TestCase):
    def test_binds_loopback_and_exposes_only_selected_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.html"
            report.write_text("<!doctype html><title>Glasshouse</title>")
            other = Path(tmp) / "secret.html"
            other.write_text("secret")
            server, url = create_server(report, 0)
            self.assertEqual(server.server_address[0], "127.0.0.1")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
                connection.request("GET", "/")
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertIn(b"Glasshouse", response.read())
                connection.request("GET", "/secret.html")
                self.assertEqual(connection.getresponse().status, 404)
            finally:
                server.shutdown(); server.server_close(); thread.join()

    def test_rejects_non_html_and_missing_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = Path(tmp) / "report.txt"; text.write_text("no")
            with self.assertRaises(ValueError):
                create_server(text, 0)
            with self.assertRaises(FileNotFoundError):
                create_server(Path(tmp) / "missing.html", 0)

    def test_serve_opens_exact_url_and_closes_after_interrupt(self):
        fake_server = Mock()
        fake_server.serve_forever.side_effect = KeyboardInterrupt
        browser = Mock()
        with patch("glasshouse.server.create_server", return_value=(fake_server, "http://127.0.0.1:4321/report.html")):
            self.assertEqual(serve_report(Path("report.html"), browser_open=browser), 0)
        browser.assert_called_once_with("http://127.0.0.1:4321/report.html")
        fake_server.server_close.assert_called_once()
