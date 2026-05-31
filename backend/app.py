from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify

from backend.config import BASE_DIR, Config
from backend.models import db
from backend.routes import bp
from backend.time_utils import format_local_datetime


def configure_logging(app: Flask) -> None:
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / "usbshadow.log", maxBytes=2_000_000, backupCount=5
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    handler.setLevel(app.config["LOG_LEVEL"])
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config["LOG_LEVEL"])


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "dashboard" / "templates"),
        static_folder=str(BASE_DIR / "dashboard" / "static"),
    )
    app.config.from_object(config_object)
    configure_logging(app)
    db.init_app(app)
    app.register_blueprint(bp)

    @app.context_processor
    def inject_time_settings():
        return {"app_timezone": app.config["APP_TIMEZONE"]}

    @app.template_filter("localtime")
    def localtime_filter(value, fmt="%Y-%m-%d %H:%M:%S"):
        return format_local_datetime(value, app.config["APP_TIMEZONE"], fmt)

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "bad_request", "message": str(error.description)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "not_found", "message": "Resource not found"}), 404

    @app.errorhandler(Exception)
    def server_error(error):
        app.logger.exception("Unhandled exception")
        return jsonify({"error": "server_error", "message": "Internal server error"}), 500

    with app.app_context():
        db.create_all()
        for directory in ("evidence", "logs", "screenshots"):
            Path(BASE_DIR / directory).mkdir(exist_ok=True)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
