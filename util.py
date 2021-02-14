  
""" 
    Miscellaneous functions. 
"""

import json
import numpy as np

# Lists with common applications
yes_list = ['y', 'yes', 'yeah', 'confirm']
no_list = ['n', 'no', 'back', 'cancel']
quit_list = ['q', 'quit', 'exit', 'quit()', 'exit()', 'cls']

def load_json_data(file_name):
    """ Loads the data from a json file, returns it.
    r-type: dict 
    """
    try:
        with open(f"data/{file_name}.json") as jf:
            content = json.load(jf)
    except FileNotFoundError:
        return False
    return content

def yn(msg=None):
    """ While user's response is not in no/yes list, keeps prompting
    if in yes_list -> True
    elif in no_list -> False. """
    pre_string = "y/n:\n> "
    string = f"{msg} {pre_string}" if msg else pre_string
    while True:
        user_response = input(string)
        if user_response in quit_list:
            quit()
        elif user_response in yes_list:
            return True
        elif user_response in no_list:
            return False
        print("Sorry, I didn't understand your response!")

def list_of_unique_dicts(x):
    """ 
    Removes duplicate values from a list of dicts.
    """
    return list({v['filmId']:v for v in x}.values())


