import requests as r
from flask import request, Response, make_response
from helpers.verify_jwt import verify_jwt
from helpers.status_codes import code
from google.cloud import client
from helpers.auth0 import auth0_app


class AuthController:
    def __init__(self, client: client) -> None:
        self.client: client = client
        self.client_id = auth0_app.client_id
        self.client_secret = auth0_app.client_secret
        self.domain = auth0_app.domain
        self.kind = "users"

    def login(self, req: request) -> Response:
        body = {
            "grant_type": "password",
            "username": req.get_json().get("username"),
            "password": req.get_json().get("password"),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"content_type": "application/json"}
        auth0_res = r.post(
            f"https://{self.domain}/oauth/token", json=body, headers=headers
        )
        res = make_response(auth0_res.json())
        res.status_code = code.ok
        res.content_type = "application/json"
        return res

    def decode(self, req: request) -> Response:
        payload = verify_jwt(req, self.domain, self.client_id)
        res = make_response(payload)
        res.status_code = code.ok
        return res
