from __future__ import annotations
from typing import TYPE_CHECKING
from flask import Response, request
from google.cloud import client as gcc, datastore
from models.dogs import Dog
from controllers.parent_controller import Controller
from helpers.make_res import build_response

if TYPE_CHECKING:
    from controllers.users import UserController
    from controllers.toys import ToyController
    from models.toys import Toy

from datetime import date
from pprint import pprint


class DogController(Controller):
    def __init__(self, client: gcc) -> None:
        Controller.__init__(self, client)
        self.kind = 'dogs'

    def give_toy(self, dog: Dog, toy: Toy, tc: ToyController) -> Response:
        print(f'Giving {dog.name} a {toy.name}')

        with self.client.transaction():
            key = self.client.key(self.kind, dog.id)
            ds_dog = self.client.get(key)
            ds_dog['toys'].append(toy.id)
            self.client.put(ds_dog)

        tc.assign_toy(toy, dog)

        return build_response('', 204)

    def delete(self, toy_id: int) -> Response:
        res = Controller.delete(self, toy_id)

        # TODO: handle deleting relation, if any
        print(f'Deleting {self.kind[:-1]}: {toy_id}')
        return res

    def replace(self, req: request, owner_id: str, _id):
        old_dog = self.get_obj_by_id(_id)

        data = req.get_json()
        data['owner_id'] = owner_id
        data['owner_name'] = old_dog.owner_name
        data['adoption_date'] = old_dog.adoption_date
        new_dog = self.build_entity(data, _id=old_dog.id)

        with self.client.transaction():
            key = self.client.key(self.kind, _id)
            ds_dog = self.client.get(key)
            ds_dog['name'] = new_dog.name
            ds_dog['breed'] = new_dog.breed
            ds_dog['toys'] = new_dog.toys
            self.client.put(ds_dog)

        dog = self.get_obj_by_id(_id)
        return build_response(dog.hash(req.url_root), 200)

    def get_dogs(self, req: request, payload: dict) -> Response:
        owner_id = payload.get('sub')
        query = self.client.query(kind=self.kind)
        query.add_filter('owner_id', '=', owner_id)
        results = list(query.fetch())
        dogs = [self.build_entity(dog, _id=dog.key.id).hash(
            req.url_root) for dog in results]

        for dog in dogs:
            if dog['toys']:
                for i, toy_id in enumerate(dog['toys']):
                    dog['toys'][i] = {'id': toy_id,
                                      'self': f'{req.url_root}toys/{toy_id}'}

        return build_response(dogs, 200)

    def _add_dog(self, dog: Dog) -> None:
        with self.client.transaction():
            incomplete_key = self.client.key(self.kind)
            ds_dog = datastore.Entity(key=incomplete_key)
            ds_dog.update({
                'name': dog.name,
                'breed': dog.breed,
                'toys': dog.toys,
                'adoption_date': dog.adoption_date,
                'owner_id': dog.owner_id,
                'owner_name': dog.owner_name
            })
            self.client.put(ds_dog)
        dog.id = ds_dog.key.id

    def post_one(self, req: request, ur: UserController, payload: dict) -> Response:
        data = req.get_json()
        data['adoption_date'] = date.today().strftime("%m/%d/%y")
        data['owner_id'] = payload.get('sub')
        data['owner_name'] = payload.get('name')

        try:
            dog = self.build_entity(data)
        except KeyError:
            return build_response('invalid attributes, check documentation', 403)

        self._add_dog(dog)
        # ur.adopt(dog)
        return build_response(dog.hash(req.url_root), 201)

    @classmethod
    def build_entity(cls, data, _id=None) -> Dog:
        return Dog(
            name=data.get('name'),
            breed=data.get('breed'),
            owner_id=data.get('owner_id'),
            owner_name=data.get('owner_name'),
            adoption_date=data.get('adoption_date'),
            toys=data.get('toys'),
            id=_id
        )
