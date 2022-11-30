from os import getenv
from dataclasses import dataclass


@dataclass
class Auth:
    client_id:      str
    domain:         str
    client_secret:  str


auth0_app = Auth(
    client_id=getenv('CLIENT_ID'),
    domain=getenv('DOMAIN'),
    client_secret=getenv('CLIENT_SECRET')
)
