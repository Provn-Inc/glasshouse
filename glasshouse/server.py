from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlsplit
import webbrowser


class _ReportHandler(BaseHTTPRequestHandler):
    report: Path

    def do_GET(self):
        requested = urlsplit(self.path).path
        allowed = {"/", "/" + quote(self.report.name)}
        if requested not in allowed:
            self.send_error(404, "Report not found")
            return
        content = self.report.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(content)

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, format, *args):
        return


def create_server(report: Path | str, port: int = 0):
    report = Path(report).resolve()
    if report.suffix.lower() != ".html":
        raise ValueError("report must be an .html file")
    if not report.is_file():
        raise FileNotFoundError(report)
    handler = type("ReportHandler", (_ReportHandler,), {"report": report})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{server.server_port}/{quote(report.name)}"
    return server, url


def serve_report(report: Path | str, port: int = 0, open_browser: bool = True, browser_open=webbrowser.open):
    server, url = create_server(report, port)
    print(f"Serving {Path(report)} at {url}")
    print("Press Ctrl-C to stop.")
    if open_browser:
        browser_open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGlasshouse server stopped.")
    finally:
        server.server_close()
    return 0
