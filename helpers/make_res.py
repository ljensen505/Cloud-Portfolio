from flask import make_response, Response


def build_response(data, code: int, content_type="application/json") -> Response:
    res = make_response(data)
    res.status_code = code
    res.headers.set("Content-Type", content_type)
    return res
