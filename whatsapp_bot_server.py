import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import local Q&A engine
from whatsapp_engine import process_whatsapp_query

PORT = int(os.environ.get("PORT", 8080))

class WhatsAppRequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, content_type, body_str, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body_str.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(body_str.encode('utf-8'))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self._send_response("application/json", json.dumps({"status": "ok", "service": "DU 5th Grade WhatsApp Bot"}))
        elif parsed.path == "/api/query":
            params = urllib.parse.parse_qs(parsed.query)
            query = params.get('q', ['!help'])[0]
            reply = process_whatsapp_query(query)
            self._send_response("application/json", json.dumps({"query": query, "reply": reply}))
        else:
            welcome_msg = (
                "🤖 DU 5th Grade WhatsApp Parent Bot Server is Running!\n"
                "Endpoints:\n"
                "  • GET /api/query?q=what+is+due+tomorrow\n"
                "  • POST /webhook (JSON or Twilio form-data)\n"
            )
            self._send_response("text/plain", welcome_msg)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        content_type = self.headers.get('Content-Type', '')

        user_query = "!help"
        is_twilio = False

        if "application/json" in content_type:
            try:
                data = json.loads(post_data)
                user_query = data.get('query') or data.get('message') or data.get('Body') or "!help"
            except Exception as e:
                print(f"[SERVER ERROR] JSON parse error: {e}")
        else:
            # Assume form-urlencoded (Twilio standard)
            parsed_params = urllib.parse.parse_qs(post_data)
            if 'Body' in parsed_params:
                is_twilio = True
                user_query = parsed_params['Body'][0]
            elif 'query' in parsed_params:
                user_query = parsed_params['query'][0]

        print(f"[WHATSAPP BOT] Received query: '{user_query}'")
        reply = process_whatsapp_query(user_query)

        if is_twilio:
            # Return TwiML XML
            twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply}</Message></Response>'
            self._send_response("application/xml", twiml)
        else:
            # Return JSON
            self._send_response("application/json", json.dumps({"reply": reply, "query": user_query}))

def run_server(port=PORT):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WhatsAppRequestHandler)
    print(f"============================================================")
    print(f"🤖 DU 5th Grade WhatsApp Bot HTTP Server listening on port {port}...")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
