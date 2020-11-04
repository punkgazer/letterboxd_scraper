
""" For creating the requests.Session() object that is used to make requests
to letterboxd.com """

# Local Imports
from exceptions import LoginException

# Imports
import re
import json
import requests
from bs4 import Beautifulsoup as bs


# Global vars
FN_USER_DETAILS = "data/user_details.json"
FN_USER_AGENT = "data/user_agent.json" 

# Get user details from file
with open(FN_USER_DETAILS) as jf:
    USER_DETAILS = json.load(jf)

# Get user agent
with open(FN_USER_AGENT) as jf:
    USER_AGENT = json.load(jf)

def make_soup(request):
    """ Converts a request object into a beautifulsoup object for webscraping. """
    return bs(request.text, 'lxml')


class Session(requests.Session):
    """ The Session class for creating a SESSION object. 
    Only one instance needs to be created. """

    MAIN_URL = "https://letterboxd.com"
    
    def __init__(self):
        super().__init__()

        ## Add User Agent
        self.headers.update(USER_AGENT)

        ## Set CSRF Token
        # A necessesary component in making post requests to Letterboxd
        token = self.__get_token()
        self.cookie_params = {'__csrf': token}

        ## Login details
        self.logged_in = False
        self.username = USER_DETAILS['username']
        self.password = USER_DETAILS['password']

    def __repr__(self):
        """ Example: < Session  Username: ..... > """
        cls_name = self.__class__.__name__
        string = f"\tUsername: {self.username}"
        string += f"\tLogged In: {self.logged_in}"
        return f"< {cls_name}\n{string} >"

    def __call__(self):
        """ Logs into Letterboxd if not already logged in. """
        if self.logged_in:
            print("Already logged in.")
        else:
            self.__login()
            self.logged_in = True

    def request(self, request_type, suburl='', **kwargs):
        """ Customise Request to default to main Letterboxd url.
        And to include CSRF token if it's a POST request with data """

        # Edge case
        if not isinstance(suburl, str): 
            raise TypeError("Suburl must be string or empty string")

        # If method is POST, add CSRF token to data passed
        if request_type == "POST":
            if not kwargs.get("data"):
                kwargs['data'] = self.cookie_params
            else:
                kwargs['data'] = dict(self.cookie_params, **kwargs['data'])

        # Invoke the Session.request method, passing the MAIN_URL for Letterboxd
        # by default and appending the suburl on the end. This will also work
        # if suburl is empty string.
        return super().request(request_type, f"{self.MAIN_URL}{suburl}", **kwargs)

    def __get_token(self):
        """ Get the __csrf token using a standard GET request 
        Called by __init__. """
        self.request("GET")
        token = self.cookies['com.xk72.webparts.csrf']
        return token

    @property
    def login_details(self):
        """ Convert username and password to dict for passing it as data to a request. """
        return {"username": self.username, "password": self.password}

    def __login(self):
        """ Attempt to login to Letterboxd.
        If result is not successful, attempt to return the error
        displayed by the webpage """

        # Make request to login form
        request = self.request("POST", suburl="/user/login.do", data=self.login_details)
        soup = make_soup(request)
        text = soup.text

        # Grab the result of the request from the HTML
        result_pattern = r"\"result\": \"(\w+)\""
        result = re.findall(result_pattern, text)[0]

        if result == "success":
            # Login successful
            print(f"Login successful! Welcome, {self.username}")
            return True

        # Pattern for getting messages in the event of the result being unsuccessful
        error_msg_pattern = r"\"messages\": \[([^\]]+)"

        try:
            # Try to find specific error in HTML
            error = re.findall(error_msg_pattern, text)[0]
        except IndexError:
            # Could not find specific error
            raise LoginException("Unknown Exception")
        else:
            raise LoginException(error)


# Create Sesion
SESSION = Session()

# Login
SESSION()
