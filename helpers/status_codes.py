from dataclasses import dataclass


@dataclass(frozen=True)
class Status:
    ok = 200
    created = 201
    no_content = 204
    bad_request = 400
    unauthorized = 401
    forbidden = 403
    not_found = 404
    method_not_allowed = 405
    not_acceptable = 406


code = Status()
