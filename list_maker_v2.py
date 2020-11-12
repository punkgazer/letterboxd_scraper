
# Imports
import json
import re

# Local Imports
from session import SESSION, make_soup
import util

class LetterboxdList():
    """ A class for creating and modifying a Letterboxd list.
    NOTE: For lists owned by the user, instead use the child class: MyList. """

    def __init__(self, name, username):
        """ Initialise the LetterboxdList object
        
        Parameters:
            - name (str) - the name of the list

        Keyword Arguments:
            - username (str) | defaults to user running this app
        
        If you are creating a new list, instead use the new_list constructor.
        """

        if username == SESSION.username and self.__class__.__name__ == "LetterboxdList":
            raise Exception("Use MyList for your own lists!")

        self.user_defined_name = name
        
        # Edge case - ensure that list name is string
        if not name or not isinstance(name, str):
            raise ValueError(f"list_name must be valid non-empty str, not {name}")

        self.soup = self.__load(username)

    @property
    def formatted_list_name(self):
        """ Produces a formatted_list_name based on self.list_name
        The formatted_list_name is the expected url for the list. 
        r-type: str """
        list_name = self.user_defined_name.lower()
        formatted_list_name = list_name.replace(' ', '-')
        formatted_list_name = formatted_list_name.replace('_', '')
        unknown_chrs = "|".join(set([c for c in formatted_list_name if not any( [c.isalpha(), c.isnumeric(), '-'] )]))
        
        # Replace characters which do not show in URL links with spaces
        formatted_list_name = re.sub(unknown_chrs, "", formatted_list_name)

        # Then replace any excess spaces
        formatted_list_name = re.sub(" +", " ", formatted_list_name).strip()
        return formatted_list_name

    def __load(self, username):
        """ Load an instance for an existing list, given the list name. """
        list_name = self.formatted_list_name
        view_list = f"{username}/list/{list_name}/"

        request = SESSION.request("GET", view_list)
        soup = make_soup(request)

        ## TODO: check page found

        return soup

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f"{cls_name}\n\tUsername: {self.username}\n\t {self.name} ({self.formatted_list_name})"

    def __str__(self):
        return f"{self.name}, a Letterboxd List from {self.username}"

    def __len__(self):
        """ Returns the number of entries in the list. """
        if not self.entries:
            return 0
        return len(self.entries)

    @property
    def view_list(self):
        return f"{self.username}/list/{self.name}"

    """
    ** List Attributes **
    """
    @property
    def username(self):
        """ Returns the username of the person who owns the list.
        r-type: str 
        """
        return self.soup.find('body', class_='list-page').get('data-owner')

    @property
    def name(self):
        """ Returns the name of the list.
        This should correspond exactly with the name you used when creating the list. 
        r-type: str
        """
        return self.soup.find('meta', attrs={'property': 'og:title'}).get('content')

    @property
    def tags(self):
        """ Returns the list of tags the list has.
        If the list has no tags, returns the empty list.
        r-type: list. """
        tags_list = self.soup.find('ul', class_='tags').find_all('li')
        return [i.text for i in tags_list]

    @property
    def ranked(self):
        """ Returns a bool value based on if the list is ranked.
        r-type: bool """
        if not self.entries:
            return False
        is_ranked = bool(self.soup.find('ul', class_='poster-list').find('li', class_=['numbered_list-item']))
        return is_ranked

    @property
    def description(self):
        """ Returns the list's description; keeps all whitespacing.
        r-type: str. """
        return self.soup.find('meta', attrs={'property': 'og:description'}).get('content')

    @property
    def entries(self):
        """ Returns the list's entries
        NOTE: this also includes any notes that have been added for each film. 
        r-type: list of dicts

        Example:
        {"filmId": 290472} """

        entries_list = self.soup.find('ul', class_='poster-container').find_all('li')
        entries = [int(i.get('data-film-id')) for i in entries_list]

        # Convert list to entries dict
        return [{"filmId": i} for i in entries]
    
    def add_comment(self):
        """ Adds a comment to the list. """
        pass

    def delete_comment(self):
        """ Deletes a specific comment from the list. """
        pass


