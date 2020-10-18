
# Local Imports
from session import SESSION, make_soup, MAIN_URL
from film_search import FilmSearch
from film_rating import FilmRating
from util import replace_dict

import json

class LetterboxdList():
    """ A class for creating and modifying a Letterboxd list. """

    class Decorators():

        @classmethod
        def if_not_soup_return_false(self, func, *args, **kwargs):
            def inner(self):
                if not self.soup:
                    return False
                return func(*args, **kwargs)
            return inner

    save_url = 's/save-list'

    default_values = {
            'list_id': '',
            'tags': [],
            'public': False,
            'ranked': False,
            'description': '',
            'entries': []
        }

    def __init__(self, *args, **kwargs):
        
        # Edge cases
        if not any([args, kwargs]):
            raise AttributeError("No attributes passed!")
        elif all([args, kwargs]):
            raise AttributeError("You passed both args and kwargs. Please use the latter to create a new list")
        elif len(args) > 2:
            raise AttributeError("Invalid number of args. Use all keyword arguments to create a list")
        
        elif args:
            # Prexisting list
            self.soup = args[0]
        else:
            # New list
            self.__create(kwargs)

    def __create(self, list_attributes):
        """ Create a list, given the list's parameters including
        list name at minimum. """
        if not (list_name := list_attributes.pop('list_name')):
            raise ValueError("Missing required field: list_name")

        ## Convert data to post data
        default = self.default_values
        attributes = replace_dict(default, list_attributes)
        attributes['list_name'] = list_name
        post_data = self.convert_data(attributes)

        ## Create list
        request = SESSION.post(
            suburl=self.save_url,
            headers={'referer': f'{MAIN_URL}list/new/'},
            data=post_data
        )        

        ## Create soup
        self.soup = make_soup(request)

    @classmethod
    def load(cls, list_name):
        """ Load an instance for an existing list, given the list name. """
        ## Get edit URL
        edit_url = cls.get_edit_url(list_name)

        # Set soup
        request = SESSION.get(edit_url)
        soup = make_soup(request)

        return cls(soup)

    @staticmethod
    def get_edit_url(name, username=SESSION.username):
        return f"{username}/list/{name.lower().replace(' ', '-')}/edit/"

    def update(self, **kwargs):
        data = self.data

        # Replace any vars
        for k, v in kwargs.items():
            if k not in data.keys():
                raise KeyError(f"Unknown key: {k} with value {v}")
            data[k] = v

        current_attributes = self.data
        updated_attributes = replace_dict(current_attributes, data)
        post_data = self.convert_data(updated_attributes)

        request = SESSION.post(
            suburl=self.save_url,
            data=post_data 
        )

        ## Update soup
        self.soup = make_soup(request)

        self.check_valid_soup(self.soup)

    @property
    def data(self):
        """ Convert instance attributes into a dict that can be passed to update a list. """
        if not self.list_id:
            raise Exception("Cannot get data")
        return {
            'list_id': self.list_id,
            'list_name': self.list_name,
            'tags': self.tags,
            'public': self.public,
            'ranked': self.ranked,
            'description': self.description,
            'entries': self.entries
        }

    def convert_data(self, data):
        # Convert filmId to str
        # data['entries'] = [ {k:str(v) if k == "filmId" else v for k,v in i.items()} for i in data['entries'] ]
        return {
            'filmListId': str(data['list_id']),
            'name': data['list_name'],
            'tags': '',
            'tag': data['tags'],
            'publicList': self.bool_to_str(data['public']),
            'numberedList': self.bool_to_str(data['ranked']),
            'notes': data['description'],
            'entries': str(data['entries'])
        }

    @staticmethod
    def bool_to_str(b):
        return str(b).lower()

    @staticmethod
    def check_valid_soup(soup):
        try:
            response_dict = json.loads(soup.text)
            if not response_dict['result']:
                raise Exception(response_dict['messages'])
        except:
            pass

    @Decorators.if_not_soup_return_false
    @property
    def list_id(self):
        return int(self.soup.find('input', attrs={'name': 'filmListId'}).get('value'))

    @Decorators.if_not_soup_return_false
    @property
    def list_name(self):
        return self.soup.find('input', attrs={'name': 'name'}).get('value')

    @Decorators.if_not_soup_return_false
    @property
    def description(self):
        description = self.soup.find('textarea', attrs={'name': 'notes'}).text
        return description if description else ''
    
    @Decorators.if_not_soup_return_false
    @property
    def tags(self):
        return [i.get('value') for i in self.soup.find_all('input', attrs={'name': 'tag'})]

    @Decorators.if_not_soup_return_false
    @property
    def ranked(self):
        return bool(self.soup.find('input', attrs={'id': 'show-item-numbers', 'checked':True}))

    @Decorators.if_not_soup_return_false
    @property
    def public(self):
        return bool(self.soup.find('input', attrs={'id': 'list-is-public', 'checked':True}))

    @Decorators.if_not_soup_return_false
    @property
    def entries(self):
        """ Returns information for each film in the list. """

        def get_film_data(soup):
            """ Returns the data for an individual film in the entries. """
            film_id = int(soup.get('data-film-id'))
            notes = soup.find('input', attrs={'name': 'review', 'value': True}).get('value')
            if not notes:
                contains_spoilers = False
            else:
                contains_spoilers = bool(soup.find('input', attrs={'name': 'containsSpoilers', 'value': 'true'}))
            if notes:
                return {'filmId': film_id, 'review': notes, 'containsSpoilers': contains_spoilers}
            else:
                return {'filmId': film_id}

        list_items = self.soup.find_all('li', class_='film-list-entry')
        entries = [get_film_data(film) for film in list_items]
        return entries


if __name__ == "__main__":

    # test_list = LetterboxdList.load("1890s horror")
    # test_list.update(list_name="And the description")

    test_list2 = LetterboxdList(list_name="test101", description="this is a test creating a list", tags=['horror', 'minecraft'], ranked=True)
    print(test_list2.data)

