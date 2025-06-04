def write(handler, data):
    handler.wfile.write(data)

class VercelWSGI:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, handler):
        from io import BytesIO
        
        environ = {
            'REQUEST_METHOD': handler.command,
            'PATH_INFO': handler.path,
            'QUERY_STRING': handler.query,
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.url_scheme': 'https',
            'wsgi.input': BytesIO(),
            'wsgi.errors': handler.wfile,
            'wsgi.version': (1, 0),
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False
        }
        
        def start_response(status, headers):
            handler.send_response(int(status.split()[0]))
            for header, value in headers:
                handler.send_header(header, value)
            handler.end_headers()
            return write
        
        result = self.app(environ, start_response)
        try:
            for data in result:
                if data:
                    handler.wfile.write(data)
        finally:
            if hasattr(result, 'close'):
                result.close()