class MyList(LetterboxdList):
    """ Subclass of LetterboxdList, specifically meant for lists
    which are owned by the user. """

    # URL for saving a list
    save_url = 's/save-list'

    def __init__(self, name):
        super().__init__(name, username=SESSION.username)

    def __load(self, name):
        list_name = self.formatted_list_name
        edit_url = f"{SESSION.username}/list/{list_name}/"

        request = SESSION.request("GET", edit_url)
        soup = make_soup(request)

        ## TODO: check page found
        return soup

    """
    Alternative Constructors
    """
    @classmethod
    def new_list(cls, name, **kwargs):
        """ 
        :: Alternative Constructor ::
        Creates a new list, as opposed to initialising this class
        regularly, which expects the list_name passed to already exist as a list on Letterboxd.

        This method makes a request first to create the list
        It then returns an instance in the regular way by calling the __init__ method(),
        which anticipates an existing list. Since we have already created the list, this is fine.

        Parameters:
            - name (str) - the name of the list 
        
        Optional Parameters
            - tags (list) - e.g. [horror, 1980s]
            - public (bool)
            - ranked (bool)
            - description (str) - e.g. "These are my favourite films"
            - entries (list of dicts) - films in the list and any notes about them
        """ 

        if not name or not isinstance(name, str):
            raise ValueError(f"list_name must be valid non-empty str, not {name}")
            
        # Default values for the list which will be used in the event
        # that they were not passed explicitly in kwargs
        default_values = {
            'tags': [],
            'public': False,
            'ranked': False,
            'description': '',
            'entries': []
        }

        ## Add default values for any missing keys
        list_data = {attribute: value if attribute not in kwargs else kwargs[attribute] 
            for attribute, value in default_values.items()}

        ## Add list_name and empty_id 
        # (the id_ will be generated automatically when making the list creation request)
        list_data['list_name'] = name
        list_data['list_id'] = ''

        ## Convert the list_data into values which can be passed to a request
        # This involves changing the types of some of the values.
        post_data = cls.make_post_data(list_data)

        ## Create list
        request = SESSION.request(
            "POST",
            suburl=cls.save_url,
            data=post_data 
        )

        # soup = make_soup(request)   
        # TODO cls.check_valid_soup()
        
        return cls(name)

    @classmethod
    def duplicate_list(self, list_to_copy, new_list_name):
        """
        :: Alternative Constructor ::
        Creates a new list based on an existing list.

        Parameters:
        - Existing List (LetterboxdList Object)
        """
        pass

    """
    ** Misc. 
    """
    @staticmethod
    def make_post_data(data):
        """ Converts data to that which can be passed to save a list. 
        r-type: dict """
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
        """ Checks to see if response_dict in the soup
        created from a response object indicates that 
        the request was successful.

        Parameters:
        - soup (BeautifulSoup object)
        
        Returns:
        - Returns True if the request was successful
        - Otherwise attempts to return the error messages given by Letterboxd
        within the response dict.
        - Failing this, returns a general erorr. """
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
    def edit_url(self):
        """ Returns the suburl that is the list's edit page. """
        return f"{self.username}/list/{self.name.lower().replace(' ', '-')}/edit/"

    """
    ** List Attributes **
    """
    @property
    def _id(self):
        """ Returns the list_id
        NOTE: the list_id cannot be set; it is assigned upon creation of the list. 
        r-type: int
        """
        return int(self.soup.find('input', attrs={'name': 'filmListId'}).get('value'))

    @property
    def public(self):
        """ Returns a bool value based on if the list is public.
        r-type: bool """
        return bool(self.soup.find('input', attrs={'id': 'list-is-public', 'checked':True}))

    """ 
    ** List Attributes (overloaded) 
    
    These properties have to be overloaded because, in MyList, we're working with
    a different soup.
    
    Whereas LetterboxdList makes use of the list view, 
    MyList makes use of the edit list view. 
    
    The reason for this change is that you (obviously) cannot edit someone else's list
    And the edit page makes things cleaner whilst also allowing more information to be grabbed
    Specifically the public/private status of the list, and the list-id, as defined above**
    """ 
    @property
    def name(self):
        return self.soup.find('input', attrs={'name': 'name'}).get('value')

    @property
    def tags(self):
        return [i.get('value') for i in self.soup.find_all('input', attrs={'name': 'tag'})]

    @property
    def ranked(self):
        return bool(self.soup.find('input', attrs={'id': 'show-item-numbers', 'checked':True}))

    @property
    def description(self):
        description = self.soup.find('textarea', attrs={'name': 'notes'}).text
        return description if description else ''

    @property
    def entries(self):
        """ Returns information for each film in the list.
        r-type: list of dicts """

        def get_film_data(soup):
            """ Returns the data for an individual film in the entries.
            This consists the film_id
            And, if one exists, the review (notes), and if the review (notes) contain spoilers
            
            r-type: dict
            """
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

    """
    ** Setter Methods **

    These setter method should be utilised if you want to change a single setting
    Otherwise, it's more efficient to use the update_values() method.
    """
    @name.setter
    def name(self):
        """ Setter for the list_name. """

    @tags.setter
    def tags(self):
        """ Setter for the tags. """

    @public.setter
    def public(self):
        """ Setter for whether a list is public/private. """

    @ranked.setter
    def ranked(self):
        """ Setter for whether a list is ranked or not. """

    @description.setter
    def description(self):
        """ Setter for the list's description. """

    """ 
    ** List Modifciation. ** 
    """
    def delete_list(self):
        """ Warning: this cannot be undone.
        Letterboxd is set up such that once you use a name, you
        cannot have a list with the same url again, even if you delete the list. 
        
        e.g. once you have deleted a list 'my-fav-films',
        creating a new list with the same name will produce
        a list with the url of my-fav-films-2
        """
        pass

    def update_values(self, **kwargs):
        """ Used to update one or more attributes for the list.
        However, to change a single attribute, using the setters may be easier.
        
        Optional Parameters
            - name (str)
            - tags (list)
            - public (bool)
            - ranked (bool)
            - description (str)
            - entries (list of dicts)

        NOTE: if you optional parameters are passed, the function simply returns
        """
        if not kwargs:
            return

    def replace_entries(self):
        """ Replace the entries of a list with the entries passed to this function. """
        pass

    def add_entries(self):
        """ Add to the current entries with the entries passed to this function. """
        pass

    def remove_entries(self):
        """ Removes all entries that currently exist in the list,
        and which occur in the passed entries list. """
        pass


