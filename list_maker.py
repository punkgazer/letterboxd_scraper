""" 
    For working with Letterboxd lists. 
        - LetterboxdList (general class for lists on Letterboxd)
        - MyList (subclass for lists owned by the user)
"""

# Imports
import re

# Local Imports
from session import SESSION, make_soup
import util
from exceptions import LetterboxdException

import pendulum

# BUG: can change name of list but this messes up soup. The list updates, but properties of the instance do not update
    # because the load() method fails when called
    # NOTE: I think I fixed this # TODO double check

# TODO maybe move data to LetterboxdList as it's sometimes convenient to get all info about list at once
# TODO add get_film_names() code
# TODO edit list to sort by x (e.g. film release date)


class LetterboxdList():
    """ A list in Letterboxd. 
    For lists owned by user, use MyList for ability to modify/delete, etc. """
    
    def __init__(self, name, username):
        """
        Parameters:
            - name (str) - the name of the list
            - username (str)
        """
        # Edge case 
        if not name or not isinstance(name, str):
            raise TypeError(f"name must be valid non-empty str, not {name}")

        if username == SESSION.username and self.__class__.__name__ == "LetterboxdList":
            raise Exception("You should use MyList for your own lists!")

        # The user_defined_name is the original name passed to the instance, as opposed to the one grabbed from the property
        self.user_defined_name = name
        self.load(username)

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f"{cls_name}\n\tUsername: {self.username}\n\tName: {self.name} ({self.formatted_name})"

    def __str__(self):
        return f"{self.name}, a Letterboxd List from {self.username}"

    def __len__(self):
        """ Returns the number of entries in the list. """
        if not self.entries:
            return 0
        return len(self.entries)
        
    @property
    def formatted_name(self):
        """ Produces a formatted_name based on self.name
        The formatted_name is the expected url for the list. 
        r-type: str """
        list_name = self.user_defined_name.lower()
        formatted_name = list_name.replace(' ', '-')
        formatted_name = formatted_name.replace('_', '')

        # Get a set of unique characters which will not make up url for list page
        unknown_chrs = set([c for c in formatted_name if not any( [c.isalpha(), c.isnumeric(), c=='-'] )])
        # Make sure parenthesis are proceeded by a backslash, to avoid unmatched parenthesis error
        unknown_chrs = "|".join([i if i not in ("(", ")") else f"\{i}" for i in unknown_chrs])
        
        # Replace characters which do not show in URL links with spaces
        formatted_name = re.sub(unknown_chrs, "", formatted_name)

        # Then replace any excess spaces
        formatted_name = re.sub(" +", " ", formatted_name).strip()
        return formatted_name

    def load(self, username):
        """ load an instance for an existing list, given its name. """
        list_name = self.formatted_name
        view_list = f"{username}/list/{list_name}/"

        # Make request to list url on Letterboxd
        response = SESSION.request("GET", view_list)
        soup = make_soup(response)
        self.soup = soup

    @property
    def view_list(self):
        return f"{self.username}/list/{self.name}"

    """
    ** List Attributes **
    """
    @property
    def _id(self):
        """ Returns the list_id
        NOTE: the list_id cannot be set; it is assigned upon creation of the list. 
        r-type: int
        """
        list_id_string = self.soup.select_one("div[id*=report]").get('id') # *= means: contains
        pattern = r"-(\d+)$"
        try:
            match = int(re.findall(pattern, list_id_string)[0])
        except IndexError:
            raise Exception("Could not get id")
        else:
            return match

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
        return [i.text.strip() for i in tags_list]

    @property
    def ranked(self):
        """ Returns a bool value based on if the list is ranked.
        r-type: bool """
        if not self.entries:
            return False
        entries_list = self.soup.find('ul', class_='poster-list')
        numbered_entry = entries_list.find('li', class_='numbered-list-item')
        return bool(numbered_entry)

    @property
    def description(self):
        """ Returns the list's description; keeps all whitespacing.
        r-type: str. """
        return self.soup.find('meta', attrs={'name': 'description'}).get('content')

    @property
    def entries(self):
        """ Returns the list's entries
        NOTE: this also includes any notes that have been added for each film. 
        r-type: list of dicts
        Example:
        {"filmId": 290472} """

        entry_list_items = self.soup.find('ul', class_='poster-list').find_all('div')


        # Convert list to entries dict
        return [{"filmId": i.get('data-film-id')} for i in entry_list_items]

    """
    ** Comment Manipulation **
    """

    @property
    def add_comment_url(self):
        """ Returns the suburl for adding a comment to a list. """
        return f's/filmlist:{self._id}/add-comment'
    
    @property
    def comment_soup(self):
        """ Returns the soup containing information about the list's existing comments."""
        response = SESSION.request(
            "GET", f"csi/list/{self._id}/comments-section/?", 
            params={'esiAllowUser': True}
            )
        soup = make_soup(response)
        return soup

    @property
    def comments(self):
        """ Returns a dictionary of comments on the list. 
        Example: [{'username': 'LostInStyle', 'comment': 'Hello World', 'date_created':2020-11-15}]
        """
        body = self.comment_soup.find('div', class_='body')
        valid_comments = [i for i in body.find_all('li', attrs={'data-person': True})]
        
        if not valid_comments:
            return None

        def get_comment_text(suburl):
            """ Returns the body of the comment. """
            response = SESSION.request("GET", suburl)
            return make_soup(response).get_text()

        def convert_timestamp(timestamp):
            """ Convert the timestamp 'data-creation-timestamp' into a valid pendulum timestamp. """
            return pendulum.from_timestamp(timestamp)

        comments = [
            {
            'id': int(i['id'].split('-')[1]),
            'username': i['data-person'],
            'date_created': convert_timestamp( int(i['data-creation-timestamp'][:-3]) ),
            'comment': get_comment_text(i.find('div', class_='comment-body').get('data-full-text-url')),
            }
            for i in valid_comments]
        return comments

    @property
    def num_comments(self):
        # BUG: does not work!
        """ Returns the number of comments a list has received, not included any that have been removed. """
        if not self.comments:
            return 0
        data_comments_link = f"/{self.username.lower()}/list/{self.formatted_name}/#comments"
        num_comments_text = self.comment_soup.find('h2', attrs={'data-comments-link': data_comments_link}).text.strip()
        pattern = r"^\d+"
        try:
            match = re.findall(pattern, num_comments_text)[0]
        except IndexError:
            return 0
        else:
            return int(match)

    def add_comment(self, comment):
        """ Adds a comment to the list. """
        SESSION.request("POST", self.add_comment_url, data={'comment': comment})

    def delete_comment(self, comment_id):
        """ Deletes a comment on a list, given that comment's id. """
        # Edge cases
        if not (comments := self.comments):
            raise Exception("No comments to delete!")
        if type(comment_id) not in (str, int):
            raise TypeError(f"Invalid type for comment_id: {type(comment_id)}. Should be int")
        if isinstance(comment_id, str):
            comment_id = int(comment_id)

        if comment_id not in [i['id'] for i in comments]:
            raise Exception(f"Unable to locate id: {comment_id}")

        delete_comment_url = f"ajax/filmListComment:{comment_id}/delete-comment/"

        # Make post request to delete comment
        SESSION.request("POST", suburl=delete_comment_url)


