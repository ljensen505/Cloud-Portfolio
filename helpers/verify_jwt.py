from flask import request
from six.moves.urllib.request import urlopen
from jose import jwt
import json


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# This code is borrowed from the python sample in module 7
# Verify the JWT in the request's Authorization header
def verify_jwt(req: request, domain: str, client_id: str) -> dict:
    if 'Authorization' in req.headers:
        auth_header = req.headers['Authorization'].split()
        token = auth_header[1]
    else:
        raise AuthError({"code": "no auth.py header",
    "description":
    "Authorization header is missing"}, 401)

    jsonurl = urlopen(f"https://{domain}/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
    "description":
    "Invalid header. "
    "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
    "description":
    "Invalid header. "
    "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=client_id,
                issuer=f"https://{domain}/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
        "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
        "description":
        "incorrect claims,"
        " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
        "description":
        "Unable to parse authentication"
        " token."}, 401)

        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
    "description":
    "No RSA key in JWKS"}, 401)
