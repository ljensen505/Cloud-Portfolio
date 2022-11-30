from __future__ import annotations
from typing import TYPE_CHECKING, Union

from flask import Response, request
from google.cloud import client as gcc, datastore

from controllers.parent_controller import Controller

from helpers.make_res import build_response
from models.users import User

# from model.dogs import Dog
# from helpers.make_res import build_response
#
# if TYPE_CHECKING:
#     from controller.dogs import DogController
#     from controller.toys import ToyController

from pprint import pprint


class UserController(Controller):
    def __init__(self, client: gcc) -> None:
        Controller.__init__(self, client)
        self.kind = "users"

    # def adopt(self, dog: Dog) -> None:
    #     query = self.client.query(kind=self.kind)
    #     query.add_filter('user_id', '=', dog.owner_id)
    #     results = list(query.fetch())
    #     ds_owner = results[0]
    #     owner: User = self.build_user(ds_owner)
    #     if dog.id not in owner.dogs:
    #         owner.dogs.append(dog.id)
    #     ds_owner['dogs'] = owner.dogs
    #     self.client.put(ds_owner)

    def get_by_user_id(self, user_id: str) -> User:
        query = self.client.query(kind=self.kind)
        query.add_filter('user_id', '=', user_id)
        result = list(query.fetch())[0]
        user = self.build_entity(result, _id=result.key.id)
        return user

    def get_all(self, req: request, dc) -> Union[Response, list]:
        users = super(UserController, self).get_all(req, self.kind)
        # TODO: dc is a DogController and needs type hinting when available

        # optional change: add 'self' for each dog
        # for user in users:
        #     for i, dog_id in enumerate(user['dogs']):
        #         user['dogs'][i] = dc.get_obj_by_id(dog_id).hash(req.url_root)
        #         user['dogs'][i] = {'id': user['dogs'][i]['id'], 'self': user['dogs'][i]['self']}

        # optional TODO: paginate

        return build_response(users, 200)

    def add_user(self, user: User) -> None:
        with self.client.transaction():
            incomplete_key = self.client.key(self.kind)
            ds_user = datastore.Entity(key=incomplete_key)
            ds_user.update({
                    'name': user.name,
                    'email': user.email,
                    'user_id': user.user_id,
                    'dogs': user.dogs
                })
            self.client.put(ds_user)
        user.id = ds_user.key.id

    def process_user(self, user_info: dict) -> None:
        # pprint(user_info)
        user = User(name=user_info['name'],
                    email=user_info['email'],
                    user_id=user_info['sub'])

        # query for pre-existing user
        query = self.client.query(kind=self.kind)
        query.add_filter('user_id', '=', user.user_id)
        results = list(query.fetch())

        if not results:
            self.add_user(user)
        else:
            user.dogs = results[0]['dogs']
            user.id = results[0].key.id

    @classmethod
    def build_entity(cls, data, _id=None) -> User:
        return User(
            name=data.get('name'),
            email=data.get('email'),
            user_id=data.get('user_id'),
            dogs=data.get('dogs'),
            id=_id
        )
