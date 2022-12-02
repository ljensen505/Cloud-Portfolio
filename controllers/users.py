from typing import Union
from flask import Response, request
from google.cloud import client as gcc, datastore
from controllers.parent_controller import Controller
from helpers.make_res import build_response
from helpers.status_codes import code
from models.users import User


class UserController(Controller):
    def __init__(self, client: gcc) -> None:
        Controller.__init__(self, client)
        self.kind = "users"

    def get_by_user_id(self, user_id: str) -> User:
        query = self.client.query(kind=self.kind)
        query.add_filter("user_id", "=", user_id)
        result = list(query.fetch())[0]
        user = self.build_entity(result, _id=result.key.id)
        return user

    def get_all(self, req: request, dc=None) -> Union[Response, list]:
        users = super(UserController, self).get_all(req, self.kind)
        return build_response(users, code.ok)

    def add_user(self, user: User) -> None:
        with self.client.transaction():
            incomplete_key = self.client.key(self.kind)
            ds_user = datastore.Entity(key=incomplete_key)
            ds_user.update(
                {
                    "name": user.name,
                    "email": user.email,
                    "user_id": user.user_id,
                    "dogs": user.dogs,
                }
            )
            self.client.put(ds_user)
        user.id = ds_user.key.id

    def process_user(self, user_info: dict) -> None:
        user = User(
            name=user_info["name"], email=user_info["email"], user_id=user_info["sub"]
        )

        # query for pre-existing user
        query = self.client.query(kind=self.kind)
        query.add_filter("user_id", "=", user.user_id)
        results = list(query.fetch())

        if not results:
            self.add_user(user)
        else:
            user.dogs = results[0]["dogs"]
            user.id = results[0].key.id

    @classmethod
    def build_entity(cls, data, _id=None) -> User:
        return User(
            name=data.get("name"),
            email=data.get("email"),
            user_id=data.get("user_id"),
            dogs=data.get("dogs"),
            id=_id,
        )
