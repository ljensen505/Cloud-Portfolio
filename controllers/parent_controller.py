from __future__ import annotations
from typing import Union, TYPE_CHECKING
from flask import Response, request
from google.cloud import client as gcc
from helpers.make_res import build_response
from helpers.exceptions import IdError
from helpers.status_codes import code
from models.users import User
from models.dogs import Dog
from models.toys import Toy

if TYPE_CHECKING:
    from controllers.toys import ToyController


class Controller:
    def __init__(self, client: gcc) -> None:
        self.client: gcc = client
        self.kind = "parent"
        self.fixed = []  # a list of non-changeable attributes

    def delete(self, _id: int, tc: ToyController = None) -> Response:
        key = self.client.key(self.kind, _id)
        data = self.client.get(key)

        if not data:
            return build_response(f"{self.kind[:-1]} not found", code.not_found)

        self.client.delete(key)
        return build_response("", code.no_content)

    def update(self, req: request, _id: int) -> Response:

        with self.client.transaction():
            key = self.client.key(self.kind, _id)
            ds_entity = self.client.get(key)
            for key, value in req.get_json().items():
                if key not in self.fixed:
                    ds_entity[key] = value
            self.client.put(ds_entity)

        entity_obj = self.get_obj_by_id(_id)
        return build_response(entity_obj.hash(req.url_root), code.ok)

    def get_obj_by_id(self, _id) -> Union[Dog, Toy, User]:
        key = self.client.key(self.kind, _id)
        ds_entity = self.client.get(key)

        if ds_entity is None:
            raise IdError(
                {
                    "code": "invalid id",
                    "description": f"Could not find a {self.kind[:-1]} with that id",
                },
                404,
            )

        entity = self.build_entity(ds_entity, _id=ds_entity.key.id)

        return entity

    def get_one(self, req: request, _id: int) -> Response:
        return build_response(self.get_obj_by_id(_id).hash(req.url_root), code.ok)

    def count_all(self, req: request) -> int:
        return len(self.get_all(req, self.kind))

    def get_all(self, req: request, kind: str) -> list[Union[User]]:
        query = self.client.query(kind=kind)
        results = list(query.fetch())
        entities = [
            self.build_entity(entity, _id=entity.key.id).hash(req.url_root)
            for entity in results
        ]

        return entities

    @classmethod
    def build_entity(cls, data: dict, _id: int = None) -> Union[User, Dog, Toy]:
        pass
