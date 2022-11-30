from flask import Blueprint, render_template, request, Response, session, redirect, url_for
from helpers.auth0 import auth0_app
from urllib.parse import quote_plus, urlencode

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/')
def test() -> Response:
    return redirect('/')


@bp.route('/token', methods=['GET'])
def show_token() -> str:
    id_token: str = request.args.get('id_token')
    name: str = request.args.get('name')
    user_id: str = request.args.get('user_id')
    return render_template('welcome.html', id_token=id_token, name=name, user_id=user_id)


@bp.route("/logout")
def logout() -> Response:
    session.clear()
    encoded = urlencode(
        {'returnTo': url_for('index', _external=True),
            'client_id': auth0_app.client_id},
        quote_via=quote_plus,)
    return redirect(
        f"https://{auth0_app.domain}/v2/logout?{encoded}"
    )
