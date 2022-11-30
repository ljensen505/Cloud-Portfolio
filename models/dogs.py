from dataclasses import dataclass, field, asdict
from helpers.exceptions import ParamError


@dataclass
class Dog:
    name:           str
    owner_id:       str  # will be automatically collected
    owner_name:     str  # will be automatically collected
    breed:          str  # required
    adoption_date:  str = None
    toys:           list = field(default_factory=list)
    id:             int = None  # provided by datastore

    def __post_init__(self):
        err_msg = ''
        if not self.name:
            err_msg = 'Does your dog have a name?'
        elif not self.breed:
            err_msg = 'Does your dog have a breed?'
        elif not isinstance(self.name, str):
            err_msg = 'Name must be a string'

        if err_msg:
            raise ParamError({
                "code": "invalid request",
                "description": err_msg
            }, 403)

    def hash(self, path: str):
        dog = asdict(self)
        dog['self'] = f'{path}dogs/{self.id}'
        if not self.id:
            del dog['id']
        if dog['toys']:
            for i, toy_id in enumerate(dog['toys']):
                dog['toys'][i] = {'id': toy_id,
                                  'self': f'{path}toys/{toy_id}'}
        return dog
