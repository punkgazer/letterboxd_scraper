import requests
from bs4 import BeautifulSoup as bs
import re

from session import SESSION, MAIN_URL
from letterboxd import GENRE_LIST




def construct_full_url(year, genre):
    """ Construct a full URL given the arguments passed to the init function.
    NOTE that letterboxd does not make use of URL parameters, so 
    the URL has to be constructed in this ugly manner.
    """
    initial = f"{MAIN_URL}films/ajax/popular/"
    if year: initial += f"year/{year}/"
    if genre: initial += f"genre/{genre}/"
    final = initial + "size/small/"
    return final

def get_films(soup):
    divs = [i.find('div') for i in soup.find_all('li', class_=['listitem', 'poster-container'])]
    film_ids = [int(i.get('data-film-id')) for i in divs]
    return film_ids
    
def get_films_with_links(soup):
    divs = [i.find('div') for i in soup.find_all('li', class_=['listitem', 'poster-container'])]
    films = {int(i.get('data-film-id')): i.get('data-film-link') for i in divs}
    return films

def get_film_ids(genre=None, year=None, page_limit=1):
    # Ensure valid arguments
    if year not in range(1860, 2030):
        raise ValueError(f"Inavlid year: {year}")
    if genre not in GENRE_LIST:
        raise ValueError(f"Invalid genre: {genre}")

    full_url = construct_full_url(year=year, genre=genre)
    request = SESSION.get(full_url)
    soup = bs(request.text, 'lxml')

    h2_text = soup.find('h2', class_='ui-block-heading').text
    num_films = int(re.findall(r"([\d,]+)", h2_text)[0].replace(',', ''))
    num_pages = num_films//72+1

    films = get_films(soup)



class FilmSearch():
    """ 
    Conducts a film search
    """

    def __init__(
            self, 
            with_links=False, 
            genre='horror', 
            year=2020, 
            page_limit=1, # Limit the number of results.
            min_ratings=5 # The minimum number of ratings the film must have received from users
        ): 

        if year not in range(1860, 2030):
            raise ValueError(f"Inavlid year: {year}")
        if genre not in GENRE_LIST:
            raise ValueError(f"Invalid genre: {genre}")

        self.with_links = with_links
        self.genre = genre
        self.year = year
        self.page_limit = page_limit
        self.min_ratings = min_ratings

    @property
    def full_url(self):
        """ Construct a full URL given the arguments passed to the init function.
        NOTE that letterboxd does not make use of URL parameters, so 
        the URL has to be constructed in this ugly manner.
        """
        initial = f"{MAIN_URL}films/ajax/popular/"
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
            
            if self.page_limit and len(films) > self.page_limit:
                break

            page_num += 1
            request = SESSION.get(f"{self.full_url}/page/{page_num}")
            soup = bs(request.text, 'lxml')

            print(f"Updating films with entries from page {page_num}/{num_pages}")

            if self.with_links:
                films.update(self.get_films_with_links(soup))
            else:
                films += (self.get_films(soup))
        
        return films

    @staticmethod
    def get_films(soup):
        divs = [i.find('div') for i in soup.find_all('li', class_=['listitem', 'poster-container'])]
        film_ids = [int(i.get('data-film-id')) for i in divs]
        return film_ids
        
    @staticmethod
    def get_films_with_links(soup):
        divs = [i.find('div') for i in soup.find_all('li', class_=['listitem', 'poster-container'])]
        films = {int(i.get('data-film-id')): i.get('data-film-link') for i in divs}
        return films






if __name__ == "__main__":
    
    app = FilmSearch(genre='horror', year=2020)
    print(app())








# # Edge cases
# try:
#     if max_score < min_score:
#         raise ValueError("max_score cannot be less than min_score!")
# except TypeError:
#     raise TypeError("min_score and max_score must be int/float values")
# if any([x*2 not in range(1, 11) for x in (min_score, max_score)]):
#     raise ValueError("min_score and max_score must be within inclusive range 0.5 to 5")