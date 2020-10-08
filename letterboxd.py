""" Grabs general information about Letterboxd such as the current genre list. """

from session import SESSION, MAIN_URL
from util import make_soup
import re

def __genre_list():
    """ Returns the list of genres you can search by on Letterboxd. """
    films_suburl = "films/"
    request = SESSION.get(f"{MAIN_URL}{films_suburl}")
    soup = make_soup(request)
    return [i.text for i in soup.find_all('a', attrs={'class': 'item', 'href': re.compile('/films/genre/')})]

GENRE_LIST = __genre_list()