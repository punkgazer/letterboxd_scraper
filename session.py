""" For creating the requests.Session() that is used to make requests as a user. """

# Imports
import requests
from bs4 import BeautifulSoup as bs
import re
import json # NOTE for getting user details. TODO May change method of doing this later

# Local Imports
from exceptions import LoginException


MAIN_URL = "https://letterboxd.com/"

# Get user details from file
with open("data/user_details.json") as jf:
    USER_DETAILS = json.load(jf)

def make_soup(request):
    return bs(request.text, 'lxml')

class LetterboxdSession(requests.Session):
    """ Creates a session object that can be used to create requests as a user. """
    def __init__(self):
        super().__init__()

        # Add User Agent
        self.headers.update({'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36"})

        # Set CSRF token
        self.__set_token()

        # Login details
        self.logged_in = False
        self.username = USER_DETAILS['username']
        self.password = USER_DETAILS['password']

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

    def get(self, suburl=None, **kwargs):
        """ Customise Get Request to default to main Letterboxd url. """
        full_url = MAIN_URL
        if suburl: full_url += suburl
        return super().get(full_url, **kwargs)

    def post(self, suburl=None, data={}, **kwargs):
        """ Customise the post request to include the cookies. """
        full_url = MAIN_URL
        if suburl: full_url += suburl
        return super().post(full_url, data=dict(self.cookie_params, **data), **kwargs)

    @property
    def login_details(self):
        """ Convert username and password to dict for passing it as data to a request. """
        return {"username": self.username, "password": self.password}

    def __set_token(self):
        """ Get the __csrf token and pass its value to an instance variable
        Called by __init__ """
        self.get()
        token = self.cookies['com.xk72.webparts.csrf']
        self.cookie_params = {'__csrf': token}

    def __login(self):
        """ Attempt to login to Letterboxd.
        If result is not successful, attempt to return the error
        displayed by the webpage """
        request = self.post(suburl = "/user/login.do", data = self.login_details)
        soup = make_soup(request)
        text = soup.text

        result_pattern = r"\"result\": \"(\w+)\""
        result = re.findall(result_pattern, text)[0]

        if result == "success":
            # Login successful
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


# Create Session
SESSION = LetterboxdSession()

# Login
SESSION()



