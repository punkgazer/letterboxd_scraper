
# Imports
import json
import re
from tqdm import tqdm

# Local Imports
from session import SESSION, make_soup, MAIN_URL
from film_search import FilmSearch
from film_rating import FilmRating
from util import replace_dict
from exceptions import LetterboxdException
from sentence_maker import SentenceMaker

class LetterboxdList():
    """ A class for creating and modifying a Letterboxd list. """

    save_url = 's/save-list'    

    def __init__(self, list_name, **kwargs):

        # This may be differnet to the actual list_name
        # For example if you create two lists (regardless of whether you delete one of them)
        # that are both called 'horror', the second list will have the url 'horror-1'
        self.user_defined_list_name = list_name

        # Edge cases
        if (soup := kwargs.get("soup")):
            self.soup = soup
        elif not list_name:
            raise Exception("No name given")
        else:
            # Load list
            self.soup = self.load(list_name)

    @classmethod 
    def new_list(cls, list_name, **kwargs):
        """ Create a list, given the list's parameters including
        list name at minimum. 
        
        Optional arguments:
        - description (str)
        - tags (list)
        - public (bool)
        - ranked (bool)
        - entries (???) # TODO
        """

        if not list_name:
            raise ValueError("Missing required field: list_name")

        default_values = {
            'tags': [],
            'public': False,
            'ranked': False,
            'description': '',
            'entries': []
        }

        # Add default values for any missing keys
        list_data = {i:j if i not in kwargs else kwargs[i] for i,j in default_values.items()}

        # Add the list_name and id 
        list_data['list_name'] = list_name
        list_data['list_id'] = ''

        post_data = cls.convert_data(list_data)

        ## Create list
        request = SESSION.request(
            "POST", 
            suburl=cls.save_url,
            headers={'referer': f'{MAIN_URL}list/new/'},
            data=post_data
        )
        soup = make_soup(request)

        cls.check_valid_soup(soup)

        ## Return instance of LetterboxdList
        return cls(None, soup=soup)

    @property
    def formatted_list_name(self):
        list_name = self.user_defined_list_name.lower()
        formatted_list_name = list_name.replace(' ', '-')
        formatted_list_name = formatted_list_name.replace('_', '')
        unknown_chrs = "|".join(set([c for c in formatted_list_name if not any( [c.isalpha(), c.isnumeric(), '-'] )]))
        
        # Replace characters which do not show in URL links with spaces
        formatted_list_name = re.sub(unknown_chrs, "", formatted_list_name)

        # Then replace any excess spaces
        formatted_list_name = re.sub(" +", " ", formatted_list_name).strip()
        return formatted_list_name


    def load(self, list_name):
        """ Load an instance for an existing list, given the list name. """
        
        list_name = list_name.replace(' ', '-')
        list_name = list_name.replace('_', '')
        unknown_chrs = "|".join(set([c for c in list_name if not any( [c.isalpha(), c.isnumeric(), '-'] )]))
        
        # Replace characters which do not show in URL links with spaces
        list_name = re.sub(unknown_chrs, "", list_name)

        # Then replace any excess spaces
        list_name = re.sub(" +", " ", list_name).strip()

        # Get edit URL
        edit_url = self.get_edit_url(list_name)

        # Set soup
        request = SESSION.get(edit_url)
        soup = make_soup(request)

        def check_page_found(soup):
            """ Returns True if page found. """
            if not (msg := soup.find('section', class_='message')):
                return True
            try:
                msg = msg.find('p').text
            except:
                raise Exception("Could not locate page. Raised fallback exception as could not Letterboxd message")
            else:
                raise LetterboxdException(str(msg))
            
        check_page_found(soup)
        return soup

    @staticmethod
    def get_edit_url(name, username=SESSION.username):
        """ Returns the suburl that is the list's edit page. """
        return f"{username}/list/{name.lower().replace(' ', '-')}/edit/"

    @staticmethod
    def get_view_url(name, username=SESSION.username):
        return f"{username}/list/{name.lower().replace(' ', '-')}/"

    @property
    def add_comment_url(self):
        """ Returns the suburl for adding a comment to a list. """
        return f's/filmlist:{self.list_id}/add-comment'

    def add_comment(self, comment):
        """ Adds a comment to the list. """
        SESSION.request("POST", self.add_comment_url, data={'comment': comment})

    def update(self, **kwargs):
        """ Update a list with new data. """
        if 'list_name' in kwargs:
            self.original_name = kwargs.pop('list_name')
        
        data = self.data

        # Replace any vars
        for k, v in kwargs.items():
            if k not in data.keys():
                raise KeyError(f"Unknown key: {k} with value {v}")
            elif k == "list_id":
                raise Exception("list_id cannot be modified!")
            data[k] = v

        current_attributes = self.data
        updated_attributes = replace_dict(current_attributes, data)
        post_data = self.convert_data(updated_attributes)

        request = SESSION.request(
            "POST", 
            suburl=self.save_url,
            data=post_data 
        )

        ## Update soup
        soup = make_soup(request)
        self.check_valid_soup(soup)
        self.soup = make_soup(request)

    def update_entries(self, entries, show_changes=False):

        if entries == self.entries:
            print("These entries are identical to the current list!")
            return

        if show_changes:

            extract_ids = lambda entries: [e['filmId'] for e in entries] 
            existing, new = set(extract_ids(self.entries)), set(extract_ids(entries))

            removed = existing - new
            added = new - existing

            film_names = self.get_film_names()
            removed_films = [film_names[_id] for _id in removed]
            added_films = get_names_of_entries(added).values()

            bolden = lambda x: f"<strong>{x}</strong>"
            comment = ''

            if removed_films:
                comment += f"{bolden('Removed')}:"
                comment += ''.join([f"\n- {v}" for v in removed_films])
                comment += "\n\n"

            if added_films:
                comment += f"{bolden('Added')}:"
                comment += ''.join([f"\n- {v}" for v in added_films])

            # Ensure no trailing whitespace
            comment = comment.strip()
            self.add_comment(comment)

        self.update(entries=entries)

    @property
    def data(self):
        """ Convert instance attributes into a dict that can be passed to update a list. """
        if not self.list_id:
            raise Exception("Cannot get data")
        return {
            'list_id': self.list_id,
            'list_name': self.formatted_list_name,
            'tags': self.tags,
            'public': self.public,
            'ranked': self.ranked,
            'description': self.description,
            'entries': self.entries
        }

    @staticmethod
    def convert_data(data):
        """ Converts data to that which can be passed to 
        save a list. """
        bool_to_str = lambda x: str(x).lower()
        return {
            'filmListId': str(data['list_id']),
            'name': data['list_name'],
            'tags': '',
            'tag': data['tags'],
            'publicList': bool_to_str(data['public']),
            'numberedList': bool_to_str(data['ranked']),
            'notes': data['description'],
            'entries': str(data['entries'])
        }

    @staticmethod
    def check_valid_soup(soup):
        try:
            response_dict = json.loads(soup.text)
            if not response_dict['result']:
                raise Exception(response_dict['messages'])
            else:
                pass
                # print(response_dict['result'])
        except:
            raise

    @property
    def list_id(self):
        return int(self.soup.find('input', attrs={'name': 'filmListId'}).get('value'))

    @property
    def list_name(self):
        return self.soup.find('input', attrs={'name': 'name'}).get('value')

    @property
    def description(self):
        description = self.soup.find('textarea', attrs={'name': 'notes'}).text
        return description if description else ''
    
    @property
    def tags(self):
        return [i.get('value') for i in self.soup.find_all('input', attrs={'name': 'tag'})]

    @property
    def ranked(self):
        return bool(self.soup.find('input', attrs={'id': 'show-item-numbers', 'checked':True}))
    
    @property
    def public(self):
        return bool(self.soup.find('input', attrs={'id': 'list-is-public', 'checked':True}))

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
    
    def get_film_names(self):
        """ Returns each id in the film list together with the corresponding film_name. """

        view_url = self.get_view_url(self.formatted_list_name)
        request = SESSION.request("GET", view_url)
        soup = make_soup(request)

        ul = soup.find('ul', class_='film-list')
        if not ul:
            return {}
        # {id: film_name}
        return {int(li.find('div').get('data-film-id')): li.find('img').get('alt') for li in ul.find_all('li')}

