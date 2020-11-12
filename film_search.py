""" For searching for films by genre and decade/year. """

# Imports
import re

# Debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Local Imports
from session import SESSION, make_soup

class FilmSearch():
    """ Search for all the films (unless a page limit is specificed) for
    a given year, genre, or both. """

    def __init__(self, genre=None, decade=None, year=None, page_limit=None):

        # Ensure lower case otherwise requests don't work
        if genre: genre = genre.lower()

        # Ensure valid data
        if year and decade:
            raise Exception("You cannot search by both decade and year!")  
        if year and year not in range(SESSION.year_range):
            raise ValueError(f"Invalid year: {year}")
        if decade and decade not in range(*SESSION.year_range, 10):
            raise ValueError(f"Invalid decade: {decade}")
        if genre and genre not in SESSION.genre_list:
            raise ValueError(f"Inavlid genre: {genre}")

        # Convert decade to string for making requests
        if decade: decade = f"{decade}s"

        self.genre = genre
        self.year = year
        self.decade = decade
        self.page_limit = page_limit

    def __call__(self):
        """ Return film data as a list of dicts, each dict containing 'id' and 'link'
        r-type: list of dicts """
        page_num = 0
        suburl = self.suburl
        film_data = []

        # Identify stopping point for while loop
        pages_to_scrape = self.num_pages if not self.page_limit else min(self.num_pages, self.page_limit)

        logging.debug(f"Scraping data\nGenre: {self.genre}\nDecade: {self.decade}\nYear: {self.year}\n Pages {pages_to_scrape}")
        
        ## Commence scraping
        while page_num < pages_to_scrape:
            page_num += 1
            logging.debug(f"Attempting to scrape data from page {page_num}")
            request = SESSION.request("GET", f"{suburl}page/{page_num}/")
            soup = make_soup(request) 
            film_data += self.get_page_of_films(soup)

        return film_data

    @property
    def suburl(self):
        """ Construct a full suburl given the arguments passed to the init function.
        NOTE that letterboxd does not make use of URL parameters, so 
        the URL has to be constructed in this ugly manner.
        r-type: str
        """
        initial = "films/ajax/popular/"

        ## Add Years
        if self.year: 
            initial += f"year/{self.year}/"
        elif self.decade:
            initial += f"decade/{self.decade}/"

        ## Add Genres
        if self.genre: initial += f"genre/{self.genre}/"

        ## Finalise suburl
        final = initial + "size/small/"
        return final

    @property
    def num_pages(self):
        """ Return the number of pages in the selected search.
        r-type: int """
        request = SESSION.request("GET", self.suburl)
        soup = make_soup(request)

        h2_text = soup.find('h2', class_='ui-block-heading').text
        num_films = int(re.findall(r"([\d,]+)", h2_text)[0].replace(',', ''))
        num_pages = num_films//72+1
        return num_pages

    @staticmethod
    def get_page_of_films(soup):
        """ Return a list of dictionaries containing film data for a single page.
        r-type: list of dicts """
        divs = [i.find('div') for i in soup.find_all('li', class_=['listitem', 'poster-container'])]
        link_name_getter = lambda x: re.findall(r"/film/([\w\d:-]+)/", x)[0] # NOTE digits are necessesary e.g. /film/boat-2009/
        films = [ {'filmId': int(i.get('data-film-id')), 'link': link_name_getter(i.get('data-film-link'))} for i in divs ]
        return films

    
if __name__ == "__main__":

    F = FilmSearch(decade=1910, genre='horror', page_limit=None)
    data = F()