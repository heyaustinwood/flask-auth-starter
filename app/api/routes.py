from flask import jsonify, request, current_app
from app.api import bp
from app.api.auth import token_auth
from app.api.external_service import get_property_data, get_blackknight_data
from app.api.housecanary_service import get_housecanary_data
from werkzeug.exceptions import BadRequest, InternalServerError
from app import limiter
from flask import render_template, request, jsonify, current_app
import json
from datetime import datetime
import requests

@bp.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify(error="Bad Request", message=str(e)), 400

@bp.errorhandler(InternalServerError)
def handle_internal_server_error(e):
    return jsonify(error="Internal Server Error", message="An unexpected error occurred"), 500

@bp.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, requests.exceptions.RequestException):
        return jsonify(error="External API Error", message=str(e)), 503
    current_app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify(error="Unexpected Error", message="An unexpected error occurred"), 500

def validate_input():
    address = request.args.get('address')
    city = request.args.get('city')
    state = request.args.get('state')
    zip_code = request.args.get('zip')
    
    if not all([address, city, state, zip_code]):
        raise BadRequest("Missing required parameters")
    
    # Add more specific validations as needed
    return address, city, state, zip_code, request.args.get('apn'), request.args.get('fips')

def log_api_call(user, endpoint, params, response_status, response_data):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user": user,
        "endpoint": endpoint,
        "params": params,
        "response_status": response_status,
        "response_data": response_data
    }
    current_app.logger.info(f"API Call: {json.dumps(log_entry)}")

@bp.route('/property', methods=['GET'])
@token_auth.login_required
@limiter.limit("10 per minute")
def get_property():
    try:
        address, city, state, zip_code, apn, fips = validate_input()
        api_provider = request.args.get('api_provider', 'batchdata')  # Default to batchdata if not specified
        
        if api_provider == 'batchdata':
            external_data = get_property_data(address, city, state, zip_code, apn, fips)
        elif api_provider == 'blackknight':
            external_data = get_blackknight_data(address, city, state, zip_code, apn, fips)
        elif api_provider == 'housecanary':
            external_data = get_housecanary_data(address, city, state, zip_code, apn, fips)
        else:
            raise BadRequest(f"Invalid API provider: {api_provider}")

        # Print the raw response
        print(f"Raw response from {api_provider}:")
        print(external_data)

        # Log the API call
        user = token_auth.current_user()
        log_api_call(user, '/api/v1/property', request.args, 200, external_data)

        return jsonify(external_data)
    except BadRequest as e:
        log_api_call(token_auth.current_user(), '/api/v1/property', request.args, 400, str(e))
        return handle_bad_request(e)
    except Exception as e:
        current_app.logger.error(f"An error occurred: {str(e)}")
        log_api_call(token_auth.current_user(), '/api/v1/property', request.args, 500, str(e))
        return handle_exception(e)
