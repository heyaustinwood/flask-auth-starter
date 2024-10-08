import requests
from flask import current_app

def get_property_data(address, city, state, zip_code, apn, fips):
    url = current_app.config['BATCHDATA_API_URL']
    headers = {
        'Authorization': f"Bearer {current_app.config['BATCHDATA_API_TOKEN']}",
        'Content-Type': 'application/json'
    }
    
    payload = {
        "requests": [
            {
                "address": {
                    "street": address,
                    "city": city,
                    "state": state,
                    "zip": zip_code
                },
                "apn": apn,
                "countyFipsCode": fips
            }
        ],
        "options": {
            "showRequests": True
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()

def get_blackknight_data(address, city, state, zip_code, apn, fips):
    url = current_app.config['BLACKKNIGHT_API_URL']
    headers = {
        'Authorization': f"Bearer {current_app.config['BLACKKNIGHT_API_TOKEN']}",
        'Content-Type': 'application/json'
    }
    
    payload = {
        "address": address,
        "city": city,
        "state": state,
        "zipCode": zip_code,
        "apn": apn,
        "fips": fips
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()
