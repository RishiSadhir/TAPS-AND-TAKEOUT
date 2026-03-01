import logging
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

from .routes.admin import admin_bp
from .routes.public import public_bp
from .storage import create_store


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[], storage_uri="memory://")


def create_app():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app = Flask(
        __name__,
        template_folder=os.path.join(root_dir, "templates"),
        static_folder=os.path.join(root_dir, "static"),
        static_url_path="/static",
    )
    app.secret_key = require_env("FLASK_SECRET_KEY")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
    app.extensions["content_store"] = create_store()

    csrf.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    limiter.limit("10 per minute", exempt_when=lambda: app.config.get("TESTING", False))(app.view_functions["admin.admin_login"])

    return app
