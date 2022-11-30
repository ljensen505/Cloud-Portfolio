from __future__ import annotations
from typing import Union

from flask import Response, request
from google.cloud import client as gcc

from helpers.make_res import build_response
from helpers.exceptions import IdError
from models.users import User
from models.dogs import Dog
from models.toys import Toy

from pprint import pprint


class Controller:
    def __init__(self, client: gcc) -> None:
        self.client: gcc = client
        self.kind = 'parent'

    def delete(self, _id: int) -> Response:
        """
        Deletes an entity from the datastore. Does NOT handle any side effects.
        These must be handled by child Controllers.  Entity id must be pre-validated
        :param _id: id of the entity in the datastore
        :return: Response object
        """
        key = self.client.key(self.kind, _id)
        data = self.client.get(key)

        if not data:
            return build_response(f'{self.kind[:-1]} not found', 404)

        self.client.delete(key)
        return build_response('', 204)

    def update(self, req: request, _id: int) -> Response:

        with self.client.transaction():
            key = self.client.key(self.kind, _id)
            ds_entity = self.client.get(key)
            for key, value in req.get_json().items():
                ds_entity[key] = value
            self.client.put(ds_entity)

        entity_obj = self.get_obj_by_id(_id)
        return build_response(entity_obj.hash(req.url_root), 200)

    def get_obj_by_id(self, _id) -> Union[Dog, Toy, User]:
        key = self.client.key(self.kind, _id)
        ds_entity = self.client.get(key)

        if ds_entity is None:
            raise IdError({
                "code": "invalid id",
                "description": f'Could not find a {self.kind[:-1]} with that id'
            }, 404)

        entity = self.build_entity(ds_entity, _id=ds_entity.key.id)

        return entity

    def get_one(self, req: request, _id: int) -> Response:
        return build_response(self.get_obj_by_id(_id).hash(req.url_root), 200)

    def get_all(self, req: request, kind: str) -> list[Union[User]]:
        query = self.client.query(kind=kind)
        results = list(query.fetch())
        entities = [self.build_entity(entity, _id=entity.key.id).hash(
            req.url_root) for entity in results]

        return entities

    @classmethod
    def build_entity(cls, data: dict, _id: int = None) -> Union[User, Dog, Toy]:
        pass
