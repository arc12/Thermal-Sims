"""Base Flask app"""
import importlib
import logging
import os
from flask import Flask, request

from app.views import base_app
from config import Config


def create_app(test_config=None):
    """Create and configure Flask app"""

    app = Flask(__name__)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_object(Config)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_blueprint(base_app)

    # Find all Dash apps files (names ends with "_dash_app.py")
    files = [f for f in os.listdir(os.path.join(os.path.dirname(__file__), "dash_apps")) if f.endswith("_dash_app.py")]

    # Import all Dash apps and call their create_app() function
    for file in files:
        module = importlib.import_module("app.dash_apps." + file[:-3])
        app = module.create_dash(app)

    # log exceptions
    @app.errorhandler(Exception)
    def basic_error(e):
        logging.error("Error processing request to {}. Exception information follows:".format(request.path))
        logging.exception(e)
        return "An error occurred. It has been logged."

    return app
