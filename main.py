import json
from flask import Flask, Response, request, make_response, render_template,\
    session, url_for, redirect
from google.cloud import datastore
from authlib.integrations.flask_client import OAuth
from helpers.auth0 import auth0_app
from controllers.auth import AuthController
from controllers.users import UserController
from blueprints import auth as auth_bp,\
    users as users_bp,\
    dogs as dogs_bp,\
    toys as toys_bp
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = '2b7df4bd724f79483e7f5f9cdb5966f3'
bps = [auth_bp, users_bp, dogs_bp, toys_bp]
[app.register_blueprint(bp.bp) for bp in bps]

client = datastore.Client()

oauth = OAuth(app)
oauth.register(
    'auth0',
    client_id=auth0_app.client_id,
    client_secret=auth0_app.client_secret,
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{auth0_app.domain}/.well-known/openid-configuration'
)

uc = UserController(client)
ac = AuthController(client)


@app.route('/')
def index() -> str:
    return render_template('home.html',
                           session=session.get('user'),
                           pretty=json.dumps(session.get('user'),
                                             indent=4))


@app.route('/login', methods=['GET', 'POST'])
def login() -> Response:
    if request.method == 'POST':
        return ac.login(request)
    elif request.method == 'GET':
        return oauth.auth0.authorize_redirect(
            redirect_uri=url_for("callback", _external=True)
        )
    else:
        res = make_response(f'Method {request.method} not allowed.')
        res.status_code = 405
        return res


@app.route("/callback", methods=["GET", "POST"])
def callback() -> Response:
    token = oauth.auth0.authorize_access_token()
    # check if user in datastore, add if new
    uc.process_user(token['userinfo'])
    id_token = token['id_token']
    name = token['userinfo']['name']
    user_id = token['userinfo']['sub']
    session["user"] = token
    return redirect(f'/auth/token?id_token={id_token}&name={name}&user_id={user_id}')


if __name__ == '__main__':
    load_dotenv()
    app.run(host='0.0.0.0', port=8080, debug=True)
