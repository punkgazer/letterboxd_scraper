
# Imports
import re
import requests
from types import SimpleNamespace

# Debugging
import logging
logging.basicConfig(level=logging.WARNING)

# Local Imports
from session import SESSION, make_soup, MAIN_URL


class Watched():

    def __init__(self, **kwargs):

        """
        Keyword Arguments:

            username(str): 
                Letterboxd username

            search_for(str): 
                What do you want to search for?
                Options :-
                - Watched
                - Ratings
                - Diary
                - Reviews
            
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
                - must be in filters_list
                Options :-
                - show-liked OR hide-liked
                - show-logged OR hide-logged
                - show-reviewed OR hide-reviewed
                - show-watchlisted OR hide-watchlisted
                - show-shorts OR hide-shorts
                - hide-docs
                - hide-unreleased
        """

        # If you are searching for a specific rating
        # Must do so by ratings view
        if "rating" in kwargs:
            kwargs["search_for"] = "ratings"

        # Build URL with remaining keyword arguments
        self.__get_suburl(**kwargs)

        # Set filters to empty
        self.filters = ''

    def __call__(self):
        """ Returns the film_ids for the instance's search. """

        # Add cookies 
        requests_jar = requests.cookies.RequestsCookieJar()
        requests_jar.set("filmFilter", self.filters)

        # Make request with cookies
        
        film_ids = []
        page_num = 1
        while len(film_ids) % 18 == 0:
            print("page", page_num)
            request = SESSION.request("GET", self.suburl + f"page/{page_num}/", cookies=requests_jar)
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

    def __get_suburl(self, **kwargs):

        """
        Example URL:
        username/films/ratings/   year(or decade)/2015/genre/horror/on/amazon-gbr/by/rating
        """

        default_search = {
            'username': SESSION.username,
            'search_for': '',
            'year': None,
            'genre': None,
            'service': None,
            'rating': None,
            'sort_by': 'name'
        }

        # TODO ensure genre in genre_list
        # TODO ensure service in service_list
        # TODO ensure >all< filter(s) in filters list
        # TODO ensure sort_by in valid sort_options

        # Get any custom search parameters
        search_dict = {k:kwargs[k] if k in kwargs else v for k,v in default_search.items()}

        # Ensure lower case for string types
        search_dict = {k:v if type(v) is not str else v.lower() for k,v in search_dict.items()}

        # Create namespace for readability
        ns = SimpleNamespace(**search_dict)

        def get_year_str(year):
            """ Converts a year to a section of the URL. """
            if not year: 
                return ''

            # Ensure year has correct format
            elif not re.match(r"\d{4}s?", year): # 1975 or 1970s
                raise Exception("Invalid year/decade:", year)
            
            elif 's' in year: 
                return f"decade/{year}/"
            else:
                return f"year/{year}/"

        def get_rating_str(rating):
            """ Converts a rating to a section of the URL. """
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

        # Edge cases with ratings
        if ns.rating and ns.search_for != "ratings":
            raise Exception("Tried to search for specific rating in non-ratings view")
        elif ns.search_for == "ratings" and not ns.rating:
            raise Exception("You tried to search by ratings but did not provide a specific rating!")

        # Get parts of suburl
        username_str = (lambda x: f"{x}/")(ns.username)
        search_str = (lambda x: f"{x}/" if x else '')(ns.search_for)
        year_str = get_year_str(ns.year)
        genre_str = (lambda x: f"genre/{x}/" if x else '')(ns.genre)
        service_str = (lambda x: f"service/{x}/" if x else '')(ns.service)
        rating_str = get_rating_str(ns.rating)
        sort_by_str = (lambda x: f"by/{x}/" if x else '')(ns.sort_by)

        # Create full suburl
        self.suburl = f"{username_str}films/{search_str}{rating_str}{year_str}{genre_str}{service_str}{sort_by_str}"
        
        logging.debug(f"final url: {self.suburl}")

    def add_filters(self, *args):
        """ Add filters to results (e.g. show only liked films).
        This function sets the filters instance variable that is
        used by the __call__ func when generating search results. """
        if not args:
            self.filters = ''
            return

        args = [i.strip().replace(' ', '-') for i in args]

        filter_types = [i.split('-')[-1] for i in args]
        if len(filter_types) != len(set(filter_types)):
            raise Exception("Can only accept one of each filter type")

        self.filters = '%20'.join(args)


if __name__ == "__main__":
    # watched = Watched(search_for="ratings", rating=1.0)
    # watched.add_filters("hide liked", "show reviewed", "hide shorts")
    # results = watched()
    
    # print(results)
    # films_for_list = Watched(username="theninthheart", rating=0.5)
    # print(films_for_list())

    from social_network import get_following
    from list_maker import LetterboxdList
    
    people_i_follow = get_following()
    
    films = []
    i = 0
    for person in people_i_follow:
        search = Watched(username=person, rating=5)
        films += search()

    films = [{"filmId": i} for i in set(films)]

    test_list = LetterboxdList.new_list(
        "5 star films according to my followers", 
        entries=films, 
        description="Films those I follow have rated 5 stars",
        tags=["best"],
        public=True)



    




        