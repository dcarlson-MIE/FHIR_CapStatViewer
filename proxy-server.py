#!/usr/bin/env python3
"""
FHIR CORS Proxy Server (Python)
Simple proxy to bypass CORS restrictions for FHIR CapabilityStatement requests
"""

import http.server
import urllib.request
import urllib.parse
import urllib.error
import json
import sys
from http import HTTPStatus

class CORSProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler with CORS support for FHIR proxying"""
    
    def _set_cors_headers(self):
        """Set CORS headers to allow cross-origin requests"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept')
    
    def _send_json_response(self, status_code, data):
        """Send JSON response with proper headers"""
        json_data = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data)
    
    def do_OPTIONS(self):
        """Handle preflight OPTIONS requests"""
        self.send_response(HTTPStatus.OK)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        # Parse the URL and query parameters
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Get the target URL from query parameter
        target_url = query_params.get('url', [None])[0]
        
        if not target_url:
            self._send_json_response(HTTPStatus.BAD_REQUEST, {
                'error': 'Missing url parameter'
            })
            return
        
        # Validate URL format
        try:
            parsed_url = urllib.parse.urlparse(target_url)
            if parsed_url.scheme != 'https':
                self._send_json_response(HTTPStatus.BAD_REQUEST, {
                    'error': 'Only HTTPS URLs are allowed'
                })
                return
        except Exception:
            self._send_json_response(HTTPStatus.BAD_REQUEST, {
                'error': 'Invalid URL format'
            })
            return
        
        # Fetch from the target FHIR server
        try:
            req = urllib.request.Request(
                target_url,
                headers={
                    'Accept': 'application/fhir+json, application/json',
                    'User-Agent': 'FHIR-CapabilityStatement-Viewer/1.0'
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                # Get response data
                content = response.read()
                content_type = response.headers.get('Content-Type', 'application/json')
                
                # Send successful response
                self.send_response(response.status)
                self._set_cors_headers()
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                
                # Log success
                print(f"✓ Proxied request to: {target_url} (HTTP {response.status})")
        
        except urllib.error.HTTPError as e:
            # HTTP error from target server
            print(f"✗ HTTP Error {e.code} from: {target_url}")
            self._send_json_response(e.code, {
                'error': f'FHIR server returned HTTP {e.code}',
                'details': str(e.reason)
            })
        
        except urllib.error.URLError as e:
            # Network/connection error
            print(f"✗ Connection error to: {target_url} - {e.reason}")
            self._send_json_response(HTTPStatus.BAD_GATEWAY, {
                'error': 'Failed to connect to FHIR server',
                'details': str(e.reason)
            })
        
        except Exception as e:
            # Other errors
            print(f"✗ Unexpected error: {e}")
            self._send_json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {
                'error': 'Internal server error',
                'details': str(e)
            })
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        # Only log errors, not every request
        if args[1] not in ['200', '304']:
            sys.stderr.write("%s - - [%s] %s\n" %
                           (self.address_string(),
                            self.log_date_time_string(),
                            format % args))


def run_proxy_server(port=3001):
    """Start the CORS proxy server"""
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, CORSProxyHandler)
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║  FHIR CORS Proxy Server                                    ║
║  Running on: http://localhost:{port}                     ║
║  Usage: http://localhost:{port}/proxy?url=<FHIR_URL>     ║
╚════════════════════════════════════════════════════════════╝

Press Ctrl+C to stop the server
    """)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        httpd.server_close()


if __name__ == '__main__':
    # Get port from command line or use default
    port = 3001
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    run_proxy_server(port)
