""" Main module. """

# Imports
import requests
from bs4 import BeautifulSoup as bs
import re
import json

# Local Imports
from exceptions import LoginException


MAIN_URL = "https://letterboxd.com/"
# Load user details
with open("data/user_details.json") as jf:
    USER_DETAILS = json.load(jf)

class Session(requests.Session):

    def __init__(self):
        super().__init__()

        # Add User Agent
        self.headers.update({'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36"})

        # Set CSRF token
        self.get(MAIN_URL)
        token = self.cookies['com.xk72.webparts.csrf']
        self.cookie_params = {'__csrf': token}

        # Login Details
        self.logged_in = False
        self.login_details = USER_DETAILS

    def __str__(self):
        return f"Session (Logged in == {self.logged_in})"

    def __call__(self):
        """ Login if not already logged in. """
        if self.logged_in:
            print("Already logged in!")
        else:
            self.__login()
            self.logged_in = True
        
    def __login(self):
        """ Attempt to login to Letterboxd. """
        request = self.post(MAIN_URL + '/user/login.do', data=dict(self.cookie_params, **self.login_details))
        text = bs(request.text, 'lxml').text
        
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
            raise LoginException("Unknown Exception")
        else:
            raise LoginException(error)
        
SESSION = Session()
SESSION()

if __name__ == "__main__":
    # Testing code
    r = SESSION.get("https://letterboxd.com/films/ajax/popular/decade/2020s/genre/horror/size/small/")
    soup = bs(r.text, 'lxml')
    print(soup)
