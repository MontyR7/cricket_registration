from waitress import serve
from app import app

if __name__ == '__main__':
    # Production settings
    serve(
        app,
        host='0.0.0.0',  # Listen on all available network interfaces
        port=8080,       # Use port 8080 for production
        threads=4,       # Number of threads to handle requests
        url_scheme='http'
    )