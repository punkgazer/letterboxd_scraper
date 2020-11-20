""" 
    This module mimics the behaviour of a user browsing through someone's watched films.
    
    You can get the film_ids a user has watched.
    You could also then use the (TODO) get_film_names() function to get the name of these films.
    
    You can also search by criteria (e.g. films released in 2007 that the user rated 4*)
"""

# Imports
import re
import requests
from types import SimpleNamespace

# Local Imports 
from session import SESSION, make_soup


class Watched():

    default_search = {
        'username': SESSION.username,
        'rated_only': False,
        'year': None,
        'genre': None,
        'service': None,
        'rating': None,
        'sort_by': 'name'
    }

    def __init__(self, username=SESSION.username):
        """
        Creates an object associated with a particular Letterboxd username.
        Keyword Arguments:

        username(str):
            Constraints :-
            - must be valid Letterboxd username
                Be sure to use the name in the URL, rather than the one in the profile,
                as the latter can be modified without change to the former.
        """
        self.username = username

    def __call__(self, **kwargs):
        """
        Returns a list of film_ids that correspond with the given search parameters.

        If not parameters are given, all film_ids in the watched_list will be returned

        Keyword Arguments:

            rated_only(bool)

            year(str or None):
                Options :-
                - 4 digits e.g. 1975
                - 4 digits + s e.g. 1970s # functions as decade

            genre(str or None):
                Contraints :-
                - must be in genre_list

            service(str or None):
                Constraints :-
                - must be in service_list

            rating(float or None):
                Constraints :-
                    - must be in inclusive range (0.5, 5)
                    - decimal must be 0.5 or 0, like Letterboxd ratings

            sort_by(str):
                How do you want the results sorted?
                Constraints :-
                - must be in sort_list
                Options :-
                - name
                - popular
                - date-earliest (release date)
                - date-latest
                - rating (average rating)
                - rating-lowest
                - your-rating (session user's rating)
                - your-rating-lowest
                - entry-rating (username's rating)
                - entry-rating-lowest
                - shortest (film length)
                - longest

            filters(list):
                Constraints :-
                - must be in SESSION's filters_dict
                Options :- (updated: 2020-11-20)
                - show-liked OR hide-liked
                - show-logged OR hide-logged
                - show-reviewed OR hide-reviewed
                - show-watchlisted OR hide-watchlisted
                - show-shorts OR hide-shorts
                - hide-docs
                - hide-unreleased

        Example suburl in full:
        - username/films/ratings/   year(or decade)/2015/genre/horror/on/amazon-gbr/by/rating
        """

        # Get valid filters for the request
        if 'filters' in kwargs:
            filters = self.get_valid_filters(kwargs.pop('filters'))
        else:
            filters = ''

        # Set cookie according to filters
        requests_jar = requests.cookies.RequestsCookieJar()
        requests_jar.set('filmFilter', filters)

        # Get the suburl for request
        suburl = self.build_suburl(**kwargs)
        
        film_ids = []
        page_num = 1
        while len(film_ids) % 18 == 0:
            print("page", page_num)
            request = SESSION.request("GET", suburl + f"page/{page_num}/", cookies=requests_jar)
            soup = make_soup(request)

            films_on_page = [i.find('div').get('data-film-id') for i in soup.find_all('li', class_='poster-container')]

            """ Edge case: the last page has exactly 18 films.
            The scraper goes to the next page which is blank, 
            This means that the films_on_page list is empty, so can use this to break from the loop. """
            if not films_on_page:
                break

            film_ids += films_on_page
            page_num += 1
        return film_ids

    def build_suburl(self, **kwargs):
        """ Returns a suburl passed on the suburl parameters passed to __call__(). """
        # TODO ensure sort_by in valid sort_options

        # Get any custom search parameters
        search_dict = {k:kwargs[k] if k in kwargs else v for k,v in self.default_search.items()}

        # Ensure lower case for string types
        search_dict = {k:v if type(v) is not str else v.lower() for k,v in search_dict.items()}

        # Create namespace for readability
        ns = SimpleNamespace(**search_dict)

        # Get parts of suburl
        username_str = (lambda x: f"{x}/")(ns.username)
        rated_only_str = 'rating/' if ns.rated_only else ''
        year_str = self.get_year_str(ns.year)
        genre_str = self.get_genre_str(ns.genre)
        service_str = self.get_service_str(ns.service)
        rating_str = self.get_rating_str(ns.rating)
        sort_by_str = (lambda x: f"by/{x}/" if x else '')(ns.rated_only)

        # Create full suburl
        suburl = f"{username_str}films/{rated_only_str}{rating_str}{year_str}{genre_str}{service_str}{sort_by_str}"
        return suburl

    """
    ** Methods for getting suburl parts for WatchedList search. **
    """
    @staticmethod
    def get_year_str(year):
        """ Converts a year to a section of the URL.
        r-type: str """
        if not year: 
            return ''

        # Ensure year has correct format
        elif not re.match(r"\d{4}s?", year): # 1975 or 1970s
            raise Exception("Invalid year/decade:", year)
        
        # Decade format
        elif 's' in year:
            if year[3] != "0":
                raise Exception(f"Mixed year/decade format: {year}! Please use one or other.")
            elif int(year[:-1]) not in range(SESSION.year_range):
                raise Exception(f"Invalid decade: {year}")
            return f"decade/{year}/"
        # Standard year format
        else:
            if int(year) not in range(SESSION.year_range):
                raise Exception(f"Invalid year: {year}")
            return f"year/{year}/"

    @staticmethod
    def get_genre_str(genre):
        """ Converts a genre to a section of the URL.
        r-type: str """
        if not genre:
            return ''
        elif genre not in SESSION.genre_list:
            raise Exception(f"Invalid genre: {genre}")
        return f"genre/{genre}/"

    @staticmethod
    def get_service_str(service):
        """ Converts a service to a section of the URL.
        r-type: str. """
        if not service:
            return ''
        elif service not in SESSION.service_list:
            raise Exception(f"Invalid service: {service}")
        return f"service/{service}/"

    @staticmethod
    def get_rating_str(rating):
        """ Converts a rating to a section of the URL.
        r-type: str. """
        if not rating:
            return ''

        # Edge cases where number after decimal is not 0 or .5
        elif not (after_decimal := divmod(rating, 1)[1] in (0.5, 0)):
            raise Exception(f"Must be 0 or 0.5 after the decimal to be a valid rating! Not {after_decimal}") 

        # Ensure that rating in inclusive 0.5 to 5 range
        elif not rating*2 in range(1,11):
            raise ValueError("Rating must be in inclusive range (0.5, 5)")

        rating = str(rating)
        if after_decimal == 0.5:
            # Taken from HTML encoding reference
            # This is the string placeholder for a 1/2 star 
            rating = rating[:-2] + "%C2%BD"
        return f"rated/{rating}/"

    """
    ** Filters **
    """

    @staticmethod
    def get_valid_filters(filters_tuple):
        """ 
        Given a tuple of filters (args),
        merges all into a valid filters string that can 
        subsequently be passed as a cookie to a search request

        Parameters:
        - Filters
            (e.g. show-watched)
        """
        # Check that format of each filter is correct
        pattern = r"^\w+-{1}\w+$" # >text-text<
        if not all([re.findall(pattern, i) for i in filters_tuple]):
            raise Exception("Invalid filters. Please use proper format.")
        
        # Checks each passed filter against those scraped from Letterboxd
        # to ensure that they are all valid
        filters = {}
        temp_args = list(filters_tuple)
        while temp_args:
            data_type, data_cat = temp_args.pop().split('-')
            if data_cat not in SESSION.filters_dict.keys():
                raise Exception(f"Invalid data_category: {data_cat}")
            elif data_type not in SESSION.filters_dict[data_cat]:
                raise Exception(f"Invalid data_type {data_type} for data_category: {data_cat}")

        filters = '%20'.join(filters_tuple)
        return filters
        

if __name__ == "__main__":
    watched = Watched()
    watched(
        username="lucindaj",
        filters=["show-reviewed"]
        )
    # results = watched(search_for="ratings", rating=1.0, filters=("hide-liked", "show-reviewed", "hide-shorts"))
    # print(results)