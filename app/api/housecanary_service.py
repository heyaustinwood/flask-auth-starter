import requests
from flask import current_app

def get_housecanary_data(address, city, state, zip_code, apn, fips):
    url_base = current_app.config['HOUSECANARY_API_URL']
    api_key = current_app.config['HOUSECANARY_API_KEY']
    api_secret = current_app.config['HOUSECANARY_API_SECRET']
    
    params = {
        "address": address,
        "zipcode": zip_code
    }

    endpoints = [
        "details_enhanced",
        "ltv_details",
        "nod"
    ]

    results = {}

    try:
        for endpoint in endpoints:
            url = f"{url_base}/{endpoint}"
            response = requests.get(url, params=params, auth=(api_key, api_secret))
            response.raise_for_status()
            results[endpoint] = response.json()
        return results
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 401:
            raise Exception("Authentication failed. Check your HouseCanary API key and secret.")
        elif response.status_code == 403:
            raise Exception("Insufficient permissions for HouseCanary API")
        else:
            raise Exception(f"HTTP error occurred: {http_err}")
    except Exception as e:
        raise Exception(f"Error fetching data from HouseCanary API: {str(e)}")
