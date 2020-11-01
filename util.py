
# Local imports
import re

def replace_dict(a, b):
    changed_keys = set(a.keys()) & set(b.keys())
    return {k:v if k not in changed_keys else b[k] for k,v in a.items()}

def remove_full_stops(string):
    """ Removes full stops from a sentence IF they are NOT part of an acronym. """

    full_stop = '.'
    char_list = list(string)
    
    chars_deleted = 0
    for i, char in enumerate(string):
        if char != full_stop:
            continue
        
        # Allow full stop at beginning of string 
        if i in range(0,2):
            continue
        
        # If the character two previous was also a full stop
        # Then this is likely an acronym - allow
        if char_list[i-2] == full_stop or (i not in range(len(string)-2, len(string)) and string[i+2] == full_stop):
            continue

        # Otherwise remove the full stop from the char_list
        else:
            del char_list[i-chars_deleted]
            chars_deleted += 1

    # Convert the char_list back to a string and return
    return ''.join(char_list)

def merge_lists(lists):
    if type(lists) != list or any([type(i) is not list for i in lists]):
        raise TypeError("Must be list of lists")
    new_list = []
    while lists:
        [new_list.append(i) for i in lists.pop()]
    return new_list
    

        

