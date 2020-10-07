
from session import SESSION
from bs4 import BeautifulSoup as bs

from film_search import FilmSearch

# NOTE Move this to make it global everywhere
MAIN_URL = "https://letterboxd.com/"

token = SESSION.cookies['com.xk72.webparts.csrf']
cookie_params = {'__csrf': token}

def list_maker(film_ids='[{"filmId":"51518"},{"filmId":"99758"}]', publicList=False):
    # name, film_ids, **kwargs
    
    data = {
        'filmListId': '',
        'name': 'test4',
        'tags': '',
        'tag': ['pyth', 'snake'],
        'publicList': str(publicList).lower(),
        'numberedList': 'true',
        'notes': 'Horror films released in the year of 2020',
        'entries': film_ids
        }

    request = SESSION.post(
        f"{MAIN_URL}s/save-list",
        headers={'referer': 'https://letterboxd.com/list/new/'},
        data=dict(cookie_params, **data)
    )

    soup = bs(request.text, 'lxml')
    print(soup)

def film_ids_to_list(film_ids):
    return str([{"filmId":str(i)} for i in film_ids]) 



F = FilmSearch()
film_ids = F()

film_ids = film_ids_to_list(film_ids)

list_maker(film_ids=film_ids)

