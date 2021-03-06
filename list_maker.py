""" 
    For working with Letterboxd lists. 
        - LetterboxdList (general class for lists on Letterboxd)
        - MyList (subclass for lists owned by the user)

    NOTE: throughout this module, the word 'entries' 
    is used to refer to films within a list. 
"""

# Imports
import re
import pendulum

# Local Imports
from session import SESSION, make_soup
import util
from exceptions import LetterboxdException

import itertools


# TODO edit list to sort by x (e.g. film release date)

# BUG forward/back(?) slashes in name result in 404 not found

## TODO __show_changes()
    # BUG: prints out duplicates in comment (not sure why - ids are sets. Possibly multiple films with same name?)
    # TODO: print links to films rather than just names
    # TODO: order films alphabetically


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
        """ TODO write out format """
        cls_name = self.__class__.__name__
        return f"{cls_name}\n\tUsername: {self.username}\n\tName: {self.name} ({self.get_formatted_name()})"

    def __str__(self):
        return f"{self.name}, a Letterboxd List from {self.username}"

    def __len__(self):
        """ Returns the number of entries in the list. """
        if not self.entries:
            return 0
        return len(self.entries)

    def __add__(self, other):
        entries = self.entries
        entries.update(other.entries)
        return {'filmId': x for x in set(entries.values())}
        
    def get_formatted_name(self):
        """ Produces a formatted_name based on self.name
        The formatted_name is the expected url for the list. 
        r-type: str """
        list_name = self.user_defined_name.lower()
        formatted_name = list_name.replace(' ', '-')

        # Get a set of unique characters which will not make up url for list page
        unknown_chrs = set([c for c in formatted_name if not any( [c.isalpha(), c.isnumeric(), c in ('-', '_')] )])
        # Make sure parenthesis are proceeded by a backslash, to avoid unmatched parenthesis error
        unknown_chrs = "|".join([i if i not in ("(", ")") else f"\{i}" for i in unknown_chrs])
        
        # Replace characters which do not show in URL links with spaces
        formatted_name = re.sub(unknown_chrs, "", formatted_name)

        # Then replace any excess spaces
        formatted_name = re.sub(" +", " ", formatted_name).strip()
        return formatted_name

    def load(self, username):
        """ load an instance for an existing list, given its name. """
        list_name = self.get_formatted_name()
        view_list = f"{username}/list/{list_name}/"

        # Make request to list url on Letterboxd
        response = SESSION.request("GET", view_list)
        soup = make_soup(response)
        self.soup = soup

    """
    ** Misc. **
    """
    @property
    def view_list(self):
        return f"{self.username}/list/{self.get_formatted_name()}/"

    @property
    def data(self):
        """ Creates a dictionary of list attributes using the instance's properties
        grabbed from the soup. """
        try:
            data_dict = {
                'list_id': self._id,
                'name': self.name,
                'tags': self.tags,
                'ranked': self.ranked,
                'description': self.description,
                'entries': self.entries
            }
        except Exception as e:
            raise Exception(f"Could not get data\n{e}")
        else:
            return data_dict

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
        if not (tags_ul := self.soup.find('ul', class_='tags')):
            # The tags list could not be found - there are no tags
            return []
        tags_list = tags_ul.find_all('li')
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
        return [{"filmId": int(i.get('data-film-id'))} for i in entry_list_items]

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
        """ Returns the number of comments a list has received, not included any that have been removed. """
        if not self.comments:
            return 0
        data_comments_link = f"/{self.username.lower()}/list/{self.get_formatted_name()}/#comments"
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

    """
    ** Film names **
    """
    def get_page_of_film_names(self, page_num):
        """ Returns a dictionary 
            key: film_id
            value: film_name
        for all the films on that page of the list. 
            
        Example: {film_id: film_name}
        """
        response = SESSION.request("GET", f"{self.view_list}page/{page_num}/")
        soup = make_soup(response)

        ul = soup.find('ul', class_='film-list')
        page_results = {int(li.find('div').get('data-film-id')): li.find('img').get('alt') for li in ul.find_all('li')} 
        return page_results

    def get_film_names(self):
        """ Returns each id in the film list together with the corresponding film_name. """

        response = SESSION.request("GET", self.view_list)
        soup = make_soup(response)

        if not ( page_navigator := soup.find('div', class_='pagination') ):
            last_page = 1
        else:
            last_page = int(page_navigator.find_all('li', class_='paginate-page')[-1].find('a').text)

        current_page = 1
        results = {}
        while current_page <= last_page:
            page_results = self.get_page_of_film_names(current_page)
            if not page_results:
                break
            results.update(page_results)
            current_page += 1

        return results


