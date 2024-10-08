import requests
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class BlackKnightAPI:
    def __init__(self):
        self.base_url = current_app.config.get('BLACKKNIGHT_API_URL')
        self.client_key = current_app.config.get('BLACKKNIGHT_CLIENT_KEY')
        self.client_secret = current_app.config.get('BLACKKNIGHT_CLIENT_SECRET')

        logger.debug(f"BLACKKNIGHT_API_URL: {self.base_url}")
        logger.debug(f"BLACKKNIGHT_CLIENT_KEY: {self.client_key[:5]}...")
        logger.debug(f"BLACKKNIGHT_CLIENT_SECRET: {self.client_secret[:5]}...")

        if not self.base_url:
            raise ValueError("BLACKKNIGHT_API_URL is not set in the configuration")
        if not self.client_key or not self.client_secret:
            raise ValueError("BLACKKNIGHT_CLIENT_KEY or BLACKKNIGHT_CLIENT_SECRET is not set in the configuration")

    def get_oauth_token(self):
        token_url = f"{self.base_url}/ls/apigwy/oauth2/v1/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "client_credentials"}
        
        response = requests.post(token_url, auth=(self.client_key, self.client_secret), headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception(f"Failed to obtain token. Error: {response.json()}")

    def get_property_data(self, address, city, state, zip_code, apn, fips):
        token = self.get_oauth_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "addr": address,
            "lastLine": f"{city}, {state} {zip_code}",
            "apn": apn,
            "fips": fips,
            "options": "search_exclude_nonres=Y"
        }
        
        search_url = f"{self.base_url}/realestatedata/search"
        response = requests.get(search_url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching property data: {response.status_code} - {response.text}")

def get_blackknight_data(address, city, state, zip_code, apn, fips):
    try:
        api = BlackKnightAPI()
        return api.get_property_data(address, city, state, zip_code, apn, fips)
    except ValueError as e:
        raise Exception(f"Black Knight API configuration error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error fetching data from Black Knight API: {str(e)}")

def format_blackknight_response(response):
    # Assuming the first location is the most relevant
    location = response.get('Locations', [{}])[0]
    
    formatted_response = {
        "property_address": {
            "street_address": location.get('Address', ''),
            "city": location.get('City', ''),
            "state": location.get('State', ''),
            "zip_code": location.get('ZIP', '')
        },
        "apn": location.get('APN', ''),
        "owner_name": location.get('Owner', ''),
        "property_type": location.get('UseCodeDescription', ''),
        "year_built": '',  # Not provided in the sample response
        "bedrooms": '',  # Not provided in the sample response
        "bathrooms": '',  # Not provided in the sample response
        "square_feet": '',  # Not provided in the sample response
        "lot_size": '',  # Not provided in the sample response
        "estimated_value": ''  # Not provided in the sample response
    }
    return formatted_response
