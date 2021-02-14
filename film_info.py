"""
    Get information about a film given its url.
"""

# Imports
import re

# Local Imports
from session import SESSION, make_soup


class FilmInfo():
    """ For getting information about a given film on Letterboxd. """

    def __init__(self, film_path):
        """
        Parameters:
        - film_path (str): the path to the film on Letterboxd 
            e.g. black-swan
            NOTE: DO NOT include 'film/' or trailing backslash
        """

        # Remove '/film/' part of path if passed
        # As this will be added later via property suburl
        pattern = r"(/film/)?([\w-]+)/?"

        try:
            self.path = re.findall(pattern, film_path)[0][1]
        except:
            raise IndexError("Could not extract film path from string:", film_path)

        # Film page
        self.page_wrapper = self.__get_info_soup()
        
        # Load the film's properties into memory
        self.__get_film_info()

        # Ratings are stored on a separate page
        # So a second request is necessesary
        self.rating_soup = self.__get_rating_soup()

    def __repr__(self):
        cls_name = self.__class__.__name__
        string = f"\tPath: {self.path}"
        string += f"\tName: {self.name}"
        return f"< {cls_name}{string} >"

    def __str__(self):
        s = ''
        s += f"Name: {self.name}"
        if self.director: s += f"\nDirector: {self.director}"
        if self.cast: s += f"\nCast: {self.cast}"
        if self.genres: s += f"\nGenre(s): {self.genres}"
        if self.release_year: s += f"\nYear: {self.release_year}"
        if self.language: s += f"\nLanguage: {self.language}"
        if self.country: s+= f"\nCountry: {self.country}"
        if self.ratings: s+= f"\nRating: {self.avg_rating} ({self.true_avg_rating})"
        return s

    @property
    def suburl(self):
        """ Returns the suburl for this film
        Used for making the request to the film's page on Letterboxd. """
        return f"film/{self.path}/"

    # Soup Getters

    def __get_info_soup(self):
        """ Go the main film_page and grab the soup. 
        r-type: BeautifulSoup"""
        request = SESSION.request("GET", self.suburl)
        soup = make_soup(request)
        page_wrapper = soup.find('div', id='film-page-wrapper')
        return page_wrapper

    def __get_rating_soup(self):
        """ The film's rating info is loaded from a different page
        Hence we make the request to this separate page to get it
        r-type: BeautifulSoup """
        suburl = f"csi/film/{self.path}/rating-histogram/"
        request = SESSION.request("GET", suburl)
        return make_soup(request)

    ## Info getters

    def __get_film_info(self):
        """ Grab the information available from the main page.
        - id
        - name
        - release year
        - poster_url
        - language
        - country
        - genre(s)
        - director
        - cast
        r-type: None
        All information is set to instance variables
        """
        
        ## --- Info ---
        
        info = self.page_wrapper.find('div', class_='film-poster')
        
        self.id_ = info.get('data-film-id')
        self.name = info.get('data-film-name')
        self.poster_url = info.get('data-poster-url')

        try:
            self.release_year = info.get('data-film-release-year')
        except:
            self.release_year = None

        ## --- Details ---

        tab_details = self.page_wrapper.find('div', id="tab-details")

        # Language
        try:
            language_string = str(tab_details.find('a', attrs={'href': re.compile("/films/language/")}).get('href'))
        except:
            self.language = None
        else:
            self.language = language_string.split('language/')[1][:-1]

        # Country
        try:       
            country_string = str(tab_details.find('a', attrs={'href': re.compile("/films/country/")}).get('href'))
        except:
            self.country = None
        else:        
            self.country = country_string.split('country/')[1][:-1]

        ## Genres
        try:
            tab_genres = self.page_wrapper.find('div', id="tab-genres")
            genre_links = tab_genres.find_all('a', class_='text-slug', attrs={'href': re.compile('/films/genre/')})
        except:
            self.genres = []
        else:
            self.genres = [i.get('href').split('genre/')[1][:-1] for i in genre_links]

        ## Cast
        try:
            tab_cast = self.page_wrapper.find('div', id="tab-cast")
            cast_list = tab_cast.find('div', class_='cast-list')
        except:
            self.cast = []
        else:
            self.cast = [i.text for i in cast_list.find_all('a')]
        
        ## Director
        try:
            film_header = self.page_wrapper.find('section', id='featured-film-header')
            self.director = film_header.find('a', href=re.compile('director')).text
        except:
            self.director = None

    @property
    def film_length(self):
        """ Uses the page wrapper to grab the film_length. """
        footer = self.page_wrapper.find('p', class_=['text-link', 'text-footer'])
        text = footer.text
        film_length = re.findall(r"([\d,]+)", text)[0]
        return int(film_length)

    ## Rating getters

    @property
    def ratings(self):
        """ Scrapes the user's Letterboxd profile to get the 
        number of times they have rated a film each score between 0.5 and 5.0
        Returns a dict of each score and the corresponding the user has rated that score.
        r-type: dict. """
        if not self.rating_soup.text:
            return None

        """ There are 10 li tags, 1 for each score 0.5 -> 5
        Within these li tags, there is a link provided that the user has rated >1 film with that rating. """
        ratings_data = [i.find('a') for i in self.rating_soup.find_all('li', class_='rating-histogram-bar')]
        if len(ratings_data) != 10:
            raise ValueError("Number of possible rating scores should be 10, not", len(ratings_data))
        
        """ This link has an attribute 'title', at the start of which is the value for the number 
        of times the user has rated a movie that score. """
        score_count_pattern = r"[\d,]+"
        get_quantity = lambda x: int(re.findall(score_count_pattern, x.get('title'))[0].replace(',', '')) if x else 0
        score_quantities = [get_quantity(i) for i in ratings_data]

        return {score+1: quantity for score, quantity in enumerate(score_quantities)} # {0.5: 44, 1.0: 108... 5.0: 91}

    @property
    def num_ratings(self):
        return self.get_total_ratings()

    def get_total_ratings(self, rating=None):
        """
        Returns the count of a given rating for the film (e.g number of 4* ratings)
        
        If no argument passed, will return total ratings.
        However, you should use num_ratings property to get this info.

        Params:
        - rating (int), inclusive range 1 to 10.
        r-type: int """
        if not self.ratings:
            return 0
        elif not rating:
            return sum(self.ratings.values())
        return self.ratings[rating]

    @property
    def total_rating_score(self):
        return sum([s*q for s,q in self.ratings.items()])

    @property
    def true_avg_rating(self):
        """ Computes the average of the ratings collected in self.ratings.
        r-type: float """
        if not self.ratings:
            return None
        return self.total_rating_score / self.num_ratings

    @property
    def avg_rating(self):
        return self.get_avg_rating()

    def get_avg_rating(self, round_to=0):
        """
        If a film has been rated one time with a 1/2 star rating, it is not the worst
        film on Letterboxd.

        Use this method (as opposed to the property avg_rating) if you need to round the score.

        params:
        - round_to (int), 0 or positive
        """
        num_ratings = self.num_ratings

        # Film has 30 ratings or above - just use standard Letterboxd ratings
        if not self.is_obscure: return self.true_avg_rating

        # Film has under 30 ratings - create some fake ratings with average score.
        fake_ratings = (30 - num_ratings) / 2

        score = self.total_rating_score
        average_score = 5
        
        score += fake_ratings * average_score

        pre_rounded_score = score / (num_ratings + fake_ratings)
        return round(pre_rounded_score, round_to)

    @property
    def is_obscure(self):
        """ Checks the ratings soup to ensure that the film does not have enough ratings
        to be given a standard rating - otherwise creating an instance of this class
        is pointless because grabbing the standard rating would be easier. """
        return self.num_ratings < 30

    
if __name__ == "__main__":

    for film in ['black-swan', 'coherence', 'triangle', 'shrek', 'citizen-kane']:
        test = FilmInfo(film)