import logging

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.db import close_db


def create_app(config_object: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app.teardown_appcontext(close_db)

    return app


