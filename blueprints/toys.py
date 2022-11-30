from flask import Blueprint, Response, request, make_response
from controllers.toys import ToyController
from controllers.users import UserController
from controllers.dogs import DogController
from helpers.verify_jwt import verify_jwt, AuthError
from helpers.make_res import build_response
from google.cloud import datastore
from helpers.auth0 import auth0_app
from helpers.exceptions import IdError, ParamError
from models.toys import Toy

bp = Blueprint('toy', __name__, url_prefix='/toys')
client = datastore.Client()
tc = ToyController(client)
uc = UserController(client)


@bp.route('/', methods=['GET', 'POST'])
def toys() -> Response:
    # anybody can view toys
    if request.method == 'GET':
        return tc.get_toys(request, uc)

    # check jwt for further actions
    try:
        payload = verify_jwt(request, client_id=auth0_app.client_id, domain=auth0_app.domain)
    except AuthError as e:
        return build_response(e.error, e.status_code)

    if request.method == 'POST':
        try:
            test_build(payload)
        except ParamError as e:
            return build_response(e.error, e.status_code)
        return tc.post_one(request, payload)


@bp.route('/<int:_id>', methods=['GET', 'DELETE', 'PUT', 'PATCH'])
def toy(_id: int) -> Response:
    # no jwt verification to view a single toy
    # verify that toy with toy_id exists
    try:
        tc.get_obj_by_id(_id)
    except IdError as e:
        return build_response(e.error, e.status_code)

    if request.method == 'GET':
        return tc.get_one(request, _id)

    # check jwt for further actions
    try:
        payload = verify_jwt(request, client_id=auth0_app.client_id, domain=auth0_app.domain)
    except AuthError as e:
        return build_response(e.error, e.status_code)

    # verify requester is the purchaser of the toy
    purchaser_id = payload['sub']
    if purchaser_id != tc.get_obj_by_id(_id).purchased_by:
        return build_response('Not authorized', 401)

    if request.method == 'DELETE':
        return tc.delete(_id)
    elif request.method == 'PATCH':
        return tc.update(request, _id)
    elif request.method == 'PUT':
        return tc.replace(request, purchaser_id, _id)


def test_build(payload: dict) -> None:
    data = dict(request.get_json())
    data['purchased_by'] = payload['sub']
    tc.build_entity(data)
