from dataclasses import dataclass, asdict
from helpers.exceptions import ParamError


@dataclass
class Toy:
    name: str
    description: str
    price: float
    purchased_by: str  # user_id, ex. google-oauth2|1000503...
    in_use: bool = False
    used_by: int = None  # id of dog who owns it
    id: int = None  # provided by datastore

    def __post_init__(self):
        err_msg = ''
        try:
            self.price = float(self.price)
        except TypeError:
            err_msg = 'Did that toy have a valid price tag?'
        if not self.name or not self.description:
            err_msg = 'Does this toy have a name?'
        elif not isinstance(self.name, str) or not isinstance(self.description, str):
            err_msg = 'Name and Description must be strings'

        if err_msg:
            raise ParamError({
                "code": "invalid request",
                "description": err_msg
            }, 403)

    def hash(self, path: str):
        toy = asdict(self)
        toy['self'] = f'{path}toys/{self.id}'
        if not self.id:
            del toy['id']
        if toy['in_use']:
            dog_id = toy['used_by']
            toy['used_by'] = {'id': dog_id,
                              'self': f'{path}dogs/{dog_id}'}
        return toy
