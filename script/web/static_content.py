from flask import Blueprint, send_from_directory
import os

static_content_blueprint = Blueprint('static_content', __name__)

# Get the absolute path to the landing-page directory
landing_page_dir = os.path.join(os.path.dirname(__file__), 'landing-page')

@static_content_blueprint.route('/')
def serve_landing_page():
    return send_from_directory(landing_page_dir, 'index.html')

@static_content_blueprint.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory(landing_page_dir, path)

