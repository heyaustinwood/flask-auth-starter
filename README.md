# RedataPro API v1

This is the API for RedataPro, serving as a middleware for property data retrieval.

## Endpoints

### GET /api/v1/property

Retrieves property information based on the provided query parameters.

Query Parameters:
- address (required)
- city (required)
- state (required)
- zip (required)
- apn (optional)
- fips (optional)

### Response Format

The API response will be in JSON format with the following structure:

```json
{
  "data": {
    "property": {
      "address": string,
      "unit_type": string,
      "unit": string,
      "city": string,
      "state": string,
      "zipcode": string,
      "label": string,
      "geo_precision": string,
      "lat": number,
      "lon": number
    },
    "parcel": {
      "apn": string,
      "apn_unformatted": string,
      "fips": string,
      "county_name": string,
      "use_code": string,
      "subdivision": string,
      "lot_size": number,
      "lot_number": string,
      "legal_description": string,
      "mailing_address": {}
    },
    "owner": {
      "name": string,
      "mailing_address": {},
      "owner_occupied": boolean,
      "owner_type": string
    },
    "building": {
      "year_built": number,
      "beds": number,
      "baths": number,
      "living_area": number,
      "type": string
    },
    "tax": {
      "tax_amount": number,
      "tax_year": number,
      "tax_delinquent": boolean,
      "tax_delinquent_year": number,
      "assessed_year": number,
      "assessed_value_land": number,
      "assessed_value_imp": number,
      "assessed_value_total": number
    },
    "valuation": {
      "estimated_value": number,
      "estimated_value_high": number,
      "estimated_value_low": number,
      "estimated_value_asof": string,
      "estimated_equity": number,
      "estimated_ltv": number,
      "estimated_equity_percentage": number,
      "estimated_price_per_sqft": number
    },
    "foreclosure": {
      "is_active": boolean,
      "status": string,
      "doc_date": string,
      "doc_type": string,
      "doc_number": string,
      "case_number": string,
      "auction_date": string,
      "auction_bid": number
    },
    "mortgages": [
      {
        "loan_type": string,
        "loan_amount": number,
        "loan_position": string,
        "loan_term_months": number,
        "loan_term_years": number,
        "loan_number": string,
        "loan_due_date": string,
        "loan_doc_number": string,
        "loan_doc_date": string,
        "lender_name": string,
        "lender_type": string,
        "borrower_name": string,
        "interest_rate": number,
        "interest_rate_type": string
      }
    ],
    "liens": [
      {
        "amount": number,
        "filing_type": string,
        "filing_date": string,
        "filing_number": string,
        "filing_jurisdiction": string,
        "filing_agency": string,
        "creditor_name": string,
        "creditor_address": string,
        "debtor_name": string,
        "debtor_address": string
      }
    ]
  }
}
```

The response contains a `data` object with various properties related to a property, including:
- `property`: General property information
- `parcel`: Parcel-specific details
- `owner`: Owner information
- `building`: Building characteristics
- `tax`: Tax-related data
- `valuation`: Property valuation estimates
- `foreclosure`: Foreclosure details, if applicable
- `mortgages`: Array of mortgage information
- `liens`: Array of lien information

Note: Some fields may be empty or not present depending on the availability of data for a specific property.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables:
   - SECRET_KEY
   - BATCHDATA_API_URL
   - BATCHDATA_API_TOKEN
3. Run the application: `python run.py`

## Authentication

This API uses Bearer Token authentication. Include the token in the Authorization header of your requests.

## API Documentation

Interactive API documentation is available at `/api/docs` when the application is running.
