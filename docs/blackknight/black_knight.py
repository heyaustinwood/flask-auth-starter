import requests
import enum
import logging
import os
import shutil
import tempfile

from datetime import datetime
from typing import Optional
from functools import partial

from collections import OrderedDict
from django.core.cache import cache
from django.conf import settings as django_settings
from django.http import FileResponse, HttpResponse

from .types import JobType, Record, SearchProperty

logger = logging.getLogger(__name__)


FEED_ID_OWNERSHIP = 100001
FEED_ID_FORECLOSURE = 100002


FEED_TYPE_CHOICES = [
    ("20240101", "Foreclosure"),
    ("19500101", "Ownership Change"),
]


class ClientAPI:
    """
    A python wrapper to interact with Black Knight/SiteXPro REST API.

    >>> api_url = "http://test.com"
    >>> client_secret = "secret"
    >>> client_key = "key"
    >>> api = BlackKnightAPI(api_url, client_key, client_secret)
    >>> api.search.property("123 Main St", "Jacksonville, FL 32256")
    >>> api.jobs.get(12345)
    """

    CO_DEV_URL = "https://api-co-dev.dev.bkitest.com"
    UAT_URL = "https://api.uat.bkitest.com"
    PROD_URL = "https://api.bkiconnect.com"
    TOKEN_KEY = "BLACKKNIGHT_TOKEN"
    token_timeout = 60 * 10  # 10 minutes

    def __init__(self, api_url: str, client_key: str, client_secret: str):
        self.api_url = api_url
        self.client_key = client_key
        self.client_secret = client_secret
        self.jobs = Job(self)
        self.search = Search(self)

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }

    def get(self, *args, **kwargs):
        kwargs = {
            **{"headers": self.get_headers()},
            **kwargs,
        }
        return requests.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        kwargs = {
            **{"headers": self.get_headers()},
            **kwargs,
        }
        return requests.post(*args, **kwargs)

    def get_oauth_token(self) -> str:
        """
        Get the OAuth token from the Black Knight API.
        """

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        # Data payload
        data = {
            "grant_type": "client_credentials",
        }
        response = requests.post(
            f"{self.api_url}/ls/apigwy/oauth2/v1/token",
            auth=(self.client_key, self.client_secret),
            headers=headers,
            data=data,
        )
        # Check if the request was successful
        if response.status_code == 200:
            logger.info("Oauth token successful")
            return response.json()["access_token"]
        else:
            msg = f"Failed to obtain token. Error: {response.json()}"
            logger.error(msg)
            raise Exception(msg)

    def get_token(self) -> str:
        """
        Get the OAuth token from the cache or request a new one if it's
        not available.
        """
        token = cache.get(self.TOKEN_KEY, None)
        if not token:
            token = self.get_oauth_token()
            cache.set(self.TOKEN_KEY, token, self.token_timeout)
        return token


