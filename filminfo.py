
# Imports
import re
import json

# Local Imports
from session import SESSION, make_soup

class FilmInfo():

    def __init__(self, film_path):
        self.film_path = film_path
        self.__get_soup()
        self.__get_film_data()

    @property
    def suburl(self):
        """ Returns the suburl for this film.
        Used for making the request to get the information
        for information on the film listed below. """
        return f"film/{self.film_path}/"

    def __get_soup(self):
        request = SESSION.request("GET", self.suburl)
        soup = make_soup(request)
        self.page_wrapper = soup.find('div', id='film-page-wrapper')

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
        footer = self.page_wrapper.find('p', class_=['text-link', 'text-footer'])
        text = footer.text
        film_length = re.findall(r"([\d,]+)", text)[0]
        return int(film_length)


if __name__ == "__main__":

    FI = FilmInfo('the-happening')
    print(FI.film_length)
