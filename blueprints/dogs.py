from typing import Union
from flask import Blueprint, Response, request
from controllers.dogs import DogController
from controllers.users import UserController
from controllers.toys import ToyController
from helpers.verify_jwt import verify_jwt, AuthError
from helpers.make_res import build_response
from helpers.status_codes import code
from google.cloud import datastore
from helpers.auth0 import auth0_app
from datetime import date
from helpers.exceptions import IdError, ParamError

bp = Blueprint("dog", __name__, url_prefix="/dogs")
client = datastore.Client()
dc = DogController(client)
uc = UserController(client)
tc = ToyController(client)


@bp.route("/", methods=["POST", "GET"])
def dogs() -> Response:
    if not request.accept_mimetypes.accept_json:
        return build_response(
            {"Error": "I can only respond with application/json"}, code.not_acceptable
        )
    try:
        payload = verify_jwt(
            request, client_id=auth0_app.client_id, domain=auth0_app.domain
        )
    except AuthError as e:
        return build_response(e.error, e.status_code)

    if request.method == "GET":
        return dc.get_dogs(request, payload)

    if request.method == "POST":
        # verify dog can be created
        try:
            test_build(payload)
        except ParamError as e:
            return build_response(e.error, e.status_code)

        return dc.post_one(request, payload, uc)


@bp.route("/<int:dog_id>", methods=["GET", "DELETE", "PATCH", "PUT"])
def one_dog(dog_id: int) -> Response:
    if not request.accept_mimetypes.accept_json:
        return build_response(
            {"Error": "I can only respond with application/json"}, code.not_acceptable
        )
    try:
        payload = verify_jwt(
            request, client_id=auth0_app.client_id, domain=auth0_app.domain
        )
    except AuthError as e:
        return build_response(e.error, e.status_code)

    # verify a dog with dog_id exists
    try:
        test_dog = dc.get_obj_by_id(dog_id)
    except IdError as e:
        return build_response(e.error, e.status_code)

    # verify owner match
    owner_oauth_id = payload["sub"]

    if owner_oauth_id != test_dog.owner_id:
        return build_response({"Error": "Not Authorized"}, code.unauthorized)

    if request.method == "GET":
        return dc.get_one(request, dog_id)
    elif request.method == "PATCH":
        return dc.update(request, dog_id)
    elif request.method == "PUT":
        # verify request body
        try:
            test_build(payload)
        except Exception as e:
            return build_response({"Error": str(e)}, code.not_acceptable)
        return dc.replace(request, owner_oauth_id, dog_id)

    elif request.method == "DELETE":
        return dc.delete(dog_id, tc, uc)


@bp.route("/<int:dog_id>/toys", methods=["GET"])
def toys(dog_id: int):
    if not request.accept_mimetypes.accept_json:
        return build_response(
            {"Error": "I can only respond with application/json"}, code.not_acceptable
        )
    owner_id, err = verify_owner(request)
    if err:
        return err

    # verify that dog exists
    try:
        dog = dc.get_obj_by_id(dog_id)
    except IdError as e:
        return build_response(e.error, e.status_code)

    if dog.owner_id != owner_id:
        return build_response({"Error": "Not Authorized"}, code.forbidden)

    if request.method == "GET":
        toy_list = dog.toys
        for i, toy in enumerate(toy_list):
            toy_list[i] = {"id": toy, "self": f"{request.url_root}toys/{toy}"}
        return build_response(toy_list, code.ok)


@bp.route("/<int:dog_id>/toys/<int:toy_id>", methods=["DELETE", "POST"])
def dog_has_toys(dog_id: int, toy_id: int):
    if not request.accept_mimetypes.accept_json:
        return build_response(
            {"Error": "I can only respond with application/json"}, code.not_acceptable
        )
    owner_id, err = verify_owner(request)
    if err:
        return err

    # verify that dog exists
    try:
        dog = dc.get_obj_by_id(dog_id)
    except IdError as e:
        return build_response(e.error, e.status_code)
    # verify that toy exists
    try:
        toy = tc.get_obj_by_id(toy_id)
    except Exception as e:
        if isinstance(e, IdError):
            return build_response(e.error, e.status_code)
        else:
            return build_response(
                {
                    "Error": "Could not validate that toy. Check documentation and request."
                },
                code.not_acceptable,
            )

    if request.method == "POST":
        if toy.in_use:
            return build_response(
                {"Error": "That toy is already in use"}, code.forbidden
            )
        elif owner_id != dog.owner_id:
            return build_response({"Error": "Not Authorized"}, code.forbidden)
        return dc.give_toy(dog, toy, tc)
    elif request.method == "DELETE":
        if dog.id != toy.used_by:
            return build_response(
                {"Error": "That dog does not have that toy"}, code.forbidden
            )
        elif owner_id != dog.owner_id:
            return build_response(
                {"Error": "Only the dog's owner can take a toy from it"}, code.forbidden
            )

        return dc.take_toy(dog, toy, tc)


def test_build(payload: dict) -> None:
    data = dict(request.get_json())
    data["adoption_date"] = date.today().strftime("%m/%d/%y")
    data["owner_id"] = payload.get("sub")
    data["owner_name"] = payload.get("name")
    dc.build_entity(data)


def verify_owner(req: request) -> tuple[str, Union[None, Response]]:
    owner_id = ""
    err: Union[None, Response] = None
    try:
        payload = verify_jwt(
            req, client_id=auth0_app.client_id, domain=auth0_app.domain
        )
        owner_id = payload["sub"]
    except AuthError as e:
        err: Response = build_response(e.error, e.status_code)

    return owner_id, err
