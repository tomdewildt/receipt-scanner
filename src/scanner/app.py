from flask import Flask
from werkzeug.exceptions import HTTPException

from scanner.repositories import OpenCVRepository, TesseractRepository
from scanner.resources import resources


def create_app():
    # Create app
    app = Flask(__name__)

    # Register resources
    app.register_blueprint(resources)

    # Register health
    @app.route("/api/health/")
    def default_health():
        return {"status": "OK"}

    # Register errors
    @app.errorhandler(HTTPException)
    def default_handler(error):
        return {"message": error.name}, error.code

    # Create repositories
    setattr(
        app,
        "repositories",
        {
            "image_repository": OpenCVRepository(),
            "ocr_repository": TesseractRepository(),
        },
    )

    return app