def get_film_names(entries):
    """ 
    Creates or edits a list used by the program which 
    is then used by this function to determine the names which
    correspond to the given ids.

    Parameters:
    - Entries (entries dict / list of ids)

    Actions:
    - Creates a temporary list or edits one if it already exists:
        - Adds every film_id in the id list to the temp_list
        - Examines the new_list to get each list_name
    - Deletes all entries from the temp_list so it is empty again

    Returns:
    - Dictionary of list_ids and their corresponding names:
    r-type: dict
    """

    temp_list_name = "__TEMPLIST"

    ## Try to ensure correct format of data
    # List of dicts
    if not ( isinstance(entries, list) and all([type(x) is dict for x in entries]) ):
        # List of ints, where each int is assumed to be a film_id
        if not all([type(x) is int for x in entries]):
            # Invalid type
            raise TypeError(f"Invalid input. Expected list of dicts or list, not {entries}")
        # Convert to list of dicts
        film_ids = [{'filmId': film_id} for film_id in film_ids]

    try:
        pass
    except:
        # Create the temp_list
        try:
            pass
        except:
            # Could not create the temp_list
            raise
    finally:
        ## Update list
        pass


if __name__ == "__main__":
    
    other_list = LetterboxdList("1001 Movies You Must See Before You Die", "peterstanley")
    my_list = MyList("2020 ranked")

    print(other_list.name)
    print(my_list.name)


