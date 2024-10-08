import requests

# API credentials
api_key = 'test_XQ2MN005OY3QNCWJWXF6'
api_secret = '5rr866gvlPk5jq9Bp84JzHejWd8D6pHh'

# Test address
address = '7904 Verde Springs Dr'
zipcode = '89128'

# API endpoint
url = 'https://api.housecanary.com/v2/property/details'

# Parameters
params = {
    'address': address,
    'zipcode': zipcode
}

# Make the API request
response = requests.get(url, params=params, auth=(api_key, api_secret))

# Check the response
if response.status_code == 200:
    print("API request successful!")
    print("Response:")
    print(response.json())
else:
    print(f"API request failed with status code: {response.status_code}")
    print("Error message:")
    print(response.text)