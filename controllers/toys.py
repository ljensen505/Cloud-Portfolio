from __future__ import annotations
from typing import TYPE_CHECKING
from flask import Response, request
from google.cloud import client as gcc, datastore
from models.toys import Toy
from controllers.parent_controller import Controller
from helpers.make_res import build_response
from helpers.status_codes import code

if TYPE_CHECKING:
    from controllers.users import UserController
    from controllers.dogs import DogController
    from models.dogs import Dog


class ToyController(Controller):
    def __init__(self, client: gcc):
        Controller.__init__(self, client)
        self.kind = 'toys'

    def delete(self, toy_id: int, dc: DogController = None) -> Response:
        toy = self.get_obj_by_id(toy_id)
        if toy.in_use:
            dog = dc.get_obj_by_id(toy.used_by)
            dc.return_toy(dog, toy)
        Controller.delete(self, toy_id)
        res = build_response('', code.no_content)
        return res

    def assign_toy(self, toy: Toy, dog: Dog) -> None:
        with self.client.transaction():
            key = self.client.key(self.kind, toy.id)
            ds_toy = self.client.get(key)
            ds_toy['in_use'] = True
            ds_toy['used_by'] = dog.id
            self.client.put(ds_toy)

    def free_toy(self, toy: Toy) -> None:
        with self.client.transaction():
            key = self.client.key(self.kind, toy.id)
            ds_toy = self.client.get(key)
            ds_toy['in_use'] = False
            ds_toy['used_by'] = None
            self.client.put(ds_toy)

    def replace(self, req: request, purchaser_id: str, _id: int) -> Response:
        old_toy = self.get_obj_by_id(_id)

        data = req.get_json()
        data['purchased_by'] = purchaser_id
        new_toy = self.build_entity(data, old_toy.id)

        with self.client.transaction():
            key = self.client.key(self.kind, _id)
            ds_toy = self.client.get(key)
            ds_toy['name'] = new_toy.name
            ds_toy['description'] = new_toy.description
            ds_toy['price'] = new_toy.price
            self.client.put(ds_toy)

        toy = self.get_obj_by_id(_id)
        return build_response(toy.hash(req.url_root), code.ok)

    def get_toys(self, req: request, ur: UserController) -> Response:
        query = self.client.query(kind=self.kind)
        q_limit = int(req.args.get('limit', 5))
        q_offset = int(req.args.get('offset', 0))
        l_iter = query.fetch(limit=q_limit, offset=q_offset)
        pages = l_iter.pages
        results = list(next(pages))

        if l_iter.next_page_token:
            next_offset = q_offset + q_limit
            next_url = f'{request.base_url}?limit={str(q_limit)}&offset={str(next_offset)}'
        else:
            next_url = None

        toys = [self.build_entity(toy, _id=toy.key.id).hash(req.url_root)
                for toy in results]

        for toy in toys:
            purchaser = ur.get_by_user_id(toy.get('purchased_by')).hash(req.url_root)

            toy['purchased_by'] = {
                'user_id': toy['purchased_by'],
                'self': purchaser['self']
            }

        output = {self.kind: toys}
        if next_url:
            output["next"] = next_url
        return build_response(output, code.ok)

    def _add_toy(self, toy: Toy) -> None:
        with self.client.transaction():
            incomplete_key = self.client.key(self.kind)
            ds_toy = datastore.Entity(key=incomplete_key)
            ds_toy.update({
                'name': toy.name,
                'description': toy.description,
                'price': toy.price,
                'in_use': toy.in_use,
                'purchased_by': toy.purchased_by,
                'used_by': toy.used_by
            })
            self.client.put(ds_toy)
        toy.id = ds_toy.key.id

    def post_one(self, req: request, payload: dict) -> Response:
        # toys are unassigned upon creation
        # they can later be assigned to a dog
        data = req.get_json()
        data['purchased_by'] = payload.get('sub')  # user id, NOT name

        try:
            toy = self.build_entity(data)
        except KeyError:
            return build_response('invalid attributes, check documentation', code.forbidden)

        self._add_toy(toy)

        return build_response(toy.hash(req.url_root), code.created)

    @classmethod
    def build_entity(cls, data, _id=None) -> Toy:
        return Toy(
            name=data.get('name'),
            description=data.get('description'),
            price=data.get('price'),
            purchased_by=data.get('purchased_by'),
            used_by=data.get('used_by'),
            in_use=data.get('in_use'),
            id=_id
        )
