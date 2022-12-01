from dataclasses import dataclass, field, asdict
from helpers.exceptions import ParamError
from helpers.status_codes import code


@dataclass
class User:
    name:       str
    email:      str
    user_id:    str
    dogs:       list[int] = field(default_factory=list)  # a list of dog ids
    id:         int = None

    def __post_init__(self):
        if not self.name or not self.email or not self.user_id:
            raise ParamError({'msg': 'Insufficient parameters'}, code.forbidden)
        if not isinstance(self.name, str):
            raise ParamError({'msg': 'Invalid name: is that a string?'}, code.forbidden)

    def hash(self, path: str):
        user = asdict(self)
        user['self'] = f'{path}users/{self.id}'
        if not self.id:
            del user['id']
        return user


@dataclass
class Auth:
    client_id:      str
    domain:         str
    client_secret:  str


auth0_app = Auth(
    client_id='996g0c7PtnxX73Yzz3jjTll9JAnhoDsZ',
    domain='cloud-portfolio.us.auth0.com',
    client_secret='ZXOlBx9rx5hvyiqA7dHf1OkfyB0pwhiCGOAvHZWiD35dJEPkH39kwB4_Af8dPVCT'
)