class MyList(LetterboxdList):
    """ Subclass for Letterboxd Lists owned by the user.
    
    To Create a new list:
        use the new_list() constructor
    Otherwise, MyList expects list_name to already exist

    # Create
    # Delete
    # Edit
        # Set individual attribute (e.g. description)
        # Change multiple attributes (e.g. description, tags)
        # Add entries - add together two or more list entries
        # Subtract entries - remove entries from one list if part of one or more other lists.
        # Duplicate entries given a list
        # Merge entries given two or more lists
        # Clear entries
    """

    # For saving any list when modifying it
    save_url = 's/save-list'

    def __init__(self, name):
        super().__init__(name, username=SESSION.username)

    def load(self, *args):
        """ Overload of load from parent class.
        Uses the edit view rather than standard list view. """
        list_name = self.formatted_name
        edit_url = f"{SESSION.username}/list/{list_name}/edit"
        request = SESSION.request("GET", edit_url)
        soup = make_soup(request)
        self.soup = soup

    def __len__(self):
        """ Return the number of films in the list. """
        if not self.entries:
            return 0
        return len(self.entries)

    @staticmethod
    def make_post_data(data):
        """ Converts data to a dictionary that can be passed directly
        a save-list request.

        Parameters:
        - data (dict)
        
        r-type: dict
        """
        bool_to_str = lambda x: str(x).lower()

        return {
            'filmListId': str(data['list_id']),
            'name': data['name'],
            'tags': '',
            'tag': data['tags'],
            'publicList': bool_to_str(data['public']),
            'numberedList': bool_to_str(data['ranked']),
            'notes': data['description'],
            'entries': str(data['entries'])
        }
    
    """
    ** Alternative Constructors **
    """

    @classmethod
    def new_list(cls, name, **kwargs):
        """ 
        :: Alternative Constructor ::
        Creates a new list, as opposed to initialising this class
        regularly, which expects the name passed to already exist as a list on Letterboxd.
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

        # Edge case - list name passed is not of type string
        if not name or not isinstance(name, str):
            raise ValueError(f"list_name must be valid non-empty string, not {name}")

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
        # This involves changing the types of some of the values
        post_data = cls.make_post_data(list_data)

        ## Create list
        response = SESSION.request(
            "POST",
            suburl=cls.save_url,
            data=post_data 
        )

        if not response.ok:
            raise response.status_code
        
        return cls(name)

    """
    ** Misc **
    """
    @property
    def suburl_delete(self):
        """ The suburl used to make a request to delete a list. """
        return f"{self.username}/list/{self.formatted_name}/delete/"

    @property
    def data(self):
        """ Creates a dictionary of list attributes using the instance's properties
        grabbed from the soup. """
        try:
            data_dict = {
                'list_id': self._id,
                'name': self.name,
                'tags': self.tags,
                'public': self.public,
                'ranked': self.ranked,
                'description': self.description,
                'entries': self.entries
            }
        except Exception as e:
            raise Exception(f"Could not get data\n{e}")
        else:
            return data_dict

    """
    ** List Manipulation **
    """
    @staticmethod
    def __merge_entries(entries_lists, keep_notes=True):
        """ Given a nested list in the form
        [Lblist.entries, Lblist.entries, Lblist.entries, ...]
        Return the result of merging each list, keeping only filmId key, value pairs. """
        # Edge cases
        if not all( [isinstance(i, list) for i in entries_lists] ):
            raise TypeError("All arguments must be lists")
        if not entries_lists:
            raise Exception("No arguments provided")

        results = []
        
        if keep_notes:
            [[results.append(entry) for entry in entries] for entries in entries_lists]

            unique_film_ids = set([i['filmId'] for i in results])
            unique_results = []
            for i in results:
                if (film_id := i['filmId']) not in unique_film_ids:
                    continue
                unique_results.append(i)
                unique_film_ids.remove(film_id)

        else:
            [[results.append(entry['filmId']) for entry in entries] for entries in entries_lists]

            unique_film_ids = set(results)
            unique_results = []
            for i in results:
                if i not in unique_film_ids:
                    continue
                unique_results.append({'filmId': i})
                unique_film_ids.remove(i)

        return unique_results

    def delete_list(self):
        """ Deletes the list from Letterboxd. This cannot be undone! """
        if not util.yn("Are you sure you want to delete the list? This cannot be undone!"):
            return
        SESSION.request("POST", self.suburl_delete)

    def update_list(self, **kwargs):
        """ Update information about the list e.g. description, tags. """

        ## Replace any vars
        new_attrs = self.data
        for k, v in kwargs.items():
            if k not in new_attrs.keys():
                raise KeyError(f"Unknown key: {k} with value: {v}")
            elif k == "list_id":
                raise Exception("list_id cannot be modified")
            new_attrs[k] = v

        ## Update 
        # TODO IS THIS NECESSARY? ISN'T NEW_ATTRS ALREADY UPDATED_ATTRS?
        current_attrs = self.data
        updated_attrs = util.replace_dict(current_attrs, new_attrs)

        ## Convert data to post_data for request to update list on Letterboxd
        post_data = self.make_post_data(updated_attrs)

        ## Make post request to update data
        response = SESSION.request(
            "POST",
            suburl=self.save_url,
            data=post_data
        )

        """ Ensure that user_defined_name (which is called by self.formatted_name)
        is up to date, since it may have been changed with the postr request
        if kwarg 'name' was passed to the method. 
        """ 
        if 'name' in kwargs:
            self.user_defined_name = kwargs.pop('name')

        ## Make get request to update soup
        self.load()

    def clear(self):
        """ Remove all films from the list. """
        self.update_list(entries=[])

    def replace(self, *args):
        """ A -> B. """
        other = util.merge_lists([i.entries for i in args])
        merged_others = self.__merge_entries(other, keep_notes=False)
        self.update_list(entries=merged_others)

    # BUG: Problem I have now is that notes will be deleted for original list

    def merge(self, *args):
        """ A, B -> A + B """
        current = self.entries
        other = util.merge_lists([i.entries for i in args])
        merged_others = self.__merge_entries(other, keep_notes=False)
        
        final_pre_merge = [current, merged_others]
        final = self.__merge_entries(final_pre_merge)   
        self.update_list(entries=final)
        
    def diff(self, *args):
        """ A, B -> A - B """
        current = self.entries
        other = util.merge_lists([i.entries for i in args])
        merged_others = self.__merge_entries(other, keep_notes=False)
        
        remaining = [i for i in current if i['filmId'] not in [j['filmId'] for j in merged_others]]
        self.update_list(entries=remaining)

    """
    ** List Attributes **
    """
    @property
    def public(self):
        """ Returns a bool value based on if the list is public.
        r-type: bool """
        return bool(self.soup.find('input', attrs={'id': 'list-is-public', 'checked':True}))

    """ 
    ** List Attributes (overloaded) **
    
    These properties have to be overloaded because, in MyList, we're working with
    a different soup.
    
    Whereas LetterboxdList makes use of the list view, 
    MyList makes use of the edit list view. 
    
    Initially I considered the edit-list view to be superior.
    The information is more easily grabbed. However, it is possible to grab every necessesary attribute
    using the view-list soup alone (with the exception of the public status of the list)
    """ 
    @property
    def _id(self):
        """ Returns the list_id
        NOTE: the list_id cannot be set; it is assigned upon creation of the list. 
        r-type: int
        """
        return int(self.soup.find('input', attrs={'name': 'filmListId'}).get('value'))

    @property
    def username(self):
        return self.soup.find('body', class_='lists-edit').get('data-owner')

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
                return {'filmId': film_id}
            contains_spoilers = bool(soup.find('input', attrs={'name': 'containsSpoilers', 'value': 'true'}))
            return {'filmId': film_id, 'review': notes, 'containsSpoilers': contains_spoilers}

        list_items = self.soup.find_all('li', class_='film-list-entry')
        entries = [get_film_data(film) for film in list_items]
        return entries

    """
    ** Setter Methods **
    These setter method should be utilised if you want to change a single setting
    Otherwise, it's easier and more efficient to use the update_values() method.
    """
    @name.setter
    def name(self, name):
        """ Setter for the name. """
        # Edge case
        if not isinstance(name, str):
            raise TypeError(f"Invalid type for value: {type(name)}. Must be str")

        # Make post request to update name
        self.update_list(name=name)

    @tags.setter
    def tags(self, tags, append=False):
        """ Setter for the tags. 
        Keyword parameters:
            - append (bool)
                # If True, the tags will not be replaced; they will be added to.  
        """
        # Edge case
        if not isinstance(tags, list):
            raise TypeError(f"Invalid type for tags: {type(tags)}. Must be list.")
        if append: tags = self.tags + tags

        # Make post request to update tags
        self.update_list(tags=tags)

    @public.setter
    def public(self, value):
        """ Setter for whether a list is public/private. """
        # Edge case
        if not isinstance(value, bool):
            raise TypeError(f"Invalid type for value: {type(value)}. Must be bool.")

        # No change
        # e.g. method was passed True, when list was already public
        if value is self.public:
            print(f"List was already set to {self.public}")
            return

        # Make post request to update public/private status
        self.update_list(public=value)

    @ranked.setter
    def ranked(self, value):
        """ Setter for whether a list is ranked or not. """
        # Edge case
        if not isinstance(value, bool):
            raise TypeError(f"Invalid type for value: {type(value)}. Must be bool.")

        # No change
        # e.g. method was False, when list was already not ranked
        if value is self.ranked:
            print(f"List was already set to {self.ranked}")
            return
        
        # Make post request to update ranked/unranked status
        self.update_list(ranked=value)

    @description.setter
    def description(self, text, append=False):
        """ Setter for the tags. 
        Keyword parameters:
            - append (bool)
                If True, the description will not be replaced; the text will be 
                    appended onto the end.  
        """
        # Edge case
        if not isinstance(text, str):
            raise TypeError(f"Invalid type for value: {type(text)}. Must be str")
        if append: text = self.description + text

        # Make post request to update description
        self.update_list(description=text)

    """
    ** Overloading comments methods 
    """
    def add_comment(self, comment):
        """ Checks against the edge case to ensure that list is public,
        before calling regular parent method to add the passed comment to the list 
        """
        if not self.public:
            raise LetterboxdException("Cannot add comment to private list!")
        super().add_comment(comment)


if __name__ == "__main__":

    ## Testing code

    # test_list = LetterboxdList("Hooptober 2020!", "thegarfofficial")
    # test_list2 = LetterboxdList("top 100", "jameshealey")

    # test_list = MyList("anti letterboxd 250 ranked")
    # print(test_list.name)
    # print(test_list.user_defined_name)
    # print(test_list.description)
    # print(test_list.tags)
    # print(test_list.public)
    # print(test_list.ranked)
    # print(test_list.formatted_name)
    # print(test_list.entries)

    test_list = MyList("test003")
    # hooptober = LetterboxdList("Hooptober 2020!", "thegarfofficial")
    steve_quick = LetterboxdList("Michael Adams' 20 Worst Films", "stevequick")



    # movie_m1 = MyList("Movie Masochism #1 (Complete)")
    # movie_m2 = MyList("movie-masochism #2")
    # anti_lb = MyList("Anti-Letterboxd 250 Ranked")

    # test_list.merge(movie_m1, movie_m2)
    # test_list.replace(hooptober)
