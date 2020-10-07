import requests
from bs4 import BeautifulSoup as bs
import re
from session import SESSION

class FilmSearch():
    """ 
    Returns a list of obscure movie ids for which the rating range of the instance is True.
    An obscure movie is a movie that has yet to have received a great enough number of
    ratings to be given a number. These movies will always appear somewhere in the middle
    if you sort by rating. So this class allows you to bypass this. 
    """

    MAIN_URL = "https://letterboxd.com/"

    def __init__(self, with_titles=False, min_score=0.5, max_score=5, genre='horror', year=2020, service=None, results_limit=1, min_ratings=5): 
        
        # Edge cases
        if max_score < min_score:
            raise ValueError("max_score cannot be less than min_score!")
        try:
            if any([x*2 not in range(1, 11) for x in (min_score, max_score)]):
                raise ValueError("min_score and max_score must be within inclusive range 0.5 to 5")
        except TypeError:
            raise TypeError("min_score and max_score must be int/float values")

        # TODO ensure that genre is valid
        # TODO ensure that service is valid
        # TODO ensure that year is valid

        self.with_titles = False
        self.min_score = min_score
        self.max_score = max_score
        self.genre = genre
        self.year = year
        self.service = service
        self.results_limit = results_limit
        self.min_ratings = min_ratings

    @property
    def full_url(self):
        """ Construct a full URL given the arguments passed to the init function.
        NOTE that letterboxd does not make use of URL parameters, so 
        the URL has to be constructed in this ugly manner.
        """
        initial = f"{self.MAIN_URL}films/ajax/popular/"
        if self.year: initial += f"year/{self.year}/"
        if self.genre: initial += f"genre/{self.genre}/"
        final = initial + "size/small/"
        return final

    def __call__(self):

        print(self.full_url)
        request = SESSION.get(self.full_url)
        soup = bs(request.text, 'lxml')

        h2_text = soup.find('h2', class_='ui-block-heading').text
        num_films = int(re.findall(r"([\d,]+)", h2_text)[0].replace(',', ''))
        num_pages = num_films//72+1

        films = self.get_films(soup)

        page_num = 1
        while page_num < num_pages:
            
            if self.results_limit and len(films) > self.results_limit:
                break

            page_num += 1
            request = SESSION.get(f"{self.full_url}/page/{page_num}")
            soup = bs(request.text, 'lxml')

            print(f"Updating films with entries from page {page_num}/{num_pages}")

            if self.with_titles:
                films.update(self.get_films_with_titles(soup))
            else:
                films += (self.get_films(soup))
        
        return films

    @staticmethod
    def get_films(soup):
        divs = [i.find('div') for i in soup.find_all('li', class_=['listitem', 'poster-container'])]
        film_ids = [int(i.get('data-film-id')) for i in divs]
        return film_ids
        
    @staticmethod
    def get_films_with_titles(soup):
        divs = [i.find('div') for i in soup.find_all('li', class_=['listitem', 'poster-container'])]
        films = {int(i.get('data-film-id')): i.get('data-film-link') for i in divs}
        return films






if __name__ == "__main__":
    
    app = FilmSearch(genre='horror', year=2020)
    print(app())
