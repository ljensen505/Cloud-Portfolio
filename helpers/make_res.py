from flask import make_response, Response


def build_response(data, code: int) -> Response:
    res = make_response(data)
    res.status_code = code
    return res
