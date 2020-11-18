""" For creating the requests.Session() that is used to make requests as the user. """

# Imports
import requests
from bs4 import BeautifulSoup as bs
import re
import pendulum

# Local Imports
import util
from exceptions import LoginException


USER_DETAILS = util.load_json_data("user_details")
USER_AGENT = util.load_json_data("user_agent")

def make_soup(request):
    """ Convert a request into a BeautifulSoup object. """
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
        self.year_range = (1860, pendulum.now()._start_of_decade().year+10)
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

    def request(self, method, suburl='', **kwargs):
        """ 
        ** Overloading **
        Customise request to default to main Letterboxd url.
        And to include the __CSRF token if it's a POST request. 
        """
        if method == "POST":
            if not kwargs.get("data"):
                kwargs['data'] = self.cookie_params
            else:
                kwargs['data'] = dict(self.cookie_params, **kwargs['data'])

        response =  super().request(
            method,
            url=f"{self.MAIN_URL}{suburl}",
            **kwargs
        )
        
        if not response.ok:
            response.raise_for_status()
        return response

    @property
    def login_details(self):
        """ Convert username and password to dict for passing it as data to a request. """
        return {"username": self.username, "password": self.password}

    def __get_token(self):
        """ Get the __csrf token and pass its value to an instance variable.
        Called by __init__. """
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


if __name__ == "__main__":
    # Test code
    # SESSION.request("GET", "film/black-swan/")

    SESSION.request("GET", "film/thisojaifasfj/")


