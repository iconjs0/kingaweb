#!/usr/bin/env python3
"""Small, dependency-free development server and low-impact KingaWeb scanner."""

from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import socket
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

HOST, PORT = "127.0.0.1", 8080
HEADERS = {
    "Content-Security-Policy": "Helps reduce cross-site scripting and content injection risk.",
    "Strict-Transport-Security": "Tells browsers to keep using secure HTTPS connections.",
    "X-Content-Type-Options": "Prevents browsers from guessing unsafe content types.",
    "Referrer-Policy": "Controls how much referral information leaves the website.",
    "Permissions-Policy": "Restricts access to sensitive browser capabilities.",
}


def public_addresses(hostname):
    """Resolve and reject every non-public result to reduce SSRF risk."""
    addresses = {row[4][0] for row in socket.getaddrinfo(hostname, None)}
    if not addresses:
        raise ValueError("The domain could not be resolved.")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError("Only publicly reachable websites can be checked.")
    return sorted(addresses)


def certificate_check(hostname):
    context = ssl.create_default_context()
    started = time.monotonic()
    with socket.create_connection((hostname, 443), timeout=6) as raw:
        with context.wrap_socket(raw, server_hostname=hostname) as secure:
            certificate = secure.getpeercert()
            protocol = secure.version()
    expires = datetime.strptime(certificate["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    days = max(0, (expires - datetime.now(timezone.utc)).days)
    return protocol, days, round((time.monotonic() - started) * 1000)


def scan(raw_domain):
    value = raw_domain.strip()
    if not value:
        raise ValueError("Enter a website address.")
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a valid HTTP or HTTPS website.")
    if parsed.username or parsed.password or parsed.port not in {None, 80, 443}:
        raise ValueError("Credentials and custom ports are not supported.")

    host = parsed.hostname.rstrip(".").lower()
    addresses = public_addresses(host)
    target = f"https://{host}/"
    request = Request(target, headers={"User-Agent": "KingaWeb-Security-Monitor/0.1"}, method="GET")
    started = time.monotonic()
    try:
        response = urlopen(request, timeout=8)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError, ssl.SSLError) as error:
        raise ValueError(f"Could not establish a trusted HTTPS connection: {error.reason if hasattr(error, 'reason') else error}")
    elapsed = round((time.monotonic() - started) * 1000)
    final = urlparse(response.geturl())
    if final.hostname != host:
        public_addresses(final.hostname)

    protocol, days, tls_ms = certificate_check(host)
    checks = [
        {"name": "HTTPS", "status": "pass", "label": "Protected", "detail": f"A trusted HTTPS connection was established using {protocol}."},
        {"name": "TLS certificate", "status": "pass" if days > 14 else "caution", "label": f"{days} days left", "detail": "Renew before expiry to prevent browser security warnings."},
        {"name": "Availability", "status": "pass" if response.status < 500 else "fail", "label": f"HTTP {response.status}", "detail": f"The website responded in {elapsed} ms (TLS handshake: {tls_ms} ms)."},
        {"name": "Public address", "status": "pass", "label": "Resolved", "detail": f"Domain resolves to {len(addresses)} public address{'es' if len(addresses) != 1 else ''}."},
    ]
    earned = 55
    for name, guidance in HEADERS.items():
        present = bool(response.headers.get(name))
        checks.append({"name": name, "status": "pass" if present else "caution", "label": "Present" if present else "Missing", "detail": guidance})
        earned += 9 if present else 0
    score = min(100, earned)
    summary = "Strong foundation" if score >= 85 else "Improvements recommended" if score >= 60 else "Needs attention"
    return {"host": host, "score": score, "summary": summary, "checks": checks}


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/scan":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 4096:
                raise ValueError("Invalid request size.")
            body = json.loads(self.rfile.read(length))
            result = scan(str(body.get("domain", "")))
            self.send_json(200, result)
        except (ValueError, json.JSONDecodeError, socket.gaierror) as error:
            self.send_json(400, {"error": str(error)})
        except Exception:
            self.send_json(502, {"error": "The website could not be checked safely right now."})

    def send_json(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    print(f"KingaWeb is running at http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