def get_names_of_entries(film_ids):
    """ Creates or edits a list used by the program which 
    is then used by this function to determine the names which
    correspond to the given ids. """

    temp_list_name = "__TEMPLIST"
    
    ## Try to ensure correct format of data
    # If not list of dicts, change list into dicts
    if not all([type(x) is dict for x in film_ids]):
        if not all(type(x) is int for x in film_ids):
            raise TypeError(f"Invalid input: {film_ids}. Expected list of dicts or list.")
        film_ids = [{'filmId': film_id} for film_id in film_ids]  

    try:
        temp_list = LetterboxdList(list_name=temp_list_name)
    except:
        try:
            temp_list = LetterboxdList.new_list(
                list_name=temp_list_name, 
                description="Please do not delete me!",
                public=False,
                entries=film_ids
                )
        except:
            raise Exception("Could not load or create list")
    else:
        temp_list.update_entries(entries=film_ids, show_changes=False)

    film_names = temp_list.get_film_names()
    return film_names



if __name__ == "__main__":

    # search = FilmSearch(year=1945, genre='animation', page_limit=None)
    # film_data = search()

    # final_data = []
    # for film in tqdm(film_data):
    #     print(f"\nBefore: {film}")
    #     fr = FilmRating(film['link'])
    #     if not fr.is_obscure:
    #         print("Film is not obsure")
    #         continue
    #     elif fr.total_ratings < 5:
    #         print("Too few ratings")
    #         continue
    #     final_data.append(dict(film, **{'review': fr.avg_rating}))
    #     print(f'Updated {film}')

    # final_data = sorted(final_data, key=lambda film: film['review'], reverse=True)

    # LetterboxdList.new_list(
    #     list_name="Popular Unpopular",
    #     description="Test list",
    #     public=False,
    #     entries=final_data
    # )


    # test_list = LetterboxdList("Movie Masochism #2!")
    # test_list.update(list_name="Movie Masochism #2")

    
    # sm = SentenceMaker("Whale you be a amazing friend. I wish you smashing birthday. P.S. you tattoo super sexy")
    # results = sm()

    # lucindas_list = LetterboxdList.new_list(
    #     list_name="LucyTest2",
    #     description="Testing for Lucy v2",
    #     public=False,
    #     entries=results
    # )

    # lucindas_list = LetterboxdList(list_name="LucyTest2")
    # print(lucindas_list.get_film_names())
    # # lucindas_list.update_entries(
    # #     [{'filmId': 160163}, {'filmId': 36145}, {'filmId': 51553}, {'filmId': 45163}])

    # test_list = LetterboxdList(list_name="And the hamster")

    # test_list.update_entries(
    #     entries = [{"filmId": 36145}, {"filmId": 160163}, {"filmId": 293076}]
    # )

    # temp_list_name = "__TEMPLIST"
    film_ids = [{"filmId": 36145}, {"filmId": 160163}]
    film_ids2 = [{"filmId": 190201}, {"filmId": 258924}]
    # t = LetterboxdList(list_name=temp_list_name)
    # t.update_entries(entries=film_ids2)

    # f = FilmSearch(genre="horror", decade=1910, page_limit=2)
    # films = f()

    test_list = LetterboxdList("__TEMPLIST")
    test_list.update_entries(entries=film_ids2, show_changes=True)



