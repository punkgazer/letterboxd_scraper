""" 
    For creating the requests.Session() that is used to make requests as the user. 
"""

# Imports
import requests
from bs4 import BeautifulSoup as bs
import re
import pendulum
import json
from types import SimpleNamespace

# Local Imports
import util
from exceptions import LoginException, LetterboxdException

## FILE NAMES
FN_USER_DETAILS = "user_details"

# USER_DETAILS = util.load_json_data("user_details")
USER_AGENT = util.load_json_data("user_agent")

def make_soup(request):
    """ Convert a request into a BeautifulSoup object. """
    return bs(request.text, 'lxml')


class LetterboxdSession(requests.Session):
    """ Creates a session object that can be used to create requests as a user. """

    MAIN_URL = "https://letterboxd.com/"

    def __init__(self):
        super().__init__()

        ## Add User Agent
        self.headers.update(USER_AGENT)

        ## Set CSRF token
        token = self.__get_token()
        self.cookie_params = {'__csrf': token}

        ## Login details
        self.logged_in = False

        # If user details not found, get from user
        self.login_details = self.get_user_details()

        ## Search Options & Available filters
        response = self.request("GET", f"{self.username}/films/")
        self.__search_options = make_soup(response)

        self.year_range = (1860, pendulum.now()._start_of_decade().year+10)
        self.genre_list = self.__get_genre_list()
        self.service_list = self.__get_service_list()
        self.filters_dict = self.__get_filters_dict()

    def __str__(self):
        return f"Session (Logged in == {self.logged_in})"

    def __repr__(self):
        return f"<{type(self).__name__}>\nusername: {self.username}\nlogged_in: {self.logged_in}"

    @property
    def username(self):
        return self.login_details.username

    @property
    def password(self):
        return self.login_details.password

    def get_user_details(self):
        """ 
        Makes use of get_details_from_file and get_details_from_user functions.
        Returns the user's data
        r-type: SimpleNamespace.
        """
        if not (user_details := self.get_details_from_file()):
            self.get_details_from_user()
            user_details = self.get_details_from_file()
        return user_details

    @staticmethod
    def get_details_from_file():
        """
        Gets the user's details form the user details json file.
        r-type: SimpleNamespace.
        """
        user_details = util.load_json_data(FN_USER_DETAILS)
        assert list(user_details.keys()) == ["username", "password"]

        return SimpleNamespace(**user_details)

    def get_details_from_user(self):
        """ 
        If the details are empty, this func is called.
        
        It prompts the user for their Letterboxd username and password,
        which is required to log in and, for example, manipulate the user's lists.

        r-type: None (rather, func is called to override details)
        """
        while True:
            print("\nPlease enter your details\n")
            username = input("Letterboxd username: ")
            password = input("Letterboxd password: ")

            if not all([username, password]):
                print("Please provide both a username and password!")
                continue

            # Confirm details with user
            if not util.yn(f"Confirm\nUsername:{username}\nPassword:{password}\n"):
                continue
            
            new_details = {'username': username, 'password': password}
            self.override_details(new_details)
            return

    @staticmethod
    def override_details(new_details):
        """ Overrides any data in the user details file, with new_details. """
        with open(FN_USER_DETAILS) as jf:
            json.dump(new_details, jf)        

    def __call__(self):
        """ Login to Letterboxd if not already. """

        # Already logged in - __call__ func not needed
        if self.logged_in:
            print("Already logged in")
            return
            
        self.__login()

    def request(self, method, suburl='', **kwargs):
        """ 
        ** Overloading **
        Customise request to default to main Letterboxd url.
        And to include the __CSRF token if it's a POST request. 
        """
        if method == "POST":

            # No data passed. Create default data
            if not (data := kwargs.get("data")):
                kwargs['data'] = self.cookie_params

            else:
                # If data type is SimpleNamespace, convert to dict
                if isinstance(data, SimpleNamespace): 
                    kwargs['data'] = {i:j for i,j in data.__dict__.items()}
                
                # Add default data to passed data
                kwargs['data'] = dict(self.cookie_params, **kwargs['data'])

        response =  super().request(
            method,
            url=f"{self.MAIN_URL}{suburl}",
            **kwargs
        )
        
        if not response.ok:
            response.raise_for_status()
        
        self.get_html_response_dict(response)

        return response

    @staticmethod
    def get_html_response_dict(response):
        try:
            message_dict = json.loads(response.text)
        except:
            return

        if message_dict['result']:
            return 
        
        # The keys that exist within the message that we want to print out when raising the Exception
        error_msg_keys = [k for k in ('messages', 'errorCodes', 'errorFields') if k in message_dict.keys()]
        
        message = ''
        for key in error_msg_keys:
            message += f"\n{key}: "
            while (values := message_dict[key]):
                message += f"\n\t{values.pop(0)}"
        
        message = message.rstrip()

        # Raise the Exception because the message_dict['result'] evaluated to false
        raise LetterboxdException(message)

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

        response = self.request("POST", suburl="/user/login.do", data=self.login_details)
        soup = make_soup(response)
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
        return [i.text.lower() for i in self.__search_options.find_all('a', attrs={'class': 'item', 'href': re.compile('/films/genre/')})]

    def __get_service_list(self):
        """ Returns a list of services you can search by on Letterboxd.
        NOTE: I think these may be specific to the user. 
        The code should still work since this is scraped using the user's session. """
        return [i.text.strip() for i in self.__search_options.find('ul', id='services-menu').find_all('a')]

    def __get_filters_dict(self):
        """ Returns a list of the filters that can be applied to the session
        (e.g. hide-reviewed)
        """
        filter_li_tags = self.__search_options.find_all('li', class_='js-film-filter')
        data_categories = set([i.get('data-category') for i in filter_li_tags])
        filters = {i:[] for i in data_categories}
        [filters[i.get('data-category')].append(i.get('data-type')) for i in filter_li_tags]
        return filters



# Create Session
SESSION = LetterboxdSession()

# Login
SESSION()


if __name__ == "__main__":
    pass
    # Test code
    # SESSION.request("GET", "film/black-swan/")
    # SESSION.request("GET", "film/thisojaifasfj/")
    # response = SESSION.request("GET", "lostinstyle/list/test003/")
    # soup = make_soup(response)