class Search:
    def __init__(self, api: ClientAPI):
        self.api = api
        self.base_url = f"{self.api.api_url}/realestatedata/search"

    def property(
        self,
        addr: str,
        lastline: str,
        fips: Optional[str] = None,
        apn: Optional[str] = None,
        owner: Optional[str] = None,
        zip: Optional[str] = None,
        feed_id: Optional[int] = None,
        is_mailing_address: Optional[bool] = False,
        client_reference: Optional[str] = None,
        options: Optional[str] = None,
    ) -> SearchProperty:
        """
        Searches properties based on various criteria.

        Args:
            addr (str): First line of the property address,
                e.g., "123 Main St".
            lastline (str): Last line of the property address,
                e.g., "Jacksonville, FL 32256". Can be included in addr.
            fips (str, optional): For APN search. 5-digit county FIPS code,
                returned in Location element.
            apn (str, optional): For APN search. Assessor’s Parcel Number,
                returned in Location element.
            owner (str, optional): Tie-breaker for multiple records with the same
                address. Required for Owner search without addr, lastline, APN.
                feedid must not be specified for Owner search.
            zip (str, optional): For owner name searches or as a lastline
                alternative.
            feedid (int, optional): Numeric feed identifier. If not specified, a
                search is performed without returning feed content.
            ismailingaddress (bool, optional): Default False. When True, search by
                mailing address.
            clientreference (str, optional): Value to correlate requests on your
                side, recorded for troubleshooting.
            options (str, optional): List of name=value pairs for additional search
                options, e.g., 'search_exclude_nonres=Y'.

        Sample Response Data 404 status code
        {
            "Locations": [],
            "Feed": None,
            "Report": None,
            "OrderInfo": {
                "IsValidAddress": False,
                "SearchId": 7877828,
                "Completed": "2024-03-01 14:51:33Z",
            },
        }

        Sample Response Data 300 status code
        {
            "Locations": [
                {
                    "FIPS": "04013",
                    "APN": "302-35-375",
                    "Address": "1425 W ELLIOT RD",
                    "City": "CHANDLER",
                    "State": "AZ",
                    "ZIP": "85233",
                    "ZIP4": "85233",
                    "UnitType": "",
                    "UnitNumber": "201",
                    "UseCode": "1234",
                    "UseCodeDescription": "Residential Condominium Development (Association Assessment)",
                    "Owner": "My Company",
                },
                {
                    "FIPS": "04013",
                    "APN": "302-41-663",
                    "Address": "1234 N STREET ST",
                    "City": "CHANDLER",
                    "State": "AZ",
                    "ZIP": "85225",
                    "ZIP4": "7091",
                    "UnitType": "",
                    "UnitNumber": "",
                    "UseCode": "1234",
                    "UseCodeDescription": "Residential Condominium Development (Association Assessment)",
                    "Owner": "My Company",
                },
                ...
            ]
            "Feed": None,
            "Report": None,
            "OrderInfo": {
                "IsValidAddress": True,
                "SearchId": 7879494,
                "Completed": "2024-03-02 00:35:45Z",
            },
        }

        Notes:
            For address searches, addr and lastline are required. owner is optional
            but required for an owner search when other details are absent. APN
            searches need fips and apn. Other parameters refine search results or
            provide context.
        """
        return self.api.get(
            self.base_url,
            params={
                "addr": addr,
                "lastLine": lastline,
                "fips": fips,
                "apn": apn,
                "owner": owner,
                "zip": zip,
                "feedId": feed_id,
                "isMailingAddress": is_mailing_address,
                "clientReference": client_reference,
                "options": options,
            },
        )

    def doc(
        self,
        fips: str,
        rec_date: str,
        feed_id: int,
        doc_num: Optional[str] = None,
        book: Optional[str] = None,
        page: Optional[str] = None,
        format: Optional[str] = None,
        client_reference: Optional[str] = None,
        options: Optional[str] = None,
    ):
        """
        Fetches documents based on specified criteria.

        Args:
            fips (str): Required. 5-digit county FIPS code.
            rec_date (str): Required. Document recording date formatted as yyyyMMdd.
            feed_id (int): Required. Numeric identifier of the feed being
                requested, e.g., 100001, 100002, etc.
            doc_num (str, optional): Document number.
            book (str, optional): Document book number.
            page (str, optional): Document page number.
            format (str, optional): Default is TIF. Can also request PDF.
            client_reference (str, optional): Any value you want to correlate to a
                request on your side. Recorded in the usage log for troubleshooting.
            options (str, optional): Semi-colon or pipe delimited list of
                name=value pairs. Current supported options are: document_provider
                (specify cascade to include a third-party document image provider
                at additional charge), document_search_normalize (specify N to
                turn off parameter normalization and search by the exact values
                specified in the query string).
        """
        if not format:
            format = "TIF"
        return self.api.get(
            f"{self.base_url}/doc",
            params={
                "fips": fips,
                "recDate": rec_date,
                "docNum": doc_num,
                "book": book,
                "page": page,
                "format": format,
                "feedId": feed_id,
                "clientReference": client_reference,
                "options": options,
            },
        )

    def farm(self):
        """
        TODO: not quite sure if this is the correct implementation
        the documentation says has an example POST request

        Farm search URL
        {{api_gateway_baseUrl}}/realestatedata/search/farm

        Example POST
        {
            "ReportType": "100004",
            "Options": "farm_zipcode=92610;farm_carrier_route=C043;farm_lotsize_sqft=3900-4000",
            "Shapes": [{
                "Circle": {
                    "Latitude": 33.686883,
                    "Longitude": -117.66982,
                    "radius": 0.01
                }
            }]
        }
        """
        pass

    def farm_count(self):
        """
        TODO: not quite sure if this is the correct implementation
        the documentation says has an example POST request

        Farm count URL
        {{api_gateway_baseUrl}}/realestatedata/search/farm/count

        Example POST
        {
            "ReportType": "100004",
            "Options": "farm_zipcode=92610;farm_carrier_route=C043;farm_lotsize_sqft=3900-4000",
            "Shapes": [{
                "Circle": {
                    "Latitude": 33.686883,
                    "Longitude": -117.66982,
                    "radius": 0.01
                }
            }]
        }
        """
        pass

    def farm_country(self):
        """
        TODO: not quite sure if this is the correct implementation
        the documentation doesn't say any method GET or POST

        {{api_gateway_baseUrl}}/realestatedata/search/farm/countyinfo?fips={{fips}}

        Use this URL to retrieve a list of zip codes, cities, and subdivisions within a specific county.
        """
        pass

    def credits(self):
        """
        TODO: not quite sure if this is the correct implementation
        the documentation doesn't say any method GET or POST

        Credits info URL
        {{api_gateway_baseUrl}}/realestatedata/search/credits

        Use this URL to retrieve available credits. This URL is mainly used in the test environment.

        """
        pass

    def loi(self):
        """
        Loan Officer Insight (LOI) info URL
        TODO: implement this
        """
        pass

    def sample_info(self, feed_id: str):
        """
        Sample info URL
        {{api_gateway_baseUrl}}/realestatedata/search/sample/{{feedId}}

        Use this URL to retrieve a sample of the “feedId” data.
        """
        pass

    def options_info(self, feed_id: str):
        """
        Options info URL
        {{api_gateway_baseUrl}}/realestatedata/search/options/{{feedId}}

        Use this URL to retrieve the available options for the “feedId” data.
        """
        pass

    def county_info(self, fips: str):
        """
        County info URL
        {{api_gateway_baseUrl}}/realestatedata/search/countyinfo?fips={{fips}}

        Use this URL to retrieve information about a specific county. Fips is
        the 5 character code associated with the county – 06037 for Los Angeles CA for example.
        """
        pass


