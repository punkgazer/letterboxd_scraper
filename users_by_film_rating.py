""" 
    Find users who've rated a film a particular rating.
    If a film has received a lot of ratings, this may not work for middle-of-the-pack ratings (e.g. 4/10),
    due to how Letterboxd only allows a maximum of 10 pages when sorting either from highest to lowest or vice versa. 
"""

# Imports
import re

# Local imports
from session import SESSION, make_soup
from film_info import FilmInfo


class FilmRaters():
    
    ## Max pages Letterboxd allows
    page_limit = 10

    ## Ratings per page
    ratings_per_page = 500

    ## Max results in total
    max_results = page_limit * ratings_per_page

    ## suburls for getting ratings
    suburl_rating_highest = 'ratings/'
    suburl_rating_lowest = 'ratings/by/entry-rating-lowest/'

    def __init__(self, film):
        """ Ensure film in correct format """
        if not film or type(film) is not str:
            raise Exception(f"Invalid film name {film}, must be string")
        self.film = film.replace(' ', '-')

        ## Get information about the film's overall rating and ratings spread
        try:
            film_ratings = FilmInfo(self.film).ratings
            self.film_ratings = [v for k,v in sorted(film_ratings.items())]
        except:
            raise Exception("Failed to obtain film data for film:", self.film)

    def __repr__(self):
        """ Example:
            < FilmRaters  Film: Citizen-kane > """
        return f"< {self.__class__.__name__}\tFilm: {self.film.title()} >"

    def __len__(self):
        """ Returns the total number of ratings a film has. """
        return sum(self.film_ratings)

    @property
    def suburl_film(self):
        return f"film/{self.film}/"

    def __get_route(self, target_rating, target_rating_count):
        """ Determines the method (in a non-pythonic sense) by which
        to sort the request url in order to make sure all results 
        can be obtained.
        It will return the appropriate suburl, whether it be
        a regular or reverese (starting from the lowest rating) search.
        In addition, it will return the page number at which
        the rating starts. """

        ## Total ratings lower and higher than the target rating.
        # For example if the target_rating is 3, 
        # and there are 10 ratings of 1 and 5 ratings of 2,
        # the lower_ratings would be 15
        lower_ratings = sum([v for v in self.film_ratings[0:target_rating-1]])      
        higher_ratings = sum([v for v in self.film_ratings[target_rating+1:len(self.film_ratings)]])

        # Cannot get users with this rating because there are not enough pages to get to the middle
        # ratings. Since you can only view ratings from the top or bottom.
        if not any([i < self.max_results for i in (lower_ratings, higher_ratings)]):
            return False

        # There are less ratings above than below the target_rating
        # So we'll scrape by sorting ratings highest to lowest
        elif higher_ratings <= lower_ratings:
            page_start = ( higher_ratings // self.ratings_per_page ) + 1
            page_end = ( ( higher_ratings + target_rating_count ) // self.ratings_per_page ) + 1
            sort_by = self.suburl_rating_highest
        
        # The opposite is true: there are less ratings below than above
        # So we'll scrape by lowest to highest
        elif lower_ratings < higher_ratings:
            page_start = ( lower_ratings // self.ratings_per_page ) + 1
            page_end = ( ( lower_ratings + target_rating_count ) // self.ratings_per_page ) + 1
            sort_by = self.suburl_rating_lowest

        # Ensure that target_rating has not pushed us over maximum page limit
        if page_end > 10: page_end = 10
        
        return sort_by, page_start, page_end

    def __call__(self, target_rating=4, limit=None):
        """ Returns a list of users who've rated a film
        a given rating.
        In some instances there are too many ratings to obtain middle-ground
        ratings like 5 or 6. This is because Letterboxd limits the number of pages
        to 10, and you can only sort by highest or lowest.
        In such instances, the function will simply return False. 
        
        r-type: list (or False, if could not get results)
        """

        ## Edge cases
        if type(target_rating) is not int or target_rating not in range(1,11):
            raise ValueError("Rating must be int value within inclusive range 1-10")

        target_rating_count = self.film_ratings[target_rating-1]

        ## Get route to getting results
        if not (route := self.__get_route(target_rating, target_rating_count)):
            # Could not get any results
            return False
        sort_by, page_start, page_end = route

        ## Begin scraping process
        users = [] # results list
        if not limit: limit = target_rating_count # loop will break at result limit
        suburl = f"{self.suburl_film}{sort_by}"
        page_num = page_start
        while page_num in range(page_start, page_end+1) and len(users) < limit:

            ## Make request to each page
            full_suburl = f"{suburl}page/{page_num}"
            request = SESSION.request("GET", full_suburl)
            soup = make_soup(request)

            ## Could not find tag associated with target_rating
            if not (target_rating := soup.find('span', class_=f'rated-large-{target_rating}')):
                if not users:
                    # Failed to get any results
                    raise Exception("Could not get results")
                else:
                    # There is no section for the int(rating) on this page
                    break
            
            # Parent tag that contains the information on users listed under each rating
            rating_group = target_rating.parent.parent
            page_results = [i.get('href')[1:-1] for i in rating_group.find_all('a', class_='avatar')]

            users += page_results
            page_num += 1

        ## If list count exceeds limit, remove the extra data
        if len(users) > limit:
            return users[0:limit]
        return users

    
if __name__ == "__main__":

    F = FilmRaters("the-exorcist-iii")
    print(F(target_rating=2))