class MyList(LetterboxdList):
    """ Subclass for Letterboxd Lists owned by the user.
    
    To Create a new list:
        use the new_list() constructor
    Otherwise, MyList expects list_name to already exist

    # TODO Copy List Constructor

    # Create
    # Delete
    # Edit
        # Set individual attribute (e.g. description)
        # Change multiple attributes (e.g. description, tags)
        # Merge entries (add entries to a list)
        # Diff (subtract entries from a list)
        # Merge entries given two or more lists
        # Clear entries
    # Comment
        # Add
        # Delete
    """
    
    # This url is used when making the request to make changes to a list
    save_url = 's/save-list'

    def __init__(self, name):
        """ Initialise using the parent __init__ method,
        but pass the username as the session's username (hence, MyList). """
        super().__init__(name, username=SESSION.username)

    def load(self, *args):
        """ Overload of load from parent class.
        Uses the edit view rather than standard list view. """
        list_name = self.get_formatted_name()
        edit_url = f"{SESSION.username}/list/{list_name}/edit"
        request = SESSION.request("GET", edit_url)
        soup = make_soup(request)
        self.soup = soup

    """
    ** Misc **
    """
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

    @property
    def suburl_delete(self):
        """ The suburl used to make a request to delete a list. """
        return f"{self.username}/list/{self.get_formatted_name()}/delete/"

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
    ** Alternative Constructors **
    """
    @classmethod
    def new(cls, name, **kwargs):
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

        # Edge case - list name passed is not type string
        if not name or not isinstance(name, str):
            raise TypeError(f"name must be non-empty string, not {name}")

        # Default values for the list which will be used
        # in the event that the corresponding keyword arguments are not provided
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
        list_data['name'] = name
        list_data['list_id'] = ''

        ## Convert the list_data into values which can be passed to a request
        # This involves changing the types of some of the values
        post_data = cls.make_post_data(list_data)

        ## Create list
        SESSION.request(
            "POST",
            suburl=cls.save_url,
            data=post_data 
        )

        # Since the list has been created, creating an instance should now work
        # the same way that it would with any existing list
        return cls(name)

    @classmethod
    def copy(cls, name, other):
        """ 
        :: Alternative Constructor ::

        Given the name you want for the copied list,
        and another list from which the entries can be extracted,
        Returns the new resulting list.

        Example:
        If you passed 'turtles' fav_films list, this method would
        return a new list called turtles, with the same films in it
        as the fav_films list.

        Actions:
        Calls the other alternative constructor to create a new list
        with a new name, but the existing entries of the given, existing list.

        Parameters:
        - name (str) - the name of the new copy list
        - other (LetterboxdList or MyList) - a LBList object from which the entries
            can be extracted to this new list.
        """
        if not other.__class__.__name__ in ("MyList", "LetterboxdList"):
            raise TypeError("Other must be a LetterboxdList or MyList object to copy from")
        return cls.new(name, entries=other.entries)

    """
    ** List Manipulation **
    """
    def __merge_entries(self, *entries_lists, keep_notes=True):
        """ Given a nested list in the form
        [Lblist.entries, Lblist.entries, Lblist.entries, ...]
        Return the result of merging each list, keeping only filmId key, value pairs. """
        # Edge cases
        if not all( [isinstance(i, list) for i in entries_lists] ):
            raise TypeError(f"All arguments must be lists, not {entries_lists}")
        if not entries_lists:
            raise Exception("No arguments provided")

        results = []
        
        if keep_notes:
            [[results.append(entry) for entry in entries] for entries in entries_lists]
            # must be a list of lists still somehow

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

    def __show_changes(self, new_entries):
        """ Records the changes to a list in terms of film entries, by adding a comment
        just before making the change, that says which films were removed and/or added.
        
        Parameters:
            new (list of dicts) - an entries list

        Actions:
            Comments about changes to list entries just before making the change
        """

        if not self.public:
            raise Exception("Cannot show changes on private list")

        print(f"Showing changes for {self.name}...")

        extract_ids = lambda entries: set([e['filmId'] for e in entries]) if entries else set()

        ## Get only the film ids so that items can be compared w/out notes
        new = extract_ids(new_entries)
        old = extract_ids(self.entries)

        ## If there are no changes, just return
        if set(new) == set(old):
            print("No changes")
            return

        ## Get the ids of the films to be added/removed
        added_ids = new - old
        removed_ids = old - new

        ## Get the respective names
        added_names = get_film_names(added_ids).values()

        current_film_names = self.get_film_names()
        removed_names = [current_film_names[k] for k in removed_ids]

        bolden = lambda x: f"<strong>{x}</strong>"
        comment = ''

        ## NOTE that since we have already returned in case of identical entries,
        # There will be either added or removed films, so the comment should never be empty

        # Add removed films to comment string
        if removed_ids:
            comment += f"{bolden('Removed')}:"
            comment += ''.join([f"\n- {v}" for v in removed_names])
            comment += "\n\n"

        # Add added films to comment string
        if added_ids:
            comment += f"{bolden('Added')}:"
            comment += ''.join([f"\n- {v}" for v in added_names])

        # Ensure no trailing whitespace
        comment = comment.strip()

        # Edge case
        if not comment:
            raise Exception("Could not get comment!")
        else:
            # Add comment
            self.add_comment(comment)

    def delete(self):
        """ Deletes the list from Letterboxd. This cannot be undone!
        NOTE: after deleting a list, the instance will become unusable. 
        """
        if not util.yn("Are you sure you want to delete the list? This cannot be undone!"):
            return
        SESSION.request("POST", self.suburl_delete)
        self.soup = None

    def update(self, show_changes=False, **kwargs):
        """ Modify one or more attributes of the list, including entries.
        It is called by methods which deal strictly with modifying entries,
        namely replace, add and subtract. """

        if any(unknown_keys := [k for k in kwargs if k not in self.data.keys()]):
            raise KeyError(f"Unknown keys: {unknown_keys}")

        new_attrs = {k:v if k not in kwargs else kwargs[k] for k,v in self.data.items()}

        if show_changes and 'entries' in new_attrs.keys():
            self.__show_changes(new_attrs['entries'])

        ## Convert the data into post_data for request to update list on Letterbox 
        post_data = self.make_post_data(new_attrs)

        # Make post request to update data
        r = SESSION.request(
            "POST",
            suburl=self.save_url,
            data=post_data
        )

        ## Update user-defined name to allow loading to work if list has been renamed
        if 'name' in new_attrs: 
            self.user_defined_name = new_attrs['name']

        ## Make get request to update soup
        self.load()

    def clear(self):
        """ 
        A -> []
        Clears all entries in a list. """
        self.update(entries=[])

    def replace(self, *args, show_changes=False):
        """ 
        A, B -> B        
        Replace any existing entries with the passed list(s) of entries. """
        
        # Merge the replacement lists together
        merged_others = self.__merge_entries(*args, keep_notes=False)
        
        # Update the list by replacing the current entries with the merged_others
        self.update(entries=merged_others, show_changes=show_changes)

    def append(self, *args, show_changes=False):
        """ 
        A, B -> A + B
        Add to any existing entries with the passed list(s) of entries. """
        current = self.entries
        merged_others = self.__merge_entries(*args, keep_notes=False)

        combined = self.__merge_entries(*[current, merged_others], keep_notes=True)
        self.update(entries=combined, show_changes=show_changes)

    def remove(self, *args, show_changes=False):
        """
        A, B -> A - B
        Subtract passed list(s) of entries from any entries which exist in the list currently. """
        current = self.entries
        merged_others = self.__merge_entries(*args, keep_notes=False)

        # Subtract the merged_others (other entries) from the existing entries
        remaining = [i for i in current if i['filmId'] not in [j['filmId'] for j in merged_others]]

        self.update(entries=remaining, show_changes=show_changes)

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
        return '' if not description else description

    @property
    def entries(self):

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
    ** Setter Methods
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
        self.update(name=name)

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
        self.update(tags=tags)

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
        self.update(public=value)

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
        self.update(ranked=value)

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
        self.update(description=text)

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


def get_film_names(film_ids):
    """ Creates or edits a list used by the program which 
    is then used by this function to determine the names which
    correspond to the given ids. """

    ## Try to ensure correct format of data
    # If not list of dicts, change list into dicts
    if not all([type(x) is dict for x in film_ids]):
        if not all(type(x) is int for x in film_ids):
            raise TypeError(f"Invalid input: {film_ids}. Expected list of dicts or list.")

        # If list of ints, convert to entries format (list of dicts)
        film_ids = [{'filmId': film_id} for film_id in film_ids]
    
    try:
        temp_list = MyList(name="test003")
    except:
        try:
            temp_list = MyList.new(
                name=temp_list_name, 
                description="Please do not delete me!",
                public=False,
                entries=film_ids
                )
        except:
            raise Exception("Could not load or create list")
    else:
        print("Successfully loaded temp_list")
    finally:
        temp_list.update(entries=film_ids)

    film_names = temp_list.get_film_names()
    
    ## Change temp_list back to being empty
    temp_list.clear()

    return film_names 


if __name__ == "__main__":
    pass
    # steve_quick = LetterboxdList("Michael Adams' 20 Worst Films", "stevequick")
    # print(steve_quick.data)

    # test_list = MyList("test003")
    # print("old name:", test_list.name)
    # test_list.name = "test003"
    # print("new name:", test_list.name)
    # print("new data:", test_list.data)

    ## --- Get updated horror list ---
    # from film_search import FilmSearch
    # horror_list = MyList("Horror 2020")
    # horror_update = FilmSearch(genre="Horror", year=2020, page_limit=None)
    # horror_list.replace(horror_update(), show_changes=True)

    ## --- Create new horror list ---
    # from film_search import FilmSearch

    # horror_list = MyList.new(
    #     name="Horror ajshajosgho", 
    #     tags=["horror", "2021", "2021 horror", "horror 2021", "complete", "full"],
    #     ranked=True,
    #     public=False,
    #     description="Horror films planned to be released in the year 2021.",
    #     entries=FilmSearch(genre="Horror", year=2021, page_limit=None).__call__()
    #     )

    ## --- Create new romance list ---
    from film_search import FilmSearch

    # romance_list = MyList.new(
    #     name="Romance 2020",
    #     tags = ["romance", "2020", "2020 romance", "romance 2020", "complete", "full"],
    #     public=True,
    #     description="Romance films released (or planned to be released) in the year of 2020.",
    #     entries=FilmSearch(genre="Romance", year=2020, page_limit=None).__call__()
    # )

    ## --- Get crossover list ---

    horror_entries = FilmSearch(genre="Horror", year=2020, page_limit=None).__call__()
    print(horror_entries)
    quit()
    
    romance_entries = FilmSearch(genre="Romance", year=2020, page_limit=None).__call__()

    def alternate_combine(list1, list2):
        return [x for x in itertools.chain.from_iterable(itertools.zip_longest(list1, list2)) if x]

    full_entries = alternate_combine(horror_entries.values(), romance_entries.values())

    horror_romance_crossover = MyList.new(
        name="Horror-Romance 2020 test",
        tags = ["romantic horror", "horror romance", "2020", "date movie", "crossover", "complete", "full"],
        public=False,
        ranked=True,
        description="Horror-Romance films released (or planned to be released) in the year of 2020.",
        entries=full_entries
    )



