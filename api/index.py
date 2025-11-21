from http.server import BaseHTTPRequestHandler
import asyncio
import json
from telegram import Update
from bot import create_app

app = create_app()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        update = Update.de_json(data, app.bot)
        
        asyncio.run(app.process_update(update))
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
