""" 
    For getting other users' names within a user's network. 
"""

# Local Imports
from session import SESSION, make_soup


def __get_people(soup):
    """ Scrapes the profile links (original usernames) of all people on a given person's followers/following page. """
    return [person.find('a').get('href').replace('/', '') for person in soup.find_all("td", class_="table-person")]

def get_following(username=SESSION.username):
    """ Returns a list of the users a given user follows. """
    request = SESSION.request("GET", f"{username}/following/")
    soup = make_soup(request)
    return __get_people(soup)

def get_followers(username=SESSION.username):
    """ Returns a list of the users a given user is followed by. """
    request = SESSION.request("GET", f"{username}/followers/")
    soup = make_soup(request)
    return __get_people(soup)

def get_blocked():
    """ Returns a list of the users in your block list.
    NOTE: You can only see who you've blocked, hence there is no
    username argument for this function unlike following and followers. """
    username = SESSION.username
    request = SESSION.request("GET", f"{username}/blocked/")
    soup = make_soup(request)
    return __get_people(soup)