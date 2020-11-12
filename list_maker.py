
# Imports
import json
import re

# Local Imports
from session import SESSION, make_soup
import util

class LetterboxdList():
    """ A class for creating and modifying a Letterboxd list. """

    # URL for saving a list
    save_url = 's/save-list'

    def __init__(self, list_name, **kwargs):
        """ Initialise a LetterboxdList object
        Expects the name of the list.

        If you are creating a new_list, be sure to use the new_list alternative constructor,
        which will create the soup for the list upon creating the list,
        and will pass that soup to cls() to avoid making a double request. """
        
        # This may be differnet to the actual list_name
        # For example if you create two lists (regardless of whether you delete one of them)
        # that are both called 'horror', the second list will have the url 'horror-1'
        self.user_defined_list_name = list_name

        if (soup := kwargs.get("soup")):
            # If soup is passed, must be a new_list
            # Set the soup
            self.soup = soup
        elif not list_name:
            raise Exception("No name given")
        else:
            # Otherwise list must be loaded
            # Get the soup for the existing list
            self.soup = self.load(list_name)

    @classmethod 
    def new_list(cls, list_name, **kwargs):
        """ 
        ** Alternative Constructor **
        
        Creates a list, given the list's parameters including
        list name at minimum. 
        
        Optional arguments:
        - description (str)
        - tags (list)
        - public (bool)
        - ranked (bool)
        - entries (list of dicts)
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

        # Add the list_name and empty id
        list_data['list_name'] = list_name
        list_data['list_id'] = ''

        post_data = cls.convert_data(list_data)

        ## Create list
        request = SESSION.request(
            "POST", 
            suburl=cls.save_url,
            headers={'referer': f'{SESSION.MAIN_URL}list/new/'}, # TODO Remove?
            data=post_data
        )
        soup = make_soup(request)

        cls.check_valid_soup(soup)

        ## Return instance of LetterboxdList
        return cls(None, soup=soup)

    @property
    def formatted_list_name(self):
        """ Produces a formatted_list_name based on self.list_name
        The formatted_list_name is the expected url for the list. """
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
            self.user_defined_list_name = kwargs.pop('list_name')
        
        data = self.data

        # Ensure, if passed empty entries list, that it is empty list,
        # not another arbitrary none value equivalent 
        if 'entries' in kwargs.keys():
            if kwargs['entries'] == None: 
                kwargs['entries'] = []

        # Replace any vars
        for k, v in kwargs.items():
            if k not in data.keys():
                raise KeyError(f"Unknown key: {k} with value {v}")
            elif k == "list_id":
                raise Exception("list_id cannot be modified!")
            data[k] = v

        current_attributes = self.data
        updated_attributes = util.replace_dict(current_attributes, data)
        post_data = self.convert_data(updated_attributes)

        request = SESSION.request(
            "POST", 
            suburl=self.save_url,
            data=post_data 
        )

        ## Update soup
        edit_request = SESSION.request(self.get_edit_url(self.user_defined_list_name))
        soup = make_soup(edit_request)
        self.check_valid_soup(soup)
        self.soup = soup

    def update_entries(self, entries, show_changes=False):
        """ 
        Entries (dict)
        """

        if entries == self.entries:
            print("These entries are identical to the current list!")
            return

        if show_changes:
            
            if entries:
                # Grab ids from the passed entries variable
                extract_ids = lambda entries: [e['filmId'] for e in entries]

                # Create set for new and existing ids 
                existing = set(extract_ids(self.entries))
                new = set(extract_ids(entries)) if entries else set()

            removed = existing - new
            added = new - existing

            film_names = self.get_film_names()

            removed_films = None if not removed else [film_names[id_] for id_ in removed]
            added_films = None if not added else get_names_of_entries(added).values()

            bolden = lambda x: f"<strong>{x}</strong>"
            comment = ''

            ## NOTE that since we have already returned in case of identical entries,
            # There will be either added or removed films, so the comment should never be empty

            # Add removed films to comment string
            if removed_films:
                comment += f"{bolden('Removed')}:"
                comment += ''.join([f"\n- {v}" for v in removed_films])
                comment += "\n\n"

            # Add added films to comment string
            if added_films:
                comment += f"{bolden('Added')}:"
                comment += ''.join([f"\n- {v}" for v in added_films])

            # Ensure no trailing whitespace
            comment = comment.strip()
            # Edge case
            if not comment:
                raise Exception("Could not get comment!")
            
            ## Add comment
            if comment:
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
        # If list of ints, convert to dict for valid entries
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
    
    ## Change temp_list back to being empty
    temp_list.update_entries(entries=None)

    return film_names


if __name__ == "__main__":
    film_names = get_names_of_entries([464637, 148319, 363298, 364249, 456634, 65519])
    print(film_names)

    # test_list = LetterboxdList("__TEMPLIST")
    # print(test_list.data)