class Job:
    """
    The /realestatedata/job endpoint, accessible only via the REST interface
    supports the submission of batch jobs via the SiteX Pro API and API Gateway.
    """

    class StatusCode(enum.Enum):
        CREATED = 0
        PROCESSING = 1
        COMPLETED = 2
        ERROR = 3
        PAUSED = 4
        ABANDONED = 5
        AWAITING_INPUT = 6
        ACTIVE = 7

    def __init__(self, api: ClientAPI):
        self.api = api
        self.base_url = f"{self.api.api_url}/realestatedata/job"

    def create(self, profile_id: int, job_name: str, records: list[Record]):
        """
        Allows users to create a new job from a JSON request payload.
        - Must be linked to an existing profile Id and the customer
        - Must have access to the specified profile Id.
        - Can include up to 10,000 records.
        - All records are added to that one job.
        - REF_ID should be unique per record within a job

        Sample:
        {
            "ProfileId": 12345,
            “JobName”: “testjob1”,
            “Records”: [
                {
                    “ADDRESS”: “714 VINE”,
                    “CITY”: “”,
                    “STATE”: “”,
                    “ZIP”: “92805”,
                    “REF_ID”: 2
                }
            ]
        }

        Args:
            profile_id (int): The ID of the profile to link the job to.
            job_name (str): The name of the job.
            records (list[Record]): The records to add to the job.

        Returns:
            Returns job id
        """
        data: JobType = {
            "ProfileId": profile_id,
            "JobName": job_name,
            "Records": records,
        }
        return self.api.post(
            self.base_url,
            json=data,
        )

    def get(self, job_id: int):
        """
        Fetches a job by its ID.

        Args:
            job_id (int): The ID of the job to fetch.

        Returns:
            Any: The fetched job.
        """
        return self.api.get(f"{self.base_url}/{job_id}")

    def pause(self, job_id: int):
        """
        GET /realestatedata/job/pause/{jobId}

        Pauses the specified job if it is running, but only if the job is
        owned by the requesting customer.

        Args:
            job_id (int): The ID of the job to pause.
        """
        return self.api.get(f"{self.base_url}/pause/{job_id}")

    def resume(self, job_id: int):
        """
        GET /realestatedata/job/resume/{jobId}

        Resumes the specified job if it is paused, but only if the job is
        owned by the requesting customer.

        Args:
            job_id (int): The ID of the job to resume.
        """
        return self.api.get(f"{self.base_url}/resume/{job_id}")

    def add(self, job_name: str, records: list[Record]):
        """
        POST /realestatedata/job/add

        Allows additional records to be added to an existing job.
        - Must specify an existing job Id and the job must belong to the
        requesting customer.
        - Can include up to 10,000 records to be added.
        - REF_ID should be unique per record within a job.

        Sample:
        {
            "JobName": 12345-name,
            "Records": [
                {
                    "ADDRESS": "714 VINE",
                    "CITY": "",
                    "STATE": "",
                    "ZIP": "92805",
                    "REF_ID": "6"
                }
            ]
        }

        Args:
            job_id (int): The ID of the job to add records to.
            records (list[Record]): The records to add to the job.
        """
        data: JobType = {
            "JobName": job_name,
            "Records": records,
        }
        logger.info(f"Request for Add Properties to Job \n {data}")
        return self.api.post(
            f"{self.base_url}/add",
            json=data,
        )

    def remove(self, job_id: int, ref_ids: list[int]):
        """
        POST /realestatedata/job/remove

        Allows records to be removed from an existing job.
        - Must specify an existing job Id and the job must belong to the
        requesting customer.
        - Can include up to 10,000 records to be removed.

        Sample:
        {
            "JobId": 12345,
            "Records": [
                {
                    "REF_ID": "1"
                },
                {
                    "REF_ID": "2"
                }
            ]
        }

        Args:
            job_id (int): The ID of the job to remove records from.
            ref_ids (list[int]): The reference IDs of the records to remove.
        """
        data = {
            "JobId": job_id,
            "Records": [{"REF_ID": ref_id} for ref_id in ref_ids],
        }
        return self.api.post(
            f"{self.base_url}/remove",
            json=data,
        )

    def trigger(self, job_id: int):
        """
        GET /realestatedata/job/trigger/{jobId}

        Triggers another run of an existing “OnDemand” job, but only if the
        job is owned by the requesting customer. OnDemand jobs are jobs
        that are considered “monitored” jobs, but they are not run on a set
        schedule. When it is desired to run the job, this trigger is invoked.

        Args:
            job_id (int): The ID of the job to trigger.
        """
        return self.api.get(f"{self.base_url}/trigger/{job_id}")

    def disable(self, job_id: int):
        """
        GET /realestatedata/job/disable/{jobId}

        Disables additional runs of the specified monitored job, but only if
        the job is owned by the requesting customer.

        Args:
            job_id (int): The ID of the job to disable.
        """
        return self.api.request.get(f"{self.base_url}/disable/{job_id}")

    def active(self):
        """
        GET /realestatedata/job/active

        Returns a list of jobs currently running.
        For non-System Admin users, only includes jobs for that user.
        For System Admin users, returns all jobs.
        """
        return self.api.get(f"{self.base_url}/active")

    def history(
        self,
        start_date: Optional["datetime.date"] = None,
        end_date: Optional["datetime.date"] = None,
    ):
        """
        GET /realestatedata/job/history/{startDate?}/{endDate?}

        Returns a list of all jobs within the specified date range.
        - For non-System Admin users, only includes jobs for that user.
        - For System Admin users, returns all jobs.
        - Job count is returned in the response header x-job-count.
        - Both dates are optional.
          - startDate default is 7 days ago.
          - endDate default is today.

        Args:
            start_date (str, optional): The start date of the date range.
            end_date (str, optional): The end date of the date range.
        """
        # Check if start_date and end_date are provided
        date_range = ""
        # TODO: verify if this is the correct format for the date
        date_format = "%Y%m%d"
        if start_date and end_date:
            date_range = "/".join(
                [
                    f"{start_date.strftime(date_format)}",
                    f"{end_date.strftime(date_format)}",
                ]
            )
        return self.api.get(
            f"{self.base_url}/history/{date_range}",
            params={"startDate": start_date, "endDate": end_date},
        )

    def download(self, job_id: int):
        """
        GET /realestatedata/job/download/{jobId}

        Allows users to download output data of a specific job.

        Args:
            job_id (int): The ID of the job to download.
        """
        return self.api.get(f"{self.base_url}/download/{job_id}")


