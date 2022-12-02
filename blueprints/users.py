from flask import Blueprint, Response, request
from controllers.users import UserController
from google.cloud import datastore
from helpers.exceptions import IdError
from helpers.status_codes import code
from helpers.make_res import build_response

bp = Blueprint("user", __name__, url_prefix="/users")
client = datastore.Client()
uc = UserController(client)


@bp.route("/")
def users() -> Response:
    if not request.accept_mimetypes.accept_json:
        return build_response(
            {"Error": "I can only respond with application/json"}, code.not_acceptable
        )
    return uc.get_all(request)


@bp.route("/<int:_id>")
def user(_id: int) -> Response:
    if not request.accept_mimetypes.accept_json:
        return build_response(
            {"Error": "I can only respond with application/json"}, code.not_acceptable
        )
    # verify that a user with that id exists
    try:
        uc.get_obj_by_id(_id)
    except IdError as e:
        return build_response(e.error, e.status_code)
    return uc.get_one(request, _id)
