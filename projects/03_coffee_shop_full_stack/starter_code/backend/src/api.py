import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS, cross_origin

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from sqlite3 import IntegrityError

app = Flask(__name__)
setup_db(app)
CORS(app)

AUTH0_DOMAIN = 'dev-gfdym553.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee_fsnd'

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''


# db_drop_and_create_all()


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth.split()

    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    elif len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    elif len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    token = parts[1]
    return token


def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}

    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)

        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)


def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT.'
        }, 400)

    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)
    return True


def requires_auth(permission=''):
    def requires_auth_from_server(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            payload = None
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
                check_permissions(permission, payload)
            except HTTPError as e:
                print(e.reason)
                abort(401)
            except URLError as e:
                print(e.reason)
                abort(401)
            except AuthError as e:
                print(e.error)
                abort(e.status_code)
            except:
                abort(401)

            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_from_server


# ROUTES
'''
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route("/api/drinks", methods=['GET'])
@cross_origin()
def get_drinks():
    drinks = Drink.query.all()

    if 0 == len(drinks):
        abort(404)
    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks],
    })


'''
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route("/api/drinks-detail", methods=['GET'])
@cross_origin()
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()

    if 0 == len(drinks):
        abort(404)
    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in drinks],
    })


@app.route("/api/drinks/<int:drink_id>", methods=['GET'])
@cross_origin()
def get_drink_detail(drink_id):
    drink = Drink.query.filter_by(id=drink_id).first()

    if drink is None:
        abort(404)
    return jsonify({
        'success': True,
        'drinks': drink.long(),
    })


'''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route("/api/drinks", methods=['POST'])
@cross_origin()
@requires_auth('post:drinks')
def create_a_drink(payload):
    try:
        print(request.json)
        drink = Drink(title=request.json['title'], recipe=json.dumps(request.json['recipe']))
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()],
        })
    except IntegrityError as e:
        print(e)
        abort(422)
    except Exception as e:
        print(e)
        abort(422)


'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route("/api/drinks/<int:drink_id>", methods=['PATCH'])
@cross_origin()
@requires_auth('patch:drinks')
def patch_a_drink(payload, drink_id):
    try:
        drink = Drink.query.filter_by(id=drink_id).first()
        drink.title = request.json['title']
        drink.recipe = json.dumps(request.json['recipe'])
        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except IntegrityError as e:
        print(e)
        abort(422)
    except Exception as e:
        print(e)
        abort(422)


'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route("/api/drinks/<int:drink_id>", methods=['DELETE'])
@cross_origin()
@requires_auth('delete:drinks')
def delete_a_drink(payload, drink_id):
    try:
        drink = Drink.query.filter_by(id=drink_id).first()
        drink.delete()

        return jsonify({
            'success': True,
            'delete': drink_id
        })
    except IntegrityError as e:
        print(e)
        abort(422)
    except Exception as e:
        print(e)
        abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
Handles no resource found error
'''


@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Provided resource cannot be found"
    }), 404


'''
Handles unauthorized access error
'''


@app.errorhandler(401)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unathorized access"
    }), 401


@app.errorhandler(403)
def no_permission_granted(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "No permission granted"
    }), 403
