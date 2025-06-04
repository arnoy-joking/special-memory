from http.server import BaseHTTPRequestHandler
from app import app as flask_app
import os

class VercelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        os.environ['SCRIPT_NAME'] = ''
        from wsgi import VercelWSGI
        VercelWSGI(flask_app)(self)
