import flask

from flask import Blueprint

from scanner.interactions import ReceiptInteractions


resources = Blueprint("api", __name__, url_prefix="/api")


def receipt_interactions():
    return ReceiptInteractions(**flask.current_app.repositories)


@resources.route("/scan/", methods=["POST"])
def scan():
    if not flask.request.content_type.startswith("multipart/form-data"):
        return {"message": "Invalid content type"}, 400

    if not flask.request.files.get("file"):
        return {"message": "Invalid model file"}, 400

    return receipt_interactions().scan(flask.request.files.get("file"))
