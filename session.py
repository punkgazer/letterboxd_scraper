""" For creating the requests.Session() that is used to make requests as a user. """

# Imports
import requests
from bs4 import BeautifulSoup as bs
import re
import json
import pendulum

# Local Imports
from exceptions import LoginException
import util


USER_DETAILS = util.load_json_data("user_details")
USER_AGENT = util.load_json_data("user_agent")

def make_soup(request):
    return bs(request.text, 'lxml')

class LetterboxdSession(requests.Session):
    """ Creates a session object that can be used to create requests as a user. """

    MAIN_URL = "https://letterboxd.com/"

    def __init__(self):
        super().__init__()

        # Add User Agent
        self.headers.update(USER_AGENT)

        # Set CSRF token
        token = self.__get_token()
        self.cookie_params = {'__csrf': token}

        # Login details
        self.logged_in = False
        self.username = USER_DETAILS['username']
        self.password = USER_DETAILS['password']

        ## Other
        self.year_range = (1860, pendulum.now()._end_of_decade())
        self.genre_list = self.__get_genre_list()

    def __str__(self):
        return f"Session (Logged in == {self.logged_in})"

    def __repr__(self):
        return f"<{type(self).__name__}>\nusername: {self.username}\nlogged_in: {self.logged_in}"

    def __call__(self):
        """ Login to Letterboxd if not already. """
        if self.logged_in:
            print("Already logged in")
        else:
            self.__login()
            self.logged_in = True

    def request(self, request_type, suburl='', **kwargs):
        """ Customise Request to default to main Letterboxd url.
        And to include CSRF token if it's a POST request with data """

        # Edge case
        if type(suburl) is not str: raise TypeError("Suburl must be string or empty string")

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

    @property
    def login_details(self):
        """ Convert username and password to dict for passing it as data to a request. """
        return {"username": self.username, "password": self.password}

    def __get_token(self):
        """ Get the __csrf token and pass its value to an instance variable
        Called by __init__ """
        self.request("GET")
        token = self.cookies['com.xk72.webparts.csrf']
        return token

    def __login(self):
        """ Attempt to login to Letterboxd.
        If result is not successful, attempt to return the error
        displayed by the webpage """

        request = self.request("POST", suburl="/user/login.do", data=self.login_details)
        soup = make_soup(request)
        text = soup.text

        result_pattern = r"\"result\": \"(\w+)\""
        result = re.findall(result_pattern, text)[0]

        if result == "success":
            # Login successful
            print(f"Login successful! Welcome, {self.username}")
            return True

        error_msg_pattern = r"\"messages\": \[([^\]]+)"
        try:
            # Try to find specific error in HTML
            error = re.findall(error_msg_pattern, text)[0]
        except IndexError:
            # Could not find specific error
            raise LoginException("Unknown Exception")
        else:
            raise LoginException(error)

    def __get_genre_list(self):
        """ Returns the list of genres you can search by on Letterboxd. """
        request = self.request("GET", "films/")
        soup = make_soup(request)
        return [i.text.lower() for i in soup.find_all('a', attrs={'class': 'item', 'href': re.compile('/films/genre/')})]


# Create Session
SESSION = LetterboxdSession()

# Login
SESSION()

SESSION.request("GET", "film/black-swan/")