BlackKnightAPI = partial(
    ClientAPI,
    django_settings.BLACKKNIGHT_API_URL,
    django_settings.BLACKKNIGHT_CLIENT_KEY,
    django_settings.BLACKKNIGHT_CLIENT_SECRET,
)


def download_and_save_excel(request):
    """
    Downloading an Excel file from the API and want save it temporarily
    """
    # Assuming you have a URL to the Excel file after making an API request
    excel_file_url = "URL_TO_THE_EXCEL_FILE"
    response = requests.get(excel_file_url, stream=True)

    if response.status_code == 200:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, "downloaded_file.xlsx")

        with open(file_path, "wb") as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)

        # Store the directory path in the session
        request.session["excel_file_path"] = file_path

        return HttpResponse("File downloaded and saved.")
    else:
        return HttpResponse("Failed to download the file.")


def serve_excel_file(request):
    file_path = request.session.get("excel_file_path")
    if file_path:
        response = FileResponse(
            open(file_path, "rb"),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="downloaded_file.xlsx"'
        return response
    else:
        return HttpResponse("No file found.")


def get_property_id(property_id):
    """
    `propertyId` consists of propertygroup_id and property_id separated by a hyphen.
    This value comes from the submitted valud on “Records” "REF_ID".
    """
    return int(property_id.split("-")[1])


def prepare_records(property_group_id, properties, feed_type):
    records = []
    # TODO: Remove hardcoded LOAN_ORIGINATION_DATE after BK fixes the issue
    for property in properties:
        record = {
            "ADDRESS": property.street_address,
            "CITY": property.city,
            "STATE": property.state,
            "ZIP": property.zipcode,
            "REF_ID": f"{property_group_id}-{property.id}",
            "LOAN_ORIGINATION_DATE": feed_type,
        }
        records.append(record)
    return records


class PropertyDict:
    """
    This class is used to convert a property to a dictionary that can be used
    to create a job in the Black Knight API.
    """

    def __init__(self, property_instance, property_group=None):
        self.property = property_instance
        self.property_group = property_group

    def to_dict(self):
        """
        Sample:
        {
            "PropertyFullStreetAddress": "123 Main St",
            "PropertyCity": "Anytown",
            "PropertyState": "CA",
            "PropertyZip": "12345",
            "FIPS": "06037",
            "APN": "1234567890",
            "REF_ID": "1-1",
        }
        """
        return {
            "PropertyFullStreetAddress": self.property.street_address,
            "PropertyCity": self.property.city,
            "PropertyState": self.property.state,
            "PropertyZip": self.property.zipcode,
            "FIPS": self.property.fips_code,
            "APN": self.property.apn_formatted,
            "REF_ID": self._get_ref_id(),
        }


    def _get_ref_id(self):
        if self.property_group:
            return f"{self.property_group.id}-{self.property.id}"
        return str(self.property.id)

    @classmethod
    def from_property(cls, property_instance, property_group=None):
        return cls(property_instance, property_group).to_dict()

    @classmethod
    def from_properties(cls, properties, property_group=None):
        return [cls.from_property(prop, property_group) for prop in properties]
