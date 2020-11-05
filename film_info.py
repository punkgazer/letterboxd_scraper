""" . """

# Import
import json
import re

# Local imports
from session import SESSION, make_soup


class FilmRating():


    def __init__(self, film_link):
        self.film_link = film_link
        self.__make_rating_soup()
        self.__check_if_obscure()

    def __make_rating_soup(self):
        """ Returns the rating soup for the film, from which ratings can be extracted. """
        suburl = f"csi/film/{self.film_link}/rating-histogram/"
        request = SESSION.request("GET", suburl)
        self.rating_soup = make_soup(request)

    def __check_if_obscure(self):
        """ Checks the ratings soup to ensure that the film does not have enough ratings
        to be given a standard rating - otherwise creating an instance of this class
        is pointless because grabbing the standard rating would be easier. """
        if not self.ratings:
            self.is_obscure = True
        else:
            self.is_obscure = bool(self.rating_soup.find('a', title=re.compile("Not enough ratings")))

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
    def total_ratings(self, rating=None):
        """ Returns the total number of ratings. 
        NOTE: this should align with number on the user's profile. Though it is taken from reading
        the histogram data collected from self.ratings
        r-type: int """
        if not self.ratings:
            return 0
        return sum(self.ratings.values())

    @property
    def avg_rating(self, round_to=2):
        """ Computes the average of the ratings collected in self.ratings.
        r-type: float """
        if not self.ratings:
            return None
        pre_rounded_score = sum([s*q for s,q in self.ratings.items()])/self.total_ratings
        return round(pre_rounded_score, round_to)


class FilmInfo():
    
    def __init__(self, film_path):
        self.path = film_path
        self.page_wrapper = self.__get_info_soup()
        self.__get_film_data()
        self.rating = FilmRating(self.path)

    def __repr__(self):
        cls_name = self.__class__.__name__
        string = f"\tPath: {self.path}"
        string += f"\tName: {self.name}"
        return f"< {cls_name}{string} >"

    @property
    def suburl(self):
        """ Returns the suburl for this film.
        Used for making the request to get the information
        for information on the film listed below. """
        return f"film/{self.path}/"

    def __get_info_soup(self):
        request = SESSION.request("GET", self.suburl)
        soup = make_soup(request)
        page_wrapper = soup.find('div', id='film-page-wrapper')
        return page_wrapper

    def __get_film_data(self):
        
        ## Info
        info = self.page_wrapper.find('div', class_='film-poster')
        self.id_ = info.get('data-film-id')
        self.name = info.get('data-film-name')
        self.release_year = info.get('data-film-release-year')
        self.poster_url = info.get('data-poster-url')

        ## Details
        tab_details = self.page_wrapper.find('div', id="tab-details")
        language_string = str(tab_details.find('a', attrs={'href': re.compile("/films/language/")}).get('href'))
        country_string = str(tab_details.find('a', attrs={'href': re.compile("/films/country/")}).get('href'))
        self.language = language_string.split('language/')[1][:-1]
        self.country = country_string.split('country/')[1][:-1]

        ## Genres
        tab_genres = self.page_wrapper.find('div', id="tab-genres")
        genre_links = tab_genres.find_all('a', class_='text-slug', attrs={'href': re.compile('/films/genre/')})
        self.genres = [i.get('href').split('genre/')[1][:-1] for i in genre_links]

    @property
    def film_length(self):
        """ Uses the page wrapper to grab the film_length. """
        footer = self.page_wrapper.find('p', class_=['text-link', 'text-footer'])
        text = footer.text
        film_length = re.findall(r"([\d,]+)", text)[0]
        return int(film_length)

    
if __name__ == "__main__":

    test = FilmInfo("black-swan")
    print(test.name)
    print(test.rating)

    

    



