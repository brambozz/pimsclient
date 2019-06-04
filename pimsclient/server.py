"""Interaction with a webserver running the PIMS web API
"""
import json
from os import environ

import requests
from requests_ntlm import HttpNtlmAuth


class PIMSSession:
    """A logged in session with a PIMSServer

    """

    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url

    def get(self, url):
        """Do a html get over this session

        Parameters
        ----------
        url: str
            url to call

        Raises
        ------
        PIMSServerException
            Several types of server exception if get on server does not work

        Returns
        -------
        dict
            json-decoded contents of response

        """
        response = self.check_response(self.session.get(url))
        return json.loads(response.content)

    def post(self, url, params):
        """Do a html post over this session

        Parameters
        ----------
        url: str
            url to call
        params: Dict
            dictionary of values to send

        Raises
        ------
        PIMSServerException
            Several types of server exception if get on server does not work

        Returns
        -------
        dict
            json-decoded contents of response to post

        """
        response = self.check_response(self.session.post(url, params=params))
        return json.loads(response.content)

    def close(self):
        return self.session.close()

    def username(self):
        """Get username

        Returns
        -------
        str
            Username that is being used in current session
        """
        if hasattr(self.session, "auth"):
            return self.session.auth.username
        else:
            return "unknown"

    def check_response(self, response):
        """Check response from PIMS server and raise appropriate exceptions

        Parameters
        ----------
        response: requests_mock.models.Response
            the http response to check

        Raises
        ------
        OperationForbidden
            If an action is not allowed by PIMS for the logged in user

        """
        if response.status_code == 401:
            raise Unauthorized(
                f"Credentials for '{self.username()}' do not seem to work"
            )
        elif response.status_code == 403:
            raise OperationForbidden(response.text)
        elif response.status_code == 405:
            raise OperationNotSupported(response.text)
        elif response.status_code == 404:
            raise ResourceNotFound(response.text)

        return response


class PIMSServer:
    """A connection to a PIMS API
    """

    def __init__(self, url):
        """

        Parameters
        ----------
        url: str
            URL to PIMS web API
        """
        self.url = url

    def get_session(self, user=None, password=None):
        """Get a session by logging in to Radboud hospital domain using NTLM

        Parameters
        ----------
        user: str, optional
            username to connect to PIMS API use, defaults to reading environment key ['PIMS_CLIENT_USER']
        password: str, optional
            password to connect to PIMS API, defaults to reading environment key ['PIMS_CLIENT_PASSWORD']

        Returns
        -------
        PIMSSession
            Logged in session

        """
        if not user:
            user = environ.get("PIMS_CLIENT_USER")
        if not password:
            password = environ.get("PIMS_CLIENT_PASSWORD")
        session = requests.Session()
        session.auth = HttpNtlmAuth(f"umcn\\{user}", password)
        return PIMSSession(session=session, base_url=self.url)


class PIMSServerException(Exception):
    pass


class Unauthorized(PIMSServerException):
    pass


class OperationForbidden(PIMSServerException):
    pass


class OperationNotSupported(PIMSServerException):
    pass


class ResourceNotFound(PIMSServerException):
    pass