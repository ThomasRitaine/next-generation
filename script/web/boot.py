from flask import Flask
from waitress import serve
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('APP_SECRET_KEY')

    # Import and register blueprints or routes
    with app.app_context():
        from web.static_content import static_content_blueprint
        from web.tiktok_oauth_handler import tiktok_oauth_blueprint

        app.register_blueprint(static_content_blueprint)
        app.register_blueprint(tiktok_oauth_blueprint)

    return app

def boot_web_server():
    app = create_app()
    serve(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    boot_web_server()

