from flask import request, jsonify
from flask_httpauth import HTTPTokenAuth
from flask import current_app
import secrets

token_auth = HTTPTokenAuth(scheme='Bearer')

# Store valid tokens (in a real application, use a database)
valid_tokens = set()

def generate_token():
    return secrets.token_urlsafe(32)

def add_token(token):
    valid_tokens.add(token)

def remove_token(token):
    valid_tokens.discard(token)

@token_auth.verify_token
def verify_token(token):
    if token in valid_tokens:
        return token  # Return the token as the user identifier
    return False

@token_auth.get_user_roles
def get_user_roles(user):
    return ['user']  # You can implement role-based access control here if needed

# Generate an initial token (for testing purposes)
initial_token = generate_token()
add_token(initial_token)
print(f"Initial API token: {initial_token}")
